import hashlib
import json
import os
from pathlib import Path
from threading import RLock
import chromadb
from .models import Chunk, IngestRequest, SearchHit, DocumentInfo
from .provider import Provider
from .config import Settings


class StoreError(Exception):
    pass


class Store:
    def __init__(self, settings: Settings, provider: Provider):
        self.settings, self.provider = settings, provider
        self.path = settings.db_path
        self.lock = RLock()
        self._client = None

    def client(self):
        try:
            with self.lock:
                if self._client is None:
                    self._client = chromadb.PersistentClient(path=str(self.path))
                return self._client
        except Exception:
            raise StoreError('Base vectorielle indisponible.') from None

    def active(self):
        try:
            self.client().heartbeat()
        except Exception:
            raise StoreError('Base vectorielle indisponible.') from None
        pointer = self.path / 'active.json'
        if not pointer.exists():
            return None
        try:
            state = json.loads(pointer.read_text(encoding='utf-8'))
            if state['embedding_model'] != self.settings.openai_embedding_model:
                raise StoreError('Modèle embedding modifié : réingérez le corpus.')
            return self.client().get_collection(state['collection'], embedding_function=None)
        except StoreError:
            raise
        except Exception:
            raise StoreError('Index actif indisponible.') from None

    def count(self):
        try:
            collection = self.active()
            return collection.count() if collection is not None else 0
        except StoreError:
            raise
        except Exception:
            raise StoreError('Lecture du nombre de fragments impossible.') from None

    def ingest(self, chunks: list[Chunk], options: IngestRequest):
        signature = hashlib.sha256((''.join(c.id for c in chunks) + self.settings.openai_embedding_model).encode()).hexdigest()
        name = 'eih_' + signature[:32]
        # Serialize ingestion; staging collection is never visible until fully populated.
        with self.lock:
            client = self.client()
            try:
                collection = client.get_or_create_collection(name, metadata={'hnsw:space': 'cosine'}, embedding_function=None)
                reused = collection.count() == len(chunks)
                if not reused:
                    for start in range(0, len(chunks), 64):
                        batch = chunks[start:start + 64]
                        embeddings = self.provider.embed([c.text for c in batch])
                        collection.upsert(ids=[c.id for c in batch], documents=[c.text for c in batch],
                            embeddings=embeddings, metadatas=[c.model_dump(exclude={'id', 'text'}) for c in batch])
                if collection.count() != len(chunks):
                    raise StoreError('Index incomplet ; ancien index conservé.')
                state = {'collection': name, 'embedding_model': self.settings.openai_embedding_model, 'options': options.model_dump()}
                tmp = self.path / 'active.tmp'
                tmp.write_text(json.dumps(state), encoding='utf-8')
                os.replace(tmp, self.path / 'active.json')
                return {'collection': name, 'chunks': len(chunks), 'reused': reused}
            except (StoreError, ValueError):
                raise
            except Exception as exc:
                from .provider import ProviderError
                if isinstance(exc, ProviderError):
                    raise
                raise StoreError('Échec de l’indexation ; ancien index conservé.') from None

    def all_chunks(self) -> list[Chunk]:
        collection = self.active()
        if collection is None:
            return []
        try:
            data = collection.get(include=['documents', 'metadatas'])
            return [Chunk(id=id_, text=text, **meta) for id_, text, meta in zip(data['ids'], data['documents'], data['metadatas'])]
        except Exception:
            raise StoreError('Lecture de la base impossible.') from None

    def documents(self):
        grouped = {}
        for c in self.all_chunks():
            if c.file not in grouped:
                grouped[c.file] = DocumentInfo(**c.model_dump(exclude={'id', 'text', 'page', 'section'}), chunks=0)
            grouped[c.file].chunks += 1
        return sorted(grouped.values(), key=lambda d: d.file)

    def search(self, question: str, top_k: int, type_filter: str | None = None):
        collection = self.active()
        if collection is None:
            return []
        try:
            count = collection.count()
        except Exception:
            raise StoreError('Lecture de la collection impossible.') from None
        if count == 0:
            return []
        vector = self.provider.embed([question])[0]
        try:
            result = collection.query(query_embeddings=[vector], n_results=min(top_k, count),
                where={'type': type_filter} if type_filter else None,
                include=['documents', 'metadatas', 'distances'])
            return [SearchHit(chunk=Chunk(id=id_, text=text, **meta), score=max(-1., min(1., 1. - distance)))
                for id_, text, meta, distance in zip(result['ids'][0], result['documents'][0], result['metadatas'][0], result['distances'][0])]
        except Exception:
            raise StoreError('Recherche vectorielle indisponible.') from None
