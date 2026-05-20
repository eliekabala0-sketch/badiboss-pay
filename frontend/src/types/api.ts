export type DashboardStats = {
  total_apps: number;
  total_transactions: number;
  total_commissions: number;
  revenue_today: number;
  revenue_month: number;
  active_subscriptions: number;
  wallets_merchants: number;
  settlements_pending: number;
  withdrawals: number;
  api_webhook_errors: number;
  realtime_activity: number;
};

export type ConnectedApp = {
  id: number;
  app_id: string;
  company_id: string;
  api_key: string;
  secret_key: string;
  name: string;
  app_type: string;
  callback_url: string;
  status: string;
  api_key_active: boolean;
  secret_key_active: boolean;
  commission_type: string;
  commission_value: number;
  created_at: string;
};

export type Transaction = {
  id: number;
  reference: string;
  app_id: string;
  user_id: string;
  payer_phone?: string;
  company_id: string;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_reference?: string;
  fees: number;
  commission: number;
  net_amount: number;
  payment_method?: string;
  created_at: string;
};

export type PaginatedTransactions = {
  items: Transaction[];
  page: number;
  page_size: number;
  total: number;
};

export type Subscription = {
  id: number;
  company_id: string;
  app_id: string;
  plan: string;
  amount: number;
  start_date: string;
  end_date: string;
  active: boolean;
  expired: boolean;
  created_at: string;
};
