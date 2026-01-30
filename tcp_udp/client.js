const net = require("net");
const dgram = require("dgram");

const USER = process.argv[2] || "anon";
const TCP_PORT = 9000;
const UDP_PORT = 9001;

// TCP (mensagens)
const tcp = net.createConnection({ port: TCP_PORT }, () => {
  tcp.write(USER);
});

tcp.on("data", data => {
  process.stdout.write(data.toString());
});

// UDP (status)
const udp = dgram.createSocket("udp4");

// online heartbeat
setInterval(() => {
  udp.send(`${USER} online`, UDP_PORT, "localhost");
}, 3000);

// entrada do usuário
process.stdin.on("data", data => {
  udp.send(`${USER} digitando`, UDP_PORT, "localhost");
  tcp.write(data.toString());
});
