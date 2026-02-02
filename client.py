import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import sys

# --- CONFIGURAÇÕES ---
TCP_PORT = 3000
UDP_PORT = 3001
WIN_SCORE = 500 # Pontuação para vencer

class AgarGame:
    def __init__(self, root, player_name, server_ip):
        self.root = root
        self.name = player_name
        self.server_ip = server_ip
        
        self.root.attributes('-fullscreen', True)
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        # Canvas
        self.canvas = tk.Canvas(root, width=self.screen_w, height=self.screen_h, bg='#121212', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # Placar
        self.lbl_score = tk.Label(root, text="Tamanho: 20", bg="black", fg="#00FF00", font=("Arial", 16, "bold"))
        self.lbl_score.place(x=20, y=20)
        
        tk.Label(root, text=f"META: {WIN_SCORE}", bg="black", fg="red", font=("Arial", 12)).place(x=20, y=50)

        # Chat Frame
        self.chat_frame = tk.Frame(root, bg="black")
        self.chat_frame.place(x=20, y=self.screen_h - 200, width=350, height=180)
        self.chat_log = tk.Text(self.chat_frame, height=8, bg="#1a1a1a", fg="white", font=("Arial", 9))
        self.chat_log.pack(fill=tk.BOTH, expand=True)
        self.entry_msg = tk.Entry(self.chat_frame, bg="#333", fg="white")
        self.entry_msg.pack(fill=tk.X)
        self.entry_msg.bind('<Return>', self.send_chat)

        self.my_color = random.choice(['#FF0000', '#0000FF', '#00FF00', '#FFA500', '#8A2BE2'])
        self.respawn() 

        self.other_players = {} 
        self.foods = {} 
        self.game_over = False

        if not self.connect_sockets(): return
        
        self.canvas.bind('<Motion>', self.update_position)
        self.game_loop()

    def respawn(self):
        self.x = random.randint(100, self.screen_w - 100)
        self.y = random.randint(100, self.screen_h - 100)
        self.size = 20
        self.lbl_score.config(text=f"Tamanho: {self.size}")
        self.add_log(">>> VOCÊ RENASCEU!")

    def connect_sockets(self):
        try:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.connect((self.server_ip, TCP_PORT))
            threading.Thread(target=self.listen_tcp, daemon=True).start()
            
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.sendto("INIT".encode(), (self.server_ip, UDP_PORT))
            threading.Thread(target=self.listen_udp, daemon=True).start()
            
            self.tcp.send(f"[SISTEMA] {self.name} entrou.".encode())
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")
            self.root.destroy()
            return False

    def update_position(self, event):
        if not self.game_over:
            self.x = event.x
            self.y = event.y

    def check_collisions(self):
        if self.game_over: return

        # Comidas
        to_remove = None
        for fid, data in self.foods.items():
            dist = ((self.x - data['x'])**2 + (self.y - data['y'])**2)**0.5
            if dist < self.size:
                to_remove = fid
                break
        
        if to_remove:
            self.tcp.send(f"EAT:{to_remove}".encode())
            if to_remove in self.foods: del self.foods[to_remove]
            self.grow(2)

        # PvP
        for pname, pdata in self.other_players.items():
            dist = ((self.x - pdata['x'])**2 + (self.y - pdata['y'])**2)**0.5
            if dist < self.size and self.size > (pdata['s'] + 5):
                self.tcp.send(f"KILL:{pname}".encode())
                self.grow(10)
                self.add_log(f"!!! VOCÊ DEVOROU {pname} !!!")

    def grow(self, amount):
        self.size += amount
        self.lbl_score.config(text=f"Tamanho: {self.size}")
        if self.size >= WIN_SCORE:
            self.tcp.send(f"WIN:{self.name}".encode())

    def draw_grid(self):
        for i in range(0, self.screen_w, 100):
            self.canvas.create_line(i, 0, i, self.screen_h, fill="#222")
        for i in range(0, self.screen_h, 100):
            self.canvas.create_line(0, i, self.screen_w, i, fill="#222")

    def game_loop(self):
        if self.game_over: return # Para o loop se o jogo acabou

        msg = f"{self.name},{self.x},{self.y},{self.size},{self.my_color}"
        try: self.udp.sendto(msg.encode(), (self.server_ip, UDP_PORT))
        except: pass

        self.canvas.delete("all")
        self.draw_grid()
        
        for fid, data in self.foods.items():
            self.canvas.create_oval(data['x']-5, data['y']-5, data['x']+5, data['y']+5, fill=data['c'])

        for pname, pdata in self.other_players.items():
            px, py, ps, pc = pdata['x'], pdata['y'], pdata['s'], pdata['c']
            self.canvas.create_oval(px-ps, py-ps, px+ps, py+ps, fill=pc, outline='white')
            self.canvas.create_text(px, py-ps-15, text=pname, fill="white", font="Arial 10 bold")

        self.canvas.create_oval(self.x-self.size, self.y-self.size, self.x+self.size, self.y+self.size, 
                              fill=self.my_color, outline='yellow', width=3, dash=(4,4))
        self.canvas.create_text(self.x, self.y-self.size-20, text="VOCÊ", fill="yellow", font="Arial 10 bold")

        self.check_collisions()
        self.root.after(30, self.game_loop)

    def listen_udp(self):
        while not self.game_over:
            try:
                data, _ = self.udp.recvfrom(2048)
                parts = data.decode().split(',')
                if len(parts) == 5:
                    pname, px, py, psize, pcolor = parts
                    if pname != self.name:
                        self.other_players[pname] = {'x': int(px), 'y': int(py), 's': int(psize), 'c': pcolor}
            except: pass

    def listen_tcp(self):
        while not self.game_over:
            try:
                msg = self.tcp.recv(4096).decode()
                
                if "FOOD_LIST:" in msg:
                    raw = msg.replace("FOOD_LIST:", "").split(";")
                    for item in raw:
                        if item:
                            fid, fx, fy, fc = item.split(",")
                            self.foods[fid] = {'x': int(fx), 'y': int(fy), 'c': fc}
                
                elif "RMV_FOOD:" in msg:
                    for cmd in msg.split("RMV_FOOD:"):
                        if len(cmd) >= 5: 
                            fid = cmd[:5]
                            if fid in self.foods: del self.foods[fid]

                elif "NEW_FOOD:" in msg:
                    for part in msg.split("NEW_FOOD:"):
                        if "," in part:
                            d = part.split(",")
                            if len(d) >= 4: self.foods[d[0]] = {'x': int(d[1]), 'y': int(d[2]), 'c': d[3]}

                elif "DIE:" in msg:
                    victim = msg.split("DIE:")[1]
                    if victim == self.name:
                        self.add_log(">>> VOCÊ FOI DEVORADO! T_T")
                        self.respawn()
                    else:
                        self.add_log(f"!!! {victim} virou almoço!")

                elif "GAME_OVER:" in msg:
                    winner = msg.split("GAME_OVER:")[1]
                    self.show_game_over_screen(winner)
                    
                else:
                    self.add_log(msg)
            except: break

    def show_game_over_screen(self, winner):
        self.game_over = True # Finaliza o jogo
        
        frame_go = tk.Frame(self.root, bg="#111", bd=5, relief="ridge")
        frame_go.place(relx=0.5, rely=0.5, anchor="center", width=500, height=300)

        # Mensagem de Vitória ou Derrota
        if winner == self.name:
            msg_title = "PARABÉNS!"
            msg_sub = "VOCÊ VENCEU A RODADA!"
            color = "#00FF00" 
        else:
            msg_title = "FIM DE JOGO!"
            msg_sub = f"O JOGADOR {winner} VENCEU."
            color = "#FF0000"

        tk.Label(frame_go, text=msg_title, bg="#111", fg=color, font=("Impact", 40)).pack(pady=20)
        tk.Label(frame_go, text=msg_sub, bg="#111", fg="white", font=("Arial", 16)).pack(pady=10)

        # Botões de Ação
        btn_frame = tk.Frame(frame_go, bg="#111")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="VOLTAR AO MENU", command=self.return_to_menu, 
                  bg="blue", fg="white", font=("Arial", 12, "bold"), width=20).pack(pady=5)
        
        tk.Button(btn_frame, text="SAIR DO JOGO", command=self.root.destroy, 
                  bg="gray", fg="white", font=("Arial", 10), width=20).pack(pady=5)

    def return_to_menu(self):
        # Fecha conexões
        try:
            self.tcp.close()
            self.udp.close()
        except: pass

        # Fecha o jogo
        self.root.destroy()
        
        # Cria um novo menu
        new_root = tk.Tk()
        MainMenu(new_root)

    def send_chat(self, event):
        txt = self.entry_msg.get()
        if txt:
            self.tcp.send(f"{self.name}: {txt}".encode())
            self.add_log(f"Eu: {txt}")
            self.entry_msg.delete(0, tk.END)

    def add_log(self, text):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, text + "\n")
        self.chat_log.see(tk.END)
        self.chat_log.config(state='disabled')

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Agar PvP")
        self.root.geometry("400x350")
        self.root.configure(bg="#111")
        
        tk.Label(root, text="AGAR.IO PvP", font=("Impact", 30), bg="#111", fg="#00FF00").pack(pady=20)
        
        tk.Label(root, text="Seu Nickname:", bg="#111", fg="white", font=("Arial", 12)).pack()
        self.entry_name = tk.Entry(root, font=("Arial", 12))
        self.entry_name.pack(pady=5)
        
        tk.Label(root, text="IP do Host:", bg="#111", fg="white", font=("Arial", 12)).pack()
        self.entry_ip = tk.Entry(root, font=("Arial", 12))
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=5)
        
        tk.Button(root, text="ENTRAR NA ARENA", command=self.start, 
                  bg="#FF0000", fg="white", font=("Arial", 14, "bold"), width=20, height=2).pack(pady=30)

    def start(self):
        name = self.entry_name.get()
        ip = self.entry_ip.get()
        if name and ip:
            self.root.destroy()
            game_root = tk.Tk()
            AgarGame(game_root, name, ip)
            game_root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()