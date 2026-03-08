import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldCheck, Cloud, Key, Terminal, FileCode, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

const STEPS = [
  {
    title: "Google Cloud setup",
    icon: Cloud,
    items: [
      "Go to Google Cloud Console and create or select a project.",
      "APIs & Services → Library: enable Smart Device Management API.",
      "OAuth consent screen: External, add scope https://www.googleapis.com/auth/sdm.service, add your account as test user.",
      "Credentials → Create OAuth client ID → Desktop app. Download the JSON (client_secret_*.json).",
    ],
  },
  {
    title: "Get the refresh token",
    icon: Key,
    items: [
      "From the repo root (where client_secret_*.json is):",
      "uv run pip install google-auth-oauthlib",
      "uv run python scripts/get_nest_refresh_token.py",
      "A browser opens; sign in with the Google account that has Nest Protect in Google Home. Copy the printed refresh token.",
    ],
  },
  {
    title: "Env vars",
    icon: FileCode,
    items: [
      "Create .env in the repo root (do not commit):",
      "NEST_CLIENT_ID=xxxx.apps.googleusercontent.com",
      "NEST_CLIENT_SECRET=xxxx",
      "NEST_PROJECT_ID=your-project-id",
      "NEST_REFRESH_TOKEN=1//xxxx (from the script)",
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
