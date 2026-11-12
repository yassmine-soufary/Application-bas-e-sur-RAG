# Assistant Scolarité EIH

Application universitaire RAG : FastAPI/Pydantic, React/TypeScript/Vite, embeddings et Responses OpenAI, ChromaDB persistant. Les réponses utilisent exclusivement les sept PDF fournis. Aucun outil web ni File Search n'est exposé au modèle.

## Démarrage sous Windows / PowerShell

Depuis la racine du projet :

```powershell
# Installation sur une nouvelle machine (Python 3.11+ et Node 20.19+)
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
# Renseigner OPENAI_API_KEY dans backend/.env sans publier ce fichier.
Copy-Item frontend/.env.example frontend/.env
npm --prefix frontend install
```

L'environnement `.venv` et les dépendances frontend ont déjà été préparés dans ce dossier. Le `python` système est un alias Windows non fonctionnel dans l'environnement de développement ; utilisez directement `.venv\Scripts\python.exe`.

Terminal 1 :

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Terminal 2 :

```powershell
npm --prefix frontend run dev
```

Ouvrir http://localhost:5173. Documentation interactive : http://127.0.0.1:8000/docs.

Dans **Documents**, cliquer sur **Indexer les documents** après avoir ajouté la clé et redémarré le backend. Cette action envoie les fragments aux embeddings OpenAI et engage les coûts API de votre compte. Le corpus reste inchangé. L'interface n'affiche que les documents réellement indexés.

