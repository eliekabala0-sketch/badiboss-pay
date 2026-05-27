import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { formatMoney, statusLabel } from "../utils/format";

type Settlement = { id: number; app_id: string; company_id: string; reference: string; amount: number; currency: string; status: string };

function SettlementsPage() {
  const [items, setItems] = useState<Settlement[]>([]);

  useEffect(() => {
    apiClient.get<Settlement[]>("/finance/settlements").then((response) => setItems(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Reversements</h2>
      <p className="text-sm text-slate-600">Suivi des reversements marchands en attente, effectués ou échoués.</p>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Référence</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b last:border-0">
                <td className="py-2">{item.reference}</td>
                <td className="py-2">{item.app_id}</td>
                <td className="py-2">{item.company_id}</td>
                <td className="py-2">{formatMoney(item.amount, item.currency)}</td>
                <td className="py-2">{statusLabel(item.status)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={5}>Aucun reversement.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SettlementsPage;
