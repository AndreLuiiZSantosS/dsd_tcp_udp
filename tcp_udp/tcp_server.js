const net = require("net");

const PORT = 9000;
let clients = [];

const server = net.createServer(socket => {
  socket.once("data", data => {
    socket.username = data.toString().trim();
    clients.push(socket);
    console.log(`${socket.username} conectado via TCP`);
  });

  socket.on("data", data => {
    const msg = data.toString().trim();
    clients.forEach(c => {
      if (c !== socket) {
        c.write(`${socket.username}: ${msg}\n`);
      }
    });
  });

  socket.on("end", () => {
    clients = clients.filter(c => c !== socket);
    console.log(`${socket.username} saiu`);
  });
});

server.listen(PORT, () => {
  console.log(`Servidor TCP rodando na porta ${PORT}`);
});
