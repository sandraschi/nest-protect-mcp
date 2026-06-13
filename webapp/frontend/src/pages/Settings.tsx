import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Save, RefreshCw, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { mcpClient } from '@/lib/mcp-client'

function LLMSettings() {
  const [providers, setProviders] = useState<Record<string, {name:string}[]>>({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [status, setStatus] = useState<"loading"|"ready"|"error">("loading");
  useEffect(() => {
    fetch("/api/llm/providers").then(r => r.json()).then(d => {
      setProviders(d);
      const savedP = localStorage.getItem("llm_provider") || "ollama";
      const savedM = localStorage.getItem("llm_model") || "";
      setSelectedProvider(savedP);
      const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
      setSelectedModel(savedM && models.some((m:{name:string}) => m.name === savedM) ? savedM : (models[0]?.name || ""));
      setStatus(models.length > 0 ? "ready" : "error");
    }).catch(() => {
      setProviders({ ollama: [{name:"llama3.2:3b"}] });
      setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
      setStatus("ready");
    });
  }, []);
  const save = (p:string, m:string) => { localStorage.setItem("llm_provider", p); localStorage.setItem("llm_model", m); };
  const models = providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Local LLM</CardTitle>
        <CardDescription>Provider and model selection</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Provider</label>
          <select className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
            value={selectedProvider} onChange={(e) => { setSelectedProvider(e.target.value); save(e.target.value, ""); }}>
            <option value="ollama">Ollama</option>
            <option value="lm_studio">LM Studio</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Model</label>
          <select className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
            value={selectedModel} onChange={(e) => { setSelectedModel(e.target.value); save(selectedProvider, e.target.value); }}>
            {models.map((m) => <option key={m.name} value={m.name}>{m.name}</option>)}
          </select>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Settings() {
  const [baseUrl, setBaseUrl] = useState('http://localhost:7771')
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [serverOk, setServerOk] = useState<boolean | null>(null)

  useEffect(() => {
    (async () => {
      try {
        const ok = await mcpClient.connect()
        setServerOk(ok)
      } catch {
        setServerOk(false)
      }
    })()
  }, [])

  const testConnection = async () => {
    setStatus('saving')
    try {
      const sys = await mcpClient.getSystemStatus()
      setServerOk((sys as { success?: boolean }).success ?? false)
      setStatus('saved')
    } catch {
      setServerOk(false)
      setStatus('error')
    }
    setTimeout(() => setStatus('idle'), 2000)
  }

  const saveConfig = async () => {
    setStatus('saving')
    try {
      await mcpClient.updateConfig({ base_url: baseUrl })
      setStatus('saved')
    } catch {
      setStatus('error')
    }
    setTimeout(() => setStatus('idle'), 2000)
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <SettingsIcon className="h-16 w-16 text-primary mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-4">Settings</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          Configure the MCP testing environment
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Server Connection</CardTitle>
          <CardDescription>Status: {serverOk === true ? 'Connected' : serverOk === false ? 'Disconnected' : 'Checking…'}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Base URL</label>
            <input
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
              value={baseUrl}
              onChange={e => setBaseUrl(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={testConnection}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Test Connection
            </Button>
            <Button variant="outline" onClick={saveConfig} disabled={status === 'saving'}>
              <Save className="h-4 w-4 mr-2" />
              {status === 'saving' ? 'Saving…' : status === 'saved' ? 'Saved' : status === 'error' ? 'Error' : 'Save'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {serverOk && (
        <Card>
          <CardHeader>
            <CardTitle>Server Info</CardTitle>
            <CardDescription>Live status from the MCP API</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 dark:text-gray-400">
            <p>The MCP server is reachable. Use the <strong>MCP Status</strong> page for detailed health data, or the <strong>Device Testing</strong> page to interact with Nest Protect units.</p>
          </CardContent>
        </Card>
      )}

      <LLMSettings />
    </div>
  )
}
