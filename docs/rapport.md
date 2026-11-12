# Assistant Scolarité EIH — Rapport universitaire

## Page 1 — Objectif et corpus

Auteures · Hafsa Mottaki, Aya Kmaiti et Yassmine Soufary.

L'objectif est de répondre aux questions de scolarité d'une école fictive en conservant une justification documentaire pour chaque affirmation. Le système utilise exclusivement sept PDF : règlement, stages/PFE, mobilité, calendrier, vie étudiante, FAQ et note modificative. Le corpus représente 19 pages et couvre des procédures, tableaux, conditions, exceptions et changements de règles.

Les documents ont été extraits de l'archive fournie et copiés sans modification. Un manifeste SHA-256 vérifie leurs octets avant chaque ingestion. Internet sert uniquement à consulter la documentation des outils de développement ; il n'entre jamais dans le contexte du RAG. Une question telle que le prix d'un repas doit être refusée si les documents ne donnent que les horaires de restauration.

La demande universitaire a été traitée en cinq séances : extraction/découpage, indexation, génération contrôlée, interface et évaluation. Les commits locaux rendent cette progression consultable. La clé OpenAI reste une configuration privée côté serveur.

## Page 2 — Extraction et découpage

pdfplumber extrait chaque page et les tableaux. Les métadonnées sont lues dans la table de présentation : référence, type, date, version et statut. Les marges répétées sont retirées du texte indexé ; le texte brut reste disponible pour l'audit. Les pages sont numérotées à partir de 1 selon le PDF original.

Une ligne de tableau devient un texte autonome associant chaque valeur à son en-tête. Cette transformation évite d'associer une date à la mauvaise procédure. Les titres en gras et les motifs article/section/question définissent des unités structurelles ; les listes numérotées internes restent dans leur article. Les paires question-réponse de la FAQ sont préservées.

Le découpage fixe produit des fenêtres de 500 caractères avec chevauchement de 100, validées par 0 <= chevauchement < taille. Le découpage structurel conserve une unité logique entière. Les deux stratégies restent dans une page et conservent identifiant déterministe, source, référence, date, version, statut, page et section. Les exports JSON permettent une inspection sans API.

## Page 3 — Indexation et recherche

Le SDK officiel OpenAI crée les embeddings avec text-embedding-3-small, configurable. ChromaDB conserve ces vecteurs localement. La recherche de question utilise exactement le même modèle embedding et une collection cosinus. Le score est 1 moins la distance, borné entre -1 et 1 ; ce n'est pas une probabilité de vérité.

Chaque index est identifié par les empreintes de ses fragments et de son modèle. Une réingestion identique réutilise les vecteurs. Un changement de découpage active une collection distincte après indexation complète, par remplacement atomique du pointeur. Une erreur garde l'index précédent accessible. L'application de démonstration fonctionne avec un seul processus serveur.

Les routes /api/health, /api/ingest, /api/documents et /api/search exposent le statut, l'ingestion, les métadonnées et les passages. Top-k et filtre par type sont contrôlés. L'interface de recherche n'appelle pas la génération mais crée un embedding pour la question. Le seuil initial 0,50 est une hypothèse expérimentale à calibrer.

## Page 4 — Réponses, citations et versions

Si aucun passage ne dépasse le seuil, aucun appel de génération n'est fait. Le refus exact est : « Je ne trouve pas cette information dans les documents de l'École. » Sinon, Responses reçoit la question avec les fragments identifiés et un prompt système rédigé manuellement. Les documents sont traités comme des données, jamais comme des instructions.

La réponse structurée comprend des affirmations, citations et preuves textuelles. Python vérifie les identifiants, la présence exacte des preuves et la correspondance citation-source. Une seconde requête vérifie l'appui sémantique, la complétude et les exceptions. Une vérification par modèle demeure faillible et doit être complétée par une évaluation humaine.

Un détecteur générique repère les statuts modificatifs, références cibles et formulations de remplacement ; il exige une date postérieure. Il ajoute les deux documents, y compris portée et préambule. Le modèle doit citer les justifications et signaler la modification. Il ne peut conclure à une priorité par la seule date. L'expansion est volontairement large sur ce petit corpus et augmente le coût en tokens.

## Page 5 — Interface et vérifications

React, TypeScript et Vite fournissent une interface responsive en français, fond clair et bleu marine. Les quatre écrans sont Conversation, Sources, Documents et Recherche. Les citations ouvrent les extraits correspondants ; les messages restent en mémoire pour la session. Les documents affichés viennent de l'index actif, sans données fictives de remplissage.

FastAPI et Pydantic valident les entrées et documentent les contrats dans /docs. Les erreurs 422, 502 et 503 distinguent validation, service OpenAI et base vectorielle. Les erreurs d'authentification, quota et réseau ne révèlent pas les clés. Le navigateur ne reçoit jamais la configuration secrète.

Les tests emploient les PDF réels pour la traçabilité et des mocks pour les appels payants. Un vrai Chroma temporaire permet de vérifier persistance, idempotence et activation d'index. Les tests contrôlent aussi découpage, tableaux, citations, refus, vérification et erreurs. Les commandes et le compte rendu effectivement exécuté figurent dans README.md et docs/verification.md.

## Page 6 — Évaluation, limites et perspectives

Le jeu contient 20 questions : 8 simples, 5 synthèses, 2 versions et 5 hors corpus. Chaque attendu documenté possède référence, page, section et extrait vérifié. Les configurations imposées sont A : fixe, k=3 ; B : structurel, k=8. Le runner calcule Hit@k, MRR, rappel des passages, refus correct et refus à tort ; la notation 0-2 et la fidélité sont produites avec l'option de jugement OpenAI, identifiée comme telle, ou laissées non renseignées pour revue humaine.

L’index structurel actif contient 177 fragments. Après correction de la récupération du contexte et du contrôle des citations, les quatre suggestions de l’interface ont obtenu des réponses citées lors d’essais ciblés. La suite locale a compté 18 tests réussis lors de la vérification du contexte et des citations. Ces observations décrivent des essais fonctionnels. La comparaison chiffrée A/B sur les 20 questions reste à réaliser.

Le changement simultané de k et de stratégie ne permet pas d'attribuer une différence au seul découpage. Les autres limites sont l'absence d'OCR, les continuations entre pages, le détecteur modificatif conservateur, le seuil à calibrer et la faillibilité du vérificateur. Les prochaines étapes sont la revue personnelle du jeu, l'évaluation réelle, la calibration, puis une éventuelle authentification avant exposition réseau. L'annexe séparée déclare le recours à l'IA sans se substituer à la validation de l'étudiant.
