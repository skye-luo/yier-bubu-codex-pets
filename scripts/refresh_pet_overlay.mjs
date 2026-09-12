// Refresh only the pet overlay. Never opens settings or changes the selected pet.
const port = process.env.CODEX_REMOTE_DEBUGGING_PORT || "9341";
if (!/^\d{1,5}$/.test(port) || Number(port) > 65535) process.exit(1);
try {
  const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(1500) });
  if (!response.ok) throw new Error("debug endpoint unavailable");
  const targets = await response.json();
  const target = targets.find(item => item.type === "page" && /initialRoute=%2Favatar-overlay|initialRoute=\/avatar-overlay/.test(item.url || ""));
  if (!target?.webSocketDebuggerUrl) process.exit(2);
  const endpoint = new URL(target.webSocketDebuggerUrl);
  if (!["127.0.0.1", "localhost", "[::1]"].includes(endpoint.hostname)) process.exit(1);
  await new Promise((resolve, reject) => {
    const socket = new WebSocket(endpoint);
    const timer = setTimeout(() => { socket.close(); reject(new Error("timeout")); }, 3000);
    socket.addEventListener("open", () => socket.send(JSON.stringify({ id: 1, method: "Page.reload", params: { ignoreCache: true } })));
    socket.addEventListener("message", event => {
      const message = JSON.parse(String(event.data));
      if (message.id !== 1) return;
      clearTimeout(timer); socket.close();
      message.error ? reject(new Error("reload failed")) : resolve();
    });
    socket.addEventListener("error", () => { clearTimeout(timer); socket.close(); reject(new Error("connection failed")); });
  });
} catch { process.exit(2); }
