import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../api/client";
import DrcPhoneInput from "../components/DrcPhoneInput";
import { formatDate, formatMoney, statusLabel } from "../utils/format";

type Balance = { id: number; app_id: string; company_id: string; available_balance: number; pending_balance: number; currency: string };
type Withdrawal = {
  id: number; app_id: string; company_id: string; reference: string; amount: number; currency: string; status: string;
  destination_type?: string; mobile_operator?: string; mobile_phone?: string; bank_name?: string; account_name?: string;
  account_number?: string; provider_reference?: string; failure_reason?: string; created_at: string;
};

const initialForm = {
  balanceId: "", amount: "", destination_type: "mobile_money", mobile_operator: "OM", mobile_phone: "",
  bank_name: "", account_name: "", account_number: "", bank_swift: "",
};

function WithdrawalsPage() {
  const [items, setItems] = useState<Withdrawal[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selectedBalance = useMemo(() => balances.find((item) => String(item.id) === form.balanceId), [balances, form.balanceId]);

  function load() {
    Promise.all([
      apiClient.get<Withdrawal[]>("/finance/withdrawals"),
      apiClient.get<Balance[]>("/finance/balances"),
    ]).then(([withdrawals, merchantBalances]) => {
      setItems(withdrawals.data);
      setBalances(merchantBalances.data);
    }).catch(() => setError("Impossible de charger les retraits."));
  }

  useEffect(() => { load(); }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedBalance) return;
    setError(null);
    setMessage(null);
    try {
      const response = await apiClient.post<Withdrawal>("/finance/withdrawals", {
        app_id: selectedBalance.app_id,
        company_id: selectedBalance.company_id,
        currency: selectedBalance.currency,
        amount: Number(form.amount),
        destination_type: form.destination_type,
        mobile_operator: form.destination_type === "mobile_money" ? form.mobile_operator : null,
        mobile_phone: form.destination_type === "mobile_money" ? `243${form.mobile_phone}` : null,
        bank_name: form.destination_type === "bank_account" ? form.bank_name : null,
        account_name: form.destination_type === "bank_account" ? form.account_name : null,
        account_number: form.destination_type === "bank_account" ? form.account_number : null,
        bank_swift: form.destination_type === "bank_account" ? form.bank_swift : null,
      });
      setForm(initialForm);
      if (response.data.status === "processing") {
        setMessage("Reversement Mobile Money transmis à SerdiPay. Le montant reste réservé jusqu'à la confirmation finale.");
      } else if (response.data.status === "failed") {
        setError(response.data.failure_reason ?? "SerdiPay a refusé le reversement. Le montant a été remis dans le solde disponible.");
      } else {
        setMessage("Demande bancaire enregistrée et montant réservé en attente de la référence bancaire.");
      }
      load();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail ?? "Impossible de créer la demande de retrait.");
    }
  }

  function destination(item: Withdrawal) {
    if (item.destination_type === "mobile_money") return `${item.mobile_operator ?? "Mobile Money"} +${item.mobile_phone ?? ""}`;
    if (item.destination_type === "bank_account") return `${item.bank_name ?? "Banque"} - ${item.account_name ?? ""} - ${item.account_number ?? ""}`;
    return "Non renseignée";
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Retraits marchands</h2>
      <p className="text-sm text-slate-600">Demandez un reversement vers Mobile Money ou un compte bancaire. Seuls les paiements confirmés par callback alimentent le solde disponible.</p>
      {message && <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">{message}</p>}
      {error && <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <form className="mt-4 grid gap-3 rounded bg-white p-4 shadow-sm md:grid-cols-2" onSubmit={submit}>
        <h3 className="font-semibold md:col-span-2">Nouvelle demande</h3>
        <select className="rounded border px-3 py-2" value={form.balanceId} onChange={(event) => setForm((prev) => ({ ...prev, balanceId: event.target.value }))} required>
          <option value="">Choisir un solde</option>
          {balances.map((balance) => <option key={balance.id} value={balance.id}>{balance.company_id} / {balance.app_id} - {formatMoney(balance.available_balance, balance.currency)} disponible</option>)}
        </select>
        <input className="rounded border px-3 py-2" type="number" min="0.01" max={selectedBalance?.available_balance} step="0.01" placeholder="Montant" value={form.amount} onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))} required />
        <select className="rounded border px-3 py-2" value={form.destination_type} onChange={(event) => setForm((prev) => ({ ...prev, destination_type: event.target.value }))}>
          <option value="mobile_money">Mobile Money</option>
          <option value="bank_account">Compte bancaire</option>
        </select>
        {form.destination_type === "mobile_money" ? <>
          <select className="rounded border px-3 py-2" value={form.mobile_operator} onChange={(event) => setForm((prev) => ({ ...prev, mobile_operator: event.target.value }))}>
            <option value="OM">Orange Money</option><option value="AM">Airtel Money</option><option value="MP">M-Pesa</option><option value="AF">Afrimoney</option>
          </select>
          <DrcPhoneInput className="md:col-span-2" value={form.mobile_phone} onChange={(mobile_phone) => setForm((prev) => ({ ...prev, mobile_phone }))} required />
        </> : <>
          <input className="rounded border px-3 py-2" placeholder="Nom de la banque" value={form.bank_name} onChange={(event) => setForm((prev) => ({ ...prev, bank_name: event.target.value }))} required />
          <input className="rounded border px-3 py-2" placeholder="Titulaire du compte" value={form.account_name} onChange={(event) => setForm((prev) => ({ ...prev, account_name: event.target.value }))} required />
          <input className="rounded border px-3 py-2" placeholder="Numéro de compte / IBAN" value={form.account_number} onChange={(event) => setForm((prev) => ({ ...prev, account_number: event.target.value }))} required />
          <input className="rounded border px-3 py-2" placeholder="SWIFT/BIC (optionnel)" value={form.bank_swift} onChange={(event) => setForm((prev) => ({ ...prev, bank_swift: event.target.value }))} />
        </>}
        <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white md:col-span-2" type="submit">Demander le reversement</button>
      </form>

      <div className="mt-4 overflow-x-auto rounded bg-white p-3 shadow-sm">
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left"><th className="py-2">Référence</th><th>Entreprise</th><th>Destination</th><th>Montant</th><th>Statut</th><th>Référence externe</th><th>Date</th></tr></thead>
          <tbody>
            {items.map((item) => <tr key={item.id} className="border-b last:border-0"><td className="py-2">{item.reference}</td><td>{item.company_id}</td><td>{destination(item)}</td><td>{formatMoney(item.amount, item.currency)}</td><td>{statusLabel(item.status)}</td><td>{item.provider_reference ?? "-"}</td><td>{formatDate(item.created_at)}</td></tr>)}
            {items.length === 0 && <tr><td className="py-6 text-center text-slate-500" colSpan={7}>Aucun retrait.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default WithdrawalsPage;
