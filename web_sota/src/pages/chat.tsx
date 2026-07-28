import { Bot, Download, Eraser, Loader2, Send, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const HISTORY_KEY = "nest-protect-chat-history";
const PERSONALITY_KEY = "nest-protect-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
  "Safety Monitor":
    "You are a Nest Protect safety monitor. Prioritize alarm status, CO levels, smoke detection, and battery health. Alert on any safety-critical issues immediately.",
  "Home Manager":
    "You are a home management assistant. Provide a holistic view of all Nest Protect devices, their locations, and maintenance needs. Suggest actions to keep the home safe.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  Custom: "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  {
    group: "Alarms",
    prompts: [
      "List devices",
      "Check status of device_01",
      "Run safety check on device_01",
    ],
  },
  {
    group: "Safety",
    prompts: ["System status", "Show offline devices", "Battery health report"],
  },
  {
    group: "Home",
    prompts: [
      "Devices in the kitchen",
      "Recent alarm history",
      "Schedule a test",
    ],
  },
];

const API = "/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function Chat() {
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(PERSONALITY_KEY) || "Safety Monitor",
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [health, setHealth] = useState<string>("checking");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);
  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personality);
  }, [personality]);
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/health`);
        const d = await r.json();
        setHealth(d.success ? "ok" : "error");
        setMessages([
          {
            role: "assistant",
            content:
              "Nest Protect MCP ready. Try: list devices, check status of [id], run safety check on [id].",
          },
        ]);
      } catch {
        setHealth("unreachable");
        setMessages([
          {
            role: "assistant",
            content: "Cannot reach Nest Protect API. Start the backend first.",
          },
        ]);
      }
    })();
  }, []);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput("");
    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => {
      const next = [...prev, userMsg];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
    setSending(true);
    try {
      const lower = q.toLowerCase();

      if (lower === "list devices" || lower === "devices") {
        const r = await fetch(`${API}/devices`);
        const d = await r.json();
        if (d.success && d.result?.devices?.length) {
          const lines = d.result.devices.map(
            (dev: { device_id: string; name?: string; location?: string }) =>
              `  \u00b7 ${dev.name || dev.device_id}${dev.location ? ` (${dev.location})` : ""}`,
          );
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `${d.result.devices.length} device(s):\n${lines.join("\n")}`,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: "No devices found." },
          ]);
        }
      } else if (lower.startsWith("safety check") || lower.startsWith("test")) {
        const parts = lower.split(" ");
        const deviceId = parts[parts.length - 1];
        if (deviceId && deviceId !== "check" && deviceId !== "test") {
          const r = await fetch(
            `${API}/devices/${encodeURIComponent(deviceId)}/test`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ test_type: "full" }),
            },
          );
          const d = await r.json();
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: d.success
                ? `Safety check passed for ${deviceId}.`
                : `Check failed: ${d.error}`,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: "Specify a device ID, e.g.: safety check device_01",
            },
          ]);
        }
      } else if (lower.startsWith("status") || lower.startsWith("check")) {
        const parts = lower.split(" ");
        const deviceId = parts[parts.length - 1];
        if (deviceId && deviceId !== "status" && deviceId !== "check") {
          const r = await fetch(
            `${API}/devices/${encodeURIComponent(deviceId)}`,
          );
          const d = await r.json();
          if (d.success && d.result?.device) {
            const dev = d.result.device;
            const lines = Object.entries(dev).map(
              ([k, v]) => `  \u00b7 ${k}: ${v}`,
            );
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: `Device ${deviceId}:\n${lines.join("\n")}`,
              },
            ]);
          } else {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: `Device ${deviceId} not found.` },
            ]);
          }
        } else {
          const r = await fetch(`${API}/system/status`);
          const d = await r.json();
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `System: ${d.result?.mcp_server ?? "unknown"}, devices: ${d.result?.device_count ?? 0}, last check: ${d.result?.last_health_check ?? "\u2014"}`,
            },
          ]);
        }
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Unknown command. Try: "list devices", "status [id]", "safety check [id]", "system status".`,
          },
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${(e as Error).message}` },
      ]);
    }
    setSending(false);
  }, [input, sending]);

  const exportChat = () => {
    const text = messages
      .map((m) => `[${m.role.toUpperCase()}] ${m.content}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "nest-protect-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div
      data-testid="chat-page"
      className="flex h-[calc(100vh-8rem)] flex-col space-y-4"
    >
      <div
        data-testid="chat-controls"
        className="flex items-center justify-between flex-wrap gap-2"
      >
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Command Interface
          </h2>
          <p className="text-slate-400">
            Nest Protect MCP \u00b7{" "}
            {health === "ok"
              ? "connected"
              : health === "unreachable"
                ? "offline"
                : "connecting\u2026"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
            skill:nest-protect-expert
          </span>
          <select
            data-testid="personality-select"
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {Object.keys(PERSONALITIES).map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button
            data-testid="chat-export"
            onClick={exportChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Export"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            data-testid="chat-clear"
            onClick={clearChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Connecting\u2026
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border ${msg.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-1">
                <span
                  className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-blue-400"}`}
                >
                  {msg.role === "user" ? "Operator" : "System AI"}
                </span>
                <div
                  className={`text-sm p-3 rounded-md border inline-block whitespace-pre-wrap ${msg.role === "user" ? "text-slate-300 bg-slate-900/50 border-slate-800" : "text-slate-300 bg-blue-950/10 border-blue-900/30"}`}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          ))
        )}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Processing...
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      <div data-testid="example-prompts" className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((group) => (
          <div key={group.group} className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
            {group.prompts.map((p) => (
              <button
                key={p}
                onClick={() => setInput(p)}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded"
              >
                {p}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          data-testid="chat-input"
          className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder='Try: "list devices", "status [id]", "safety check [id]"\u2026'
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          data-testid="chat-send"
          onClick={send}
          disabled={sending || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md"
        >
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
