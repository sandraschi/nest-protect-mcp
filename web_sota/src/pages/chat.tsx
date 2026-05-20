import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Loader2 } from "lucide-react";

const API = "http://127.0.0.1:7771/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [health, setHealth] = useState<string>("checking");

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/health`);
        const d = await r.json();
        setHealth(d.success ? "ok" : "error");
        setMessages([{ role: "assistant", content: "Nest Protect MCP ready. Try: list devices, check status of [id], run safety check on [id]." }]);
      } catch {
        setHealth("unreachable");
        setMessages([{ role: "assistant", content: "Cannot reach Nest Protect API on port 7771. Start the backend first." }]);
      }
    })();
  }, []);

  const send = async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: q }]);
    setSending(true);
    try {
      const lower = q.toLowerCase();

      if (lower === "list devices" || lower === "devices") {
        const r = await fetch(`${API}/devices`);
        const d = await r.json();
        if (d.success && d.result?.devices?.length) {
          const lines = d.result.devices.map((dev: { device_id: string; name?: string; location?: string }) =>
            `  · ${dev.name || dev.device_id}${dev.location ? ` (${dev.location})` : ""}`
          );
          setMessages(prev => [...prev, { role: "assistant", content: `${d.result.devices.length} device(s):\n${lines.join("\n")}` }]);
        } else {
          setMessages(prev => [...prev, { role: "assistant", content: "No devices found." }]);
        }
      } else if (lower.startsWith("safety check") || lower.startsWith("test")) {
        const parts = lower.split(" ");
        const deviceId = parts[parts.length - 1];
        if (deviceId && deviceId !== "check" && deviceId !== "test") {
          const r = await fetch(`${API}/devices/${encodeURIComponent(deviceId)}/test`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ test_type: "full" }) });
          const d = await r.json();
          setMessages(prev => [...prev, { role: "assistant", content: d.success ? `Safety check passed for ${deviceId}.` : `Check failed: ${d.error}` }]);
        } else {
          setMessages(prev => [...prev, { role: "assistant", content: "Specify a device ID, e.g.: safety check device_01" }]);
        }
      } else if (lower.startsWith("status") || lower.startsWith("check")) {
        const parts = lower.split(" ");
        const deviceId = parts[parts.length - 1];
        if (deviceId && deviceId !== "status" && deviceId !== "check") {
          const r = await fetch(`${API}/devices/${encodeURIComponent(deviceId)}`);
          const d = await r.json();
          if (d.success && d.result?.device) {
            const dev = d.result.device;
            const lines = Object.entries(dev).map(([k, v]) => `  · ${k}: ${v}`);
            setMessages(prev => [...prev, { role: "assistant", content: `Device ${deviceId}:\n${lines.join("\n")}` }]);
          } else {
            setMessages(prev => [...prev, { role: "assistant", content: `Device ${deviceId} not found.` }]);
          }
        } else {
          const r = await fetch(`${API}/system/status`);
          const d = await r.json();
          setMessages(prev => [...prev, { role: "assistant", content: `System: ${d.result?.mcp_server ?? "unknown"}, devices: ${d.result?.device_count ?? 0}, last check: ${d.result?.last_health_check ?? "—"}` }]);
        }
      } else {
        setMessages(prev => [...prev, { role: "assistant", content: `Unknown command. Try: "list devices", "status [id]", "safety check [id]", "system status".` }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${(e as Error).message}` }]);
    }
    setSending(false);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Command Interface</h2>
          <p className="text-slate-400">Nest Protect MCP · {health === "ok" ? "connected" : health === "unreachable" ? "offline" : "connecting…"}</p>
        </div>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center gap-2 text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Connecting…</div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className="flex gap-3">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center border ${msg.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}>
                  {msg.role === "user" ? <User className="h-4 w-4 text-slate-400" /> : <Bot className="h-4 w-4 text-blue-400" />}
                </div>
                <div className="flex-1 space-y-1">
                  <span className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-blue-400"}`}>
                    {msg.role === "user" ? "Operator" : "System AI"}
                  </span>
                  <div className={`text-sm p-3 rounded-md border inline-block whitespace-pre-wrap ${msg.role === "user" ? "text-slate-300 bg-slate-900/50 border-slate-800" : "text-slate-300 bg-blue-950/10 border-blue-900/30"}`}>
                    {msg.content}
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
              placeholder='Try: "list devices", "status [id]", "safety check [id]"…'
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()}
            />
            <Button size="icon" className="bg-blue-600 hover:bg-blue-700" disabled={sending || !input.trim()} onClick={send}>
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
