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
  app_slug: string;
  company_id: string;
  api_key: string;
  secret_key: string;
  webhook_secret: string;
  name: string;
  app_type: string;
  callback_url: string;
  status: string;
  api_key_active: boolean;
  secret_key_active: boolean;
  commission_type: string;
  commission_value: number;
  created_at: string;
  payment_url: string;
  status_url: string;
  callback_badiboss_pay: string;
  transactions_count: number;
  total_usd: number;
  total_cdf: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  api_secret_once?: string | null;
  webhook_secret_once?: string | null;
};

export type Transaction = {
  id: number;
  reference: string;
  app_id: string;
  payment_link_id?: number | null;
  user_id: string;
  customer_name?: string;
  payer_phone?: string;
  company_id: string;
  amount: number | null;
  currency: string;
  status: string;
  provider: string;
  provider_reference?: string;
  provider_session_id?: string;
  raw_payload?: string;
  callback_url?: string;
  metadata_json?: string;
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
  updated_at: string;
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

export type PaymentLink = {
  id: number;
  slug: string;
  title: string;
  description: string;
  brand_name: string;
  brand_logo_url: string;
  custom_domain: string;
  amount: number;
  currency: string;
  status: string;
  is_active: boolean;
  expires_at?: string | null;
  max_uses?: number | null;
  success_redirect_url: string;
  failure_redirect_url: string;
  created_at: string;
  public_url: string;
  payments_count: number;
  total_usd: number;
  total_cdf: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
};

export type AppApiJournalItem = {
  date: string;
  route: string;
  status_code?: number | null;
  reference: string;
  transaction_id: string;
  phone_masked?: string | null;
  amount: number;
  currency: string;
  telecom?: string | null;
  result: string;
};

export type WebhookLog = {
  id: number;
  direction: string;
  provider: string;
  event_type?: string | null;
  reference?: string | null;
  app_id?: string | null;
  company_id?: string | null;
  status_code?: number | null;
  payload?: string | null;
  response_body?: string | null;
  error_message?: string | null;
  created_at: string;
};
