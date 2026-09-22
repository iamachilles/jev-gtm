#!/usr/bin/env python3
"""Fait décider Jev (TypeSafe) sur chaque ligne d'un CSV, à partir d'une question prête à l'emploi.

Aucune dépendance à installer : bibliothèque standard Python 3.10 ou plus.

    python3 jev_csv.py --question questions/intitule-role.json --csv ma_liste.csv --dry-run
    python3 jev_csv.py --question questions/intitule-role.json --csv ma_liste.csv --apply

Sans `--apply`, rien ne part sur le réseau : le script relit le CSV, vérifie les colonnes,
estime le nombre de tokens et le coût, et s'arrête. Avec `--apply`, il appelle l'API
TypeSafe (clé `TYPESAFE_API_KEY` dans l'environnement ou dans un fichier `.env` à côté),
met chaque réponse en cache (`.cache/<slug>.jsonl`, jamais repayée) et écrit un CSV de
sortie avec, pour chaque question, la décision, la confiance et les probabilités.

Le CSV de sortie ajoute une colonne `a_verifier` : 1 quand la confiance d'au moins une
question passe sous le seuil du fichier de question. C'est la ligne à faire relire par
un humain ou par un LLM, les autres se traitent automatiquement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

API = "https://api.typesafe.ai/v1/systemone"
MODELE = "jev-latest"
PRIX_PAR_MILLION_TOKENS = 0.042  # 42 $ le milliard de tokens en entrée, sortie gratuite (docs.typesafe.ai, sept. 2026)
CHARS_PAR_TOKEN = 3.5  # estimation prudente pour de l'anglais et du français mélangés


def charger_env() -> None:
    """Lit un fichier .env à côté du script, sans écraser l'environnement."""
    env = Path(__file__).resolve().parent / ".env"
    if not env.exists():
        return
    for ligne in env.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            k, v = ligne.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def charger_question(chemin: Path) -> dict:
    q = json.loads(chemin.read_text(encoding="utf-8"))
    for cle in ("slug", "titre", "colonnes", "questions"):
        if cle not in q:
            sys.exit(f"Fichier de question invalide : clé {cle!r} absente dans {chemin}")
    q.setdefault("seuil_confiance", 0.9)
    q.setdefault("model", MODELE)
    return q


def lire_csv(chemin: Path, limite: int | None) -> tuple[list[str], list[dict]]:
    with chemin.open(encoding="utf-8-sig", newline="") as f:
        lecteur = csv.DictReader(f)
        colonnes = lecteur.fieldnames or []
        lignes = [dict(l) for l in lecteur]
    if limite:
        lignes = lignes[:limite]
    return colonnes, lignes


def construire_state(question: dict, ligne: dict) -> dict:
    """Le state envoyé à Jev : les colonnes listées dans le fichier de question, tronquées."""
    max_chars = question.get("max_chars_par_colonne", 3000)
    state = {}
    for col in question["colonnes"]:
        if isinstance(col, dict):  # {"cle": "sirene", "colonnes": ["nom", "ville"]} -> sous-objet
            state[col["cle"]] = {c: (ligne.get(c) or "")[:max_chars] for c in col["colonnes"]}
        else:
            state[col] = (ligne.get(col) or "")[:max_chars]
    return state


def colonnes_attendues(question: dict) -> list[str]:
    cols: list[str] = []
    for col in question["colonnes"]:
        cols.extend(col["colonnes"] if isinstance(col, dict) else [col])
    return cols


def questions_api(question: dict) -> dict:
    """Les questions telles qu'envoyées à l'API : sans les clés privées (préfixe `_`) du fichier."""
    return {qid: {k: v for k, v in q.items() if not k.startswith("_")} for qid, q in question["questions"].items()}


def estimer_tokens(question: dict, state: dict) -> int:
    corps = json.dumps({"state": state, "questions": questions_api(question)}, ensure_ascii=False)
    return int(len(corps) / CHARS_PAR_TOKEN) + 40


