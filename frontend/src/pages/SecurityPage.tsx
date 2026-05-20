import { useEffect, useState } from "react";

import { apiClient } from "../api/client";

type BlacklistRow = { ip_address: string; reason?: string; is_active: boolean };
type LoginHistory = { email: string; success: boolean; ip_address?: string; created_at: string };

function SecurityPage() {
  const [ip, setIp] = useState("");
  const [reason, setReason] = useState("");
  const [blacklist, setBlacklist] = useState<BlacklistRow[]>([]);
  const [logins, setLogins] = useState<LoginHistory[]>([]);

  function load() {
    apiClient.get<BlacklistRow[]>("/security/blacklist").then((response) => setBlacklist(response.data));
    apiClient.get<LoginHistory[]>("/security/admin-logins").then((response) => setLogins(response.data));
  }

  useEffect(() => {
    load();
  }, []);

  async function addIp() {
    await apiClient.post("/security/blacklist", null, { params: { ip_address: ip, reason } });
    setIp("");
    setReason("");
    load();
  }

  async function removeIp(ipAddress: string) {
    await apiClient.delete(`/security/blacklist/${ipAddress}`);
    load();
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Securite plateforme</h2>
      <div className="mt-3 flex gap-2">
        <input className="rounded border px-2 py-1" placeholder="IP a blacklister" value={ip} onChange={(event) => setIp(event.target.value)} />
        <input className="rounded border px-2 py-1" placeholder="Raison" value={reason} onChange={(event) => setReason(event.target.value)} />
        <button className="rounded bg-red-600 px-3 py-1 text-sm text-white" onClick={addIp}>
          Ajouter blacklist
        </button>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded bg-white p-3 shadow-sm">
          <h3 className="mb-2 font-semibold">IP blacklist</h3>
          <ul className="space-y-2 text-sm">
            {blacklist.map((row) => (
              <li key={row.ip_address} className="flex items-center justify-between gap-2">
                <span>
                  {row.ip_address} ({row.reason ?? "no reason"}) [{row.is_active ? "active" : "inactive"}]
                </span>
                <button className="rounded bg-slate-700 px-2 py-1 text-xs text-white" onClick={() => removeIp(row.ip_address)}>
                  Desactiver
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded bg-white p-3 shadow-sm">
          <h3 className="mb-2 font-semibold">Historique connexions admin</h3>
          <ul className="space-y-2 text-sm">
            {logins.slice(0, 20).map((row, index) => (
              <li key={`${row.email}-${index}`}>
                {row.email} - {row.success ? "success" : "failed"} - {row.ip_address ?? "-"}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default SecurityPage;
