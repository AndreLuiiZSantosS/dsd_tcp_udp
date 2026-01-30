const net = require("net");
const readline = require("readline");

const client = new net.Socket();
client.connect(9000, "127.0.0.1");

client.on("data", data => {
  console.log("Mensagem recebida:", data.toString());
});

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.on("line", line => {
  client.write(line);
});
