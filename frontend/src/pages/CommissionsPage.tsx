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

function CommissionsPage() {
  const [items, setItems] = useState<Commission[]>([]);
  const [revenue, setRevenue] = useState<{ total_commissions: number; total_provider_fees: number; total_net_platform: number } | null>(null);

  useEffect(() => {
    apiClient.get<Commission[]>("/finance/commissions").then((response) => setItems(response.data));
    apiClient.get("/finance/platform-revenue").then((response) => setRevenue(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Commissions / Revenus plateforme</h2>
      <p className="text-sm text-slate-600">Suivi des commissions Badiboss, frais fournisseur et revenu net plateforme.</p>
      {revenue && (
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
          <Metric label="Commissions Badiboss" value={revenue.total_commissions} />
          <Metric label="Frais provider" value={revenue.total_provider_fees} />
          <Metric label="Net final plateforme" value={revenue.total_net_platform} />
        </div>
      )}
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Référence</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Type</th>
              <th className="py-2">Valeur</th>
              <th className="py-2">Montant collecté</th>
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
                <td className="py-2">{formatMoney(item.amount_collected, item.currency)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={6}>Aucune commission enregistrée.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-white p-3 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{formatMoney(value)}</p>
    </div>
  );
}

export default CommissionsPage;
