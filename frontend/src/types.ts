/** Типы ответов API (согласованы с backend Pydantic). */

export type AdminSetting = {
  id: number;
  service_title: string;
  budget_range: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type BehaviorMetricsCreate = {
  time_on_page_seconds?: number | null;
  return_visits?: number;
  button_events?: Record<string, unknown> | unknown[] | null;
  cursor_metrics?: Record<string, unknown> | unknown[] | null;
  raw_payload?: Record<string, unknown> | null;
};

export type LeadApplicationCreate = {
  first_name: string;
  last_name: string;
  middle_name?: string | null;
  business_info?: string | null;
  budget_label?: string | null;
  preferred_contact_method?: string | null;
  comments?: string | null;
  business_niche?: string | null;
  company_size?: string | null;
  task_scope?: string | null;
  role_type?: string | null;
  business_scale?: string | null;
  need_scope?: string | null;
  result_deadline?: string | null;
  task_category?: string | null;
  product_interest?: string | null;
  convenient_contact_time?: string | null;
  behavior?: BehaviorMetricsCreate | null;
};

export type LeadApplicationRead = LeadApplicationCreate & {
  id: number;
  created_at: string;
  updated_at: string;
};
