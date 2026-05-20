import { AuthWizard } from "@/components/AuthWizard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldCheck, Cloud, Key, Terminal, FileCode, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

const STEPS = [
  {
    title: "Google Cloud + Nest Device Access",
    icon: Cloud,
    items: [
      "Register at Google Nest Device Access if you have not — you get a Device Access project id (UUID).",
      "Google Cloud Console: enable Smart Device Management API.",
      "OAuth consent screen (External): add restricted scope https://www.googleapis.com/auth/sdm.service (shows as Smart Device Management / home automation). Add yourself as a test user.",
      "Credentials → OAuth client ID → Desktop app. Download client_secret_*.json. In Authorized redirect URIs add http://127.0.0.1:8080/ (matches the refresh-token script default).",
    ],
  },
  {
    title: "Get the refresh token (PCM)",
    icon: Key,
    items: [
      "From repo root (with client_secret_*.json and NEST_PROJECT_ID set):",
      "uv run python scripts/get_nest_refresh_token.py --project-id YOUR_DEVICE_ACCESS_PROJECT_ID",
      "Uses Partner Connections (nestservices.google.com), not the generic Google login URL. Browser completes PCM; terminal prints NEST_REFRESH_TOKEN.",
      "Optional: set NEST_OAUTH_LOCAL_PORT if 8080 is taken; add that redirect URI to the OAuth client.",
    ],
  },
  {
    title: "Env vars",
    icon: FileCode,
    items: [
      "Create .env in the repo root (do not commit):",
      "NEST_CLIENT_ID / NEST_CLIENT_SECRET — from the OAuth JSON.",
      "NEST_PROJECT_ID — your Nest Device Access project id (UUID), same as enterprises/{id} in the SDM API — not the numeric GCP project number.",
      "NEST_REFRESH_TOKEN — from the script. Optional: NEST_SDM_OAUTH_SCOPE only if Google assigned a different scope (default is sdm.service).",
    ],
  },
  {
    title: "Run the webapp",
    icon: Terminal,
    items: [
      "From repo root: web_sota\\start.ps1",
      "Backend loads .env and uses the refresh token. Open the dashboard; devices and fire/CO status should load.",
    ],
  },
];

const TROUBLESHOOTING = [
  { issue: "invalid_client", fix: "Wrong client ID/secret or swapped; check the JSON and .env." },
  { issue: "access_denied", fix: "Add your account as test user on OAuth consent screen; use the account that owns Nest Protects." },
  { issue: "invalid_scope", fix: "Scope must be exactly https://www.googleapis.com/auth/sdm.service." },
  { issue: "No refresh token", fix: "Revoke app access for your Google account, then run the script again." },
  { issue: "No devices", fix: "Same Google account must have Nest Protect in Google Home; wait a few minutes after linking." },
];

export function Onboarding() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Setup &amp; auth
        </h2>
        <p className="text-slate-400 mt-1">
          One-time Google OAuth setup so the dashboard and MCP server can talk to Nest Protect (fire/CO).
        </p>
      </div>

      <AuthWizard />

      <div className="grid gap-6 md:grid-cols-1">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          return (
            <Card key={i} className="border-slate-800 bg-slate-950/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-white">
                  <Icon className="h-5 w-5 text-emerald-500" />
                  {step.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
                  {step.items.map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-amber-900/50 bg-amber-950/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2 text-amber-200">
            <AlertCircle className="h-5 w-5" />
            Troubleshooting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {TROUBLESHOOTING.map((t, i) => (
              <li key={i} className="text-slate-300">
                <span className="font-mono text-amber-400">{t.issue}</span>
                {" — "}
                {t.fix}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="flex gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          <ShieldCheck className="h-4 w-4" />
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
