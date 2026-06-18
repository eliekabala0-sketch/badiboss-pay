import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { formatDate } from "../utils/format";

type WebhookRow = {
  id: number;
  direction: string;
  provider: string;
  event_type: string;
  reference: string;
  status_code: number;
  payload?: string;
  error_message?: string;
  created_at?: string;
};

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
      <p className="text-sm text-slate-600">Suivi des callbacks entrants et sortants, erreurs API et relances.</p>
      {status && (
        <p className="mt-2 text-sm text-slate-600">
          Total : {status.total} | Reussis : {status.success} | Echoues : {status.failed}
        </p>
      )}
      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full min-w-[1120px] text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Sens</th>
              <th className="py-2">Fournisseur</th>
              <th className="py-2">Evenement</th>
              <th className="py-2">Reference</th>
              <th className="py-2">TransactionId</th>
              <th className="py-2">SessionId</th>
              <th className="py-2">Code statut</th>
              <th className="py-2">Payload</th>
              <th className="py-2">Erreur</th>
              <th className="py-2">Date</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const payload = parsePayload(row.payload);
              return (
                <tr key={row.id} className="border-b align-top last:border-0">
                  <td className="py-2">{directionLabel(row.direction)}</td>
                  <td className="py-2">{row.provider}</td>
                  <td className="py-2">{row.event_type}</td>
                  <td className="py-2">{row.reference}</td>
                  <td className="py-2">{payload.transactionId ?? "-"}</td>
                  <td className="py-2">{payload.sessionId ?? "-"}</td>
                  <td className="py-2">{row.status_code ?? "-"}</td>
                  <td className="max-w-[280px] truncate py-2 text-xs" title={row.payload ?? ""}>{row.payload ?? "-"}</td>
                  <td className="py-2">{row.error_message ?? "-"}</td>
                  <td className="py-2">{formatDate(row.created_at)}</td>
                  <td className="py-2">
                    <button className="rounded bg-blue-600 px-2 py-1 text-xs text-white disabled:opacity-40" disabled={!row.reference} onClick={() => retry(row.id)}>
                      Relancer
                    </button>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={11}>Aucun webhook enregistre.</td>
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
    INBOUND: "Entrant",
    OUTBOUND: "Sortant",
    incoming: "Entrant",
    outgoing: "Sortant",
  };
  return labels[value] ?? value;
}

function parsePayload(value: string | undefined): { transactionId?: string; sessionId?: string } {
  try {
    const payload = JSON.parse(value ?? "{}");
    const payment = payload.payment && typeof payload.payment === "object" ? payload.payment : {};
    return {
      transactionId: payment.transactionId ?? payload.transactionId,
      sessionId: payment.sessionId ?? payload.sessionId,
    };
  } catch {
    return {};
  }
}
