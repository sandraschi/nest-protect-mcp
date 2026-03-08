import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { HelpCircle } from "lucide-react";

interface HelpModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function HelpModal({ open, onOpenChange }: HelpModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Setup &amp; auth</DialogTitle>
          <DialogDescription>
            One-time Google OAuth so the dashboard and MCP server can talk to Nest Protect (fire/CO).
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 text-sm text-slate-300">
          <p>
            You need a Google Cloud project with Smart Device Management API enabled, OAuth Desktop credentials,
            and a <strong className="text-white">refresh token</strong> from a browser sign-in.
          </p>
          <ol className="list-decimal list-inside space-y-2">
            <li>Google Cloud Console: enable Smart Device Management API; OAuth consent screen (External, scope sdm.service); create Desktop OAuth client; download client_secret_*.json.</li>
            <li>Run <code className="rounded bg-slate-800 px-1 py-0.5">uv run python scripts/get_nest_refresh_token.py</code> from repo root; sign in in the browser; copy the printed refresh token.</li>
            <li>Create <code className="rounded bg-slate-800 px-1 py-0.5">.env</code> in repo root with NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_PROJECT_ID, NEST_REFRESH_TOKEN.</li>
            <li>Run <code className="rounded bg-slate-800 px-1 py-0.5">web_sota\\start.ps1</code>; the backend loads .env and the dashboard shows devices.</li>
          </ol>
          <p>
            <Link
              to="/onboarding"
              onClick={() => onOpenChange(false)}
              className="text-emerald-400 hover:underline font-medium"
            >
              Full setup guide (onboarding)
            </Link>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function HelpTrigger() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 bg-slate-900/50 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        aria-label="Help"
      >
        <HelpCircle className="h-4 w-4" />
      </button>
      <HelpModal open={open} onOpenChange={setOpen} />
    </>
  );
}
