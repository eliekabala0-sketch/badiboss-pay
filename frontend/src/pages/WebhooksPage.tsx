import { useEffect, useState } from "react";

import { apiClient } from "../api/client";

type WebhookRow = { id: number; direction: string; provider: string; event_type: string; reference: string; status_code: number; error_message?: string };

function WebhooksPage() {
  const [rows, setRows] = useState<WebhookRow[]>([]);
  const [status, setStatus] = useState<{ total: number; success: number; failed: number } | null>(null);

  function load() {
    apiClient.get<WebhookRow[]>("/webhooks/history").then((response) => setRows(response.data));
    apiClient.get("/webhooks/status").then((response) => setStatus(response.data));
  }

  useEffect(() => {
    load();
  }, []);

  async function retry(logId: number) {
    await apiClient.post(`/webhooks/retry/${logId}`);
    load();
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Webhooks</h2>
      <p className="text-sm text-slate-600">Suivi des rappels entrants et sortants, erreurs API et relances.</p>
      {status && (
        <p className="mt-2 text-sm text-slate-600">
          Total : {status.total} | Réussis : {status.success} | Échoués : {status.failed}
        </p>
      )}
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Sens</th>
              <th className="py-2">Fournisseur</th>
              <th className="py-2">Événement</th>
              <th className="py-2">Référence</th>
              <th className="py-2">Code statut</th>
              <th className="py-2">Erreur</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b last:border-0">
                <td className="py-2">{directionLabel(row.direction)}</td>
                <td className="py-2">{row.provider}</td>
                <td className="py-2">{row.event_type}</td>
                <td className="py-2">{row.reference}</td>
                <td className="py-2">{row.status_code ?? "-"}</td>
                <td className="py-2">{row.error_message ?? "-"}</td>
                <td className="py-2">
                  <button className="rounded bg-blue-600 px-2 py-1 text-xs text-white" onClick={() => retry(row.id)}>
                    Relancer
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={7}>Aucun webhook enregistré.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default WebhooksPage;

function directionLabel(value: string) {
  const labels: Record<string, string> = {
    incoming: "Entrant",
    outgoing: "Sortant",
  };
  return labels[value] ?? value;
}
