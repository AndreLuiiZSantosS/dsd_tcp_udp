const dgram = require("dgram");
const client = dgram.createSocket("udp4");

const USER = "andre";

setInterval(() => {
  const msg = Buffer.from(`${USER}|ONLINE`);
  client.send(msg, 5001, "127.0.0.1");
}, 2000);
