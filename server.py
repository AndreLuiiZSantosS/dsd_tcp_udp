import socket
import threading
import random
import time

# --- CONFIGURAÇÕES ---
TCP_PORT = 3000
UDP_PORT = 3001
HOST = '0.0.0.0'
MAP_WIDTH = 1920
MAP_HEIGHT = 1080

clients_tcp = []
clients_udp = set()
foods = {} 

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def create_single_food():
    fid = str(random.randint(10000, 99999))
    fx = random.randint(50, MAP_WIDTH - 50)
    fy = random.randint(50, MAP_HEIGHT - 50)
    fcolor = random.choice(['#FFD700', '#00FFFF', '#FF00FF', '#00FF00', '#FF4500']) 
    foods[fid] = (fx, fy, fcolor)
    return fid, fx, fy, fcolor

def generate_food(count=50):
    for i in range(count):
        create_single_food()

def broadcast_tcp(message, sender_socket=None):
    for client in clients_tcp:
        if client != sender_socket:
            try:
                client.send(message.encode())
            except:
                clients_tcp.remove(client)

def handle_tcp(client, addr):
    print(f"[TCP] Conectado: {addr}")
    
    # Envia lista de comidas
    food_data = [f"{fid},{fx},{fy},{fc}" for fid, (fx, fy, fc) in foods.items()]
    if food_data:
        client.send(("FOOD_LIST:" + ";".join(food_data)).encode())

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg: break
            
            if msg.startswith("EAT:"):
                _, fid = msg.split(":")
                if fid in foods:
                    del foods[fid]
                    broadcast_tcp(f"RMV_FOOD:{fid}")
                    if len(foods) < 40:
                        nid, nx, ny, nc = create_single_food()
                        broadcast_tcp(f"NEW_FOOD:{nid},{nx},{ny},{nc}")

            elif msg.startswith("KILL:"):
                _, victim_name = msg.split(":")
                broadcast_tcp(f"DIE:{victim_name}", client)
                client.send(f"DIE:{victim_name}".encode()) 

            elif msg.startswith("WIN:"):
                _, winner_name = msg.split(":")
                print(f"[FIM] {winner_name} venceu a rodada!")
                # Avisa TODOS (incluindo o vencedor) que acabou
                broadcast_tcp(f"GAME_OVER:{winner_name}")
                client.send(f"GAME_OVER:{winner_name}".encode())
            else:
                broadcast_tcp(msg, client)

        except:
            break
            
    if client in clients_tcp: clients_tcp.remove(client)
    client.close()

def start_tcp():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, TCP_PORT))
    server.listen()
    while True:
        client, addr = server.accept()
        clients_tcp.append(client)
        threading.Thread(target=handle_tcp, args=(client, addr), daemon=True).start()

def start_udp():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((HOST, UDP_PORT))
    while True:
        try:
            data, addr = udp.recvfrom(1024)
            if addr not in clients_udp: clients_udp.add(addr)
            for c in clients_udp:
                if c != addr: udp.sendto(data, c)
        except: pass

if __name__ == "__main__":
    generate_food()
    print(f"HOST IP: {get_local_ip()}")
    threading.Thread(target=start_tcp, daemon=True).start()
    start_udp()