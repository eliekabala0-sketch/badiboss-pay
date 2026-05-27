import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { DashboardStats } from "../types/api";
import { formatMoney } from "../utils/format";

function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<DashboardStats>("/dashboard/stats")
      .then((response) => setStats(response.data))
      .catch(() => setError("Impossible de charger les statistiques."));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Tableau de bord</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {stats && (
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Card label="Total encaissé" value={formatMoney(stats.total_collected ?? 0)} />
          <Card label="Frais SerdiPay / fournisseur" value={formatMoney(stats.total_provider_fees ?? 0)} />
          <Card label="Commission Badiboss" value={formatMoney(stats.total_commissions)} />
          <Card label="Net marchand" value={formatMoney(stats.merchant_net ?? 0)} />
          <Card label="Solde marchand disponible" value={formatMoney(stats.merchant_available_balance ?? 0)} />
          <Card label="Transactions" value={stats.total_transactions} />
          <Card label="Revenus aujourd'hui" value={formatMoney(stats.revenue_today)} />
          <Card label="Revenus ce mois" value={formatMoney(stats.revenue_month)} />
          <Card label="Abonnements actifs" value={stats.active_subscriptions} />
          <Card label="Applications connectées" value={stats.total_apps} />
          <Card label="Portefeuilles marchands" value={stats.wallets_merchants} />
          <Card label="Reversements en attente" value={stats.settlements_pending} />
          <Card label="Reversements effectués" value={stats.settlements_done ?? 0} />
          <Card label="Erreurs reversement" value={stats.settlement_errors ?? 0} />
          <Card label="Demandes de retrait" value={stats.withdrawals} />
          <Card label="Retraits en attente" value={stats.withdrawals_pending ?? 0} />
          <Card label="Erreurs API/Webhooks" value={stats.api_webhook_errors} />
          <Card label="Activité sur 30 min" value={stats.realtime_activity} />
        </div>
      )}
      {!stats && !error && <p className="mt-4 text-sm text-slate-600">Chargement des indicateurs...</p>}
    </section>
  );
}

function Card({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}

export default DashboardPage;
