import json
from openai import OpenAI, OpenAIError, AuthenticationError, RateLimitError, APIConnectionError
from .config import Settings


class ProviderError(Exception):
    pass


class Provider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def client(self):
        key = self.settings.openai_api_key.get_secret_value()
        if not key:
            raise ProviderError('Clé OpenAI absente. Configurez backend/.env.')
        return OpenAI(api_key=key, timeout=45, max_retries=1)

    def call(self, operation):
        try:
            return operation(self.client())
        except AuthenticationError:
            raise ProviderError('Authentification OpenAI refusée.') from None
        except RateLimitError:
            raise ProviderError('Quota OpenAI épuisé ou limite de débit atteinte.') from None
        except APIConnectionError:
            raise ProviderError('Connexion à OpenAI impossible.') from None
        except OpenAIError:
            raise ProviderError('Service OpenAI indisponible ou modèle inaccessible.') from None

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for start in range(0, len(texts), 64):
            batch = texts[start:start + 64]
            if any(len(t) > 24000 for t in batch):
                raise ValueError('Un fragment dépasse la limite locale : revoir le découpage.')
            result = self.call(lambda client: client.embeddings.create(
                model=self.settings.openai_embedding_model, input=batch, encoding_format='float'))
            vectors.extend(item.embedding for item in sorted(result.data, key=lambda item: item.index))
        return vectors

    def structured(self, instructions: str, payload: dict, schema: dict, name: str):
        response = self.call(lambda client: client.responses.create(
            model=self.settings.openai_model, instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False), store=False,
            text={'format': {'type': 'json_schema', 'name': name, 'strict': True, 'schema': schema}}))
        try:
            return json.loads(response.output_text)
        except (ValueError, TypeError):
            raise ProviderError('Réponse OpenAI illisible ou incomplète.') from None
