# Pool Coupe du Monde 2026 — Solution Réfrigaz (site full auto)

Site web du pool qui se met à jour **tout seul chaque matin** : un robot GitHub
va chercher les résultats, reconstruit la page, et Netlify republie. Ton ordi
peut être fermé — tout tourne dans le cloud. **Le lien à partager ne change jamais.**

## Ce qu'il y a dans ce dossier
- `index.html` — le site complet (autonome).
- `scripts/update.py` — va chercher les résultats et met à jour le site.
- `.github/workflows/daily.yml` — le robot qui lance le script chaque matin (8h, heure de l'Est).

---

## Configuration — une seule fois (~10 min)

### 1) Créer un compte GitHub (gratuit)
Va sur https://github.com → **Sign up**. (Je ne peux pas le faire à ta place.)

### 2) Créer le dépôt et y déposer ces fichiers
- En haut à droite : **+ → New repository**.
- Nom : `pool-refrigaz` · garde-le **Public** · clique **Create repository**.
- Sur la page du dépôt : **Add file → Upload files**, puis **glisse le contenu de ce
  dossier** (en gardant la structure : `index.html`, le dossier `scripts/`, et le
  dossier `.github/`). Clique **Commit changes**.
  - Astuce : glisse les dossiers eux-mêmes pour conserver les chemins. Si GitHub ne
    garde pas l'arborescence, crée les fichiers à la main avec **Add file → Create new file**
    et tape le chemin exact (ex. `.github/workflows/daily.yml`).

### 3) Brancher Netlify sur le dépôt (déploiement continu)
- Sur https://app.netlify.com : **Add new site → Import an existing project → GitHub**.
- Autorise GitHub, choisis le dépôt `pool-refrigaz`.
- **Build command** : laisse **vide**. **Publish directory** : `.` (la racine).
- **Deploy**. Netlify te donne l'URL (ex. `pool-refrigaz.netlify.app`) — renomme-la
  dans *Site configuration → Change site name*. **C'est cette URL que tu partages.**
- À partir de maintenant, **chaque mise à jour dans GitHub redéploie automatiquement**.

### 4) Tester le robot tout de suite
- Dans le dépôt GitHub : onglet **Actions → Maj quotidienne du pool → Run workflow**.
- En ~30 sec il va chercher les résultats, committe si besoin, et Netlify republie.
- Recharge ton URL Netlify : le classement reflète les derniers scores.

✅ **C'est fini.** Chaque matin vers 8h (heure de l'Est), le robot tourne seul.

---

## Bon à savoir (transparence)
- **Source des résultats** : flux ouvert `fixturedownload.com/feed/json/fifa-world-cup-2026`.
  Si une équipe n'est pas reconnue, elle est ignorée et signalée dans les logs Actions
  (rare). Si la source est momentanément indisponible, le site garde les derniers résultats.
- **Heure** : le cron est à 12:00 UTC = 8h00 HE pendant le tournoi (EDT).
- **Rondes éliminatoires** : le pointage (16es=2, 8es=3, quarts=4, demis=5, finale=6 × cote)
  est géré automatiquement dès que le flux fournit ces matchs.
- **Calendrier « matchs du jour »** : déjà intégré et basé sur la date du visiteur —
  il change tout seul même sans redéploiement.
- **Courriel-récap de 8h** : géré séparément par la tâche planifiée dans l'app Cowork
  (elle te prépare le texte à envoyer). Le robot GitHub, lui, s'occupe du **site**.
