import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { formatDate, statusLabel } from "../utils/format";

type BlacklistRow = { ip_address: string; reason?: string; is_active: boolean };
type LoginHistory = { email: string; success: boolean; ip_address?: string; created_at: string };
type AdminProfile = { email: string; full_name: string; role: string; is_active: boolean };

function SecurityPage() {
  const [ip, setIp] = useState("");
  const [reason, setReason] = useState("");
  const [blacklist, setBlacklist] = useState<BlacklistRow[]>([]);
  const [logins, setLogins] = useState<LoginHistory[]>([]);
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "" });
  const [message, setMessage] = useState<string | null>(null);

  function load() {
    apiClient.get<AdminProfile>("/auth/me").then((response) => setProfile(response.data));
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
    setMessage("Adresse IP ajoutée à la liste de blocage.");
    load();
  }

  async function removeIp(ipAddress: string) {
    await apiClient.delete(`/security/blacklist/${ipAddress}`);
    setMessage("Adresse IP désactivée.");
    load();
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await apiClient.post("/auth/change-password", passwords);
    setPasswords({ current_password: "", new_password: "" });
    setMessage("Mot de passe changé.");
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Profil & sécurité</h2>
      <p className="text-sm text-slate-600">Gérez le compte administrateur, le mot de passe, les connexions et le blocage IP.</p>
      {message && <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">{message}</p>}

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="rounded bg-white p-4 shadow-sm">
          <h3 className="font-semibold">Profil administrateur</h3>
          {profile && (
            <div className="mt-3 space-y-1 text-sm">
              <p><span className="font-medium">Nom :</span> {profile.full_name}</p>
              <p><span className="font-medium">Adresse e-mail :</span> {profile.email}</p>
              <p><span className="font-medium">Rôle :</span> {roleLabel(profile.role)}</p>
              <p><span className="font-medium">Statut :</span> {statusLabel(profile.is_active)}</p>
            </div>
          )}
          <p className="mt-3 text-sm text-slate-600">Les identifiants initiaux viennent de ADMIN_EMAIL et ADMIN_PASSWORD dans Railway. Aucun hash n'est présenté comme mot de passe utilisateur.</p>
        </div>

        <form className="rounded bg-white p-4 shadow-sm" onSubmit={changePassword}>
          <h3 className="font-semibold">Changer le mot de passe</h3>
          <div className="mt-3 space-y-3">
            <input className="w-full rounded border px-3 py-2" type="password" placeholder="Mot de passe actuel" value={passwords.current_password} onChange={(event) => setPasswords((prev) => ({ ...prev, current_password: event.target.value }))} required />
            <input className="w-full rounded border px-3 py-2" type="password" placeholder="Nouveau mot de passe" value={passwords.new_password} onChange={(event) => setPasswords((prev) => ({ ...prev, new_password: event.target.value }))} required minLength={8} />
            <button className="rounded bg-blue-600 px-3 py-2 text-sm text-white">Enregistrer le mot de passe</button>
          </div>
        </form>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="rounded bg-white p-4 shadow-sm">
          <h3 className="font-semibold">Blocage IP</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            <input className="rounded border px-3 py-2" placeholder="Adresse IP à bloquer" value={ip} onChange={(event) => setIp(event.target.value)} />
            <input className="rounded border px-3 py-2" placeholder="Raison" value={reason} onChange={(event) => setReason(event.target.value)} />
            <button className="rounded bg-red-600 px-3 py-2 text-sm text-white" onClick={addIp} type="button">Bloquer</button>
          </div>
          <ul className="mt-4 space-y-2 text-sm">
            {blacklist.map((row) => (
              <li key={row.ip_address} className="flex items-center justify-between gap-2 rounded border p-2">
                <span>{row.ip_address} - {row.reason || "Sans raison"} - {statusLabel(row.is_active)}</span>
                <button className="rounded bg-slate-700 px-2 py-1 text-xs text-white" onClick={() => removeIp(row.ip_address)}>Désactiver</button>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded bg-white p-4 shadow-sm">
          <h3 className="font-semibold">Historique des connexions</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {logins.slice(0, 20).map((row, index) => (
              <li key={`${row.email}-${index}`} className="rounded border p-2">
                {row.email} - {row.success ? "Réussie" : "Échouée"} - {row.ip_address ?? "-"} - {formatDate(row.created_at)}
              </li>
            ))}
            {logins.length === 0 && <li className="text-slate-500">Aucune connexion enregistrée.</li>}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default SecurityPage;

function roleLabel(value: string) {
  const labels: Record<string, string> = {
    SUPER_ADMIN: "Super administrateur",
    FINANCE_ADMIN: "Administrateur finance",
    SUPPORT_ADMIN: "Administrateur support",
    VIEWER: "Lecture seule",
  };
  return labels[value] ?? value;
}
