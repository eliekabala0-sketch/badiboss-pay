import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { DashboardStats } from "../types/api";
import { formatMoney } from "../utils/format";

const currencies = ["USD", "CDF"] as const;

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
        <>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            {currencies.map((currency) => {
              const item = stats.by_currency?.[currency];
              return (
                <div key={currency} className="rounded bg-white p-4 shadow-sm">
                  <h3 className="text-sm font-semibold text-slate-700">{currency}</h3>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <MiniMetric label="Total encaisse" value={formatMoney(item?.total_collected ?? 0, currency)} />
                    <MiniMetric label="Frais fournisseur" value={formatMoney(item?.total_provider_fees ?? 0, currency)} />
                    <MiniMetric label="Commission Badiboss" value={formatMoney(item?.total_commissions ?? 0, currency)} />
                    <MiniMetric label="Net marchand" value={formatMoney(item?.merchant_net ?? 0, currency)} />
                    <MiniMetric label="Solde marchand" value={formatMoney(item?.merchant_available_balance ?? 0, currency)} />
                    <MiniMetric label="Transactions" value={item?.total_transactions ?? 0} />
                    <MiniMetric label="Succes" value={item?.success ?? 0} />
                    <MiniMetric label="Echec" value={item?.failed ?? 0} />
                    <MiniMetric label="En attente" value={item?.pending ?? 0} />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
            <Card label="Transactions reussies" value={stats.status_counts?.success ?? 0} />
            <Card label="Transactions echouees" value={stats.status_counts?.failed ?? 0} />
            <Card label="Transactions en attente" value={stats.status_counts?.pending ?? 0} />
            <Card label="Transactions totales" value={stats.total_transactions} />
            <Card label="Transactions devise UNKNOWN" value={stats.by_currency?.UNKNOWN?.total_transactions ?? 0} />
            <Card label="Revenus aujourd'hui USD" value={formatMoney(stats.by_currency?.USD?.revenue_today ?? 0, "USD")} />
            <Card label="Revenus aujourd'hui CDF" value={formatMoney(stats.by_currency?.CDF?.revenue_today ?? 0, "CDF")} />
            <Card label="Revenus ce mois USD" value={formatMoney(stats.by_currency?.USD?.revenue_month ?? 0, "USD")} />
            <Card label="Revenus ce mois CDF" value={formatMoney(stats.by_currency?.CDF?.revenue_month ?? 0, "CDF")} />
            <Card label="Abonnements actifs" value={stats.active_subscriptions} />
            <Card label="Applications connectees" value={stats.total_apps} />
            <Card label="Portefeuilles marchands" value={stats.wallets_merchants} />
            <Card label="Reversements en attente" value={stats.settlements_pending} />
            <Card label="Reversements effectues" value={stats.settlements_done ?? 0} />
            <Card label="Erreurs reversement" value={stats.settlement_errors ?? 0} />
            <Card label="Demandes de retrait" value={stats.withdrawals} />
            <Card label="Retraits en attente" value={stats.withdrawals_pending ?? 0} />
            <Card label="Erreurs API/Webhooks" value={stats.api_webhook_errors} />
            <Card label="Activite sur 30 min" value={stats.realtime_activity} />
          </div>
        </>
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

function MiniMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold">{value}</p>
    </div>
  );
}

export default DashboardPage;
