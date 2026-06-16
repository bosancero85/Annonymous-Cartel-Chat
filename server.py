import socket
import threading
import json

class ChatServer:
    def __init__(self, host='0.0.0.0', port=55555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Erlaubt das sofortige Wiederverwenden des Ports nach einem Neustart
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = {}  # Format: { nickname: client_socket }
        print(f"[*] PandoraIRC-Server läuft stabil auf {host}:{port}...")

    def broadcast_user_list(self):
        """Sendet die Liste aller aktiven Nutzernamen an alle Clients."""
        packet = json.dumps({"type": "user_list", "data": list(self.clients.keys())})
        # Newline-Framing hinzufügen, um Paket-Verschmelzung zu verhindern
        framed_packet = (packet + "\n").encode('utf-8')
        
        for name, client in list(self.clients.items()):
            try:
                client.sendall(framed_packet)
            except:
                self.remove_client(name)

    def remove_client(self, nickname):
        """Entfernt einen Client sauber aus dem System."""
        if nickname in self.clients:
            client = self.clients[nickname]
            del self.clients[nickname]
            try:
                client.close()
            except:
                pass
            print(f"[-] {nickname} hat das Netzwerk verlassen.")
            self.broadcast_user_list()

    def handle(self, nickname, client):
        """Verarbeitet eingehende Datenpakete des Clients mit Newline-Framing."""
        buffer = ""
        while True:
            try:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    self.remove_client(nickname)
                    break
                
                buffer += data
                # Verarbeite alle vollständigen JSON-Pakete im Puffer
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    
                    packet = json.loads(line)
                    
                    # Öffentliche Nachricht im Global-Chat
                    if packet["type"] == "public":
                        out_packet = json.dumps({
                            "type": "public",
                            "sender": nickname,
                            "payload": packet["payload"]
                        })
                        framed_out = (out_packet + "\n").encode('utf-8')
                        
                        for name, sock in self.clients.items():
                            if name != nickname:  # Nicht an den Sender zurücksenden
                                try:
                                    sock.sendall(framed_out)
                                except:
                                    pass
                    
                    # Private Nachricht an spezifischen Nutzer
                    elif packet["type"] == "private":
                        target = packet["target"]
                        if target in self.clients:
                            out_packet = json.dumps({
                                "type": "private",
                                "sender": nickname,
                                "payload": packet["payload"]
                            })
                            framed_out = (out_packet + "\n").encode('utf-8')
                            try:
                                self.clients[target].sendall(framed_out)
                            except:
                                pass
            except:
                self.remove_client(nickname)
                break

    def receive(self):
        while True:
            try:
                client, address = self.server.accept()
                print(f"[+] Verbindung aufgebaut mit {str(address)}")
                
                # Der erste Empfang ist der reine Nickname (für das Server-Log)
                nickname = client.recv(1024).decode('utf-8').strip()
                if not nickname:
                    client.close()
                    continue
                
                # Kollisionsschutz bei identischen Namen
                if nickname in self.clients:
                    nickname = f"{nickname}_{os.urandom(1).hex()}"
                
                self.clients[nickname] = client
                print(f"[+] {nickname} ist dem Kartell beigetreten.")
                self.broadcast_user_list()

                thread = threading.Thread(target=self.handle, args=(nickname, client))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"[!] Verbindungsfehler: {e}")

if __name__ == "__main__":
    server = ChatServer()
    server.receive()

# curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
# echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
# sudo apt update && sudo apt install ngrok
# ngrok config add-authtoken DEIN_PERSONAL_AUTH_TOKEN
# ngrok tcp 55555
# python3 server.py
