import { useEffect, useState } from "react";

import { apiClient } from "../api/client";

type Settlement = { id: number; app_id: string; company_id: string; reference: string; amount: number; currency: string; status: string };

function SettlementsPage() {
  const [items, setItems] = useState<Settlement[]>([]);

  useEffect(() => {
    apiClient.get<Settlement[]>("/finance/settlements").then((response) => setItems(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Settlements</h2>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Reference</th>
              <th className="py-2">App</th>
              <th className="py-2">Company</th>
              <th className="py-2">Amount</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b last:border-0">
                <td className="py-2">{item.reference}</td>
                <td className="py-2">{item.app_id}</td>
                <td className="py-2">{item.company_id}</td>
                <td className="py-2">{item.amount} {item.currency}</td>
                <td className="py-2">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SettlementsPage;
