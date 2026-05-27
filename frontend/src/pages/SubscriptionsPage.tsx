import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { Subscription } from "../types/api";
import { formatDate, formatMoney, planLabel, statusLabel } from "../utils/format";

function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ company_id: "", app_id: "", plan: "monthly", amount: 0, start_date: "", end_date: "" });

  function load() {
    apiClient
      .get<Subscription[]>("/subscriptions")
      .then((response) => setSubscriptions(response.data))
      .catch(() => setError("Impossible de charger les abonnements."));
  }

  useEffect(() => {
    load();
  }, []);

  async function createSubscription(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await apiClient.post("/subscriptions/pay", {
      ...form,
      start_date: new Date(form.start_date).toISOString(),
      end_date: new Date(form.end_date).toISOString(),
    });
    setForm({ company_id: "", app_id: "", plan: "monthly", amount: 0, start_date: "", end_date: "" });
    load();
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Abonnements SaaS</h2>
      <p className="text-sm text-slate-600">Suivez les abonnements mensuels, trimestriels, annuels et les essais gratuits.</p>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <form className="mt-4 grid grid-cols-1 gap-2 rounded bg-white p-4 shadow-sm md:grid-cols-3 xl:grid-cols-6" onSubmit={createSubscription}>
        <input className="rounded border px-3 py-2" placeholder="Entreprise" value={form.company_id} onChange={(event) => setForm((prev) => ({ ...prev, company_id: event.target.value }))} required />
        <input className="rounded border px-3 py-2" placeholder="Application" value={form.app_id} onChange={(event) => setForm((prev) => ({ ...prev, app_id: event.target.value }))} required />
        <select className="rounded border px-3 py-2" value={form.plan} onChange={(event) => setForm((prev) => ({ ...prev, plan: event.target.value }))}>
          <option value="monthly">Mensuel</option>
          <option value="quarterly">Trimestriel</option>
          <option value="yearly">Annuel</option>
          <option value="trial">Essai gratuit</option>
        </select>
        <input className="rounded border px-3 py-2" type="number" step="0.01" placeholder="Montant" value={form.amount} onChange={(event) => setForm((prev) => ({ ...prev, amount: Number(event.target.value) }))} required />
        <input className="rounded border px-3 py-2" type="date" value={form.start_date} onChange={(event) => setForm((prev) => ({ ...prev, start_date: event.target.value }))} required />
        <input className="rounded border px-3 py-2" type="date" value={form.end_date} onChange={(event) => setForm((prev) => ({ ...prev, end_date: event.target.value }))} required />
        <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white md:col-span-2 xl:col-span-1">Ajouter</button>
      </form>

      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Entreprise</th>
              <th className="py-2">Application</th>
              <th className="py-2">Formule</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Début</th>
              <th className="py-2">Fin</th>
              <th className="py-2">Statut</th>
              <th className="py-2">Historique paiement</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.map((sub) => (
              <tr key={sub.id} className="border-b last:border-0">
                <td className="py-2">{sub.company_id}</td>
                <td className="py-2">{sub.app_id}</td>
                <td className="py-2">{planLabel(sub.plan)}</td>
                <td className="py-2">{formatMoney(sub.amount)}</td>
                <td className="py-2">{formatDate(sub.start_date)}</td>
                <td className="py-2">{formatDate(sub.end_date)}</td>
                <td className="py-2">{sub.expired ? "Expiré" : statusLabel(sub.active)}</td>
                <td className="py-2">Voir dans Ventes / Paiements</td>
              </tr>
            ))}
            {subscriptions.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={8}>Aucun abonnement enregistré.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SubscriptionsPage;
