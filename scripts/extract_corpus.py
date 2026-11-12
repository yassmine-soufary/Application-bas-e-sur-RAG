"""Run from the repository root; no OpenAI call."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.extraction import extract, export
from app.chunking import chunk_documents
from app.models import IngestRequest
from app.config import ROOT

documents = extract()
export(documents)
for strategy in ('fixed', 'structural'):
    chunks = chunk_documents(documents, IngestRequest(strategy=strategy))
    (ROOT / f'data/extracted/chunks_{strategy}.json').write_text(json.dumps([c.model_dump() for c in chunks], ensure_ascii=False, indent=2), encoding='utf-8')
    print(strategy, len(chunks), 'fragments')
for d in documents:
    print(d['reference'], d['date'], len(d['pages']), 'pages')
