import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { statusLabel } from "../utils/format";

type Wallet = { id: number; app_id: string; company_id: string; wallet_reference: string; currency: string; status: string };

function WalletsPage() {
  const [items, setItems] = useState<Wallet[]>([]);
  const [appId, setAppId] = useState("");
  const [companyId, setCompanyId] = useState("");

  function load() {
    apiClient.get<Wallet[]>("/finance/wallets").then((response) => setItems(response.data));
  }

  useEffect(() => {
    load();
  }, []);

  async function createWallet() {
    await apiClient.post("/finance/wallets", null, { params: { app_id: appId, company_id: companyId } });
    load();
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Portefeuilles marchands</h2>
      <p className="text-sm text-slate-600">Créez et consultez les portefeuilles liés aux applications et entreprises.</p>
      <div className="mt-3 flex flex-wrap gap-2 rounded bg-white p-3 shadow-sm">
        <input className="rounded border px-3 py-2" placeholder="Application" value={appId} onChange={(event) => setAppId(event.target.value)} />
        <input className="rounded border px-3 py-2" placeholder="Entreprise" value={companyId} onChange={(event) => setCompanyId(event.target.value)} />
        <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white" onClick={createWallet}>
          Créer le portefeuille
        </button>
      </div>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Référence</th>
              <th className="py-2">Application</th>
              <th className="py-2">Entreprise</th>
              <th className="py-2">Devise</th>
              <th className="py-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {items.map((wallet) => (
              <tr key={wallet.id} className="border-b last:border-0">
                <td className="py-2">{wallet.wallet_reference}</td>
                <td className="py-2">{wallet.app_id}</td>
                <td className="py-2">{wallet.company_id}</td>
                <td className="py-2">{wallet.currency}</td>
                <td className="py-2">{statusLabel(wallet.status)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-center text-slate-500" colSpan={5}>Aucun portefeuille.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default WalletsPage;
