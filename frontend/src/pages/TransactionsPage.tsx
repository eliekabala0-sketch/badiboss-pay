import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { PaginatedTransactions } from "../types/api";

function TransactionsPage() {
  const [transactions, setTransactions] = useState<PaginatedTransactions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [appId, setAppId] = useState("");

  useEffect(() => {
    apiClient
      .get<PaginatedTransactions>("/transactions", { params: { search, page, app_id: appId || undefined } })
      .then((response) => setTransactions(response.data))
      .catch(() => setError("Impossible de charger les transactions."));
  }, [search, page, appId]);

  function exportCsv() {
    const params = new URLSearchParams();
    if (appId) params.append("app_id", appId);
    window.open(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/transactions/export?${params.toString()}`, "_blank");
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Transactions</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        <input className="rounded border px-2 py-1" placeholder="Recherche ref/user/phone/app" value={search} onChange={(event) => setSearch(event.target.value)} />
        <input className="rounded border px-2 py-1" placeholder="Filtre app_id" value={appId} onChange={(event) => setAppId(event.target.value)} />
        <button onClick={exportCsv} className="rounded bg-blue-600 px-3 py-1 text-sm text-white">
          Export CSV
        </button>
      </div>
      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Reference</th>
              <th className="py-2">App</th>
              <th className="py-2">Company</th>
              <th className="py-2">Telephone</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {(transactions?.items ?? []).map((tx) => (
              <tr key={tx.id} className="border-b last:border-0">
                <td className="py-2">{tx.reference}</td>
                <td className="py-2">{tx.app_id}</td>
                <td className="py-2">{tx.company_id}</td>
                <td className="py-2">{tx.payer_phone ?? "-"}</td>
                <td className="py-2">
                  {tx.amount} {tx.currency}
                </td>
                <td className="py-2">{tx.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button className="rounded border px-2 py-1 text-sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          Prev
        </button>
        <span className="text-sm">Page {transactions?.page ?? page}</span>
        <button
          className="rounded border px-2 py-1 text-sm"
          disabled={Boolean(transactions && transactions.page * transactions.page_size >= transactions.total)}
          onClick={() => setPage((value) => value + 1)}
        >
          Next
        </button>
      </div>
    </section>
  );
}

export default TransactionsPage;
