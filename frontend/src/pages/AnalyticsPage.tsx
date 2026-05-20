import { useEffect, useState } from "react";

import { apiClient } from "../api/client";

type AnalyticsPayload = {
  transactions_by_country: Array<{ country: string; transactions: number }>;
  transactions_by_city: Array<{ city: string; transactions: number }>;
  users_by_application: Array<{ app_id: string; transactions: number }>;
  device_types: Array<{ device_type: string; transactions: number }>;
  platforms: Array<{ platform: string; transactions: number }>;
  recent_activity: Array<{
    ip: string;
    country: string;
    city: string;
    app_id: string;
    device: string;
    os: string;
    browser: string;
    phone_brand: string;
    source_application: string;
  }>;
};

function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsPayload | null>(null);

  useEffect(() => {
    apiClient.get<AnalyticsPayload>("/analytics").then((response) => setData(response.data));
  }, []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Geolocalisation / IP Analytics</h2>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <SimpleList title="Utilisateurs par pays" items={(data?.transactions_by_country ?? []).map((entry) => `${entry.country}: ${entry.transactions}`)} />
        <SimpleList title="Utilisateurs par ville" items={(data?.transactions_by_city ?? []).map((entry) => `${entry.city}: ${entry.transactions}`)} />
        <SimpleList title="Utilisateurs par application" items={(data?.users_by_application ?? []).map((entry) => `${entry.app_id}: ${entry.transactions}`)} />
        <SimpleList title="Types appareils" items={(data?.device_types ?? []).map((entry) => `${entry.device_type}: ${entry.transactions}`)} />
        <SimpleList title="Android / iPhone / Desktop" items={(data?.platforms ?? []).map((entry) => `${entry.platform}: ${entry.transactions}`)} />
      </div>
      <div className="mt-4 rounded bg-white p-3 shadow-sm">
        <h3 className="mb-2 font-semibold">Activite recente (IP / device / navigateur)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2">IP</th>
                <th className="py-2">Pays</th>
                <th className="py-2">Ville</th>
                <th className="py-2">App</th>
                <th className="py-2">Device</th>
                <th className="py-2">OS</th>
                <th className="py-2">Browser</th>
                <th className="py-2">Marque</th>
                <th className="py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {(data?.recent_activity ?? []).map((entry, index) => (
                <tr key={`${entry.ip}-${index}`} className="border-b last:border-0">
                  <td className="py-2">{entry.ip ?? "-"}</td>
                  <td className="py-2">{entry.country ?? "-"}</td>
                  <td className="py-2">{entry.city ?? "-"}</td>
                  <td className="py-2">{entry.app_id ?? "-"}</td>
                  <td className="py-2">{entry.device ?? "-"}</td>
                  <td className="py-2">{entry.os ?? "-"}</td>
                  <td className="py-2">{entry.browser ?? "-"}</td>
                  <td className="py-2">{entry.phone_brand ?? "-"}</td>
                  <td className="py-2">{entry.source_application ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function SimpleList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded bg-white p-3 shadow-sm">
      <h3 className="mb-2 font-semibold">{title}</h3>
      <ul className="space-y-1 text-sm text-slate-700">
        {items.slice(0, 10).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default AnalyticsPage;