Alternative d'ingestion :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/ingest -ContentType application/json -Body '{"strategy":"structural","chunk_size":500,"overlap":100}'
```

## Corpus et traçabilité

Les sept PDF ont été extraits de `corpus (1).zip`, sans ressources `__MACOSX`. Le manifeste SHA-256 `data/corpus_manifest.json` contrôle l'identité de chaque original à chaque ingestion. Il interdit d'indexer un huitième PDF ou un fichier modifié. Les originaux ne sont jamais réécrits.

L'extraction réelle contient 19 pages. Les exports `data/extracted/documents.json` et `chunks_{fixed,structural}.json` conservent les pages physiques (1 à N), références, types, dates, versions et statuts. Le texte brut de chaque page est également conservé. Les lignes des tableaux sont transformées en associations en-tête/valeur ; ces séparateurs sont une représentation fidèle des cellules, pas un extrait typographique continu du PDF.

```powershell
.\.venv\Scripts\python.exe scripts/extract_corpus.py
.\.venv\Scripts\python.exe scripts/build_evaluation.py
```

L'extraction ne nécessite ni clé, ni LLM. Les métadonnées proviennent des tableaux des PDF. Les titres sont reconnus par leur structure et la police en gras ; les listes numérotées dans un article restent dans cet article. Les paires FAQ restent dans un même fragment, par page. Une disposition continuée sur une autre page reste traçable par des fragments séparés ; le corpus fourni comporte cette situation pour la section 5.4 du guide. Une extraction OCR des PDF scannés n'est pas implémentée, les sept originaux étant textuels.

## Architecture

`backend/app/extraction.py` → `chunking.py` → `provider.py` (embeddings) → `store.py` (collection Chroma cosinus).

`/ask` → embedding de question → recherche top-k → seuil → expansion des relations modificatives → Responses avec schéma JSON → contrôle des citations et preuves exactes → seconde vérification de fidélité par Responses → réponse et sources.

La stratégie fixe utilise 500 caractères et 100 de chevauchement par défaut, par unité documentaire et sans traverser une page. La stratégie structurelle préserve un article, une section, une paire FAQ ou une ligne autonome de tableau. `chunk_size` et `overlap` restent validés dans les deux cas mais ne limitent que la stratégie fixe. Les unités structurelles ne sont pas tronquées pour forcer une taille arbitraire. Un fragment de plus de 24 000 caractères provoque un refus explicite avant embedding.

Un index distinct est nommé par l'empreinte des fragments et le modèle embedding. L'activation est atomique après vérification du nombre de fragments. Une réingestion identique réutilise l'index sans nouveaux embeddings ; une interruption garde l'ancien index actif. Les anciennes collections sont conservées pour faciliter les comparaisons. Un changement de modèle embedding impose une réingestion, même si les dimensions correspondent. Le verrou est local au processus : exécuter **un seul worker**, sans lancer simultanément l'évaluation et l'ingestion via l'interface.

Chroma renvoie une distance cosinus. Le score publié est `1 - distance`, borné à [-1, 1] : ce n'est ni une probabilité, ni une confiance dans la réponse. Le seuil initial 0,50 reste à calibrer. Une source ajoutée par relation documentaire a le score sentinelle -1, affiché « Contexte lié » dans l'interface, et non un score de recherche mesuré.

## Modifications réglementaires

Le détecteur ne connaît aucun numéro de fichier ni aucune valeur réglementaire. Il exige un statut explicitement modificatif, une référence cible connue, une formulation de remplacement dans le texte et une date postérieure. Il récupère ensuite les deux documents, y compris préambule et portée. Le prompt et le vérificateur contrôlent la disposition concernée et son champ avant toute conclusion. Une référence à l'article 20 n'est pas assimilée à une modification de cet article.

Sur ce petit corpus, tous les fragments des deux documents liés sont transmis pour préserver les exceptions et les règles inchangées. Le filtre par type s'applique à la recherche initiale ; l'expansion peut inclure un autre type nécessaire pour déterminer la règle applicable. `/search` montre le top-k brut, `/ask` peut ajouter ce contexte. Le détecteur est conservateur et dépend du français et du format de référence du corpus ; il ne constitue pas un moteur universel d'interprétation juridique. Une relation non reconnue ne doit jamais être présentée comme résolue par la seule date.

## Contrats API

- `GET /api/health` : état du serveur, Chroma et nombre de fragments ; 503 si base indisponible. Une base accessible mais vide reste saine et affiche 0.
- `POST /api/ingest` : `{strategy:"fixed"|"structural",chunk_size:500,overlap:100}` ; 422 si invalide.
- `GET /api/documents` : documents de l'index actif, métadonnées et comptes.
- `POST /api/search` : `{question,top_k,filters:{type:null}}` ; passages et scores, sans génération.
- `POST /api/ask` : même entrée ; `{answer,found,sources,invalid_citations,latency_ms}`.

Une question vide ou un top-k hors [1,30] renvoie 422. Authentification, quota, connexion ou indisponibilité OpenAI renvoient 502 avec un message explicite sans clé ni contenu d'erreur brut. Les erreurs Chroma renvoient 503. La clé reste backend, enveloppée en `SecretStr`, et ignorée par Git. Aucune journalisation des prompts ou des clés n'est implémentée. `store=False` est envoyé aux Responses.

Le modèle est configurable (`OPENAI_MODEL=gpt-4.1-mini`), le modèle embedding aussi (`text-embedding-3-small`). Les noms vides et les seuils invalides sont rejetés ; la disponibilité du modèle sur votre compte ne peut être vérifiée qu'au premier appel réel. `TOP_K_DEFAULT=5`, `VITE_API_URL` configure le navigateur. Ne créez jamais de variable `VITE_OPENAI_API_KEY`.

Le modèle ne reçoit jamais une question sans fragments admissibles. Chaque affirmation produite doit citer des sources, fournir des preuves présentes exactement dans les fragments et passer une seconde vérification d'appui sémantique. Ces garde-fous réduisent le risque d'invention ; un contrôle par modèle demeure faillible. Une revue humaine des réponses et du jeu d'évaluation reste nécessaire.

En l'absence de preuve, le système retourne exactement :

> Je ne trouve pas cette information dans les documents de l'École.

L'historique est conservé uniquement dans l'état React pendant la session. Chaque question est traitée indépendamment côté RAG ; les pronoms dépendant d'un message antérieur doivent être reformulés. Aucun contenu utilisateur n'est injecté en HTML.

## Vérifications et évaluation

```powershell
.\.venv\Scripts\python.exe -m pytest
npm --prefix frontend run build
# Appels API payants, seulement après ajout de la clé :
.\.venv\Scripts\python.exe eval/run_eval.py --run-live --judge
# Nouvelle exécution pour calibrer un seuil candidat :
.\.venv\Scripts\python.exe eval/run_eval.py --run-live --judge --threshold 0.55
```

Les tests utilisent un vrai Chroma temporaire et des embeddings/Responses simulés, jamais un fournisseur alternatif ni des réponses de démonstration dans l'application. Ils couvrent validation, extraction réelle, pages, tableaux, découpage, relations modificatives, citations, refus, vérification, erreurs 502/503, idempotence, persistance et échec d'ingestion.

`eval/questions.jsonl` comprend 8 simples, 5 synthèses, 2 versions et 5 hors corpus. Les attendus ont été rédigés à partir des PDF et accompagnés de passages vérifiés par le générateur local. Le calendrier contient certains libellés de jours incohérents avec les dates : le système ne corrige pas silencieusement le document.

Le runner compare A (fixe, k=3) à B (structurel, k=8), puis restaure l'index actif précédent. Hit@k et MRR concernent les passages **avant seuil et expansion** et les 15 questions documentées. Hit@k vaut 1 si au moins un passage attendu est retrouvé ; `all_passages_recall` complète cette mesure pour les questions multi-documents. Un passage pertinent doit correspondre à référence, page et section. Taux de refus correct = refus exact sur les 5 questions hors corpus ; refus à tort = proportion des 15 questions documentées refusées.

Avec `--judge`, l'exactitude 0/1/2 et la fidélité 0..1 sont notées par OpenAI sur un barème explicite. Ce sont des jugements automatisés, à confronter à une notation humaine. Sans cette option ces deux métriques restent `null`, jamais zéro inventé. Les résultats effectivement mesurés sont horodatés dans `eval/results/`, accompagnés des réponses, sources et rangs ; ils restent exclus de Git par défaut. Le script sans `--run-live` ne fait aucun appel et ne crée aucun score. La clé n'ayant pas été fournie, la comparaison de qualité reste à exécuter.

Les deux réglages changent simultanément stratégie et k : la comparaison demandée n'isole pas l'effet causal du découpage. Exemple à examiner : l'article 3 de la note est plus long que 500 caractères, donc susceptible de perdre une condition en découpage fixe ; le tableau de mobilité est conservé par ligne avec ses en-têtes dans les deux stratégies. Seule l'évaluation réelle permettra de quantifier ces différences.

## Livraison et soutenance

Voir `docs/rapport.md`, `docs/rapport.pdf`, `docs/annexe_ia.md` et `docs/soutenance.md`. Le rapport PDF est limité à six pages. Les séances sont matérialisées par des commits locaux ; aucun push. Cette application vise une démonstration locale : aucune authentification multi-utilisateur ni exposition Internet du endpoint d'ingestion n'est prévue.

Documentation officielle consultée pour l'intégration : [Responses Python](https://developers.openai.com/api/reference/python/resources/responses/methods/create), [Embeddings Python](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create). Ces pages servent au développement du logiciel et ne sont pas ajoutées au corpus de réponses.
