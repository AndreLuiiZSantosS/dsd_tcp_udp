import socket
import threading
import random

# ================= CONFIGURAÇÕES =================
HOST = "0.0.0.0"          # Escuta toda a LAN (Wi-Fi incluso)
TCP_PORT = 3000
UDP_PORT = 3001

MAP_WIDTH = 1920
MAP_HEIGHT = 1080

# ================= ESTADO DO JOGO =================
clients_tcp = []
clients_udp = set()
foods = {}

# ================= FUNÇÕES =================
def get_local_ip():
    """Retorna o IP real da LAN"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def create_single_food():
    fid = str(random.randint(10000, 99999))
    fx = random.randint(50, MAP_WIDTH - 50)
    fy = random.randint(50, MAP_HEIGHT - 50)
    fcolor = random.choice([
        "#FFD700", "#00FFFF", "#FF00FF", "#00FF00", "#FF4500"
    ])
    foods[fid] = (fx, fy, fcolor)
    return fid, fx, fy, fcolor


def generate_food(qty=50):
    for _ in range(qty):
        create_single_food()


def broadcast_tcp(message, sender=None):
    for client in clients_tcp[:]:
        if client != sender:
            try:
                client.send(message.encode())
            except:
                clients_tcp.remove(client)


# ================= TCP =================
def handle_tcp(client, addr):
    print(f"[TCP] Cliente conectado: {addr}")

    # Envia todas as comidas existentes
    food_data = [
        f"{fid},{fx},{fy},{fc}"
        for fid, (fx, fy, fc) in foods.items()
    ]
    if food_data:
        client.send(("FOOD_LIST:" + ";".join(food_data)).encode())

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break

            if msg.startswith("EAT:"):
                _, fid = msg.split(":")
                if fid in foods:
                    del foods[fid]
                    broadcast_tcp(f"RMV_FOOD:{fid}")

                    if len(foods) < 40:
                        nid, nx, ny, nc = create_single_food()
                        broadcast_tcp(f"NEW_FOOD:{nid},{nx},{ny},{nc}")

            elif msg.startswith("KILL:"):
                _, victim = msg.split(":")
                broadcast_tcp(f"DIE:{victim}")
                client.send(f"DIE:{victim}".encode())

            elif msg.startswith("WIN:"):
                _, winner = msg.split(":")
                print(f"[FIM] {winner} venceu!")
                broadcast_tcp(f"GAME_OVER:{winner}")
                client.send(f"GAME_OVER:{winner}".encode())

            else:
                # Mensagens normais (posição, estado, etc)
                broadcast_tcp(msg, client)

        except:
            break

    if client in clients_tcp:
        clients_tcp.remove(client)
    client.close()
    print(f"[TCP] Cliente saiu: {addr}")


def start_tcp():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, TCP_PORT))
    server.listen()

    print(f"[TCP] Servidor rodando na porta {TCP_PORT}")

    while True:
        client, addr = server.accept()
        clients_tcp.append(client)
        threading.Thread(
            target=handle_tcp,
            args=(client, addr),
            daemon=True
        ).start()


# ================= UDP =================
def start_udp():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((HOST, UDP_PORT))
    print(f"[UDP] Servidor rodando na porta {UDP_PORT}")

    while True:
        try:
            data, addr = udp.recvfrom(1024)
            clients_udp.add(addr)

            for c in clients_udp:
                if c != addr:
                    udp.sendto(data, c)
        except:
            pass


# ================= MAIN =================
if __name__ == "__main__":
    generate_food()
    print("===================================")
    print(" SERVIDOR LAN INICIADO ")
    print(f" IP DA REDE: {get_local_ip()}")
    print(f" TCP: {TCP_PORT} | UDP: {UDP_PORT}")
    print("===================================")

    threading.Thread(target=start_tcp, daemon=True).start()
    start_udp()
