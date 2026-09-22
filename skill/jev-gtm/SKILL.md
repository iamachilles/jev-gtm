---
name: jev-gtm
description: Faire décider Jev (TypeSafe) sur un CSV de leads, de comptes, de réponses ou de commentaires avec l'une des sept questions prêtes du dépôt jev-gtm (rôle d'un intitulé, prestataire aux dirigeants, tri des réponses, même société, score de signal, profil d'audience, title sweep). À utiliser quand l'utilisateur veut trier, qualifier, scorer ou dédoublonner une liste sans LLM par ligne, ou demande « passe cette liste sur Jev ».
---

# Jev en GTM

Ce skill pilote `jev_csv.py` et les fichiers `questions/*.json` du dépôt [jev-gtm](https://github.com/iamachilles/jev-gtm). Il ne rédige rien : Jev décide, le code garde la main.

## Séquence

1. **Choisir la question.** Lis le `titre` et la `description` de chaque fichier `questions/*.json` et propose celle qui colle à la demande. Si aucune ne colle, propose d'en dériver une (copie du fichier le plus proche, critères réécrits en anglais).
2. **Vérifier les colonnes.** Compare l'en-tête du CSV de l'utilisateur à `colonnes` du fichier de question. S'il manque une colonne, propose un renommage ou une adaptation du fichier de question, jamais une colonne inventée.
3. **Estimer, sans payer.** `python3 jev_csv.py --question questions/<slug>.json --csv <fichier> ` (sans `--apply`). Montre le nombre de lignes, de tokens et le coût estimé.
4. **Demander l'accord** avant tout appel payant, même à quelques centimes. Sans accord explicite, on s'arrête là.
5. **Lancer.** Ajoute `--apply`. Sur une grosse liste, commence par `--limit 100`, montre les résultats, puis lance le reste (le cache évite de repayer les 100 premières).
6. **Lire la sortie.** Ouvre le `.out.csv`, compte les décisions par valeur, et montre en priorité les lignes `a_verifier = 1` : ce sont celles à faire relire par l'utilisateur ou à passer à un LLM.

## Règles

- Jamais d'appel sans `--apply` demandé et accordé.
- Les critères restent en anglais, les données dans leur langue.
- Sur des données très françaises, proposer un test sur 100 lignes et une relecture de 20 désaccords avant de conclure.
- Le seuil de confiance est un réglage, pas une vérité : partir de celui du fichier, le montrer, le laisser changer (`--seuil`).
