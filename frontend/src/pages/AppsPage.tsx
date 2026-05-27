import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../api/client";
import { CompanySummary, ConnectedApp } from "../types/api";
import { appTypeLabel, commissionLabel, formatDate, statusLabel } from "../utils/format";

const emptyApp = {
  app_id: "",
  company_id: "",
  name: "",
  app_type: "saas",
  callback_url: "",
  status: "active",
  commission_type: "percentage",
  commission_value: 0,
};

const appTypes = [
  ["saas", "SaaS abonnement"],
  ["training", "Formation"],
  ["restaurant", "Restaurant"],
  ["church", "Église"],
  ["discovery", "Découverte"],
  ["marketplace", "Marketplace"],
  ["other", "Autre"],
];

const commissionTypes = [
  ["percentage", "Pourcentage"],
  ["fixed", "Fixe"],
  ["none", "Aucune"],
];

function AppsPage() {
  const [apps, setApps] = useState<ConnectedApp[]>([]);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [newApp, setNewApp] = useState(emptyApp);
  const [editingAppId, setEditingAppId] = useState<string | null>(null);

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
    await apiClient.post("/apps/create", newApp);
    setNewApp(emptyApp);
    setSuccess("Application créée avec ses clés API.");
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
    setSuccess("Application mise à jour.");
    loadApps();
  }

  async function setStatus(appId: string, status: "active" | "suspended") {
    await apiClient.patch(`/apps/${appId}/status`, null, { params: { status_value: status } });
    setSuccess(status === "active" ? "Application activée." : "Application suspendue.");
    loadApps();
  }

  async function setKeys(appId: string, apiKeyActive: boolean, secretKeyActive: boolean) {
    await apiClient.patch(`/apps/${appId}/keys`, null, {
      params: { api_key_active: apiKeyActive, secret_key_active: secretKeyActive },
    });
    setSuccess(apiKeyActive && secretKeyActive ? "Clés activées." : "Clés désactivées.");
    loadApps();
  }

  async function regenerateKeys(appId: string) {
    if (!window.confirm("Régénérer les clés de cette application ? Les anciennes clés ne fonctionneront plus.")) return;
    await apiClient.patch(`/apps/${appId}/keys`, null, { params: { regenerate: true } });
    setSuccess("Nouvelles clés générées.");
    loadApps();
  }

  function copy(value: string, label: string) {
    navigator.clipboard.writeText(value);
    setSuccess(`${label} copié.`);
  }

  return (
    <section>
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Applications connectées</h2>
          <p className="text-sm text-slate-600">Créez les applications clientes, configurez les commissions et gérez les clés d'intégration.</p>
        </div>
      </div>

      {error && <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {success && <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">{success}</p>}

      <form className="mt-4 rounded bg-white p-4 shadow-sm" onSubmit={createApp}>
        <h3 className="mb-3 font-semibold">Nouvelle application</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <input className="rounded border px-3 py-2" placeholder="Identifiant application (optionnel)" value={newApp.app_id} onChange={(event) => setNewApp((prev) => ({ ...prev, app_id: event.target.value }))} />
          <input className="rounded border px-3 py-2" placeholder="Entreprise cliente" value={newApp.company_id} onChange={(event) => setNewApp((prev) => ({ ...prev, company_id: event.target.value }))} required />
          <input className="rounded border px-3 py-2" placeholder="Nom de l'application" value={newApp.name} onChange={(event) => setNewApp((prev) => ({ ...prev, name: event.target.value }))} required />
          <select className="rounded border px-3 py-2" value={newApp.app_type} onChange={(event) => setNewApp((prev) => ({ ...prev, app_type: event.target.value }))}>
            {appTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <select className="rounded border px-3 py-2" value={newApp.commission_type} onChange={(event) => setNewApp((prev) => ({ ...prev, commission_type: event.target.value }))}>
            {commissionTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <input className="rounded border px-3 py-2" type="number" step="0.01" placeholder="Valeur commission" value={newApp.commission_value} onChange={(event) => setNewApp((prev) => ({ ...prev, commission_value: Number(event.target.value) }))} />
          <input className="rounded border px-3 py-2 md:col-span-2" placeholder="URL de rappel" value={newApp.callback_url} onChange={(event) => setNewApp((prev) => ({ ...prev, callback_url: event.target.value }))} required />
          <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700" type="submit">
            Créer l'application
          </button>
        </div>
      </form>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
        <div className="overflow-x-auto rounded bg-white p-3 shadow-sm">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2">Application</th>
                <th className="py-2">Entreprise</th>
                <th className="py-2">Type</th>
                <th className="py-2">Commission</th>
                <th className="py-2">Statut</th>
                <th className="py-2">Clés</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((app) => (
                <tr key={app.id} className="border-b align-top last:border-0">
                  <td className="py-3">
                    <p className="font-medium">{app.name}</p>
                    <p className="text-xs text-slate-500">{app.app_id}</p>
                    <p className="text-xs text-slate-500">{formatDate(app.created_at)}</p>
                  </td>
                  <td className="py-3">{app.company_id}</td>
                  <td className="py-3">{appTypeLabel(app.app_type)}</td>
                  <td className="py-3">{commissionLabel(app.commission_type)} ({app.commission_value})</td>
                  <td className="py-3">{statusLabel(app.status)}</td>
                  <td className="py-3 text-xs">
                    <p>API : {statusLabel(app.api_key_active)}</p>
                    <p>Secret : {statusLabel(app.secret_key_active)}</p>
                  </td>
                  <td className="py-3">
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded bg-slate-700 px-2 py-1 text-xs text-white" onClick={() => setEditingAppId(app.app_id)} type="button">Modifier</button>
                      <button className="rounded bg-green-600 px-2 py-1 text-xs text-white" onClick={() => setStatus(app.app_id, "active")} type="button">Activer</button>
                      <button className="rounded bg-amber-600 px-2 py-1 text-xs text-white" onClick={() => setStatus(app.app_id, "suspended")} type="button">Suspendre</button>
                      <button className="rounded bg-indigo-600 px-2 py-1 text-xs text-white" onClick={() => setKeys(app.app_id, !app.api_key_active, !app.secret_key_active)} type="button">
                        {app.api_key_active || app.secret_key_active ? "Désactiver clés" : "Activer clés"}
                      </button>
                      <button className="rounded bg-red-600 px-2 py-1 text-xs text-white" onClick={() => regenerateKeys(app.app_id)} type="button">Régénérer</button>
                    </div>
                  </td>
                </tr>
              ))}
              {apps.length === 0 && (
                <tr>
                  <td className="py-6 text-center text-slate-500" colSpan={7}>Aucune application enregistrée.</td>
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
              {companies.length === 0 && <p className="text-slate-500">Aucune entreprise enregistrée.</p>}
            </div>
          </div>
          {selectedApp && (
            <div className="rounded bg-white p-4 shadow-sm">
              <h3 className="font-semibold">Modifier l'application</h3>
              <div className="mt-3 space-y-2">
                <input className="w-full rounded border px-3 py-2" value={selectedApp.name} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, name: event.target.value } : item))} />
                <input className="w-full rounded border px-3 py-2" value={selectedApp.company_id} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, company_id: event.target.value } : item))} />
                <input className="w-full rounded border px-3 py-2" value={selectedApp.callback_url} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, callback_url: event.target.value } : item))} />
                <select className="w-full rounded border px-3 py-2" value={selectedApp.app_type} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, app_type: event.target.value } : item))}>
                  {appTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <select className="w-full rounded border px-3 py-2" value={selectedApp.commission_type} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, commission_type: event.target.value } : item))}>
                  {commissionTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <input className="w-full rounded border px-3 py-2" type="number" step="0.01" value={selectedApp.commission_value} onChange={(event) => setApps((items) => items.map((item) => item.app_id === selectedApp.app_id ? { ...item, commission_value: Number(event.target.value) } : item))} />
                <div className="flex gap-2">
                  <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={() => saveApp(selectedApp)} type="button">Enregistrer</button>
                  <button className="rounded border px-3 py-2 text-sm" onClick={() => setEditingAppId(null)} type="button">Annuler</button>
                </div>
              </div>
            </div>
          )}
          {selectedApp && (
            <div className="rounded bg-white p-4 shadow-sm">
              <h3 className="font-semibold">Instructions d'intégration</h3>
              <div className="mt-3 space-y-2 text-xs">
                <KeyRow label="APP_ID" value={selectedApp.app_id} onCopy={copy} />
                <KeyRow label="API_KEY" value={selectedApp.api_key} onCopy={copy} />
                <KeyRow label="SECRET_KEY" value={selectedApp.secret_key} onCopy={copy} />
                <p className="rounded bg-slate-100 p-2">Envoyez les paiements vers l'API Badiboss Pay avec APP_ID, API_KEY et SECRET_KEY. L'URL de rappel configurée recevra les mises à jour de paiement.</p>
              </div>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

function KeyRow({ label, value, onCopy }: { label: string; value: string; onCopy: (value: string, label: string) => void }) {
  return (
    <div className="rounded border p-2">
      <p className="font-semibold">{label}</p>
      <p className="break-all text-slate-600">{value}</p>
      <button className="mt-2 rounded bg-slate-800 px-2 py-1 text-xs text-white" onClick={() => onCopy(value, label)} type="button">Copier</button>
    </div>
  );
}

export default AppsPage;
