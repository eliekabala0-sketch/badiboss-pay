import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { PaginatedTransactions } from "../types/api";
import { formatDate, formatMoney, statusLabel } from "../utils/format";

function TransactionsPage() {
  const [transactions, setTransactions] = useState<PaginatedTransactions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ app_id: "", company_id: "", status: "", phone: "", date_from: "", date_to: "" });

  useEffect(() => {
    apiClient
      .get<PaginatedTransactions>("/transactions", { params: { search: search || undefined, page, ...cleanFilters(filters) } })
      .then((response) => {
        setTransactions(response.data);
        setError(null);
      })
      .catch(() => setError("Impossible de charger les ventes."));
  }, [search, page, filters]);

  function exportCsv() {
    const params = new URLSearchParams();
    Object.entries({ search, ...filters }).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
    window.open(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/transactions/export?${params.toString()}`, "_blank");
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Ventes / Paiements</h2>
      <p className="text-sm text-slate-600">Suivi des paiements, commissions, frais fournisseur et informations utilisateur.</p>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 grid grid-cols-1 gap-2 rounded bg-white p-3 shadow-sm md:grid-cols-4 xl:grid-cols-7">
        <input className="rounded border px-3 py-2" placeholder="Référence, téléphone, application" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
        <input className="rounded border px-3 py-2" placeholder="Application" value={filters.app_id} onChange={(event) => setFilters((prev) => ({ ...prev, app_id: event.target.value }))} />
        <input className="rounded border px-3 py-2" placeholder="Entreprise" value={filters.company_id} onChange={(event) => setFilters((prev) => ({ ...prev, company_id: event.target.value }))} />
        <select className="rounded border px-3 py-2" value={filters.status} onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}>
          <option value="">Tous les statuts</option>
          <option value="pending">En attente</option>
          <option value="success">Réussi</option>
          <option value="failed">Échoué</option>
        </select>
        <input className="rounded border px-3 py-2" placeholder="Téléphone" value={filters.phone} onChange={(event) => setFilters((prev) => ({ ...prev, phone: event.target.value }))} />
        <input className="rounded border px-3 py-2" type="date" value={filters.date_from} onChange={(event) => setFilters((prev) => ({ ...prev, date_from: event.target.value }))} />
        <input className="rounded border px-3 py-2" type="date" value={filters.date_to} onChange={(event) => setFilters((prev) => ({ ...prev, date_to: event.target.value }))} />
        <button onClick={exportCsv} className="rounded bg-blue-600 px-3 py-2 text-sm text-white md:col-span-2 xl:col-span-1">
          Exporter CSV
        </button>
      </div>

      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Référence</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Téléphone</th>
              <th className="py-2">Montant brut</th>
              <th className="py-2">Frais fournisseur</th>
              <th className="py-2">Commission Badiboss</th>
              <th className="py-2">Net marchand</th>
              <th className="py-2">Statut</th>
              <th className="py-2">Source / localisation</th>
              <th className="py-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {(transactions?.items ?? []).map((tx) => (
              <tr key={tx.id} className="border-b align-top last:border-0">
                <td className="py-3">{tx.reference}</td>
                <td className="py-3">{tx.app_id}</td>
                <td className="py-3">{tx.company_id}</td>
                <td className="py-3">{tx.payer_phone ?? "-"}</td>
                <td className="py-3">{formatMoney(tx.amount, tx.currency)}</td>
                <td className="py-3">{formatMoney(tx.fees, tx.currency)}</td>
                <td className="py-3">{formatMoney(tx.commission, tx.currency)}</td>
                <td className="py-3">{formatMoney(tx.net_amount, tx.currency)}</td>
                <td className="py-3">{statusLabel(tx.status)}</td>
                <td className="py-3 text-xs">
                  <p>{tx.source_application ?? "-"}</p>
                  <p>{tx.city ?? "-"} / {tx.country ?? "-"}</p>
                  <p>{tx.public_ip ?? "-"} · {tx.device_type ?? tx.device ?? "-"}</p>
                  <p>{tx.operating_system ?? "-"} · {tx.browser ?? "-"}</p>
                </td>
                <td className="py-3">{formatDate(tx.created_at)}</td>
              </tr>
            ))}
            {(transactions?.items ?? []).length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={11}>Aucune vente trouvée.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button className="rounded border px-3 py-2 text-sm disabled:opacity-50" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          Précédent
        </button>
        <span className="text-sm">Page {transactions?.page ?? page} sur {Math.max(1, Math.ceil((transactions?.total ?? 0) / (transactions?.page_size ?? 25)))}</span>
        <button
          className="rounded border px-3 py-2 text-sm disabled:opacity-50"
          disabled={Boolean(transactions && transactions.page * transactions.page_size >= transactions.total)}
          onClick={() => setPage((value) => value + 1)}
        >
          Suivant
        </button>
      </div>
    </section>
  );
}

function cleanFilters(filters: Record<string, string>) {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => Boolean(value)));
}

export default TransactionsPage;
