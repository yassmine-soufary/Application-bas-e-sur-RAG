# Déclaration d'utilisation des outils d'IA générative

Codex (OpenAI) a servi à préparer l’architecture, proposer et corriger du code, écrire des tests et documenter le projet. Il a aussi aidé à rédiger une première version du jeu d’évaluation à partir des PDF.

L'application appelle l'API OpenAI pour les embeddings, la reformulation documentée et la vérification de fidélité. Le modèle de génération et le modèle embedding sont inscrits dans la configuration ; chaque exécution d'évaluation enregistre leurs noms. L'option de notation automatique ajoute un usage d'OpenAI comme évaluateur.

Les sept PDF d'origine n'ont pas été générés ou réécrits pendant ce développement. Leur identité est vérifiée par SHA-256. Les réponses attendues et les références du jeu d'évaluation ont été rapprochées des extractions réelles. Les contrôles exécutés sont consignés dans `docs/verification.md`. Les tests n'utilisent pas d'appels payants.

ImageGen a servi à produire les deux illustrations décoratives de l’interface. Les prompts sont conservés dans frontend/public/images/prompts.json.

Des essais ciblés ont utilisé OpenAI sur le corpus pédagogique fictif. Le groupe doit relire les sources, vérifier les résultats et compléter les contributions réellement effectuées avant signature.

- Hafsa Mottaki — vérifications et signature : ____________________
- Aya Kmaiti — vérifications et signature : ____________________
- Yassmine Soufary — vérifications et signature : ____________________

Date : ____________________
