import threading
import socket


# Global dictionary to store peer lists for each seed node
seed_peer_lists = {}
log_lock = threading.Lock()  # Lock for thread-safe logging

def log_activity(message):
    with log_lock:  # Ensure thread safety
        with open("output.txt", "a") as log_file:
            log_file.write(message + "\n")
            log_file.flush()


# Function to log activity to output.txt
def log_activity(message):
    with open("output.txt", "a") as log_file:
        log_file.write(message + "\n")

def handle_peer_connection(client_socket, seed_port):
    """Handles communication with a newly connected peer."""
    try:
        peer_address = client_socket.getpeername()  # (IP, port) of the connected peer
        peer_ip, peer_port = peer_address

        # Add new peer to the peer list of this seed node
        if seed_port not in seed_peer_lists:
            seed_peer_lists[seed_port] = set()
        
        seed_peer_lists[seed_port].add((peer_ip, peer_port))

        # Convert peer list to a string and send to the newly connected peer
        peer_list_str = "\n".join([f"{ip}:{port}" for ip, port in seed_peer_lists[seed_port]])
        client_socket.sendall(peer_list_str.encode())

        log_activity(f"[Seed {seed_port}] Connected peer: {peer_ip}:{peer_port}")
    except Exception as e:
        log_activity(f"[Seed {seed_port}] Error handling peer: {str(e)}")
    finally:
        client_socket.close()

def start_seed(ip, port):
    """Starts a seed node to listen for peer connections."""
    try:
        seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seed_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        seed_socket.bind((ip, port))
        seed_socket.listen(5)

        message = f"[Seed {port}] Running at {ip}:{port}"
        print(message)
        log_activity(message)

        while True:
            client_socket, _ = seed_socket.accept()
            threading.Thread(target=handle_peer_connection, args=(client_socket, port)).start()
    except Exception as e:
        log_activity(f"[Seed {port}] Failed to start: {str(e)}")

def read_config():
    """Reads config.txt and returns a list of (IP, Port) tuples."""
    with open("config.txt", "r") as f:
        lines = f.readlines()
    return [tuple(line.strip().split(":")) for line in lines]

if __name__ == "__main__":
    open("output.txt", "w").close()  # Clear the log file at the start
    seed_nodes = read_config()
    threads = []

    for ip, port in seed_nodes:
        port = int(port)  # Convert port from string to integer
        thread = threading.Thread(target=start_seed, args=(ip, port))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()