import threading
import socket
import random
import time

log_lock = threading.Lock()

def log_activity(message):
    """Logs activity to output.txt with thread safety."""
    with log_lock:
        with open("output.txt", "a") as log_file:
            log_file.write(message + "\n")
            log_file.flush()

def assign_port():
    """Assigns a port in the range 50000-55000."""
    return random.randint(50000, 55000)

class Peer:
    def __init__(self, peer_id, seed_nodes):
        self.peer_id = peer_id
        self.peer_ip = "127.0.0.1"
        self.peer_port = assign_port()
        self.seed_nodes = seed_nodes
        self.connected_peers = set()
        self.message_list = set()
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peer_socket.bind((self.peer_ip, self.peer_port))
        self.peer_socket.listen(5)
        log_activity(f"[Peer {self.peer_id}] Started at {self.peer_ip}:{self.peer_port}")

    def register_with_seeds(self):
        """Registers with at least n/2+1 seed nodes and retrieves peer lists."""
        total_seeds = len(self.seed_nodes)
        required_seeds = total_seeds // 2 + 1
        chosen_seeds = random.sample(self.seed_nodes, required_seeds)
        
        for seed_ip, seed_port in chosen_seeds:
            try:
                seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_socket.connect((seed_ip, int(seed_port)))
                seed_socket.sendall(f"{self.peer_ip}:{self.peer_port}".encode())
                peer_list_data = seed_socket.recv(1024).decode()
                seed_socket.close()
                
                for peer in peer_list_data.split("\n"):
                    if peer:
                        self.connected_peers.add(tuple(peer.split(":")))
                
                log_activity(f"[Peer {self.peer_id}] Registered with Seed {seed_ip}:{seed_port}")
            except Exception as e:
                log_activity(f"[Peer {self.peer_id}] Failed to connect to Seed {seed_ip}:{seed_port}: {e}")
    
    def start_listening(self):
        """Starts listening for incoming messages from other peers."""
        while True:
            client_socket, _ = self.peer_socket.accept()
            threading.Thread(target=self.handle_peer_connection, args=(client_socket,)).start()
    
    def handle_peer_connection(self, client_socket):
        """Handles messages received from peers."""
        try:
            message = client_socket.recv(1024).decode()
            if message not in self.message_list:
                self.message_list.add(message)
                log_activity(f"[Peer {self.peer_id}] Received: {message}")
                self.forward_message(message)
        except Exception as e:
            log_activity(f"[Peer {self.peer_id}] Error handling peer message: {e}")
        finally:
            client_socket.close()
    
    def send_message(self, message):
        """Sends a message to all connected peers."""
        formatted_message = f"{time.time()}:{self.peer_ip}:{message}"
        self.message_list.add(formatted_message)
        log_activity(f"[Peer {self.peer_id}] Sending: {formatted_message}")
        self.forward_message(formatted_message)
    
    def forward_message(self, message):
        """Forwards the message to connected peers."""
        for peer_ip, peer_port in self.connected_peers:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, int(peer_port)))
                peer_socket.sendall(message.encode())
                peer_socket.close()
            except Exception as e:
                log_activity(f"[Peer {self.peer_id}] Failed to forward to {peer_ip}:{peer_port}: {e}")

def main():
    """Main function to start peers."""
    with open("config.txt", "r") as f:
        seed_nodes = [tuple(line.strip().split(":")) for line in f.readlines()]
    
    num_peers = int(input("Enter the number of peers to create: "))
    peers = []
    
    for i in range(num_peers):
        peer = Peer(i + 1, seed_nodes)
        peers.append(peer)
        threading.Thread(target=peer.start_listening).start()
    
    time.sleep(2)  # Give time for peers to start up
    for peer in peers:
        peer.register_with_seeds()
    
    while True:
        peer_id = int(input("Enter Peer ID to send message (or -1 to exit): "))
        if peer_id == -1:
            break
        message = input("Enter message: ")
        peers[peer_id - 1].send_message(message)

if __name__ == "__main__":
    open("output.txt", "w").close()  # Clear log file on start
    main()
