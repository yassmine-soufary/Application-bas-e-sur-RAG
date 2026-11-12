import json
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.config import ROOT, Settings
from app.models import Chunk, IngestRequest, QuestionRequest, SearchHit
from app.chunking import fixed, chunk_documents
from app.extraction import extract, digest
from app.amendments import relationships, expand
from app.rag import Rag, REFUSAL, validate, attach_citations, complete_context
from app.provider import ProviderError, Provider
from app.store import Store, StoreError
from app.main import create_app


@pytest.fixture(scope='module')
def docs():
    return extract()


@pytest.fixture
def hit():
    return SearchHit(chunk=Chunk(id='c1', file='test.pdf', reference='TEST-REG-2026',
        type='Règlement', date='2026-01-01', page=3, section='Article 1',
        text='La durée minimale est de quatre semaines.'), score=.9)


@pytest.mark.parametrize('size,overlap', [(0, 0), (5, -1), (5, 5), (-1, 0)])
def test_fixed_invalid(size, overlap):
    with pytest.raises(ValueError):
        fixed('abc', size, overlap)
    with pytest.raises(ValidationError):
        IngestRequest(chunk_size=size, overlap=overlap)


def test_fixed_overlap():
    assert fixed('abcdefghij', 6, 2) == ['abcdef', 'efghij']


def test_actual_metadata_pages_and_integrity(docs):
    assert len(docs) == 7
    assert [len(d['pages']) for d in docs] == [4, 3, 3, 2, 3, 2, 2]
    assert docs[-1]['date'] == '2026-10-05'
    assert docs[1]['version'] == '3.0'
    assert all([p['page'] for p in d['pages']] == list(range(1, len(d['pages'])+1)) for d in docs)
    manifest = json.loads((ROOT / 'data/corpus_manifest.json').read_text(encoding='utf8'))
    assert all(digest(ROOT / 'data/corpus' / name) == sha for name, sha in manifest.items())


def test_structural_keeps_article_and_faq(docs):
    chunks = chunk_documents(docs, IngestRequest())
    article = [c for c in chunks if c.reference == docs[0]['reference'] and c.section.startswith('Article 17')]
    assert len(article) == 1
    assert '180 crédits' in article[0].text and 'B2' in article[0].text
    faq = [c for c in chunks if c.section.startswith('Q4.')]
    assert len(faq) == 1 and '48' in faq[0].text and 'plafonnée' in faq[0].text
    assert faq[0].page == 1
    assert len({c.id for c in chunks}) == len(chunks)
    assert chunks == chunk_documents(docs, IngestRequest())


def test_tables_have_headers(docs):
    rows = [b for p in docs[2]['pages'] for b in p['blocks'] if b['kind'] == 'table']
    assert any('Places : 4' in b['text'] and 'Valmorel' in b['text'] for b in rows)


def test_modifications_generic_and_scope(docs):
    chunks = chunk_documents(docs, IngestRequest())
    links = relationships(chunks)
    assert links == {docs[-1]['reference']: {docs[1]['reference']}}
    old = next(c for c in chunks if c.file == docs[1]['file'] and c.section.startswith('5.3'))
    expanded, edges = expand([SearchHit(chunk=old, score=.8)], chunks)
    assert edges
    assert any('1er février 2027' in h.chunk.text and h.chunk.page == 2 for h in expanded)
    # Renaming references leaves discovery functional; date alone never establishes a link.
    renamed = [c.model_copy(update={'reference': c.reference.replace('EIH', 'XYZ'),
               'status': c.status.replace('EIH', 'XYZ'), 'text': c.text.replace('EIH', 'XYZ')}) for c in chunks]
    assert 'XYZ-DE-NS-2026-14' in relationships(renamed)
    without_explicit_status = [c.model_copy(update={'status': 'En vigueur'}) for c in chunks]
    assert relationships(without_explicit_status) == {}


def test_citation_validation(hit):
    good = {'found': True, 'claims': [{'text': 'Quatre semaines [1].', 'evidence': [{'source': 1, 'quote': 'quatre semaines'}]}]}
    assert validate(good, [hit]) == (True, [], [1])
    bad = {'found': True, 'claims': [{'text': 'Quatre semaines [99].', 'evidence': [{'source': 99, 'quote': 'inventé'}]}]}
    assert validate(bad, [hit])[1] == [99]
    good['claims'][0]['evidence'][0]['quote'] = 'dix semaines'
    assert validate(good, [hit])[0] is False


def test_no_llm_under_threshold(hit):
    store, provider = Mock(), Mock()
    store.search.return_value = [hit.model_copy(update={'score': .1})]
    answer = Rag(Settings(), provider, store).ask(QuestionRequest(question='Hors corpus ?'))
    assert not answer.found and answer.answer == REFUSAL
    provider.structured.assert_not_called()


def test_citations_rendered_from_real_evidence(hit):
    generated = {'found': True, 'claims': [{'text': 'La durée minimale est de quatre semaines.',
        'evidence': [{'source': 1, 'quote': 'quatre semaines'}]}]}
    prepared = attach_citations(generated)
    assert prepared['claims'][0]['text'] == 'La durée minimale est de quatre semaines [1].'
    assert generated['claims'][0]['text'].endswith('semaines.')
    assert validate(prepared, [hit]) == (True, [], [1])
    provider, store = Mock(), Mock()
    store.search.return_value = [hit]
    store.all_chunks.return_value = [hit.chunk]
    provider.structured.side_effect = [generated, {'supported': True}]
    result = Rag(Settings(), provider, store).ask(QuestionRequest(question='Quelle durée ?'))
    assert result.found and '[1]' in result.answer and result.sources[0].chunk_id == hit.chunk.id


