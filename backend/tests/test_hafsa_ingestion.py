
from app.chunking import fixed, chunk_documents
from app.models import IngestRequest


def test_fixed_without_overlap():
    """Vérifier le découpage lorsque overlap = 0."""
    result = fixed("ABCDEFGHIJ", size=4, overlap=0)

    assert result == ["ABCD", "EFGH", "IJ"]


def test_fixed_text_smaller_than_chunk():
    """Un texte court doit rester dans un seul fragment."""
    result = fixed("Bonjour EIH", size=500, overlap=100)

    assert result == ["Bonjour EIH"]


def test_structural_preserves_metadata():
    """Vérifier les métadonnées des fragments structurels."""
    documents = [{
        "file": "reglement.pdf",
        "reference": "EIH-TEST-2026",
        "type": "Reglement",
        "date": "2026-07-10",
        "version": "1.0",
        "status": "En vigueur",
        "sha256": "test-hash",
        "pages": [{
            "page": 2,
            "blocks": [{
                "section": "Article 5",
                "text": "Les étudiants doivent respecter le règlement.",
                "kind": "text"
            }]
        }]
    }]

    chunks = chunk_documents(
        documents,
        IngestRequest(strategy="structural")
    )

    assert len(chunks) == 1
    assert chunks[0].file == "reglement.pdf"
    assert chunks[0].reference == "EIH-TEST-2026"
    assert chunks[0].page == 2
    assert chunks[0].section == "Article 5"
    assert chunks[0].date == "2026-07-10"
    assert chunks[0].version == "1.0"
    assert chunks[0].status == "En vigueur"
