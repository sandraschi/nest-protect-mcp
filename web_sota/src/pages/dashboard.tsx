import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, ShieldCheck, Battery, Cpu, AlertTriangle, Flame } from "lucide-react";
import { getStatus, type DeviceSummary } from "@/lib/api";

function safetyLabel(devices: DeviceSummary[]): { status: string; sub: string } {
  if (!devices?.length) return { status: "Unknown", sub: "No devices" };
  const anyAlarm = devices.some(
    (d) =>
      (d.alarm && d.alarm.toLowerCase() !== "ok" && d.alarm.toLowerCase() !== "none") ||
      (d.smoke && d.smoke.toLowerCase() !== "ok") ||
      (d.co && d.co.toLowerCase() !== "ok")
  );
  if (anyAlarm)
    return { status: "Alert", sub: "Smoke/CO or alarm active" };
  const allOk = devices.every(
    (d) =>
      (d.smoke === "OK" || !d.smoke) &&
      (d.co === "OK" || !d.co) &&
      (d.alarm === "OK" || d.alarm === "none" || !d.alarm)
  );
  if (allOk) return { status: "Nominal", sub: "No smoke/CO detected" };
  return { status: "Nominal", sub: "Devices reporting" };
}

function batteryLabel(devices: DeviceSummary[]): { status: string; sub: string } {
  if (!devices?.length) return { status: "—", sub: "No data" };
  const low = devices.filter(
    (d) =>
      d.battery &&
      (d.battery.toLowerCase().includes("low") || d.battery.toLowerCase().includes("replace"))
  );
  if (low.length) return { status: "Low", sub: `${low.length} device(s) need attention` };
  return { status: "OK", sub: "All modules healthy" };
}

const BACKEND_PORT = 10753;

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["nest-protect-status"],
    queryFn: getStatus,
  });

  const devices: DeviceSummary[] = data?.status?.devices ?? [];
  const safety = safetyLabel(devices);
  const battery = batteryLabel(devices);
  const onlineCount = devices.filter((d) => d.online !== false).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Nest Protect Dashboard
          </h2>
          <p className="text-slate-400">Device health and safety telemetry</p>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-900/50 bg-red-950/30 p-3 text-sm text-red-300">
          Backend unreachable. Run web_sota\\start.ps1 (backend on port {BACKEND_PORT}).
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Safety Status (Fire / CO)
            </CardTitle>
            {safety.status === "Alert" ? (
              <Flame className="h-4 w-4 text-amber-500" />
            ) : (
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading ? "…" : safety.status}
            </div>
            <p className="text-xs text-slate-400">{safety.sub}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Active Devices
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading ? "…" : `${onlineCount}/${devices.length}`}
            </div>
            <p className="text-xs text-slate-400">
              {devices.length
                ? devices.map((d) => d.name || d.room || d.device_id).join(", ")
                : "No devices"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Battery Level
            </CardTitle>
            <Battery className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading ? "…" : battery.status}
            </div>
            <p className="text-xs text-slate-400">{battery.sub}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Bridge Port
            </CardTitle>
            <Cpu className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{BACKEND_PORT}</div>
            <p className="text-xs text-slate-400">FastAPI bridge</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Safety (Fire / CO) by device</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] font-mono text-xs p-4 overflow-y-auto border border-slate-800 rounded-md bg-slate-900/50 text-slate-400 space-y-2">
              {isLoading && <p className="text-slate-500">Loading…</p>}
              {error && <p className="text-red-400">Could not load devices</p>}
              {!isLoading && !error && devices.length === 0 && (
                <p className="text-slate-500">No devices (auth or API may be needed)</p>
              )}
              {devices.map((d) => (
                <p key={d.device_id}>
                  <span className="text-white">{d.name || d.room || d.device_id}</span>
                  {" · "}
                  smoke: {d.smoke ?? "—"} | CO: {d.co ?? "—"} | alarm: {d.alarm ?? "—"}
                  {d.online === false && " (offline)"}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Device diagnostics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <AlertTriangle className="h-4 w-4 text-slate-400 mr-2 shrink-0" />
                <div className="ml-2 space-y-1">
                  <p className="text-sm font-medium leading-none text-white">
                    Fire / CO status
                  </p>
                  <p className="text-xs text-slate-400">
                    From Nest Protect API (alarm, smoke, co, heat)
                  </p>
                </div>
              </div>
              <div className="flex items-center">
                <Activity className="h-4 w-4 text-slate-600 mr-2 shrink-0" />
                <div className="ml-2 space-y-1">
                  <p className="text-sm font-medium leading-none text-white">
                    Backend
                  </p>
                  <p className="text-xs text-slate-500">
                    127.0.0.1:{BACKEND_PORT}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
