#!/usr/bin/env python3
"""Vérifie la cohérence du dépôt : questions valides, CSV d'exemple alignés, README à jour.

    python3 verifier.py        # sort 0 si tout passe, 1 sinon

Aucun appel réseau. À lancer après avoir modifié une question ou un CSV.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
TYPES = {"choice", "score", "noul"}
TIRETS = re.compile("[\u2013\u2014]")
ok = True


def verif(cond: bool, msg: str) -> None:
    global ok
    print(("PASS " if cond else "FAIL ") + msg)
    ok = ok and cond


def colonnes_attendues(q: dict) -> list[str]:
    cols: list[str] = []
    for c in q["colonnes"]:
        cols.extend(c["colonnes"] if isinstance(c, dict) else [c])
    return cols


def est_anglais(texte: str) -> bool:
    """Heuristique : les critères sont en anglais quand ils ne portent aucun mot-outil français très fréquent."""
    t = " " + re.sub(r"[^a-zàâçéèêëîïôûùüÿ' ]", " ", texte.lower()) + " "
    mots_fr = (" les ", " des ", " une ", " est ", " pour ", " dans ", " avec ", " sur ", " qui ", " pas ", " vous ", " nous ")
    return sum(t.count(m) for m in mots_fr) <= 2


catalogue = json.loads((RACINE / "catalogue.json").read_text(encoding="utf-8"))
attendus = [(c["id"], x["slug"]) for c in catalogue["categories"] for x in c["cas"]]
verif(len(attendus) == 50, f"{len(attendus)} cas au catalogue (attendu 50)")
verif(len({s for _, s in attendus}) == len(attendus), "slugs du catalogue uniques")
questions = sorted((RACINE / "questions").glob("*.json"))
orphelines = sorted(q.stem for q in questions if q.stem not in {s for _, s in attendus})
verif(not orphelines, f"aucune question hors catalogue ({orphelines or 'ok'})")
readme = (RACINE / "README.md").read_text(encoding="utf-8")
for cat_id, slug in attendus:
    chemin = RACINE / "questions" / f"{slug}.json"
    if not chemin.exists():
        verif(False, f"questions/{slug}.json présent")
        continue
    try:
        q = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        verif(False, f"{chemin.name} : JSON invalide ({e})")
        continue
    verif(q.get("slug") == slug, f"{chemin.name} : slug = nom du fichier")
    verif(q.get("categorie") == cat_id, f"{chemin.name} : categorie {q.get('categorie')!r} = {cat_id!r}")
    verif(all(k in q for k in ("titre", "description", "colonnes", "questions", "seuil_confiance")), f"{chemin.name} : clés de base présentes")
    verif(0 < float(q.get("seuil_confiance", 0)) <= 1, f"{chemin.name} : seuil_confiance dans ]0, 1]")
    verif(1 <= len(q.get("questions", {})) <= 6, f"{chemin.name} : 1 à 6 questions")
    for qid, qd in q.get("questions", {}).items():
        verif(qd.get("type") in TYPES, f"{chemin.name}/{qid} : type {qd.get('type')!r} dans {sorted(TYPES)}")
        verif(bool(qd.get("instructions")), f"{chemin.name}/{qid} : instructions non vides")
        crit = qd.get("criteria")
        if qd.get("type") == "choice":
            verif(isinstance(crit, dict) and 2 <= len(crit) <= 255, f"{chemin.name}/{qid} : choice avec 2 à 255 options")
        elif qd.get("type") == "score":
            verif(isinstance(crit, list) and 2 <= len(crit) <= 10, f"{chemin.name}/{qid} : score avec 2 à 10 niveaux")
        elif qd.get("type") == "noul":
            verif(crit is None or (isinstance(crit, dict) and set(crit) <= {"true", "false"}), f"{chemin.name}/{qid} : noul avec criteria true/false ou absent")
        texte = json.dumps({k: v for k, v in qd.items() if not k.startswith("_")}, ensure_ascii=False)
        verif(est_anglais(texte), f"{chemin.name}/{qid} : instructions et critères en anglais")
    verif(not TIRETS.search(chemin.read_text(encoding="utf-8")), f"{chemin.name} : aucun tiret cadratin")
    exemple = RACINE / "samples" / f"{slug}.csv"
    verif(exemple.exists(), f"samples/{slug}.csv présent")
    if exemple.exists():
        with exemple.open(encoding="utf-8-sig", newline="") as f:
            lecteur = csv.DictReader(f)
            cols = lecteur.fieldnames or []
            lignes = list(lecteur)
        manq = [c for c in colonnes_attendues(q) if c not in cols]
        verif(not manq, f"samples/{slug}.csv : colonnes attendues présentes ({manq or 'ok'})")
        verif(len(lignes) == 10, f"samples/{slug}.csv : {len(lignes)} lignes (attendu 10)")
        vides = sum(1 for l in lignes for c in colonnes_attendues(q) if not (l.get(c) or "").strip())
        verif(vides <= 1, f"samples/{slug}.csv : au plus une cellule vide dans les colonnes attendues, le cas limite voulu ({vides})")
        verif(not TIRETS.search(exemple.read_text(encoding="utf-8")), f"samples/{slug}.csv : aucun tiret cadratin")
    verif(f"`{slug}`" in readme, f"README cite `{slug}`")

verif(not TIRETS.search(readme), "README : aucun tiret cadratin")
skill = RACINE / "skill" / "jev-prospection" / "SKILL.md"
verif(skill.exists() and skill.read_text(encoding="utf-8").startswith("---"), "skill/jev-prospection/SKILL.md présent avec un frontmatter")
verif((RACINE / "jev_csv.py").exists(), "jev_csv.py présent")
verif((RACINE / "jev.py").exists(), "jev.py présent")
verif((RACINE / "LICENSE").exists(), "LICENSE présent")
print("PASS" if ok else "FAIL", "vérification du dépôt")
sys.exit(0 if ok else 1)
