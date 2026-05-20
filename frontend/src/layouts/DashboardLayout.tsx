import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";

import { clearToken } from "../auth";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/analytics", label: "Geo Analytics" },
  { to: "/apps", label: "Applications" },
  { to: "/transactions", label: "Transactions" },
  { to: "/subscriptions", label: "Abonnements" },
  { to: "/wallets", label: "Wallets" },
  { to: "/settlements", label: "Settlements" },
  { to: "/withdrawals", label: "Withdrawals" },
  { to: "/commissions", label: "Commissions" },
  { to: "/webhooks", label: "Webhooks" },
  { to: "/security", label: "Securite" },
];

function DashboardLayout() {
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState(document.documentElement.classList.contains("dark"));

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  function toggleTheme() {
    const next = !darkMode;
    setDarkMode(next);
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="w-full bg-slate-900 p-4 text-white md:w-72">
        <h1 className="mb-8 text-xl font-bold">Badiboss Pay</h1>
        <nav className="space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${isActive ? "bg-blue-600" : "hover:bg-slate-700"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          onClick={toggleTheme}
          className="mt-4 w-full rounded bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500"
        >
          {darkMode ? "Light mode" : "Dark mode"}
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="mt-8 w-full rounded bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600"
        >
          Deconnexion
        </button>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;
