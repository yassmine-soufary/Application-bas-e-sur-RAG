import hashlib
from .models import Chunk, IngestRequest


def fixed(text: str, size: int = 500, overlap: int = 100) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError('Taille et chevauchement invalides')
    pieces = []
    for start in range(0, len(text), size - overlap):
        piece = text[start:start + size].strip()
        if piece:
            pieces.append(piece)
        if start + size >= len(text):
            break
    return pieces


def chunk_documents(documents: list[dict], options: IngestRequest) -> list[Chunk]:
    chunks = []
    for doc in documents:
        meta = {k: doc[k] for k in ('file', 'reference', 'type', 'date', 'version', 'status')}
        for page in doc['pages']:
            for block_index, block in enumerate(page['blocks']):
                # Structural units are kept whole: article, FAQ pair or autonomous table row.
                pieces = fixed(block['text'], options.chunk_size, options.overlap) if options.strategy == 'fixed' else [block['text'].strip()]
                for index, text in enumerate(pieces):
                    if not text:
                        continue
                    seed = f'{doc["sha256"]}:{page["page"]}:{block_index}:{index}:{options.model_dump_json()}:{text}'
                    chunks.append(Chunk(id=hashlib.sha256(seed.encode()).hexdigest(), **meta,
                                        page=page['page'], section=block['section'], text=text))
    return chunks
