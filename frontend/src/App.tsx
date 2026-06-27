import { Navigate, Route, Routes } from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import AppsPage from "./pages/AppsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import CommissionsPage from "./pages/CommissionsPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PaymentLinksPage from "./pages/PaymentLinksPage";
import SecurityPage from "./pages/SecurityPage";
import SettlementsPage from "./pages/SettlementsPage";
import SubscriptionsPage from "./pages/SubscriptionsPage";
import TransactionsPage from "./pages/TransactionsPage";
import WalletsPage from "./pages/WalletsPage";
import WebhooksPage from "./pages/WebhooksPage";
import WithdrawalsPage from "./pages/WithdrawalsPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/apps" element={<AppsPage />} />
        <Route path="/payment-links" element={<PaymentLinksPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/wallets" element={<WalletsPage />} />
        <Route path="/settlements" element={<SettlementsPage />} />
        <Route path="/withdrawals" element={<WithdrawalsPage />} />
        <Route path="/commissions" element={<CommissionsPage />} />
        <Route path="/webhooks" element={<WebhooksPage />} />
        <Route path="/security" element={<SecurityPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
