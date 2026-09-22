#!/usr/bin/env python3
"""Fait tourner Jev sur les 50 fichiers d'exemple, une fois, et écrit samples/<slug>.out.csv.

Garde-fou de coût : un exemple dont la sortie existe déjà est sauté (sauf `--force`). Sans `--apply`,
le script n'estime que le coût total. La clé vient de `TYPESAFE_API_KEY`.

    python3 run_samples.py            # estimation totale, aucun appel
    python3 run_samples.py --apply    # les appels, seulement pour les exemples sans sortie
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jev_csv

RACINE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true", help="rejouer même les exemples qui ont déjà une sortie")
    ap.add_argument("--only", nargs="*", help="slugs à traiter")
    a = ap.parse_args()
    cat = json.loads((RACINE / "catalogue.json").read_text(encoding="utf-8"))
    slugs = [x["slug"] for c in cat["categories"] for x in c["cas"]]
    if a.only:
        slugs = [s for s in slugs if s in set(a.only)]
    total_est = total_reel = 0.0
    faits = sautes = erreurs = 0
    for slug in slugs:
        q = RACINE / "questions" / f"{slug}.json"
        csvp = RACINE / "samples" / f"{slug}.csv"
        outp = RACINE / "samples" / f"{slug}.out.csv"
        if not q.exists() or not csvp.exists():
            print(f"  {slug}: fichiers manquants, sauté", file=sys.stderr)
            erreurs += 1
            continue
        if a.apply and outp.exists() and not a.force:
            sautes += 1
            continue
        res = jev_csv.executer(q, csvp, apply=a.apply, out=outp, workers=4, silencieux=True)
        total_est += res["cout_estime"]
        if a.apply:
            total_reel += res.get("cout_reel", 0.0)
            erreurs += res.get("erreurs", 0)
            faits += 1
            print(f"  {slug}: {res['lignes']} lignes, {res.get('a_verifier')} à vérifier, {res.get('erreurs')} erreurs, {res.get('cout_reel', 0):.4f} $", flush=True)
    print(f"{len(slugs)} cas ; estimation {total_est:.4f} $" + (f" ; {faits} passés, {sautes} sautés (sortie déjà là), {erreurs} erreurs, coût réel {total_reel:.4f} $" if a.apply else " (aucun appel, ajoute --apply)"))
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
