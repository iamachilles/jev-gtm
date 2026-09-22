# Jev en GTM : 7 questions prêtes à lancer sur vos listes

Jev est le modèle de décision de [TypeSafe AI](https://typesafe.ai) : il ne rédige rien, il choisit une option, note sur une échelle ou répond oui / non, avec une probabilité. La sortie est gratuite, l'entrée coûte 42 $ le milliard de tokens. Sur une tâche de tri ou de qualification, il remplace un appel de LLM pour une fraction du prix.

Ce dépôt contient **un lanceur** (`jev_csv.py`, Python sans dépendance) et **sept questions** couvrant la chaîne d'acquisition B2B : du titre LinkedIn à trier jusqu'aux réponses de campagne à router. Chaque question vient avec un CSV d'exemple de 10 lignes et le CSV de sortie tel que Jev l'a rendu le 22 septembre 2026.

Le catalogue des cas d'usage recensés (55 familles, sources et chiffres) : [CAS-D-USAGE.md](CAS-D-USAGE.md).

Le guide qui va avec : [forward-ai.fr/ressources/jev-gtm](https://www.forward-ai.fr/ressources/jev-gtm). Pour comprendre Jev lui-même : [forward-ai.fr/ressources/jev-typesafe](https://www.forward-ai.fr/ressources/jev-typesafe).

## Les sept questions

| Slug | Étape GTM | Ce que Jev décide | Brique | Mesuré |
|---|---|---|---|---|
| `intitule-role` | ciblage | un titre LinkedIn est fondateur, directeur, salarié, indépendant ou incertain | choix | 5 079 intitulés, 80,1 % d'accord avec gpt-4o-mini, 0,17 $ |
| `prestataire-dirigeants` | qualification | la personne vend elle-même des services aux dirigeants (à écarter) | oui / non | exemple de 10 lignes |
| `tri-reponses` | réponses | une réponse de campagne est intéressée, pas maintenant, hors cible, à transférer, désinscription ou autre | choix | exemple de 10 lignes |
| `meme-societe` | dédoublonnage | une fiche SIRENE et une page LinkedIn parlent de la même société | oui / non | exemple de 10 lignes |
| `score-signal` | signaux | un signal (offre, post, levée) vaut 0, 1, 2 ou 3 sur votre grille | score | exemple de 10 lignes |
| `commentaires-audience` | audience | un commentaire parle d'un projet, vient d'un décideur, demande la ressource | 3 oui / non | exemple de 10 lignes |
| `title-sweep` | ciblage | chaque intitulé d'un compte cible vaut de 1 (exclu) à 5 (tient le problème), méthode Jordan Crawford | score | 79 601 personnes pour 9,47 $ chez Jordan Crawford |

Les critères sont rédigés **en anglais** (la langue où Jev est le plus solide) et les données restent dans leur langue : c'est la configuration mesurée sur les 5 079 intitulés, dont 60 % en français.

## Lancer une question sur votre CSV

Il faut Python 3.10 ou plus et une clé TypeSafe (`TYPESAFE_API_KEY`, dans l'environnement ou dans un fichier `.env` copié depuis `.env.example`).

```bash
# 1. estimation seule, aucun appel, aucun coût
python3 jev_csv.py --question questions/intitule-role.json --csv ma_liste.csv

# 2. lancement réel
python3 jev_csv.py --question questions/intitule-role.json --csv ma_liste.csv --apply
```

Le script vérifie que votre CSV porte les colonnes attendues (listées dans `colonnes` du fichier de question ; renommez vos colonnes ou adaptez la liste), annonce le nombre de tokens et le coût, puis, avec `--apply`, appelle l'API en parallèle, met chaque réponse en cache (`.cache/`, jamais repayée) et écrit `ma_liste.out.csv`.

Le CSV de sortie garde vos colonnes et ajoute, par question :

- `role` (ou `categorie`, `score`, `niveau`, `meme_societe`...) : la décision
- `role_confidence` : la confiance, entre 0 et 1
- `role_p_fondateur`, `role_p_directeur`... : la probabilité de chaque option
- `a_verifier` : 1 quand la confiance passe sous le seuil du fichier de question

## Le seuil de confiance, c'est là que tout se joue

Jev ne rend pas qu'une réponse, il rend sa certitude. Sur les 5 079 intitulés, l'accord avec le modèle de référence montait à 87,8 % quand la probabilité de l'option choisie dépassait 0,9, et tombait à 41,6 % sous 0,5. D'où la règle des templates : **au-dessus du seuil, la ligne se traite automatiquement ; en dessous, elle part à un humain ou à un LLM.** Chaque fichier de question porte son seuil (`seuil_confiance`), à recaler sur vos propres données. `--seuil 0.8` le change à la volée.

## Adapter une question

Ouvrez le fichier JSON. Trois choses à changer, dans l'ordre :

1. `colonnes` : les colonnes de votre CSV qui entrent dans le `state` envoyé à Jev. Un sous-objet (`{"cle": "sirene", "colonnes": [...]}`) regroupe plusieurs colonnes sous un nom que la question peut citer entre accents graves.
2. `instructions` et `criteria` : la question et la description de chaque option, niveau ou réponse. Écrivez-les en anglais, avec des exemples concrets tirés de vos propres données. Pour `title-sweep`, les règles d'achat (`buying_rules`) sont à réécrire à partir de vos appels commerciaux ; pour `score-signal`, la grille décrit un signal précis, pas « une entreprise qui va bien ».
3. `seuil_confiance` : commencez haut (0,9), regardez les lignes `a_verifier`, descendez si elles sont justes.

Puis `python3 verifier.py` : il contrôle que les questions sont valides pour l'API, que les CSV d'exemple portent les bonnes colonnes et que ce README cite chaque slug.

## Le skill Claude Code

`skill/jev-gtm/SKILL.md` se copie dans `.claude/skills/jev-gtm/`. Il apprend à Claude Code à choisir la question, vérifier les colonnes, lancer l'estimation, demander votre accord avant tout appel payant, puis lire le CSV de sortie et vous montrer les lignes à vérifier.

## Ce que ça ne fait pas

- **Rédiger.** Jev ne produit aucun texte : pas de message, pas de résumé. Pour ça, un LLM, après le tri.
- **Comprendre un contexte qu'on ne lui donne pas.** Le `state` contient tout ce que Jev sait. Un titre seul ne dit pas l'effectif de l'entreprise ; si la décision en dépend, ajoutez la colonne.
- **Deviner le français à coup sûr.** C'est la faiblesse annoncée du modèle. Les critères en anglais et le seuil de confiance sont les deux parades ; sur des données très françaises (juridique, administratif), testez sur 100 lignes avant de lancer 10 000.
- **Garder vos données chez vous.** Chaque ligne envoyée transite par l'API de TypeSafe (États-Unis). Même arbitrage que pour tout appel de LLM.

## Coût de référence

Une ligne de 300 caractères avec une question de 5 options pèse environ 800 tokens, soit 0,00003 $. Dix mille lignes : 8 millions de tokens, 0,34 $. Le lanceur vous donne le chiffre exact avant de partir, et la facture réelle en fin de course.

Licence MIT. Questions et retours : [Achille Morin-Lemoine sur LinkedIn](https://www.linkedin.com/in/achille-morin-lemoine/).
