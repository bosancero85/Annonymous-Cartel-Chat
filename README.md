# Annonymus-Cartel-Chat-
Annonymus Cartel-Chat with Military Grade Encryption
# 🛡️ Cartel-Chat
**Cartel-Chat** ist ein moderner, hochsicherer IRC-Klon, der auf Python basiert. Er kombiniert die nostalgische Chat-Struktur von mIRC mit modernem UI-Design und echter **Military Grade** End-to-End-Verschlüsselung (E2EE).

## ✨ Features
* **AES-256-GCM Verschlüsselung:** Jede Nachricht wird verschlüsselt, bevor sie den Client verlässt.
* **Zero-Knowledge-Server:** Der Server leitet nur verschlüsselte Datenpakete weiter und kann keine Nachrichten mitlesen.
* **Modernes UI:** Dunkles, elegantes Design mit `CustomTkinter`.
* **Standalone:** Kann als `.exe` für Windows kompiliert werden.

## 🚀 Installation & Start

### Voraussetzungen
Stelle sicher, dass Python 3.9+ installiert ist.

1. **Repository klonen:**
   ```bash
   git clone [https://github.com/DEIN_USERNAME/Cartel-Chat.git](https://github.com/DEIN_USERNAME/Cartel-Chat.git)
   cd Cartel-Chat
   ```
2. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```
3. Server starten:
   ```bash
   python server.py
   ```
4. Client starten:
   ```bash
   python client.py
   ```
## 🌐 Netzwerk- & Tunnel-Konfiguration (ngrok)
​Da das Projekt auf reinen TCP-Sockets basiert, ist ngrok die eleganteste Methode, um den Server ohne riskante Portfreigaben im Heim-Router weltweit erreichbar zu machen.
​1. ngrok auf Kali Linux installieren (falls nicht vorhanden)

```bash
curl -s [https://ngrok-agent.s3.amazonaws.com/ngrok.asc](https://ngrok-agent.s3.amazonaws.com/ngrok.asc) | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb [https://ngrok-agent.s3.amazonaws.com](https://ngrok-agent.s3.amazonaws.com) buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
ngrok config add-authtoken DEIN_PERSONAL_AUTH_TOKEN
```

## 2. TCP-Tunnel auf dem Server starten
​Starte den Pandora-Server lokal auf Port 55555 und öffne parallel dazu in einem neuen Terminal den ngrok TCP-Tunnel:

```bash
ngrok tcp 55555
```

3. Client anpassen
​Lies die zugewiesene Adresse aus dem ngrok-Terminal ab (z. B. Forwarding tcp://0.tcp.ngrok.io:12345). Trage diese Daten vor der Kompilierung ganz oben in den Konfigurationsblock der client.py ein:

```python
# client.py - Zeile 14-15
TARGET_HOST = '0.tcp.ngrok.io'  # ngrok Host hier eintragen
TARGET_PORT = 12345             # Aktuellen ngrok Port hier eintragen
```

## 🛠️ Kompilierung zur .exe (Windows)
​Um das Programm als eigenständige App zu nutzen, verwe```nde PyInstaller:
### Für den Server:

```bash
python -m PyInstaller --onefile --name "PandoraIRC" server.py
```
​
### Für den Client:

```bash
python -m PyInstaller --noconsole --onefile --collect-all customtkinter --name "PandoraIRC_Client" client.py
```

Die fertigen Dateien findest du anschließend im Ordner dist/.

🔒 Sicherheitshinweis

Dieses Projekt nutzt AES-256 zur Verschlüsselung. Für maximale Sicherheit in Produktion sollte der SHARED_KEY in der client.py durch einen dynamischen RSA-Schlüsselaustausch (Diffie-Hellman) ersetzt werden.
​Erstellt für Bildungszwecke im Bereich Kryptografie und Netzwerkprogrammierung.

```bash

### Profi-Tipp für die Kompilierung:
Wenn du die `.exe` erstellst, achte darauf, dass du in der `client.py` im Code bei `self.client.connect(('127.0.0.1', 55555))` die IP-Adresse deines tatsächlichen Servers (z.B. deine VPS-IP oder lokale Netzwerk-IP) einträgst, falls du nicht nur auf deinem eigenen Rechner testen willst.

```
