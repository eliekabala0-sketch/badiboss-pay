export type DashboardStats = {
  total_apps: number;
  total_transactions: number;
  total_collected: number;
  total_provider_fees: number;
  total_commissions: number;
  merchant_net: number;
  merchant_available_balance: number;
  revenue_today: number;
  revenue_month: number;
  active_subscriptions: number;
  wallets_merchants: number;
  settlements_pending: number;
  settlements_done: number;
  settlement_errors: number;
  withdrawals: number;
  withdrawals_pending: number;
  api_webhook_errors: number;
  realtime_activity: number;
  by_currency: Record<string, CurrencyStats>;
  status_counts: {
    success: number;
    failed: number;
    pending: number;
  };
};

export type CurrencyStats = {
  total_collected: number;
  total_provider_fees: number;
  total_commissions: number;
  merchant_net: number;
  merchant_available_balance: number;
  revenue_today: number;
  revenue_month: number;
  total_transactions: number;
  success: number;
  failed: number;
  pending: number;
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
  provider_session_id?: string;
  raw_payload?: string;
  fees: number;
  commission: number;
  net_amount: number;
  payment_method?: string;
  public_ip?: string;
  country?: string;
  city?: string;
  device?: string;
  browser?: string;
  operating_system?: string;
  device_type?: string;
  source_application?: string;
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

export type CompanySummary = {
  company_id: string;
  applications: number;
  transactions: number;
  subscriptions: number;
};
