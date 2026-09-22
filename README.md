# 50 cas d'usage de prospection avec Jev

Jev est le modèle de décision de [TypeSafe AI](https://typesafe.ai) : il ne rédige rien, il choisit une option, note sur une échelle ou répond oui / non, avec une probabilité. La sortie est gratuite, l'entrée coûte 42 $ le milliard de tokens. Sur une tâche de tri, de qualification ou de dédoublonnage, il remplace un appel de LLM pour quelques centimes les mille lignes.

Ce dépôt contient **50 questions prêtes à lancer**, une par cas d'usage de prospection, rangées en 9 catégories, chacune avec un fichier d'exemple de dix lignes et la décision que Jev a rendue dessus. Et **un script qui te guide** : la catégorie, le cas, l'exemple, ton fichier, le coût, ton accord, le résultat.

Le guide qui va avec : [forward-ai.fr/ressources/jev-prospection](https://www.forward-ai.fr/ressources/jev-prospection). Pour comprendre Jev lui-même : [forward-ai.fr/ressources/jev-typesafe](https://www.forward-ai.fr/ressources/jev-typesafe).

## Lancer

Il faut Python 3.10 ou plus et une clé TypeSafe (`TYPESAFE_API_KEY`, dans l'environnement ou dans un fichier `.env` copié depuis `.env.example`). Aucune dépendance à installer.

```bash
python3 jev.py            # guidé : catégorie, cas, exemple, ton fichier, coût, accord
python3 jev.py --list     # les 9 catégories et les 50 cas
python3 jev.py --cas tri-reponses --csv mes_reponses.csv          # direct, estimation seule
python3 jev.py --cas tri-reponses --csv mes_reponses.csv --apply  # direct, appels réels
```

Rien ne part sur le réseau tant que tu n'as pas confirmé. Le script vérifie que ton CSV porte les colonnes attendues (listées dans `colonnes` du fichier de question ; renomme tes colonnes ou adapte la liste), annonce le nombre de lignes, de tokens et le coût, puis, après ton accord, appelle l'API en parallèle, met chaque réponse en cache (`.cache/`, jamais repayée) et écrit `<ton_fichier>.out.csv`.

Le fichier de sortie garde tes colonnes et ajoute, par question :

- `categorie` (ou `score`, `role`, `meme_societe`...) : la décision
- `categorie_confidence` : la confiance, entre 0 et 1
- `categorie_p_<option>` : la probabilité de chaque option
- `a_verifier` : 1 quand la confiance passe sous le seuil du cas

`jev_csv.py` est le lanceur de bas niveau, utilisable seul (`python3 jev_csv.py --question questions/<slug>.json --csv fichier.csv --apply`).

## Les 50 cas

### Cibler : trouver les bonnes personnes et les bonnes entreprises

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 01 | **Trier les titres LinkedIn : fondateur, directeur, salarié, indépendant** (`titre-role`) | le titre LinkedIn | une famille de rôle parmi cinq | choix |
| 02 | **Noter tous les intitulés d'un compte cible de 1 à 5 selon leur rôle dans l'achat** (`title-sweep`) | l'intitulé, le service, encore en poste ou pas | une note de 1 (exclu) à 5 (tient le problème) | score |
| 03 | **Relire les profils complets des meilleurs intitulés sur le même barème** (`profil-complet`) | titre, présentation, postes actuels et passés | une note de 1 à 5 | score |
| 04 | **Dire si une personne correspond au persona visé** (`bon-persona`) | titre, présentation, entreprise | oui ou non, avec la probabilité | oui / non |
| 05 | **Trier son réseau LinkedIn ou ses contacts : à contacter, à revoir, à ignorer** (`trier-reseau`) | l'export des relations ou des contacts | contacter, revoir ou ignorer | choix |
| 06 | **Apparier une entreprise, une bio de dirigeant ou un message au client idéal** (`fit-client-ideal`) | la fiche ou le message, et votre client idéal | oui ou non | oui / non |

### Qualifier : dire si ça vaut le coup avant de dépenser du temps ou des crédits

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 07 | **Scorer un lead contre votre grille : chaud, tiède, froid** (`score-lead`) | la fiche du lead et votre grille | une note de 0 à 3 | score |
| 08 | **Dire si une entreprise correspond au client idéal depuis son site** (`site-client-ideal`) | la page d'accueil ou la description | oui ou non | oui / non |
| 09 | **Filtrer les leads avant de payer un enrichissement** (`avant-enrichissement`) | ce qu'on sait déjà du lead | enrichir ou pas | oui / non |
| 10 | **Écarter les prestataires qui vendent aux dirigeants (concurrents, pairs)** (`prestataire-dirigeants`) | titre et présentation | vend aux dirigeants : oui ou non | oui / non |
| 11 | **Qualifier un appel d'offres : fit et probabilité de gain** (`appel-offres`) | le texte de l'appel d'offres | une note de fit et une note de chances | score |
| 12 | **Confirmer qui est vraiment l'acheteur avec cinq questions par profil** (`acheteur-cinq-questions`) | le profil complet | cinq oui ou non | oui / non |

### Repérer les signaux : savoir qui bouge, sans lire chaque offre ni chaque post

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 13 | **Noter un signal (offre d'emploi, levée, post) de 0 à 3 sur votre grille** (`score-signal`) | le texte du signal | une note de 0 à 3 | score |
| 14 | **Détecter les signaux d'achat dans un flux de posts (Reddit, X, LinkedIn)** (`signal-posts-sociaux`) | chaque post du flux | signal d'achat : oui ou non | oui / non |
| 15 | **Extraire d'une note de vente l'intention, l'urgence et l'intérêt produit** (`notes-de-vente`) | les notes d'appel ou de CRM | trois oui ou non | oui / non |
| 16 | **Faire lire une veille (presse, concurrents) contre vos critères** (`veille-criteres`) | un titre ou une actualité | ça compte pour moi : oui ou non | oui / non |
| 17 | **Distinguer un compte en marché d'un simple bon fit** (`en-marche`) | la fiche et ses signaux récents | en marché : oui ou non | oui / non |

### Trier les réponses : et tout ce qui arrive dans la boîte

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 18 | **Trier les réponses d'une campagne : intéressé, pas maintenant, hors cible, à transférer** (`tri-reponses`) | le message envoyé et la réponse | une catégorie parmi six | choix |
| 19 | **Router une demande entrante : vente, support, facturation, spam** (`router-demande`) | le message entrant | un service | choix |
| 20 | **Classer les emails reçus : partenariat, prospection reçue, presse, autre** (`emails-pro`) | l'email | une catégorie | choix |
| 21 | **Détecter une réponse automatique (absence, bounce)** (`reponse-automatique`) | la réponse | automatique : oui ou non | oui / non |
| 22 | **Détecter le départ d'un contact dans sa réponse** (`depart-contact`) | la réponse | a quitté l'entreprise : oui ou non | oui / non |
| 23 | **Noter la maturité d'achat d'une demande entrante** (`maturite-demande`) | la demande | une note de 0 à 3 | score |
| 24 | **Détecter une demande d'arrêt ou de désinscription dans une conversation** (`desinscription`) | le dernier message | veut arrêter : oui ou non | oui / non |

### Nettoyer la base : dédoublonner, normaliser, tenir le CRM à jour sans y passer le week-end

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 25 | **Rattacher une entreprise à un secteur ou à un segment de votre liste** (`secteur-segment`) | le nom, la description, le site | un secteur parmi les vôtres | choix |
| 26 | **Dire si deux fiches désignent la même entreprise (SIRENE, LinkedIn, CRM)** (`meme-societe`) | les deux fiches | même société : oui ou non | oui / non |
| 27 | **Dire si deux contacts sont la même personne** (`meme-personne`) | les deux contacts | même personne : oui ou non | oui / non |
| 28 | **Classer une activité (appel, email, message) pour mettre le CRM à jour** (`activite-crm`) | l'activité | un type d'activité et son étape | choix |
| 29 | **Filtrer le spam et les faux leads à l'entrée** (`spam-entree`) | la soumission de formulaire | réel ou spam | oui / non |

### Comprendre son audience : ce que vos commentaires et vos abonnés disent de vos clients

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 30 | **Transformer des commentaires en colonnes : parle d'un projet, décideur, demande la ressource** (`commentaires-colonnes`) | le commentaire et le titre de son auteur | trois oui ou non | oui / non |
| 31 | **Classer les réacteurs d'un post : acheteur, pair, vendeur, recruteur** (`reacteurs-post`) | le titre de la personne | un profil parmi quatre | choix |
| 32 | **Tagger un corpus de posts pour retrouver les idées de contenu** (`tagger-posts`) | chaque post | un thème parmi les vôtres | choix |
| 33 | **Extraire la voix du client et les objections des commentaires** (`voix-client`) | le commentaire | une objection ou un besoin parmi une liste | choix |
| 34 | **Choisir les fils de discussion où répondre maintenant** (`fils-repondre`) | le fil | une note d'intérêt | score |

### Prioriser et décider : qui appeler en premier, et ce que l'agent fait seul

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 35 | **Ordonner les leads à appeler en premier** (`ordre-appels`) | la fiche et l'historique | une note de priorité | score |
| 36 | **Décider pour chaque compte : envoyer, creuser ou abandonner** (`envoyer-creuser-abandonner`) | la fiche et son score | envoyer, creuser ou abandonner | choix |
| 37 | **Noter l'urgence de relance de chaque ligne d'un tableau** (`urgence-relance`) | la ligne | une note d'urgence | score |
| 38 | **Scorer les devis morts pour décider lesquels rappeler** (`devis-morts`) | le devis et l'historique | une note de chances | score |
| 39 | **Décider si l'agent envoie, attend ou demande à un humain** (`agent-envoie-attend`) | l'état de la conversation | envoyer, attendre ou escalader | choix |
| 40 | **Choisir le prochain geste d'un agent parmi vos playbooks** (`prochain-geste`) | la situation du compte | un playbook | choix |

### Choisir le bon message : décider avant d'écrire, contrôler avant d'envoyer

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 41 | **Choisir l'angle ou la séquence adaptés à chaque prospect** (`angle-message`) | la fiche et vos angles | un angle parmi les vôtres | choix |
| 42 | **Décider s'il y a assez de matière pour personnaliser l'approche** (`assez-de-matiere`) | ce qu'on sait du prospect | personnaliser ou message standard | oui / non |
| 43 | **Contrôler un email rédigé par une IA avant envoi** (`controle-email-ia`) | l'email et le contexte | part ou à revoir | oui / non |
| 44 | **Choisir la meilleure accroche parmi plusieurs variantes** (`meilleure-accroche`) | les variantes et le prospect | la variante retenue | choix |
| 45 | **Vérifier qu'un événement de l'entreprise soutient l'angle proposé** (`evenement-angle`) | l'événement et l'angle | soutient : oui ou non | oui / non |

### Marketing et publicité : les mêmes questions fermées, côté marketing

| # | Cas d'usage | Ce que Jev reçoit | Ce qu'il rend | Brique |
|---|---|---|---|---|
| 46 | **Noter une création publicitaire : qualité, conformité, fatigue** (`creation-pub`) | le visuel ou le texte de l'annonce | une note par critère | score |
| 47 | **Étiqueter les publicités des concurrents par étape du tunnel** (`pubs-concurrents`) | l'annonce | une étape du tunnel | choix |
| 48 | **Prédire la performance d'un post avant publication** (`performance-post`) | le brouillon | une note | score |
| 49 | **Décider les correctifs SEO d'une page** (`correctifs-seo`) | la page | un correctif parmi une liste | choix |
| 50 | **Dire si un terme de recherche Google Ads vient d'un acheteur** (`terme-recherche-acheteur`) | le terme de recherche | acheteur : oui ou non | oui / non |

## Le seuil de confiance, c'est là que tout se joue

Jev ne rend pas qu'une réponse, il rend sa certitude. Sur 5 079 intitulés LinkedIn passés le 21 septembre 2026 (cas 01), l'accord avec le modèle de référence montait à 88 % quand la probabilité de l'option choisie dépassait 0,9, et tombait à 42 % sous 0,5. D'où la règle des templates : **au-dessus du seuil, la ligne se traite automatiquement ; en dessous, elle part à un humain ou à un LLM.** Chaque fichier de question porte son seuil (`seuil_confiance`), à recaler sur tes propres données. `--seuil 0.8` le change à la volée.

## Adapter un cas à ton offre

Ouvre `questions/<slug>.json`. Trois choses à changer, dans l'ordre :

1. `colonnes` : les colonnes de ton CSV qui entrent dans le `state` envoyé à Jev. Un sous-objet (`{"cle": "sirene", "colonnes": [...]}`) regroupe plusieurs colonnes sous un nom que la question peut citer entre accents graves.
2. `instructions` et `criteria` : la question et la description de chaque option, niveau ou réponse. Écris-les en anglais, avec des exemples concrets tirés de tes propres données. Les grilles livrées (score de lead, règles d'achat du title sweep, angles de message, playbooks) sont des exemples écrits pour une offre précise : réécris-les pour la tienne, à partir de tes appels, jamais de tête.
3. `seuil_confiance` : commence haut (0,9), regarde les lignes `a_verifier`, descends si elles sont justes.

Puis `python3 verifier.py` : il contrôle que les 50 questions sont valides pour l'API, que chaque exemple porte les bonnes colonnes et que ce README cite chaque slug.

## Le skill Claude Code

`skill/jev-prospection/SKILL.md` se copie dans `.claude/skills/jev-prospection/`. Il apprend à Claude Code à choisir le cas, vérifier les colonnes, lancer l'estimation, demander ton accord avant tout appel payant, puis lire le CSV de sortie et te montrer les lignes à vérifier.

## Ce que ça ne fait pas

- **Rédiger.** Jev ne produit aucun texte : pas de message, pas de résumé. Pour ça, un LLM, après le tri.
- **Comprendre un contexte qu'on ne lui donne pas.** Le `state` contient tout ce que Jev sait. Un titre seul ne dit pas l'effectif de l'entreprise ; si la décision en dépend, ajoute la colonne.
- **Deviner le français à coup sûr.** C'est la faiblesse annoncée du modèle. Les critères en anglais et le seuil de confiance sont les deux parades ; sur des données très françaises (juridique, administratif), teste sur 100 lignes avant de lancer 10 000.
- **Garder tes données chez toi.** Chaque ligne envoyée transite par l'API de TypeSafe (États-Unis). Même arbitrage que pour tout appel de LLM.

## Coût de référence

Une ligne de 300 caractères avec une question de 5 options pèse environ 800 tokens, soit 0,00003 $. Dix mille lignes : 8 millions de tokens, 0,34 $. Le script te donne le chiffre exact avant de partir, et la facture réelle en fin de course.

Les 50 cas ont été recensés en septembre 2026 sur ce qui circulait autour de Jev (posts, documentation, retours de terrain) et sur nos propres passages ; le détail des sources est dans `SOURCES.md`, pour mémoire.

Licence MIT. Questions et retours : [Achille Morin-Lemoine sur LinkedIn](https://www.linkedin.com/in/achille-morin-lemoine/).
