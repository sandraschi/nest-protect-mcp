import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getWizardCallbackRedirectUri,
  getWizardResult,
  startAuthWizard,
} from "@/lib/api";
import {
  AlertCircle,
  CheckCircle2,
  Copy,
  Download,
  ExternalLink,
  KeyRound,
} from "lucide-react";

const REDIRECT_URI = getWizardCallbackRedirectUri();
const GCP_CREDENTIALS_URL = "https://console.cloud.google.com/apis/credentials";

export function AuthWizard() {
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dotenv, setDotenv] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [copiedRedirect, setCopiedRedirect] = useState(false);

  useEffect(() => {
    const sp = new URLSearchParams(window.location.search);
    const complete = sp.get("wizard_complete");
    const errParam = sp.get("wizard_error");
    if (!complete && !errParam) return;

    const u = new URL(window.location.href);
    u.searchParams.delete("wizard_complete");
    u.searchParams.delete("wizard_error");
    window.history.replaceState({}, "", `${u.pathname}${u.search}`);

    if (errParam) {
      setError(decodeURIComponent(errParam));
      return;
    }

    getWizardResult(complete as string)
      .then((r) => {
        setDotenv(r.dotenv);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
      });
  }, []);

  async function onStart() {
    setError(null);
    setDotenv(null);
    setCopied(false);
    setLoading(true);
    try {
      const res = await startAuthWizard({
        client_id: clientId.trim(),
        client_secret: clientSecret.trim(),
        project_id: projectId.trim(),
      });
      window.location.href = res.authorize_url;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function copyDotenv() {
    if (!dotenv) return;
    await navigator.clipboard.writeText(dotenv);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  async function copyRedirectUri() {
    await navigator.clipboard.writeText(REDIRECT_URI);
    setCopiedRedirect(true);
    window.setTimeout(() => setCopiedRedirect(false), 2000);
  }

  function openGcpCredentials() {
    window.open(GCP_CREDENTIALS_URL, "_blank", "noopener,noreferrer");
  }

  function downloadDotenv() {
    if (!dotenv) return;
    const blob = new Blob([dotenv], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = ".env";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  const canSubmit =
    clientId.trim().length > 5 &&
    clientSecret.trim().length > 0 &&
    projectId.trim().length > 5;

  return (
    <Card className="border-emerald-900/40 bg-emerald-950/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg text-emerald-100">
          <KeyRound className="h-5 w-5 text-emerald-400" />
          OAuth wizard (PCM)
        </CardTitle>
        <CardDescription className="text-emerald-200/80">
          Paste OAuth client id/secret and your Nest Device Access project id. We open
          Partner Connections in this tab; after you approve Google, you return here with a
          one-time <span className="font-mono text-emerald-300">.env</span> block to save.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3 rounded-md border border-amber-900/40 bg-amber-950/30 p-3 text-sm text-amber-100/90">
          <p>
            <strong className="text-amber-200">Step 1 — Google Cloud:</strong> open your
            Desktop OAuth client, then under <em>Authorized redirect URIs</em> add this value
            (use Copy, then Save in Google):
          </p>
          <code className="block break-all rounded bg-black/40 px-2 py-1.5 text-xs text-amber-300">
            {REDIRECT_URI}
          </code>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="border-amber-800/60 bg-amber-950/50 text-amber-100 hover:bg-amber-900/50"
              onClick={openGcpCredentials}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Google Cloud credentials
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="border-amber-800/60 bg-amber-950/50 text-amber-100 hover:bg-amber-900/50"
              onClick={() => void copyRedirectUri()}
            >
              <Copy className="mr-2 h-4 w-4" />
              {copiedRedirect ? "Copied URI" : "Copy redirect URI"}
            </Button>
          </div>
        </div>

        <div className="grid gap-2">
          <Label className="text-slate-300">OAuth client ID</Label>
          <Input
            className="border-slate-800 bg-slate-900 text-slate-100"
            placeholder="xxxx.apps.googleusercontent.com"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="grid gap-2">
          <Label className="text-slate-300">OAuth client secret</Label>
          <Input
            type="password"
            className="border-slate-800 bg-slate-900 text-slate-100"
            placeholder="From client_secret JSON"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="grid gap-2">
          <Label className="text-slate-300">Device Access project id (UUID)</Label>
          <Input
            className="border-slate-800 bg-slate-900 text-slate-100"
            placeholder="Nest Device Access console — same as NEST_PROJECT_ID"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            autoComplete="off"
          />
        </div>

        {error && (
          <div className="flex gap-2 rounded-md border border-red-900/50 bg-red-950/40 p-3 text-sm text-red-200">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span className="break-words">{error}</span>
          </div>
        )}

        <Button
          type="button"
          className="w-full bg-emerald-700 text-white hover:bg-emerald-600"
          disabled={!canSubmit || loading}
          onClick={() => void onStart()}
        >
          {loading ? "Opening Google…" : "Start — sign in with Google (PCM)"}
        </Button>

        {dotenv && (
          <div className="space-y-2 rounded-md border border-emerald-800/60 bg-slate-950/80 p-4">
            <div className="flex items-center gap-2 text-emerald-300">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">Save as repo root .env</span>
            </div>
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded border border-slate-800 bg-black/50 p-3 text-xs text-slate-200">
              {dotenv}
            </pre>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                className="border-slate-700 text-slate-200 hover:bg-slate-800"
                onClick={() => void copyDotenv()}
              >
                <Copy className="mr-2 h-4 w-4" />
                {copied ? "Copied" : "Copy .env block"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="border-slate-700 text-slate-200 hover:bg-slate-800"
                onClick={downloadDotenv}
              >
                <Download className="mr-2 h-4 w-4" />
                Download .env
              </Button>
            </div>
            <p className="text-xs text-slate-500">
              Restart the backend after saving .env (or reload if it hot-reloads env). Secrets
              were shown once and removed from server memory.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
