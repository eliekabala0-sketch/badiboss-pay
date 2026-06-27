import { useEffect, useMemo, useState } from "react";
import type { Dispatch, FormEvent, SetStateAction } from "react";

import { apiClient } from "../api/client";
import { CompanySummary, ConnectedApp } from "../types/api";
import { appTypeLabel, commissionLabel, formatDate, formatMoney, statusLabel } from "../utils/format";

const emptyApp = {
  company_id: "",
  name: "",
  app_type: "app",
  callback_url: "",
  status: "active",
  commission_type: "none",
  commission_value: 0,
};

const appTypes = [
  ["app", "App"],
  ["web", "Web"],
  ["restaurant", "Restaurant"],
  ["church", "Eglise"],
  ["saas", "SaaS"],
  ["other", "Autre"],
];

const commissionTypes = [
  ["none", "Aucune"],
  ["fixed", "Fixe"],
  ["percentage", "Pourcentage"],
];

function AppsPage() {
  const [apps, setApps] = useState<ConnectedApp[]>([]);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [newApp, setNewApp] = useState(emptyApp);
  const [editingAppId, setEditingAppId] = useState<string | null>(null);
  const [createdApp, setCreatedApp] = useState<ConnectedApp | null>(null);

  const selectedApp = useMemo(() => apps.find((app) => app.app_id === editingAppId) ?? null, [apps, editingAppId]);

  function loadApps() {
    setError(null);
    apiClient
      .get<ConnectedApp[]>("/apps")
      .then((response) => setApps(response.data))
      .catch(() => setError("Impossible de charger les applications."));
    apiClient
      .get<CompanySummary[]>("/apps/companies")
      .then((response) => setCompanies(response.data))
      .catch(() => undefined);
  }

  useEffect(() => {
    loadApps();
  }, []);

  async function createApp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const response = await apiClient.post<ConnectedApp>("/apps/create", newApp);
    setCreatedApp(response.data);
    setNewApp(emptyApp);
    setSuccess("Application creee. Les secrets complets sont affiches une seule fois ci-dessous.");
    loadApps();
  }

  async function saveApp(app: ConnectedApp) {
    await apiClient.patch(`/apps/${app.app_id}`, {
      company_id: app.company_id,
      name: app.name,
      app_type: app.app_type,
      callback_url: app.callback_url,
      status: app.status,
      commission_type: app.commission_type,
      commission_value: app.commission_value,
    });
    setEditingAppId(null);
    setSuccess("Application mise a jour.");
    loadApps();
  }

  async function setStatus(appId: string, status: "active" | "suspended") {
    await apiClient.patch(`/apps/${appId}/status`, null, { params: { status_value: status } });
    setSuccess(status === "active" ? "Application activee." : "Application desactivee.");
    loadApps();
  }

  async function regenerateSecret(appId: string, target: "api" | "webhook") {
    const label = target === "api" ? "le secret API" : "le secret webhook";
    if (!window.confirm(`Regenerer ${label} ? L'ancien secret ne fonctionnera plus.`)) return;
    const response = await apiClient.patch<ConnectedApp>(`/apps/${appId}/keys`, null, { params: { regenerate: true, target } });
    setCreatedApp(response.data);
    setSuccess("Nouveau secret genere. Conservez-le maintenant.");
    loadApps();
  }

  async function downloadGuide(app: ConnectedApp) {
    const response = await apiClient.get(`/apps/${app.app_id}/integration-guide`);
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${app.app_slug}-integration-guide.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function copy(value: string, label: string) {
    navigator.clipboard.writeText(value);
    setSuccess(`${label} copie.`);
  }

  return (
    <section>
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Applications connectees</h2>
          <p className="text-sm text-slate-600">Gestion des applications clientes, cles d'integration, URLs de paiement et commissions.</p>
        </div>
      </div>

      {error && <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {success && <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">{success}</p>}

      <form className="mt-4 rounded bg-white p-4 shadow-sm" onSubmit={createApp}>
        <h3 className="mb-3 font-semibold">Nouvelle application cliente</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <input className="rounded border px-3 py-2" placeholder="Nom de l'application" value={newApp.name} onChange={(event) => setNewApp((prev) => ({ ...prev, name: event.target.value }))} required />
          <input className="rounded border px-3 py-2" placeholder="Entreprise cliente" value={newApp.company_id} onChange={(event) => setNewApp((prev) => ({ ...prev, company_id: event.target.value }))} required />
          <select className="rounded border px-3 py-2" value={newApp.app_type} onChange={(event) => setNewApp((prev) => ({ ...prev, app_type: event.target.value }))}>
            {appTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <select className="rounded border px-3 py-2" value={newApp.commission_type} onChange={(event) => setNewApp((prev) => ({ ...prev, commission_type: event.target.value }))}>
            {commissionTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <input className="rounded border px-3 py-2" type="number" step="0.01" placeholder="Valeur commission" value={newApp.commission_value} onChange={(event) => setNewApp((prev) => ({ ...prev, commission_value: Number(event.target.value) }))} />
          <input className="rounded border px-3 py-2" placeholder="Callback client optionnel" value={newApp.callback_url} onChange={(event) => setNewApp((prev) => ({ ...prev, callback_url: event.target.value }))} />
          <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700" type="submit">
            Creer l'application
          </button>
        </div>
      </form>

      {createdApp && (
        <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-4 text-sm">
          <h3 className="font-semibold text-amber-900">Secrets a conserver maintenant</h3>
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <SecretRow label="APP_ID" value={createdApp.app_id} onCopy={copy} />
            <SecretRow label="APP_SLUG" value={createdApp.app_slug} onCopy={copy} />
            <SecretRow label="API_KEY" value={createdApp.api_key} onCopy={copy} />
            {createdApp.api_secret_once && <SecretRow label="API_SECRET" value={createdApp.api_secret_once} onCopy={copy} />}
            {createdApp.webhook_secret_once && <SecretRow label="WEBHOOK_SECRET" value={createdApp.webhook_secret_once} onCopy={copy} />}
            <SecretRow label="PAYMENT_URL" value={createdApp.payment_url} onCopy={copy} />
            <SecretRow label="STATUS_URL" value={createdApp.status_url} onCopy={copy} />
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
        <div className="overflow-x-auto rounded bg-white p-3 shadow-sm">
          <table className="w-full min-w-[1380px] text-left text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2">Application</th>
                <th className="py-2">Entreprise</th>
                <th className="py-2">Identifiants</th>
                <th className="py-2">Commission</th>
                <th className="py-2">URLs</th>
                <th className="py-2">Secrets</th>
                <th className="py-2">Stats</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((app) => (
                <tr key={app.id} className="border-b align-top last:border-0">
                  <td className="py-3">
                    <p className="font-medium">{app.name}</p>
                    <p className="text-xs text-slate-500">{appTypeLabel(app.app_type)}</p>
                    <p className="text-xs text-slate-500">{formatDate(app.created_at)}</p>
                    <p className="mt-1 text-xs">{statusLabel(app.status)}</p>
                  </td>
                  <td className="py-3">{app.company_id}</td>
                  <td className="py-3 text-xs">
                    <p>slug: {app.app_slug}</p>
                    <p>app_id: {app.app_id}</p>
                  </td>
                  <td className="py-3">{commissionLabel(app.commission_type)} ({app.commission_value})</td>
                  <td className="py-3 text-xs">
                    <CopyLine label="Payment" value={app.payment_url} onCopy={copy} />
                    <CopyLine label="Status" value={app.status_url} onCopy={copy} />
                    <CopyLine label="Client callback" value={app.callback_url || "-"} onCopy={copy} />
                    <CopyLine label="Badiboss callback" value={app.callback_badiboss_pay} onCopy={copy} />
                  </td>
                  <td className="py-3 text-xs">
                    <CopyLine label="API key" value={app.api_key} onCopy={copy} />
                    <p>API secret: {app.secret_key}</p>
                    <p>Webhook: {app.webhook_secret}</p>
                  </td>
                  <td className="py-3 text-xs">
                    <p>{app.transactions_count} transaction(s)</p>
                    <p>USD: {formatMoney(app.total_usd, "USD")}</p>
                    <p>CDF: {formatMoney(app.total_cdf, "CDF")}</p>
                    <p>{app.success_count} succes / {app.failed_count} echecs / {app.pending_count} pending</p>
                  </td>
                  <td className="py-3">
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded bg-slate-700 px-2 py-1 text-xs text-white" onClick={() => setEditingAppId(app.app_id)} type="button">Modifier</button>
                      <button className="rounded bg-green-600 px-2 py-1 text-xs text-white" onClick={() => setStatus(app.app_id, "active")} type="button">Activer</button>
                      <button className="rounded bg-amber-600 px-2 py-1 text-xs text-white" onClick={() => setStatus(app.app_id, "suspended")} type="button">Desactiver</button>
                      <button className="rounded bg-indigo-600 px-2 py-1 text-xs text-white" onClick={() => regenerateSecret(app.app_id, "api")} type="button">Regenerer secret API</button>
                      <button className="rounded bg-purple-600 px-2 py-1 text-xs text-white" onClick={() => regenerateSecret(app.app_id, "webhook")} type="button">Regenerer webhook</button>
                      <button className="rounded bg-blue-600 px-2 py-1 text-xs text-white" onClick={() => downloadGuide(app)} type="button">Guide</button>
                    </div>
                  </td>
                </tr>
              ))}
              {apps.length === 0 && (
                <tr>
                  <td className="py-6 text-center text-slate-500" colSpan={8}>Aucune application enregistree.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <aside className="space-y-4">
          <div className="rounded bg-white p-4 shadow-sm">
            <h3 className="font-semibold">Entreprises clientes</h3>
            <div className="mt-3 space-y-2 text-sm">
              {companies.map((company) => (
                <div className="rounded border p-2" key={company.company_id}>
                  <p className="font-medium">{company.company_id}</p>
                  <p className="text-slate-600">{company.applications} application(s), {company.transactions} vente(s), {company.subscriptions} abonnement(s)</p>
                </div>
              ))}
              {companies.length === 0 && <p className="text-slate-500">Aucune entreprise enregistree.</p>}
            </div>
          </div>

          {selectedApp && (
            <div className="rounded bg-white p-4 shadow-sm">
              <h3 className="font-semibold">Modifier l'application</h3>
              <div className="mt-3 space-y-2">
                <input className="w-full rounded border px-3 py-2" value={selectedApp.name} onChange={(event) => updateSelectedApp(selectedApp.app_id, { name: event.target.value }, setApps)} />
                <input className="w-full rounded border px-3 py-2" value={selectedApp.company_id} onChange={(event) => updateSelectedApp(selectedApp.app_id, { company_id: event.target.value }, setApps)} />
                <input className="w-full rounded border px-3 py-2" value={selectedApp.callback_url} onChange={(event) => updateSelectedApp(selectedApp.app_id, { callback_url: event.target.value }, setApps)} />
                <select className="w-full rounded border px-3 py-2" value={selectedApp.app_type} onChange={(event) => updateSelectedApp(selectedApp.app_id, { app_type: event.target.value }, setApps)}>
                  {appTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <select className="w-full rounded border px-3 py-2" value={selectedApp.commission_type} onChange={(event) => updateSelectedApp(selectedApp.app_id, { commission_type: event.target.value }, setApps)}>
                  {commissionTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <input className="w-full rounded border px-3 py-2" type="number" step="0.01" value={selectedApp.commission_value} onChange={(event) => updateSelectedApp(selectedApp.app_id, { commission_value: Number(event.target.value) }, setApps)} />
                <div className="flex gap-2">
                  <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={() => saveApp(selectedApp)} type="button">Enregistrer</button>
                  <button className="rounded border px-3 py-2 text-sm" onClick={() => setEditingAppId(null)} type="button">Annuler</button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

function updateSelectedApp(appId: string, patch: Partial<ConnectedApp>, setApps: Dispatch<SetStateAction<ConnectedApp[]>>) {
  setApps((items) => items.map((item) => item.app_id === appId ? { ...item, ...patch } : item));
}

function CopyLine({ label, value, onCopy }: { label: string; value: string; onCopy: (value: string, label: string) => void }) {
  return (
    <p className="mb-1">
      <span className="font-medium">{label}:</span> <span className="break-all text-slate-600">{value}</span>
      {value !== "-" && <button className="ml-2 rounded border px-1 py-0.5 text-[11px]" onClick={() => onCopy(value, label)} type="button">Copier</button>}
    </p>
  );
}

function SecretRow({ label, value, onCopy }: { label: string; value: string; onCopy: (value: string, label: string) => void }) {
  return (
    <div className="rounded border border-amber-200 bg-white p-2">
      <p className="font-semibold">{label}</p>
      <p className="break-all text-slate-700">{value}</p>
      <button className="mt-2 rounded bg-slate-800 px-2 py-1 text-xs text-white" onClick={() => onCopy(value, label)} type="button">Copier</button>
    </div>
  );
}

export default AppsPage;
