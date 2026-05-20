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
      <h2 className="text-2xl font-semibold">Webhooks Management</h2>
      {status && (
        <p className="mt-2 text-sm text-slate-600">
          total: {status.total} | success: {status.success} | failed: {status.failed}
        </p>
      )}
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Direction</th>
              <th className="py-2">Provider</th>
              <th className="py-2">Event</th>
              <th className="py-2">Reference</th>
              <th className="py-2">Status</th>
              <th className="py-2">Erreur</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b last:border-0">
                <td className="py-2">{row.direction}</td>
                <td className="py-2">{row.provider}</td>
                <td className="py-2">{row.event_type}</td>
                <td className="py-2">{row.reference}</td>
                <td className="py-2">{row.status_code ?? "-"}</td>
                <td className="py-2">{row.error_message ?? "-"}</td>
                <td className="py-2">
                  <button className="rounded bg-blue-600 px-2 py-1 text-xs text-white" onClick={() => retry(row.id)}>
                    Retry
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

export default WebhooksPage;
