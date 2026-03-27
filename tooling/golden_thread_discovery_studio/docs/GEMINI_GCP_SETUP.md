# Gemini API im GCP-Projekt einrichten

Damit das Discovery Studio Gemini nutzen kann, muss die **Generative Language API** in deinem Google-Cloud-Projekt aktiviert sein und du brauchst einen API-Key.

## Option A: Über die GCP-Konsole (ohne gcloud)

1. **Projekt auswählen**
   - Öffne [Google Cloud Console](https://console.cloud.google.com/) und wähle dein Projekt.

2. **API aktivieren**
   - Gehe zu [APIs & Services → Bibliothek](https://console.cloud.google.com/apis/library).
   - Suche nach **„Generative Language API”**.
   - Öffne den Eintrag und klicke auf **„Aktivieren”**.

3. **API-Key erstellen**
   - Gehe zu [APIs & Services → Anmeldedaten](https://console.cloud.google.com/apis/credentials).
   - **„+ Anmeldedaten erstellen”** → **„API-Schlüssel”**.
   - Der Schlüssel wird erstellt; optional kannst du ihn einschränken (z. B. nur „Generative Language API”).
   - Key kopieren und in `.env` eintragen: `GOOGLE_API_KEY=<dein-key>`.

---

## Option B: Über die Kommandozeile (gcloud)

Voraussetzung: [gcloud CLI](https://cloud.google.com/sdk/docs/install) installiert und eingeloggt (`gcloud auth login`).

### 1. Projekt setzen

```bash
gcloud config set project DEINE_PROJEKT_ID
```

### 2. API aktivieren

```bash
gcloud services enable generativelanguage.googleapis.com
```

### 3. API-Key erstellen (Konsole)

Einen API-Schlüssel kannst du per gcloud nicht erstellen; dafür weiterhin [Anmeldedaten → API-Schlüssel erstellen](https://console.cloud.google.com/apis/credentials) in der Konsole nutzen.  
Alternativ: Key in [Google AI Studio](https://aistudio.google.com/app/apikey) erstellen (derselbe Key funktioniert, wenn die API im GCP-Projekt aktiv ist).

---

## Option C: Nur Google AI Studio (ohne GCP-Projekt)

- Zu [Google AI Studio → API Key](https://aistudio.google.com/app/apikey) gehen.
- Key erstellen und in `.env` als `GOOGLE_API_KEY=` eintragen.  
- Für die Nutzung im Studio reicht das; die Abrechnung läuft dann über den AI-Studio-Account.

---

## 404 „model not found“ / „not supported for generateContent“

Der Standard-Model-Name ist `gemini-2.5-flash`. Wenn dein Key oder deine Region das Modell nicht unterstützt, setze in `.env` z. B.:

- `GEMINI_MODEL=gemini-2.0-flash` oder
- `GEMINI_MODEL=gemini-1.5-flash-002`

Aktuelle Modell-Liste: [Gemini API – Models](https://ai.google.dev/gemini-api/docs/models).

---

## Kurzfassung

| Schritt              | Wo / Befehl |
|----------------------|-------------|
| API aktivieren       | Konsole: „Generative Language API” aktivieren **oder** `gcloud services enable generativelanguage.googleapis.com` |
| API-Key holen        | [Konsole → Anmeldedaten](https://console.cloud.google.com/apis/credentials) oder [AI Studio](https://aistudio.google.com/app/apikey) |
| Studio konfigurieren | In `.env`: `GOOGLE_API_KEY=<key>` setzen |

Nach dem Aktivieren der API und Eintragen des Keys im Repo-Root in `.env` startest du das Studio neu; dann wird Gemini genutzt.