def cle_cache(question: dict, state: dict) -> str:
    return hashlib.sha1(json.dumps([questions_api(question), state], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def appeler(question: dict, state: dict, api_key: str, essais: int = 8) -> dict:
    corps = json.dumps({"state": state, "model": question["model"], "questions": questions_api(question)}, ensure_ascii=False).encode()
    attente = 0.5
    for essai in range(essais):
        req = urllib.request.Request(API, data=corps, method="POST", headers={
            "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and essai < essais - 1:
                time.sleep(attente)
                attente = min(attente * 2, 8)
                continue
            detail = e.read().decode(errors="replace")[:300]
            raise RuntimeError(f"HTTP {e.code} : {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if essai < essais - 1:
                time.sleep(attente)
                attente = min(attente * 2, 8)
                continue
            raise RuntimeError(f"réseau : {e}") from e
    raise RuntimeError("appel abandonné")


def aplatir(qid: str, rep: dict, question_def: dict) -> dict:
    """Une réponse Jev -> des colonnes CSV plates."""
    t = rep.get("type")
    out: dict = {}
    if t == "choice":
        out[qid] = rep.get("choice", "")
        out[f"{qid}_confidence"] = rep.get("confidence", "")
        for opt, p in (rep.get("probabilities") or {}).items():
            out[f"{qid}_p_{opt}"] = round(p, 4)
    elif t == "score":
        niveaux = question_def.get("criteria", [])
        base = question_def.get("_base", 0)  # valeur du premier niveau (0 par défaut, 1 pour un barème 1 à 5)
        score = rep.get("score")
        out[qid] = round(score + base, 3) if isinstance(score, (int, float)) else ""
        probs = rep.get("probabilities") or {}
        if probs:
            meilleur = max(probs, key=probs.get)
            out[f"{qid}_niveau"] = int(meilleur) + base
        out[f"{qid}_confidence"] = rep.get("confidence", "")
        for k, p in probs.items():
            out[f"{qid}_p_{int(k) + base}"] = round(p, 4)
        out[f"{qid}_legende"] = " | ".join(f"{i + base}: {n}" for i, n in enumerate(niveaux))
    elif t == "noul":
        p = rep.get("noul")
        out[qid] = "oui" if isinstance(p, (int, float)) and p >= 0.5 else "non"
        out[f"{qid}_p_oui"] = round(p, 4) if isinstance(p, (int, float)) else ""
        # confiance d'un oui/non : distance au milieu, ramenée entre 0 et 1
        out[f"{qid}_confidence"] = round(abs(p - 0.5) * 2, 4) if isinstance(p, (int, float)) else ""
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--question", required=True, type=Path, help="fichier questions/<slug>.json")
    ap.add_argument("--csv", required=True, type=Path, help="CSV d'entrée (UTF-8, en-tête sur la première ligne)")
    ap.add_argument("--out", type=Path, help="CSV de sortie (défaut : <entrée>.out.csv)")
    ap.add_argument("--apply", action="store_true", help="appelle vraiment l'API (payant) ; sans ce drapeau, estimation seule")
    ap.add_argument("--dry-run", action="store_true", help="explicite : estimation seule (comportement par défaut)")
    ap.add_argument("--limit", type=int, help="ne traiter que les N premières lignes")
    ap.add_argument("--workers", type=int, default=8, help="appels en parallèle (défaut 8)")
    ap.add_argument("--seuil", type=float, help="seuil de confiance sous lequel la ligne passe en a_verifier (défaut : celui du fichier de question)")
    a = ap.parse_args()

    charger_env()
    question = charger_question(a.question)
    colonnes, lignes = lire_csv(a.csv, a.limit)
    manquantes = [c for c in colonnes_attendues(question) if c not in colonnes]
    if manquantes:
        sys.exit(f"Colonnes absentes du CSV : {manquantes}. Colonnes trouvées : {colonnes}. Renomme tes colonnes ou adapte `colonnes` dans {a.question}.")
    seuil = a.seuil if a.seuil is not None else question["seuil_confiance"]
    states = [construire_state(question, l) for l in lignes]
    tokens = sum(estimer_tokens(question, s) for s in states)
    cout = tokens / 1_000_000 * PRIX_PAR_MILLION_TOKENS
    print(f"{question['titre']} ({question['slug']})")
    print(f"{len(lignes)} lignes, {len(question['questions'])} question(s) par ligne, ~{tokens:,} tokens en entrée, coût estimé ~{cout:.4f} $ (sortie gratuite)")
    if not a.apply:
        print("Estimation seule. Ajoute --apply pour lancer les appels.")
        return 0

    api_key = os.environ.get("TYPESAFE_API_KEY", "")
    if not api_key:
        sys.exit("TYPESAFE_API_KEY absent (environnement ou fichier .env à côté du script)")
    cache_path = Path(__file__).resolve().parent / ".cache" / f"{question['slug']}.jsonl"
    cache_path.parent.mkdir(exist_ok=True)
    cache: dict[str, dict] = {}
    if cache_path.exists():
        for l in cache_path.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                cache[d["cle"]] = d["reponse"]
    a_faire = [(i, s) for i, s in enumerate(states) if cle_cache(question, s) not in cache]
    print(f"{len(states) - len(a_faire)} réponses en cache, {len(a_faire)} appels à faire")
    erreurs = 0
    tokens_reels = 0
    debut = time.time()
    with cache_path.open("a", encoding="utf-8") as fc, ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(appeler, question, s, api_key): (i, s) for i, s in a_faire}
        for n, fut in enumerate(as_completed(futs), 1):
            i, s = futs[fut]
            try:
                rep = fut.result()
            except Exception as e:  # noqa: BLE001
                erreurs += 1
                print(f"  ligne {i + 1}: erreur {e}", file=sys.stderr)
                continue
            cache[cle_cache(question, s)] = rep
            fc.write(json.dumps({"cle": cle_cache(question, s), "reponse": rep}, ensure_ascii=False) + "\n")
            tokens_reels += (rep.get("usage") or {}).get("input_tokens", 0)
            if n % 50 == 0 or n == len(a_faire):
                print(f"  {n}/{len(a_faire)} ({time.time() - debut:.0f} s)", flush=True)

    sortie = a.out or a.csv.with_suffix(".out.csv")
    nouvelles: list[str] = []
    rangs = []
    for ligne, s in zip(lignes, states):
        rep = cache.get(cle_cache(question, s))
        r = dict(ligne)
        verif = 0
        if rep:
            for qid, qdef in question["questions"].items():
                plat = aplatir(qid, rep["answers"].get(qid, {}), qdef)
                r.update(plat)
                conf = plat.get(f"{qid}_confidence")
                if isinstance(conf, (int, float)) and conf < seuil:
                    verif = 1
        else:
            verif = 1
        r["a_verifier"] = verif
        for k in r:
            if k not in colonnes and k not in nouvelles:
                nouvelles.append(k)
        rangs.append(r)
    with sortie.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes + nouvelles)
        w.writeheader()
        w.writerows(rangs)
    n_verif = sum(r["a_verifier"] for r in rangs)
    print(f"{len(rangs)} lignes écrites dans {sortie} ; {n_verif} à vérifier (confiance < {seuil}) ; {erreurs} erreurs")
    if tokens_reels:
        print(f"{tokens_reels:,} tokens facturés sur cet appel, soit {tokens_reels / 1_000_000 * PRIX_PAR_MILLION_TOKENS:.4f} $")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
