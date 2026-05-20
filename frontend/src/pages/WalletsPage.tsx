import { useEffect, useState } from "react";

import { apiClient } from "../api/client";

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
      <h2 className="text-2xl font-semibold">Wallets</h2>
      <div className="mt-3 flex gap-2">
        <input className="rounded border px-2 py-1" placeholder="app_id" value={appId} onChange={(event) => setAppId(event.target.value)} />
        <input className="rounded border px-2 py-1" placeholder="company_id" value={companyId} onChange={(event) => setCompanyId(event.target.value)} />
        <button className="rounded bg-blue-600 px-3 py-1 text-sm text-white" onClick={createWallet}>
          Creer wallet
        </button>
      </div>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Ref</th>
              <th className="py-2">App</th>
              <th className="py-2">Company</th>
              <th className="py-2">Currency</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((wallet) => (
              <tr key={wallet.id} className="border-b last:border-0">
                <td className="py-2">{wallet.wallet_reference}</td>
                <td className="py-2">{wallet.app_id}</td>
                <td className="py-2">{wallet.company_id}</td>
                <td className="py-2">{wallet.currency}</td>
                <td className="py-2">{wallet.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default WalletsPage;
