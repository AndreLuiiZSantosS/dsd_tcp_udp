const dgram = require("dgram");
const server = dgram.createSocket("udp4");

const PORT = 9001;

server.on("message", msg => {
  console.log("STATUS:", msg.toString());
});

server.bind(PORT, () => {
  console.log(`Servidor UDP rodando na porta ${PORT}`);
});
