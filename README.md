# Planning-2 — Tri automatique des mails + résumé matinal

Chaque matin vers 8h (heure de Paris), un workflow GitHub Actions :

1. lit les mails non lus de la boîte de réception Gmail ;
2. les classe en **Important** ou **Pub** (règles simples + Claude pour les
   cas ambigus) et les déplace dans le label Gmail correspondant ;
3. marque les mails **Pub** comme lus ;
4. envoie un résumé des mails **Important** sur WhatsApp (via Twilio).

## Mise en place (à faire une seule fois)

### 1. Créer les labels Gmail
Rien à faire : les labels `Important` et `Pub` sont créés automatiquement au
premier lancement.

### 2. Créer des identifiants OAuth Gmail

1. Va sur [Google Cloud Console](https://console.cloud.google.com/), crée un
   projet, puis active l'**API Gmail**.
2. Dans "Identifiants" → "Créer des identifiants" → "ID client OAuth", choisis
   le type **Application de bureau**. Télécharge le fichier JSON
   (`client_secret.json`).
3. Configure l'écran de consentement OAuth (mode "Externe" possible en mode
   test, avec ton propre compte Gmail comme utilisateur de test).
4. En local (pas en CI), installe les dépendances puis lance :

   ```bash
   pip install -r requirements.txt
   PYTHONPATH=src python scripts/generate_gmail_token.py /chemin/vers/client_secret.json
   ```

   Une page de connexion Google s'ouvre ; connecte-toi avec le compte Gmail à
   surveiller. Le script affiche un **refresh token** à la fin.

### 3. Créer un compte Twilio (WhatsApp)

1. Crée un compte sur [twilio.com](https://www.twilio.com/).
2. Active le **WhatsApp Sandbox** (Messaging → Try it out → Send a WhatsApp
   message), et suis les instructions pour relier ton propre numéro WhatsApp
   au sandbox (envoi d'un message "join ..." depuis WhatsApp).
3. Récupère l'**Account SID**, l'**Auth Token**, le numéro WhatsApp du
   sandbox (`from`, format `+14155238886` par défaut) et note ton propre
   numéro WhatsApp au format international (`to`, ex. `+33612345678`).

### 4. Clé API Anthropic

Récupère une clé API sur [console.anthropic.com](https://console.anthropic.com/).

### 5. Ajouter les secrets sur GitHub

Dans le repo GitHub : Settings → Secrets and variables → Actions → New
repository secret. Ajoute :

| Secret | Valeur |
|---|---|
| `GMAIL_CLIENT_ID` | `client_id` du fichier `client_secret.json` |
| `GMAIL_CLIENT_SECRET` | `client_secret` du fichier `client_secret.json` |
| `GMAIL_REFRESH_TOKEN` | Refresh token généré à l'étape 2.4 |
| `ANTHROPIC_API_KEY` | Clé API Anthropic |
| `TWILIO_ACCOUNT_SID` | Account SID Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token Twilio |
| `TWILIO_WHATSAPP_FROM` | Numéro WhatsApp Twilio (ex. `+14155238886`) |
| `TWILIO_WHATSAPP_TO` | Ton numéro WhatsApp (ex. `+33612345678`) |

### 6. C'est prêt

Le workflow `.github/workflows/daily-email-sort.yml` tourne automatiquement
chaque matin. Tu peux aussi le déclencher manuellement depuis l'onglet
"Actions" du repo GitHub ("Run workflow").

## Pourquoi deux horaires de cron ?

Le cron GitHub Actions est en UTC, et Paris change d'heure (CET/CEST). Le
workflow se déclenche à 6h **et** 7h UTC ; le script (`main.py`) vérifie
l'heure réelle à Paris et ne fait le travail que si on est bien à 8h,
l'autre déclenchement ne fait rien.

## Personnaliser le tri

Les règles de tri (mots-clés, expéditeurs) sont dans
`src/email_sorter/classifier.py`. Tout ce qui n'est pas reconnu par une règle
est classé par Claude.

## Lancer les tests

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m pytest
```