def test_attached_citations_do_not_bypass_grounding(hit):
    for evidence in ([{'source': 1, 'quote': 'vingt semaines'}],
                     [{'source': 99, 'quote': 'quatre semaines'}], []):
        generated = {'found': True, 'claims': [{'text': 'Une durée.', 'evidence': evidence}]}
        assert not validate(attach_citations(generated), [hit])[0]
    wrong_marker = {'found': True, 'claims': [{'text': 'Une durée [99].',
        'evidence': [{'source': 1, 'quote': 'quatre semaines'}]}]}
    assert not validate(attach_citations(wrong_marker), [hit])[0]
    multiple_sentences = {'found': True, 'claims': [{'text': 'Une durée. Une rémunération inventée.',
        'evidence': [{'source': 1, 'quote': 'quatre semaines'}]}]}
    assert not validate(attach_citations(multiple_sentences), [hit])[0]


def test_title_retrieval_completes_real_calendar(docs):
    chunks = chunk_documents(docs, IngestRequest())
    title = next(c for c in chunks if c.reference == docs[3]['reference'] and c.section == 'Présentation et métadonnées')
    result = complete_context([SearchHit(chunk=title, score=.7)], chunks)
    assert any('Examens finaux S1, S3, S5' in h.chunk.text for h in result)
    assert any('Examens finaux S2, S4' in h.chunk.text for h in result)
    assert any('Session de rattrapage unique' in h.chunk.text for h in result)
    assert all(h.chunk.file == title.file for h in result)
    assert len({h.chunk.id for h in result}) == len(result)
    assert all(h.score == -1 for h in result[1:])


def test_rag_grounded_and_verifier(hit):
    store, provider = Mock(), Mock()
    store.search.return_value = [hit]
    store.all_chunks.return_value = [hit.chunk]
    generated = {'found': True, 'claims': [{'text': 'Quatre semaines [1].', 'evidence': [{'source': 1, 'quote': 'quatre semaines'}]}]}
    provider.structured.side_effect = [generated, {'supported': True}]
    answer = Rag(Settings(), provider, store).ask(QuestionRequest(question='Quelle durée ?'))
    assert answer.found and answer.sources[0].page == 3
    provider.structured.side_effect = [generated, {'supported': False}]
    assert not Rag(Settings(), provider, store).ask(QuestionRequest(question='Quelle durée ?')).found


def test_api_validation_and_errors(hit):
    store, provider = Mock(), Mock()
    store.count.return_value = 1
    store.documents.return_value = []
    client = TestClient(create_app(Settings(), provider, store))
    for path in ('ask', 'search'):
        assert client.post(f'/api/{path}', json={'question': '  '}).status_code == 422
        assert client.post(f'/api/{path}', json={'question': 'PFE', 'top_k': 0}).status_code == 422
    assert client.post('/api/ingest', json={'chunk_size': 100, 'overlap': 100}).status_code == 422
    store.search.side_effect = ProviderError('Service OpenAI indisponible.')
    assert client.post('/api/ask', json={'question': 'PFE ?'}).status_code == 502
    store.count.side_effect = StoreError('Base indisponible')
    assert client.get('/api/health').status_code == 503


def test_chroma_idempotence_switch_failure_persistence(tmp_path, hit):
    provider = Mock()
    provider.embed.side_effect = lambda texts: [[1., 0., 0.] for _ in texts]
    settings = Settings(chroma_path=str(tmp_path))
    store = Store(settings, provider)
    assert store.count() == 0
    a = store.ingest([hit.chunk], IngestRequest(strategy='fixed'))
    b = store.ingest([hit.chunk], IngestRequest(strategy='fixed'))
    assert a['collection'] == b['collection'] and b['reused'] and store.count() == 1
    provider.embed.assert_called_once()
    changed = hit.chunk.model_copy(update={'id': 'new-chunk'})
    store.ingest([changed], IngestRequest(strategy='structural'))
    assert [c.id for c in store.all_chunks()] == ['new-chunk']
    provider.embed.side_effect = ProviderError('Réseau')
    with pytest.raises(ProviderError):
        store.ingest([hit.chunk.model_copy(update={'id': 'broken'})], IngestRequest())
    assert [c.id for c in Store(settings, provider).all_chunks()] == ['new-chunk']


def test_provider_missing_key():
    with pytest.raises(ProviderError, match='Clé OpenAI absente'):
        Provider(Settings(openai_api_key='')).embed(['test'])
def test_second_citation_points_to_correct_pdf_and_page(hit):
    second_chunk = hit.chunk.model_copy(
        update={
            "id": "c2",
            "file": "guide_stages.pdf",
            "reference": "TEST-GUIDE-STAGES",
            "page": 7,
            "text": "La convention de stage doit être signée avant le début du stage.",
        }
    )
    second_hit = hit.model_copy(update={"chunk": second_chunk, "score": 0.8})

    store, provider = Mock(), Mock()
    store.search.return_value = [hit, second_hit]
    store.all_chunks.return_value = [hit.chunk, second_chunk]
    provider.structured.side_effect = [
        {
            "found": True,
            "claims": [
                {
                    "text": "La convention doit être signée avant le début du stage.",
                    "evidence": [
                        {"source": 2, "quote": "signée avant le début du stage"}
                    ],
                }
            ],
        },
        {"supported": True},
    ]

    response = Rag(Settings(), provider, store).ask(
        QuestionRequest(question="Quand faut-il signer la convention de stage ?")
    )

    assert response.found
    assert "[2]" in response.answer
    assert response.invalid_citations == []
    assert len(response.sources) == 1
    source = response.sources[0]
    assert (source.id, source.chunk_id, source.file, source.page) == (
        2, "c2", "guide_stages.pdf", 7
    )