"""Local PDF extraction. Original bytes are checked against the trusted manifest."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import pdfplumber
from .config import ROOT

MONTHS = dict(zip('janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split(), range(1, 13)))
HEADING = re.compile(r'^(Article\s+\d+\b.*|Q\d+\.\s.*|\d+(?:\.\d+)*\.?\s+[^\d].*|Titre\s+[IVX]+.*)$')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(page) -> dict:
    # Metadata is a real two-column table, including wrapped values.
    for table in page.extract_tables():
        rows = {re.sub(r'\s+', ' ', r[0] or '').strip(): re.sub(r'\s+', ' ', ' '.join(c or '' for c in r[1:])).strip() for r in table if r}
        if 'Référence' in rows:
            date = re.search(r'(\d{1,2})(?:er)?\s+(\w+)\s+(\d{4})', rows['Date de publication'])
            if not date:
                raise ValueError('Date documentaire illisible')
            return dict(reference=rows['Référence'], type=rows['Type de document'],
                        date=f'{date[3]}-{MONTHS[date[2]]:02}-{int(date[1]):02}',
                        version=rows.get('Version', ''), status=rows.get('Statut', ''))
    raise ValueError('Table des métadonnées introuvable')


def extract(corpus: Path = ROOT / 'data/corpus', verify: bool = True) -> list[dict]:
    paths = sorted(corpus.glob('*.pdf'))
    if len(paths) != 7:
        raise ValueError('Le corpus doit contenir exactement les 7 PDF officiels.')
    if verify:
        manifest = json.loads((ROOT / 'data/corpus_manifest.json').read_text(encoding='utf-8'))
        actual = {p.name: digest(p) for p in paths}
        if actual != manifest:
            raise ValueError('Le corpus diffère du manifeste officiel ; ingestion refusée.')
    documents = []
    for path in paths:
        with pdfplumber.open(path) as pdf:
            meta = metadata(pdf.pages[0])
            raw = [p.extract_text() or '' for p in pdf.pages]
            # Repeated margins only: never remove repeated regulatory content.
            margins = Counter(line for text in raw for line in set(text.splitlines()[:1] + text.splitlines()[-1:]))
            repeated = {line for line, count in margins.items() if count > 1}
            pages = []
            section = 'Présentation et métadonnées'
            for number, page in enumerate(pdf.pages, 1):
                tables = page.find_tables()
                # Extract narrative outside all tables to avoid incoherent duplicate rows.
                def outside(obj):
                    x, y = (obj['x0'] + obj['x1']) / 2, (obj['top'] + obj['bottom']) / 2
                    return not any(t.bbox[0] <= x <= t.bbox[2] and t.bbox[1] <= y <= t.bbox[3] for t in tables)
                text = page.filter(outside).extract_text() or ''
                heading_texts = {l['text'] for l in page.extract_text_lines()
                                 if l.get('chars') and 'Bold' in l['chars'][0].get('fontname', '')}
                blocks, current = [], []
                for line in text.splitlines():
                    if line in repeated or line.startswith('Document fictif') or line.startswith("École d'Ingénieurs Hélianthe (EIH)"):
                        continue
                    line = line.replace('(cid:127)', '•').strip()
                    if HEADING.match(line) and line in heading_texts:
                        if current:
                            blocks.append({'section': section, 'text': '\n'.join(current), 'kind': 'text'})
                        section, current = line, [line]
                    else:
                        current.append(line)
                if current:
                    blocks.append({'section': section, 'text': '\n'.join(current), 'kind': 'text'})
                lines = page.extract_text_lines()
                for table in tables:
                    rows = table.extract()
                    if not rows or len(rows) < 2:
                        continue
                    if rows[0][0] and 'Organisme' in rows[0][0]:
                        continue  # already recorded as metadata
                    preceding = [l['text'] for l in lines if l['top'] < table.bbox[1] and HEADING.match(l['text'])]
                    label = preceding[-1] if preceding else section
                    headers = [re.sub(r'\s+', ' ', c or '') for c in rows[0]]
                    for row in rows[1:]:
                        cells = [re.sub(r'\s+', ' ', c or '') for c in row]
                        value = ' ; '.join(f'{headers[i] or "Colonne " + str(i+1)} : {cell}' for i, cell in enumerate(cells))
                        blocks.append({'section': label, 'text': value, 'kind': 'table'})
                pages.append({'page': number, 'raw_text': raw[number-1], 'blocks': blocks})
            documents.append({'file': path.name, **meta, 'sha256': digest(path), 'pages': pages})
    return documents


def export(documents: list[dict]):
    target = ROOT / 'data/extracted/documents.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding='utf-8')
