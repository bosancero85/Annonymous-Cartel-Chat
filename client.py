import socket
import threading
import customtkinter as ctk
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json

# ==============================================================================
# 🌐 NETZWERK- & VERBINDUNGS-KONFIGURATION
# ==============================================================================
# Variante A: Lokaler Test
# TARGET_HOST = '127.0.0.1'
# TARGET_PORT = 55555

# Variante B: DEIN NGROK TUNNEL (Einfach hier eintragen!)
TARGET_HOST = '0.tcp.ngrok.io'  # Tausche dies gegen deinen aktuellen ngrok Host aus
TARGET_PORT = 12345             # Tausche dies gegen deinen aktuellen ngrok Port aus
# ==============================================================================

# --- KRYPTO LOGIK (AES-256-GCM End-to-End) ---
SHARED_KEY = b'12345678901234567890123456789012' # 32 Bytes statischer Key

def encrypt_msg(message):
    aesgcm = AESGCM(SHARED_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
    # Konvertierung in Hex-String für fehlerfreien JSON-Transport
    return (nonce + ciphertext).hex()

def decrypt_msg(data_hex):
    try:
        data = bytes.fromhex(data_hex)
        aesgcm = AESGCM(SHARED_KEY)
        nonce = data[:12]
        ciphertext = data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    except:
        return "[Fehler beim Entschlüsseln - Falscher Key oder manipuliertes Paket]"


# --- UI LOGIK (CustomTkinter) ---
class ChatClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PandoraIRC // Crypt-Channel")
        self.geometry("950x550")
        ctk.set_appearance_mode("dark")

        # Netzwerk-Setup initialisieren
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = f"User_{os.urandom(2).hex()}"
        
        # UI Grid-Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Seitenleiste (Sidebar)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="PANDORA IRC", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=20)
        
        self.user_label = ctk.CTkLabel(self.sidebar, text="Aktive Partner", font=ctk.CTkFont(size=14, weight="bold"))
        self.user_label.pack(pady=(10, 5))
        
        self.user_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.user_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Chat Hauptbereich
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Tabview für Globalen Chat und Private Direktnachrichten
        self.tabview = ctk.CTkTabview(self.chat_frame)
        self.tabview.pack(expand=True, fill="both", padx=5, pady=5)
        self.tabview.add("Global")
        
        # Textfelder-Verwaltung für dynamische Tabs
        self.text_areas = {}
        global_txt = ctk.CTkTextbox(self.tabview.tab("Global"), state="disabled", wrap="word")
        global_txt.pack(expand=True, fill="both", padx=5, pady=5)
        self.text_areas["Global"] = global_txt
        
        # Horizontaler Eingabebereich
        self.input_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=5, pady=5)
        
        self.msg_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ende-zu-Ende verschlüsselte Nachricht...")
        self.msg_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.msg_entry.bind("<Return>", self.send_message)
        
        # Emoji-Picker (OptionMenu)
        emojis = ["😀", "🔥", "🔒", "💀", "👍", "🚀", "👀", "🤖", "💥", "👑", "👽"]
        self.emoji_menu = ctk.CTkOptionMenu(
            self.input_frame, 
            values=emojis, 
            command=self.insert_emoji, 
            width=60,
            dynamic_resizing=False
        )
        self.emoji_menu.set("😊")
        self.emoji_menu.pack(side="left", padx=(0, 5))
        
        # Senden-Button
        self.send_btn = ctk.CTkButton(self.input_frame, text="Senden", command=self.send_message, width=80)
        self.send_btn.pack(side="left")

        # Verbindung im Hintergrund-Thread starten
        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client.connect((TARGET_HOST, TARGET_PORT))
            self.client.sendall(self.nickname.encode('utf-8'))
            
            thread = threading.Thread(target=self.receive)
            thread.daemon = True
            thread.start()
            self.display_message("Global", "System", f"Erfolgreich gesichert verbunden als {self.nickname} via {TARGET_HOST}:{TARGET_PORT}")
        except Exception as e:
            self.display_message("Global", "System", f"Verbindung fehlgeschlagen! ({e})")

    def insert_emoji(self, emoji):
        """Fügt das ausgewählte Emoji an der aktuellen Cursor-Position ein."""
        self.msg_entry.insert('insert', emoji)
        self.emoji_menu.set("😊")

    def ensure_tab_exists(self, username):
        """Erstellt im Hintergrund einen Chat-Tab für einen Nutzer, falls noch keiner existiert."""
        if username not in self.text_areas:
            self.tabview.add(username)
            txt_area = ctk.CTkTextbox(self.tabview.tab(username), state="disabled", wrap="word")
            txt_area.pack(expand=True, fill="both", padx=5, pady=5)
            self.text_areas[username] = txt_area

    def open_private_chat(self, username):
        """Wechselt den visuellen Fokus auf den angeklickten User-Tab."""
        if username == self.nickname:
            return
        self.ensure_tab_exists(username)
        self.tabview.set(username)

    def update_user_list(self, users):
        """Baut die Sidebar-Liste bei Serveränderungen komplett neu auf."""
        for widget in self.user_frame.winfo_children():
            widget.destroy()
        
        for user in users:
            if user != self.nickname:
                btn = ctk.CTkButton(
                    self.user_frame, 
                    text=f"👤 {user}", 
                    fg_color="transparent", 
                    text_color="white",
                    hover_color="#2b2b2b", 
                    anchor="w",
                    command=lambda u=user: self.open_private_chat(u)
                )
                btn.pack(fill="x", pady=2)

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if msg:
            timestamp = datetime.now().strftime("%H:%M")
            active_tab = self.tabview.get()
            
            # Nachricht formatieren und verschlüsseln
            full_msg = f"[{timestamp}] {self.nickname}: {msg}"
            encrypted = encrypt_msg(full_msg)
            
            if active_tab == "Global":
                packet = {"type": "public", "payload": encrypted}
                self.display_message("Global", "Ich", msg)
            else:
                packet = {"type": "private", "target": active_tab, "payload": encrypted}
                self.display_message(active_tab, "Ich", msg)
                
            try:
                # Senden mit angehängtem Newline-Delimiter
                self.client.sendall((json.dumps(packet) + "\n").encode('utf-8'))
            except:
                self.display_message(active_tab, "System", "Senden fehlgeschlagen. Verbindung verloren.")
            
            self.msg_entry.delete(0, 'end')

    def receive(self):
        """Empfängt Datenströme vom Server und splittet sie sauber nach Newlines."""
        buffer = ""
        while True:
            try:
                data = self.client.recv(4096).decode('utf-8')
                if not data:
                    self.display_message("Global", "System", "Verbindung vom Server geschlossen.")
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    
                    packet = json.loads(line)
                    
                    if packet["type"] == "user_list":
                        self.update_user_list(packet["data"])
                        
                    elif packet["type"] == "public":
                        decrypted = decrypt_msg(packet["payload"])
                        self.display_message("Global", "Partner", decrypted, is_remote=True)
                        
                    elif packet["type"] == "private":
                        sender = packet["sender"]
                        decrypted = decrypt_msg(packet["payload"])
                        self.display_message(sender, "Partner", decrypted, is_remote=True)
            except:
                self.display_message("Global", "System", "Verbindungsfehler im Empfangskanal.")
                break

    def display_message(self, tab_name, sender, msg, is_remote=False):
        self.ensure_tab_exists(tab_name)
        txt_area = self.text_areas[tab_name]
        
        txt_area.configure(state="normal")
        time = datetime.now().strftime("%H:%M")
        # Wenn remote empfangen, ist der verschlüsselte String bereits voll formatiert
        prefix = f"[{time}] {sender}: " if not is_remote else ""
        txt_area.insert("end", f"{prefix}{msg}\n")
        txt_area.configure(state="disabled")
        txt_area.see("end")

if __name__ == "__main__":
    app = ChatClient()
    app.mainloop()

# ngrok tcp 55555
# curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
# echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
# sudo apt update && sudo apt install ngrok
# ngrok config add-authtoken DEIN_PERSONAL_AUTH_TOKEN
# python -m PyInstaller --noconsole --onefile --collect-all customtkinter --name "Pandora_Client" client.py
