import socket
import threading
import json

class ChatServer:
    def __init__(self, host='0.0.0.0', port=55555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = {}  # Format: { nickname: client_socket }
        print(f"Server läuft auf {host}:{port}...")

    def broadcast_user_list(self):
        """Sendet die Liste aller aktiven Nutzernamen an alle Clients."""
        packet = json.dumps({"type": "user_list", "data": list(self.clients.keys())})
        for client in list(self.clients.values()):
            try:
                client.send(packet.encode('utf-8'))
            except:
                pass

    def remove_client(self, nickname):
        """Entfernt einen Client sauber aus dem System."""
        if nickname in self.clients:
            client = self.clients[nickname]
            del self.clients[nickname]
            try:
                client.close()
            except:
                pass
            print(f"{nickname} hat den Server verlassen.")
            self.broadcast_user_list()

    def handle(self, nickname, client):
        """Verarbeitet eingehende Datenpakete des Clients."""
        while True:
            try:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    self.remove_client(nickname)
                    break
                
                packet = json.loads(data)
                
                # Öffentliche Nachricht im Global-Chat
                if packet["type"] == "public":
                    out_packet = json.dumps({
                        "type": "public",
                        "sender": nickname,
                        "payload": packet["payload"]
                    })
                    for name, sock in self.clients.items():
                        if name != nickname:
                            try:
                                sock.send(out_packet.encode('utf-8'))
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
                        try:
                            self.clients[target].send(out_packet.encode('utf-8'))
                        except:
                            pass
            except:
                self.remove_client(nickname)
                break

    def receive(self):
        while True:
            try:
                client, address = self.server.accept()
                print(f"Verbunden mit {str(address)}")
                
                # Der erste Empfang ist der reine Nickname
                nickname = client.recv(1024).decode('utf-8')
                if not nickname:
                    client.close()
                    continue
                
                # Kollisionsschutz bei identischen Namen
                if nickname in self.clients:
                    nickname = f"{nickname}_"
                
                self.clients[nickname] = client
                print(f"{nickname} ist dem Netzwerk beigetreten.")
                self.broadcast_user_list()

                thread = threading.Thread(target=self.handle, args=(nickname, client))
                thread.start()
            except Exception as e:
                print(f"Verbindungsfehler: {e}")

if __name__ == "__main__":
    server = ChatServer()
    server.receive()
