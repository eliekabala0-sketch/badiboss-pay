import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { clearToken } from "../auth";

const navItems = [
  { to: "/", label: "Tableau de bord" },
  { to: "/apps", label: "Applications" },
  { to: "/transactions", label: "Ventes / Paiements" },
  { to: "/subscriptions", label: "Abonnements" },
  { to: "/analytics", label: "Utilisateurs & analytics" },
  { to: "/wallets", label: "Portefeuilles" },
  { to: "/settlements", label: "Reversements" },
  { to: "/withdrawals", label: "Retraits" },
  { to: "/commissions", label: "Commissions" },
  { to: "/webhooks", label: "Webhooks" },
  { to: "/security", label: "Profil & sécurité" },
];

function DashboardLayout() {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-950 md:flex-row">
      <aside className="w-full bg-slate-950 p-4 text-white md:min-h-screen md:w-72">
        <h1 className="mb-2 text-xl font-bold">Badiboss Pay</h1>
        <p className="mb-6 text-xs text-slate-300">Administration production</p>
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
          onClick={handleLogout}
          className="mt-8 w-full rounded bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600"
        >
          Déconnexion
        </button>
      </aside>
      <main className="flex-1 overflow-x-hidden p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;
