import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { DashboardStats } from "../types/api";

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
      <h2 className="text-2xl font-semibold">Dashboard Admin</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {stats && (
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Card label="Total transactions" value={stats.total_transactions} />
          <Card label="Total commissions" value={stats.total_commissions} />
          <Card label="Revenus aujourd'hui" value={stats.revenue_today} />
          <Card label="Revenus ce mois" value={stats.revenue_month} />
          <Card label="Abonnements actifs" value={stats.active_subscriptions} />
          <Card label="Applications connectees" value={stats.total_apps} />
          <Card label="Wallets marchands" value={stats.wallets_merchants} />
          <Card label="Settlements en attente" value={stats.settlements_pending} />
          <Card label="Withdrawals" value={stats.withdrawals} />
          <Card label="Erreurs API/Webhooks" value={stats.api_webhook_errors} />
          <Card label="Activite 30 min" value={stats.realtime_activity} />
        </div>
      )}
    </section>
  );
}

function Card({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}

export default DashboardPage;
