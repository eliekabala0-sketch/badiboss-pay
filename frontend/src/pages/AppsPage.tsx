import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { ConnectedApp } from "../types/api";

function AppsPage() {
  const [apps, setApps] = useState<ConnectedApp[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [newApp, setNewApp] = useState({
    app_id: "",
    company_id: "",
    name: "",
    app_type: "saas",
    callback_url: "",
    status: "active",
    commission_type: "percentage",
    commission_value: 0,
  });

  function loadApps() {
    apiClient
      .get<ConnectedApp[]>("/apps")
      .then((response) => setApps(response.data))
      .catch(() => setError("Impossible de charger les applications."));
  }

  useEffect(() => {
    loadApps();
  }, []);

  async function createApp() {
    await apiClient.post("/apps/create", newApp);
    setNewApp({
      app_id: "",
      company_id: "",
      name: "",
      app_type: "saas",
      callback_url: "",
      status: "active",
      commission_type: "percentage",
      commission_value: 0,
    });
    loadApps();
  }

  async function suspend(appId: string) {
    await apiClient.patch(`/apps/${appId}/status`, null, { params: { status_value: "suspended" } });
    loadApps();
  }

  async function activate(appId: string) {
    await apiClient.patch(`/apps/${appId}/status`, null, { params: { status_value: "active" } });
    loadApps();
  }

  async function toggleKeys(appId: string, apiKeyActive: boolean, secretKeyActive: boolean) {
    await apiClient.patch(`/apps/${appId}/keys`, null, {
      params: { api_key_active: apiKeyActive, secret_key_active: secretKeyActive },
    });
    loadApps();
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Applications connectees</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-4 rounded bg-white p-4 shadow-sm">
        <h3 className="mb-2 font-semibold">Creer une application</h3>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-4">
          <input className="rounded border px-2 py-1" placeholder="app_id" value={newApp.app_id} onChange={(event) => setNewApp((prev) => ({ ...prev, app_id: event.target.value }))} />
          <input className="rounded border px-2 py-1" placeholder="company_id" value={newApp.company_id} onChange={(event) => setNewApp((prev) => ({ ...prev, company_id: event.target.value }))} />
          <input className="rounded border px-2 py-1" placeholder="nom" value={newApp.name} onChange={(event) => setNewApp((prev) => ({ ...prev, name: event.target.value }))} />
          <input className="rounded border px-2 py-1" placeholder="callback_url" value={newApp.callback_url} onChange={(event) => setNewApp((prev) => ({ ...prev, callback_url: event.target.value }))} />
        </div>
        <button onClick={createApp} className="mt-3 rounded bg-blue-600 px-3 py-2 text-sm text-white">
          Creer app
        </button>
      </div>
      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">App ID</th>
              <th className="py-2">Company</th>
              <th className="py-2">Nom</th>
              <th className="py-2">Type</th>
              <th className="py-2">Statut</th>
              <th className="py-2">Cles API</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {apps.map((app) => (
              <tr key={app.id} className="border-b last:border-0">
                <td className="py-2">{app.app_id}</td>
                <td className="py-2">{app.company_id}</td>
                <td className="py-2">{app.name}</td>
                <td className="py-2">{app.app_type}</td>
                <td className="py-2">{app.status}</td>
                <td className="py-2">
                  {app.api_key_active ? "API on" : "API off"} / {app.secret_key_active ? "Secret on" : "Secret off"}
                </td>
                <td className="py-2">
                  <button onClick={() => suspend(app.app_id)} className="mr-1 rounded bg-amber-500 px-2 py-1 text-xs text-white">
                    Suspendre
                  </button>
                  <button onClick={() => activate(app.app_id)} className="mr-1 rounded bg-green-600 px-2 py-1 text-xs text-white">
                    Activer
                  </button>
                  <button onClick={() => toggleKeys(app.app_id, !app.api_key_active, !app.secret_key_active)} className="rounded bg-slate-700 px-2 py-1 text-xs text-white">
                    Toggle cles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default AppsPage;
