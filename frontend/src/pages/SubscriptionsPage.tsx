import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { Subscription } from "../types/api";

function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<Subscription[]>("/subscriptions")
      .then((response) => setSubscriptions(response.data))
      .catch(() => setError("Impossible de charger les abonnements."));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Abonnements SaaS</h2>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Company</th>
              <th className="py-2">App</th>
              <th className="py-2">Plan</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Actif</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.map((sub) => (
              <tr key={sub.id} className="border-b last:border-0">
                <td className="py-2">{sub.company_id}</td>
                <td className="py-2">{sub.app_id}</td>
                <td className="py-2">{sub.plan}</td>
                <td className="py-2">{sub.amount}</td>
                <td className="py-2">{sub.active ? "Oui" : "Non"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SubscriptionsPage;
