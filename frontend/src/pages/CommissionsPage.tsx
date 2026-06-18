import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { commissionLabel, formatMoney } from "../utils/format";

type Commission = {
  id: number;
  app_id: string;
  company_id: string;
  transaction_reference: string;
  commission_type: string;
  commission_value: number;
  amount_collected: number;
  currency: string;
};

type RevenueByCurrency = Record<string, {
  total_commissions: number;
  total_provider_fees: number;
  total_net_platform: number;
}>;

type PlatformRevenue = {
  total_commissions: number;
  total_provider_fees: number;
  total_net_platform: number;
  by_currency: RevenueByCurrency;
};

function CommissionsPage() {
  const [items, setItems] = useState<Commission[]>([]);
  const [revenue, setRevenue] = useState<PlatformRevenue | null>(null);

  useEffect(() => {
    apiClient.get<Commission[]>("/finance/commissions").then((response) => setItems(response.data));
    apiClient.get<PlatformRevenue>("/finance/platform-revenue").then((response) => setRevenue(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Commissions / Revenus plateforme</h2>
      <p className="text-sm text-slate-600">Suivi des commissions Badiboss, frais fournisseur et revenu net plateforme par devise.</p>
      {revenue && (
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(["USD", "CDF"] as const).map((currency) => {
            const item = revenue.by_currency?.[currency];
            return (
              <div key={currency} className="rounded bg-white p-3 shadow-sm">
                <h3 className="font-semibold">{currency}</h3>
                <Metric label="Commissions Badiboss" value={formatMoney(item?.total_commissions ?? 0, currency)} />
                <Metric label="Frais fournisseur" value={formatMoney(item?.total_provider_fees ?? 0, currency)} />
                <Metric label="Net final plateforme" value={formatMoney(item?.total_net_platform ?? 0, currency)} />
              </div>
            );
          })}
        </div>
      )}
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Reference</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Type</th>
              <th className="py-2">Valeur</th>
              <th className="py-2">Devise</th>
              <th className="py-2">Montant collecte</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b last:border-0">
                <td className="py-2">{item.transaction_reference ?? "-"}</td>
                <td className="py-2">{item.app_id}</td>
                <td className="py-2">{item.company_id}</td>
                <td className="py-2">{commissionLabel(item.commission_type)}</td>
                <td className="py-2">{item.commission_value}</td>
                <td className="py-2 font-semibold">{item.currency}</td>
                <td className="py-2">{formatMoney(item.amount_collected, item.currency)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={7}>Aucune commission enregistree.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="mt-2">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

export default CommissionsPage;
