import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { formatMoney, statusLabel } from "../utils/format";

type Settlement = { id: number; app_id: string; company_id: string; reference: string; amount: number; currency: string; status: string; withdrawal_reference?: string; destination_type?: string; provider_reference?: string };

function SettlementsPage() {
  const [items, setItems] = useState<Settlement[]>([]);

  useEffect(() => {
    apiClient.get<Settlement[]>("/finance/settlements").then((response) => setItems(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Reversements</h2>
      <p className="text-sm text-slate-600">Journal des reversements confirmés ou échoués. Une référence externe est obligatoire avant de considérer les fonds comme versés.</p>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Référence</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Demande</th>
              <th className="py-2">Destination</th>
              <th className="py-2">Référence externe</th>
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
                <td className="py-2">{item.withdrawal_reference ?? "-"}</td>
                <td className="py-2">{item.destination_type === "mobile_money" ? "Mobile Money" : item.destination_type === "bank_account" ? "Banque" : "-"}</td>
                <td className="py-2">{item.provider_reference ?? "-"}</td>
                <td className="py-2">{statusLabel(item.status)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={8}>Aucun reversement.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SettlementsPage;
