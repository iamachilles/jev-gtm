---
name: jev-prospection
description: Faire décider Jev (TypeSafe) sur un CSV de leads, de comptes, de réponses, de signaux ou de commentaires avec l'un des 50 cas d'usage prêts du dépôt jev-prospection (9 catégories : cibler, qualifier, repérer les signaux, trier les réponses, nettoyer la base, comprendre son audience, prioriser et décider, choisir le bon message, marketing). À utiliser quand l'utilisateur veut trier, qualifier, scorer, router ou dédoublonner une liste sans LLM par ligne, ou demande « passe cette liste sur Jev », « quel cas Jev pour ça ».
---

# Jev en prospection

Ce skill pilote `jev.py`, `jev_csv.py` et les 50 fichiers `questions/*.json` du dépôt [jev-prospection](https://github.com/iamachilles/jev-prospection). Il ne rédige rien : Jev décide, le code garde la main.

## Séquence

1. **Trouver le cas.** `python3 jev.py --list` donne les 9 catégories et les 50 cas avec leur slug. Propose le cas qui colle à la demande, en citant son entrée et sa décision. Si aucun ne colle, propose d'en dériver un (copie du fichier de question le plus proche, critères réécrits en anglais).
2. **Montrer l'exemple.** Lis `samples/<slug>.csv` et `samples/<slug>.out.csv` et montre trois lignes : l'entrée, la décision rendue, la confiance. C'est ce qui permet à l'utilisateur de juger si le cas est le bon avant de payer.
3. **Vérifier les colonnes.** Compare l'en-tête du CSV de l'utilisateur à `colonnes` du fichier de question. S'il manque une colonne, propose un renommage ou une adaptation du fichier, jamais une colonne inventée.
4. **Estimer, sans payer.** `python3 jev.py --cas <slug> --csv <fichier>` (sans `--apply`). Montre le nombre de lignes, de tokens et le coût.
5. **Demander l'accord** avant tout appel payant, même à quelques centimes. Sans accord explicite, on s'arrête là.
6. **Lancer.** Ajoute `--apply`. Sur une grosse liste, commence par `--limit 100`, montre les résultats, puis lance le reste (le cache évite de repayer les 100 premières).
7. **Lire la sortie.** Ouvre le `.out.csv`, compte les décisions par valeur, et montre en priorité les lignes `a_verifier = 1` : ce sont celles à faire relire par l'utilisateur ou à passer à un LLM.

## Règles

- Jamais d'appel sans `--apply` demandé et accordé.
- Les critères restent en anglais, les données dans leur langue.
- Les grilles livrées sont des exemples : proposer de les réécrire pour l'offre de l'utilisateur avant un vrai passage.
- Sur des données très françaises, proposer un test sur 100 lignes et une relecture de 20 désaccords avant de conclure.
- Le seuil de confiance est un réglage : partir de celui du fichier, le montrer, le laisser changer (`--seuil`).
