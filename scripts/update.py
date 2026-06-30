#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Met à jour automatiquement les résultats du Pool Coupe du Monde 2026.
Lit un flux de résultats ouvert (fixturedownload.com), reconstruit le tableau
MATCHES dans index.html, rafraîchit la date « Maj ». Le classement et l'analyse
du jour se recalculent ensuite tout seuls côté navigateur.

Lancé chaque matin par GitHub Actions. Si rien n'a changé, aucun commit n'est fait.
"""
import json, re, sys, urllib.request, datetime, unicodedata, os

FEED = "https://fixturedownload.com/feed/json/fifa-world-cup-2026"
HTML = os.path.join(os.path.dirname(__file__), "..", "index.html")

# --- équipes : alias (flux, en anglais) -> nom FR utilisé dans le site ---
FR = {
"mexico":"Mexique","south africa":"Afrique du Sud","korea republic":"Corée du Sud",
"south korea":"Corée du Sud","czechia":"Tchéquie","czech republic":"Tchéquie",
"canada":"Canada","bosnia and herzegovina":"Bosnie-Herzégovine","bosnia & herzegovina":"Bosnie-Herzégovine",
"bosnia":"Bosnie-Herzégovine","qatar":"Qatar","switzerland":"Suisse","brazil":"Brésil",
"morocco":"Maroc","haiti":"Haïti","scotland":"Écosse","united states":"États-Unis","usa":"États-Unis",
"paraguay":"Paraguay","australia":"Australie","turkey":"Turquie","turkiye":"Turquie","türkiye":"Turquie",
"germany":"Allemagne","curacao":"Curaçao","ivory coast":"Côte d'Ivoire","cote d'ivoire":"Côte d'Ivoire",
"ecuador":"Équateur","netherlands":"Pays-Bas","japan":"Japon","sweden":"Suède","tunisia":"Tunisie",
"belgium":"Belgique","egypt":"Égypte","iran":"Iran","ir iran":"Iran","new zealand":"Nouvelle-Zélande",
"spain":"Espagne","cape verde":"Cap-Vert","cabo verde":"Cap-Vert","saudi arabia":"Arabie saoudite",
"uruguay":"Uruguay","france":"France","senegal":"Sénégal","iraq":"Irak","norway":"Norvège",
"argentina":"Argentine","algeria":"Algérie","austria":"Autriche","jordan":"Jordanie","portugal":"Portugal",
"dr congo":"RD Congo","congo dr":"RD Congo","democratic republic of the congo":"RD Congo","drc":"RD Congo",
"uzbekistan":"Ouzbékistan","colombia":"Colombie","england":"Angleterre","croatia":"Croatie",
"ghana":"Ghana","panama":"Panama",
}
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower().strip()
    return re.sub(r"\s+"," ",s)
def fr(team):
    return FR.get(norm(team))

MONTHS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]

# KO : le flux fixturedownload n'a pas de champ Group pour les rondes éliminatoires ;
# il fournit un entier RoundNumber. Mapping validé sur le flux 2026 (16/8/4/2/2 matchs).
ROUND_BY_NUMBER = {4: "R32", 5: "R16", 6: "QF", 7: "SF", 8: "F"}

# Vainqueurs aux tirs de but : le flux ne donne que le score réglementaire (ex. 1-1).
# Clé : (date_Est "AAAA-MM-JJ", ÉquipeA_FR, ÉquipeB_FR) -> vainqueur_FR.
# À COMPLÉTER à chaque match nul en ronde éliminatoire (sinon les points ne sont pas attribués).
PENALTY_WINNERS = {
    ("2026-06-29", "Allemagne", "Paraguay"): "Paraguay",
    ("2026-06-29", "Pays-Bas", "Maroc"): "Maroc",
}

def round_of(group_field):
    # Matchs KO : group_field est un entier (RoundNumber)
    if isinstance(group_field, int):
        return ROUND_BY_NUMBER.get(group_field)  # None si inconnu -> ignoré
    g = (str(group_field) if group_field is not None else "").strip().lower()
    if g.startswith("group"): return "group"
    if "round of 32" in g or "r32" in g: return "R32"
    if "round of 16" in g or "r16" in g: return "R16"
    if "quarter" in g: return "QF"
    if "semi" in g: return "SF"
    if "third" in g or "bronze" in g or "play-off" in g: return None  # 3e place : hors pointage
    if "final" in g: return "F"
    return None  # inconnu -> on ignore par prudence

def winner_of(et, a, ha, b, ab, rnd):
    # Renvoie le vainqueur FR pour une ronde KO, sinon None (matchs de groupe : pas de vainqueur unique).
    if rnd == "group":
        return None
    if ha > ab:
        return a
    if ab > ha:
        return b
    return PENALTY_WINNERS.get((et, a, b))  # nul -> décidé aux tirs de but

def fetch():
    req = urllib.request.Request(FEED, headers={"User-Agent":"pool-refrigaz/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def build_matches(data):
    rows = []
    # RN8 contient la finale ET le match pour la 3e place. La vraie finale est le
    # dernier match du tournoi (plus grand MatchNumber) ; l'autre est hors pointage.
    final_mn = max((m.get("MatchNumber", 0) for m in data if m.get("RoundNumber") == 8), default=None)
    for m in data:
        ha, aa = m.get("HomeTeamScore"), m.get("AwayTeamScore")
        if ha is None or aa is None:
            continue  # match pas encore joué
        a, b = fr(m.get("HomeTeam","")), fr(m.get("AwayTeam",""))
        if not a or not b:
            print("⚠️ équipe non reconnue:", m.get("HomeTeam"), "/", m.get("AwayTeam"), file=sys.stderr)
            continue
        rnd = round_of(m.get("Group") or m.get("RoundNumber"))
        if rnd is None:
            continue
        # Exclut le match pour la 3e place (RN8 qui n'est pas la finale).
        if m.get("RoundNumber") == 8 and final_mn is not None and m.get("MatchNumber") != final_mn:
            continue
        try:
            dt = datetime.datetime.fromisoformat(m["DateUtc"].replace("Z","+00:00"))
        except Exception:
            continue
        et = (dt - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")  # UTC -> heure de l'Est
        w = winner_of(et, a, int(ha), b, int(aa), rnd)
        rows.append((et, m.get("DateUtc"), a, int(ha), b, int(aa), rnd, w))
    rows.sort(key=lambda x: x[1])  # tri chronologique
    def fmt_row(et, a, ha, b, ab, rnd, w):
        # 7e champ "vainqueur" ajouté seulement en ronde KO quand il est connu.
        if w is None:
            return f' ["{et}","{a}",{ha},"{b}",{ab},"{rnd}"],'
        return f' ["{et}","{a}",{ha},"{b}",{ab},"{rnd}","{w}"],'
    lines = [fmt_row(et, a, ha, b, ab, rnd, w) for (et, _, a, ha, b, ab, rnd, w) in rows]
    return "const MATCHES = [\n" + "\n".join(lines) + "\n];", len(rows)

def main():
    data = fetch()
    block, n = build_matches(data)
    html = open(HTML, encoding="utf-8").read()
    new = re.sub(r"const MATCHES = \[.*?\];", lambda _: block, html, count=1, flags=re.S)
    today = datetime.date.today()
    datestr = f"{today.day} {MONTHS[today.month-1]} {today.year}"
    new = re.sub(r'(<b id="m-updated">)[^<]*(</b>)', r'\g<1>'+datestr+r'\g<2>', new)
    new = re.sub(r'Résultats à jour au [^<·]*', f'Résultats à jour au {datestr} ', new)
    if new != html:
        open(HTML,"w",encoding="utf-8").write(new)
        print(f"✅ index.html mis à jour — {n} matchs joués, daté du {datestr}.")
    else:
        print(f"ℹ️ Aucun changement ({n} matchs joués).")

if __name__ == "__main__":
    main()
