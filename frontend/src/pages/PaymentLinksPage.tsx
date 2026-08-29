import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { PaymentLink, Transaction } from "../types/api";
import { formatDate, formatMoney, statusLabel } from "../utils/format";

const emptyLink = {
  title: "",
  amount: 5,
  currency: "USD",
  description: "",
  validity: "7d",
  custom_expires_at: "",
  usage_limit_type: "unlimited",
  max_uses: 1,
  success_redirect_url: "",
  failure_redirect_url: "",
  slug: "",
  brand_name: "Badiboss",
  brand_logo_url: "",
  custom_domain: "",
};

type EditLinkForm = {
  id: number;
  public_url: string;
  title: string;
  amount: string;
  currency: string;
  description: string;
  brand_name: string;
  brand_logo_url: string;
  expires_at: string;
  max_uses: string;
  success_redirect_url: string;
  failure_redirect_url: string;
};

function localDateTimeValue(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function PaymentLinksPage() {
  const [links, setLinks] = useState<PaymentLink[]>([]);
  const [newLink, setNewLink] = useState(emptyLink);
  const [createdLink, setCreatedLink] = useState<PaymentLink | null>(null);
  const [selectedPayments, setSelectedPayments] = useState<Transaction[] | null>(null);
  const [editLink, setEditLink] = useState<EditLinkForm | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function loadLinks() {
    apiClient
      .get<PaymentLink[]>("/payment-links")
      .then((response) => {
        setLinks(response.data);
        setError(null);
      })
      .catch(() => setError("Impossible de charger les liens de paiement."));
  }

  useEffect(() => {
    loadLinks();
  }, []);

  async function createLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      ...newLink,
      custom_expires_at: newLink.validity === "custom" && newLink.custom_expires_at ? newLink.custom_expires_at : null,
      max_uses: newLink.usage_limit_type === "limited" ? newLink.max_uses : null,
    };
    const response = await apiClient.post<PaymentLink>("/payment-links", payload);
    setCreatedLink(response.data);
    setNewLink(emptyLink);
    setSuccess("Lien de paiement genere.");
    loadLinks();
  }

  async function setActive(link: PaymentLink, active: boolean) {
    if (!active && !window.confirm("Ce lien ne pourra plus recevoir de paiements, mais son historique restera disponible.")) return;
    await apiClient.patch(`/payment-links/${link.id}/status`, null, { params: { active } });
    setSuccess(active ? "Lien reactive." : "Lien desactive.");
    loadLinks();
  }

  async function loadPayments(link: PaymentLink) {
    const response = await apiClient.get<Transaction[]>(`/payment-links/${link.id}/payments`);
    setSelectedPayments(response.data);
  }

  function startEditing(link: PaymentLink) {
    setEditLink({
      id: link.id,
      public_url: link.public_url,
      title: link.title,
      amount: String(link.amount),
      currency: link.currency,
      description: link.description ?? "",
      brand_name: link.brand_name || "Badiboss",
      brand_logo_url: link.brand_logo_url ?? "",
      expires_at: localDateTimeValue(link.expires_at),
      max_uses: link.max_uses == null ? "" : String(link.max_uses),
      success_redirect_url: link.success_redirect_url ?? "",
      failure_redirect_url: link.failure_redirect_url ?? "",
    });
    setError(null);
    setSuccess(null);
  }

  async function saveLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editLink) return;
    setError(null);
    try {
      const response = await apiClient.patch<PaymentLink>(`/payment-links/${editLink.id}`, {
        title: editLink.title,
        amount: Number(editLink.amount),
        currency: editLink.currency,
        description: editLink.description,
        brand_name: editLink.brand_name,
        brand_logo_url: editLink.brand_logo_url,
        expires_at: editLink.expires_at ? new Date(editLink.expires_at).toISOString() : null,
        max_uses: editLink.max_uses ? Number(editLink.max_uses) : null,
        success_redirect_url: editLink.success_redirect_url,
        failure_redirect_url: editLink.failure_redirect_url,
      });
      setCreatedLink(response.data);
      setEditLink(null);
      setSuccess("Modifications enregistrees. Le lien public reste identique et ne doit pas etre repartage.");
      loadLinks();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail ?? "La modification du lien a echoue.");
    }
  }

  async function personalizeLink(link: PaymentLink) {
    const slug = window.prompt("Personnalisez la fin du lien (lettres minuscules, chiffres et tirets).", link.slug);
    if (slug === null) return;
    const brand_name = window.prompt("Nom a afficher sur la page de paiement (Badiboss sera utilise si le champ reste vide).", link.brand_name || "Badiboss");
    if (brand_name === null) return;
    const brand_logo_url = window.prompt("URL HTTPS du logo (facultatif).", link.brand_logo_url ?? "");
    if (brand_logo_url === null) return;
    const custom_domain = window.prompt("Domaine personnalise deja relie a Badiboss Pay (facultatif, ex. payer.ma-marque.com).", link.custom_domain ?? "");
    if (custom_domain === null) return;
    try {
      const response = await apiClient.patch<PaymentLink>(`/payment-links/${link.id}`, { slug, brand_name, brand_logo_url, custom_domain });
      setCreatedLink(response.data);
      setSuccess("Lien et page de paiement personnalises.");
      loadLinks();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail ?? "La personnalisation du lien a echoue.");
    }
  }

  function copy(value: string, label: string) {
    navigator.clipboard.writeText(value);
    setSuccess(`${label} copie.`);
  }

  return (
    <section>
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Liens de paiement</h2>
          <p className="text-sm text-slate-600">Creez des liens partageables WhatsApp, SMS ou email sans application cliente.</p>
        </div>
      </div>

      {error && <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {success && <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">{success}</p>}

      <form className="mt-4 rounded bg-white p-4 shadow-sm" onSubmit={createLink}>
        <h3 className="mb-3 font-semibold">Generer un lien de paiement</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <input className="rounded border px-3 py-2" placeholder="Motif du paiement" value={newLink.title} onChange={(event) => setNewLink((prev) => ({ ...prev, title: event.target.value }))} required />
          <input className="rounded border px-3 py-2" type="number" min="0" step="0.01" placeholder="Montant" value={newLink.amount} onChange={(event) => setNewLink((prev) => ({ ...prev, amount: Number(event.target.value) }))} required />
          <select className="rounded border px-3 py-2" value={newLink.currency} onChange={(event) => setNewLink((prev) => ({ ...prev, currency: event.target.value }))}>
            <option value="USD">USD</option>
            <option value="CDF">CDF</option>
          </select>
          <input className="rounded border px-3 py-2 md:col-span-3" placeholder="Description optionnelle" value={newLink.description} onChange={(event) => setNewLink((prev) => ({ ...prev, description: event.target.value }))} />
          <input className="rounded border px-3 py-2" placeholder="Fin du lien optionnelle (ex. facture-2026)" value={newLink.slug} onChange={(event) => setNewLink((prev) => ({ ...prev, slug: event.target.value }))} />
          <input className="rounded border px-3 py-2" placeholder="Nom affiche (Badiboss par defaut)" value={newLink.brand_name} onChange={(event) => setNewLink((prev) => ({ ...prev, brand_name: event.target.value }))} />
          <input className="rounded border px-3 py-2" type="url" placeholder="URL HTTPS du logo (facultatif)" value={newLink.brand_logo_url} onChange={(event) => setNewLink((prev) => ({ ...prev, brand_logo_url: event.target.value }))} />
          <input className="rounded border px-3 py-2 md:col-span-3" placeholder="Domaine personnalise deja configure (ex. payer.ma-marque.com)" value={newLink.custom_domain} onChange={(event) => setNewLink((prev) => ({ ...prev, custom_domain: event.target.value }))} />
          <select className="rounded border px-3 py-2" value={newLink.validity} onChange={(event) => setNewLink((prev) => ({ ...prev, validity: event.target.value }))}>
            <option value="24h">24h</option>
            <option value="7d">7 jours</option>
            <option value="30d">30 jours</option>
            <option value="custom">Date personnalisee</option>
            <option value="none">Sans expiration</option>
          </select>
          {newLink.validity === "custom" && <input className="rounded border px-3 py-2" type="datetime-local" value={newLink.custom_expires_at} onChange={(event) => setNewLink((prev) => ({ ...prev, custom_expires_at: event.target.value }))} />}
          <select className="rounded border px-3 py-2" value={newLink.usage_limit_type} onChange={(event) => setNewLink((prev) => ({ ...prev, usage_limit_type: event.target.value }))}>
            <option value="unlimited">Illimite</option>
            <option value="single">Usage unique</option>
            <option value="limited">Nombre limite</option>
          </select>
          {newLink.usage_limit_type === "limited" && <input className="rounded border px-3 py-2" type="number" min="1" value={newLink.max_uses} onChange={(event) => setNewLink((prev) => ({ ...prev, max_uses: Number(event.target.value) }))} />}
          <input className="rounded border px-3 py-2" placeholder="Redirection succes optionnelle" value={newLink.success_redirect_url} onChange={(event) => setNewLink((prev) => ({ ...prev, success_redirect_url: event.target.value }))} />
          <input className="rounded border px-3 py-2" placeholder="Redirection echec optionnelle" value={newLink.failure_redirect_url} onChange={(event) => setNewLink((prev) => ({ ...prev, failure_redirect_url: event.target.value }))} />
          <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white" type="submit">Generer un lien de paiement</button>
        </div>
      </form>

      {createdLink && (
        <div className="mt-4 rounded border border-blue-200 bg-blue-50 p-4 text-sm">
          <h3 className="font-semibold">Lien genere</h3>
          <p className="mt-2 break-all">{createdLink.public_url}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="rounded bg-slate-800 px-3 py-2 text-xs text-white" onClick={() => copy(createdLink.public_url, "Lien public")} type="button">Copier</button>
            <a className="rounded bg-green-600 px-3 py-2 text-xs text-white" href={`https://wa.me/?text=${encodeURIComponent(createdLink.public_url)}`} target="_blank" rel="noreferrer">WhatsApp</a>
            <a className="rounded bg-slate-600 px-3 py-2 text-xs text-white" href={`sms:?body=${encodeURIComponent(createdLink.public_url)}`}>SMS</a>
            <a className="rounded bg-indigo-600 px-3 py-2 text-xs text-white" href={`mailto:?subject=Paiement&body=${encodeURIComponent(createdLink.public_url)}`}>Email</a>
            <a className="rounded bg-purple-600 px-3 py-2 text-xs text-white" href={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(createdLink.public_url)}`} target="_blank" rel="noreferrer">QR Code</a>
          </div>
        </div>
      )}

      {editLink && (
        <form className="mt-4 rounded border border-indigo-200 bg-white p-4 shadow-sm" onSubmit={saveLink}>
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="font-semibold">Modifier les donnees du lien</h3>
              <p className="text-xs text-slate-600">L'adresse ci-dessous ne sera pas modifiee. Les personnes qui la possedent verront directement les nouvelles donnees.</p>
              <p className="mt-1 break-all text-xs font-medium text-indigo-700">{editLink.public_url}</p>
            </div>
            <button className="rounded border px-3 py-1 text-sm" onClick={() => setEditLink(null)} type="button">Annuler</button>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <input className="rounded border px-3 py-2" placeholder="Motif du paiement" value={editLink.title} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, title: event.target.value }))} required />
            <input className="rounded border px-3 py-2" type="number" min="0.01" step="0.01" placeholder="Montant" value={editLink.amount} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, amount: event.target.value }))} required />
            <select className="rounded border px-3 py-2" value={editLink.currency} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, currency: event.target.value }))}><option value="USD">USD</option><option value="CDF">CDF</option></select>
            <textarea className="rounded border px-3 py-2 md:col-span-3" placeholder="Description" value={editLink.description} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, description: event.target.value }))} />
            <input className="rounded border px-3 py-2" placeholder="Nom affiche (Badiboss par defaut)" value={editLink.brand_name} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, brand_name: event.target.value }))} />
            <input className="rounded border px-3 py-2 md:col-span-2" type="url" placeholder="URL HTTPS du logo" value={editLink.brand_logo_url} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, brand_logo_url: event.target.value }))} />
            <label className="text-xs text-slate-600">Expiration (vide = sans expiration)<input className="mt-1 w-full rounded border px-3 py-2 text-sm" type="datetime-local" value={editLink.expires_at} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, expires_at: event.target.value }))} /></label>
            <label className="text-xs text-slate-600">Nombre maximum (vide = illimite)<input className="mt-1 w-full rounded border px-3 py-2 text-sm" type="number" min="1" value={editLink.max_uses} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, max_uses: event.target.value }))} /></label>
            <div />
            <input className="rounded border px-3 py-2" type="url" placeholder="Redirection succes" value={editLink.success_redirect_url} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, success_redirect_url: event.target.value }))} />
            <input className="rounded border px-3 py-2" type="url" placeholder="Redirection echec" value={editLink.failure_redirect_url} onChange={(event) => setEditLink((prev) => prev && ({ ...prev, failure_redirect_url: event.target.value }))} />
            <button className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white" type="submit">Enregistrer sans changer le lien</button>
          </div>
        </form>
      )}

      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Motif</th>
              <th className="py-2">Montant</th>
              <th className="py-2">Statut</th>
              <th className="py-2">Paiements</th>
              <th className="py-2">Totaux</th>
              <th className="py-2">Expiration</th>
              <th className="py-2">Lien public</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {links.map((link) => (
              <tr key={link.id} className="border-b align-top last:border-0">
                <td className="py-3"><p className="font-medium">{link.title}</p><p className="text-xs text-slate-500">{link.description}</p></td>
                <td className="py-3">{formatMoney(link.amount, link.currency)}</td>
                <td className="py-3">{statusLabel(link.status)}</td>
                <td className="py-3 text-xs">{link.payments_count} total<br />{link.success_count} succes / {link.failed_count} echecs / {link.pending_count} pending</td>
                <td className="py-3 text-xs">USD: {formatMoney(link.total_usd, "USD")}<br />CDF: {formatMoney(link.total_cdf, "CDF")}</td>
                <td className="py-3">{link.expires_at ? formatDate(link.expires_at) : "Sans expiration"}</td>
                <td className="py-3 break-all text-xs">{link.public_url}</td>
                <td className="py-3">
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded bg-slate-700 px-2 py-1 text-xs text-white" onClick={() => copy(link.public_url, "Lien public")} type="button">Copier</button>
                    <button className="rounded bg-indigo-600 px-2 py-1 text-xs text-white" onClick={() => startEditing(link)} type="button">Modifier les donnees</button>
                    <button className="rounded bg-purple-600 px-2 py-1 text-xs text-white" onClick={() => personalizeLink(link)} type="button">Modifier l'adresse</button>
                    {link.is_active ? (
                      <button className="rounded bg-amber-600 px-2 py-1 text-xs text-white" onClick={() => setActive(link, false)} type="button">Desactiver</button>
                    ) : (
                      <button className="rounded bg-green-600 px-2 py-1 text-xs text-white" onClick={() => setActive(link, true)} type="button">Reactiver</button>
                    )}
                    <button className="rounded bg-blue-600 px-2 py-1 text-xs text-white" onClick={() => loadPayments(link)} type="button">Voir paiements</button>
                  </div>
                </td>
              </tr>
            ))}
            {links.length === 0 && <tr><td className="py-6 text-center text-slate-500" colSpan={8}>Aucun lien de paiement.</td></tr>}
          </tbody>
        </table>
      </div>

      {selectedPayments && (
        <div className="mt-4 rounded bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Paiements du lien</h3>
            <button className="rounded border px-3 py-1 text-sm" onClick={() => setSelectedPayments(null)} type="button">Fermer</button>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead><tr className="border-b"><th className="py-2">Reference</th><th>Payeur</th><th>Telephone</th><th>Montant</th><th>Telecom</th><th>Statut</th><th>Date</th></tr></thead>
              <tbody>
                {selectedPayments.map((tx) => (
                  <tr key={tx.id} className="border-b last:border-0">
                    <td className="py-2">{tx.reference}</td><td>{tx.customer_name ?? "-"}</td><td>{tx.payer_phone ?? "-"}</td><td>{formatMoney(tx.amount, tx.currency)}</td><td>{tx.payment_method ?? "-"}</td><td>{statusLabel(tx.status)}</td><td>{formatDate(tx.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

export default PaymentLinksPage;
