#!/usr/bin/env python3
"""Le script guidé : choisis une catégorie, un cas d'usage, regarde l'exemple, lance Jev sur ton fichier.

    python3 jev.py              # guidé, question par question
    python3 jev.py --list       # les 9 catégories et les 50 cas, sans rien lancer
    python3 jev.py --cas tri-reponses --csv mes_reponses.csv          # direct, estimation seule
    python3 jev.py --cas tri-reponses --csv mes_reponses.csv --apply  # direct, appels réels
    python3 jev.py --sample     # guidé, sur le fichier d'exemple du cas choisi

Rien ne part sur le réseau tant que tu n'as pas confirmé. Le script te montre d'abord l'exemple
(entrée et décision rendue par Jev), vérifie les colonnes de ton fichier, annonce le coût, et
attend ton accord. Sans clé (`TYPESAFE_API_KEY` dans l'environnement ou dans `.env`), il s'arrête
juste avant l'appel et t'affiche la commande à relancer.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import jev_csv

RACINE = Path(__file__).resolve().parent
BRIQUE = {"choix": "choix", "score": "score", "oui-non": "oui / non"}


def catalogue() -> dict:
    return json.loads((RACINE / "catalogue.json").read_text(encoding="utf-8"))


def demander(invite: str, defaut: str = "") -> str:
    """input() qui rend le défaut sur Entrée ou sur fin de flux (script, tube)."""
    try:
        rep = input(invite).strip()
    except EOFError:
        print()
        return defaut
    return rep or defaut


def choisir(liste: list, invite: str, libelle) -> object:
    for i, x in enumerate(liste, 1):
        print(f"  {i:>2}. {libelle(x)}")
    while True:
        rep = demander(invite, "1")
        if rep.isdigit() and 1 <= int(rep) <= len(liste):
            return liste[int(rep) - 1]
        print(f"  Tape un numéro entre 1 et {len(liste)}.")


def lister(cat: dict) -> None:
    print(cat["titre"])
    for c in cat["categories"]:
        print(f"\n{c['nom']} : {c['sous_titre']}")
        for x in c["cas"]:
            print(f"  {x['numero']:>2}. {x['nom']}  [{BRIQUE[x['brique']]}]  ({x['slug']})")


def trouver(cat: dict, slug: str) -> tuple[dict, dict]:
    for c in cat["categories"]:
        for x in c["cas"]:
            if x["slug"] == slug:
                return c, x
    raise SystemExit(f"cas inconnu : {slug} (voir `python3 jev.py --list`)")


def montrer_exemple(slug: str, question: dict, n: int = 3) -> None:
    """Les premières lignes de l'exemple, avec la décision rendue par Jev si la sortie existe."""
    entree = RACINE / "samples" / f"{slug}.csv"
    sortie = RACINE / "samples" / f"{slug}.out.csv"
    if not entree.exists():
        print("  (pas de fichier d'exemple)")
        return
    with entree.open(encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f))
    resultats = []
    if sortie.exists():
        with sortie.open(encoding="utf-8-sig", newline="") as f:
            resultats = list(csv.DictReader(f))
    cols = jev_csv.colonnes_attendues(question)
    qids = list(question["questions"])
    print(f"  Colonnes attendues : {', '.join(cols)}")
    print(f"  Exemple, {n} lignes sur {len(lignes)} :")
    for i, l in enumerate(lignes[:n]):
        morceaux = [f"{c}: {(l.get(c) or '')[:70]}" for c in cols]
        print("   " + " | ".join(morceaux))
        if i < len(resultats):
            r = resultats[i]
            dec = ", ".join(f"{q} = {r.get(q, '?')} (confiance {r.get(q + '_confidence', '?')})" for q in qids)
            print(f"      -> {dec}{'  [à vérifier]' if r.get('a_verifier') == '1' else ''}")
    if resultats:
        n_verif = sum(1 for r in resultats if r.get("a_verifier") == "1")
        print(f"  Sur les {len(resultats)} lignes de l'exemple, Jev en a rendu {len(resultats) - n_verif} sûres et {n_verif} à vérifier.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="afficher les catégories et les cas, puis sortir")
    ap.add_argument("--cas", help="slug du cas (saute le choix guidé)")
    ap.add_argument("--csv", type=Path, help="ton fichier CSV")
    ap.add_argument("--sample", action="store_true", help="utiliser le fichier d'exemple du cas")
    ap.add_argument("--apply", action="store_true", help="lancer les appels sans demander confirmation")
    ap.add_argument("--limit", type=int, help="ne traiter que les N premières lignes")
    ap.add_argument("--seuil", type=float, help="seuil de confiance (défaut : celui du cas)")
    a = ap.parse_args()

    cat = catalogue()
    if a.list:
        lister(cat)
        return 0

    print(f"\n{cat['titre']}\nJev décide, ton code garde la main. Rien ne part tant que tu n'as pas confirmé.\n")
    if a.cas:
        c, x = trouver(cat, a.cas)
    else:
        print("Qu'est-ce que tu veux faire ?")
        c = choisir(cat["categories"], "\nCatégorie (numéro) : ", lambda k: f"{k['nom']} : {k['sous_titre']}")
        print(f"\n{c['nom']} : {len(c['cas'])} cas")
        x = choisir(c["cas"], "\nCas d'usage (numéro) : ", lambda k: f"{k['nom']}  [{BRIQUE[k['brique']]}]")
    slug = x["slug"]
    qpath = RACINE / "questions" / f"{slug}.json"
    question = jev_csv.charger_question(qpath)
    print(f"\n{x['numero']:02d}. {x['nom']}")
    print(f"  Entrée : {x['entree']}\n  Décision : {x['decision']}\n")
    print(f"  {question['description']}\n")
    montrer_exemple(slug, question)

    fichier = a.csv
    if fichier is None and not a.sample:
        rep = demander("\nChemin de ton fichier CSV (Entrée = lancer sur l'exemple) : ", "")
        fichier = Path(rep).expanduser() if rep else None
    if fichier is None:
        fichier = RACINE / "samples" / f"{slug}.csv"
        print(f"  Fichier d'exemple : {fichier.relative_to(RACINE)}")
    if not fichier.exists():
        print(f"Fichier introuvable : {fichier}")
        return 2

    print()
    res = jev_csv.executer(qpath, fichier, apply=False, limit=a.limit, seuil=a.seuil, silencieux=True)
    print(f"{res['lignes']} lignes, {res['questions']} question(s) par ligne, ~{res['tokens_estimes']:,} tokens, coût estimé ~{res['cout_estime']:.4f} $ (la sortie est gratuite).")

    jev_csv.charger_env()
    if not a.apply:
        rep = demander("\nLancer les appels à Jev maintenant ? (o/N) : ", "n").lower()
        if rep not in ("o", "oui", "y", "yes"):
            print("\nRien n'est parti. Pour lancer plus tard :")
            print(f"  python3 jev.py --cas {slug} --csv {fichier} --apply")
            return 0
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("\nIl manque la clé : copie .env.example en .env et colle ta clé TypeSafe (TYPESAFE_API_KEY). Puis :")
        print(f"  python3 jev.py --cas {slug} --csv {fichier} --apply")
        return 2
    res = jev_csv.executer(qpath, fichier, apply=True, limit=a.limit, seuil=a.seuil)
    sortie = res.get("sortie", "")
    print(f"\nLe fichier de sortie est {sortie}. Regarde d'abord les lignes a_verifier = 1 : ce sont celles où Jev hésite.")
    return 1 if res.get("erreurs") else 0


if __name__ == "__main__":
    sys.exit(main())
