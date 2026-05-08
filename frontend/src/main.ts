import "./styles/app.css";
import { apiPost, fetchAdminSettingsActive } from "./api";
import { BehaviorCollector } from "./behavior";
import type { AdminSetting, LeadApplicationCreate } from "./types";

const BUDGET_LEVELS = [
  "до 100 000 ₽",
  "100 000 – 200 000 ₽",
  "200 000 – 350 000 ₽",
  "350 000 – 500 000 ₽",
  "500 000 – 750 000 ₽",
  "750 000 – 1 000 000 ₽",
  "1 000 000 – 1 500 000 ₽",
  "1 500 000 – 2 500 000 ₽",
  "свыше 2 500 000 ₽",
] as const;

const $ = <T extends HTMLElement>(id: string) => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`#${id} not found`);
  return el as T;
};

function textOrNull(value: string): string | null {
  const t = value.trim();
  return t ? t : null;
}

function setStatus(message: string, kind: "info" | "error" | "ok" = "info") {
  const node = $("formStatus");
  node.textContent = message;
  node.classList.remove("status--error", "status--ok");
  if (kind === "error") node.classList.add("status--error");
  if (kind === "ok") node.classList.add("status--ok");
}

async function loadServices() {
  const select = $<HTMLSelectElement>("serviceSelect");
  select.innerHTML = "";

  let list: AdminSetting[] = [];
  try {
    list = await fetchAdminSettingsActive();
  } catch {
    select.appendChild(new Option("Нет доступа к каталогу", "", true, true));
    select.disabled = true;
    return;
  }

  if (list.length === 0) {
    select.appendChild(new Option("Каталог пуст", "", true, true));
    select.disabled = true;
    return;
  }

  select.disabled = false;
  select.appendChild(new Option("Выберите услугу", "", true, true));
  for (const item of list) {
    const opt = new Option(item.service_title, String(item.id));
    opt.dataset.budget = item.budget_range;
    opt.dataset.title = item.service_title;
    select.add(opt);
  }
}

function syncBudgetFromSlider() {
  const range = $<HTMLInputElement>("budgetRange");
  const out = $("budgetLabelOut");
  const hidden = $<HTMLInputElement>("budgetLabel");
  const idx = Math.min(BUDGET_LEVELS.length - 1, Math.max(0, Number(range.value)));
  const label = BUDGET_LEVELS[idx] ?? "—";
  out.textContent = label;
  hidden.value = label;
}

function onServiceChange() {
  const select = $<HTMLSelectElement>("serviceSelect");
  const opt = select.selectedOptions[0];
  const product = $<HTMLInputElement>("product_interest");
  if (!opt?.dataset.title) return;
  if (!product.value.trim()) {
    product.value = opt.dataset.title;
  }
}

async function main() {
  const collector = new BehaviorCollector();
  collector.start(document.body);

  const budgetRange = $<HTMLInputElement>("budgetRange");
  budgetRange.addEventListener("input", () => syncBudgetFromSlider(), { passive: true });
  syncBudgetFromSlider();

  await loadServices();

  $<HTMLSelectElement>("serviceSelect").addEventListener("change", () => onServiceChange(), { passive: true });

  const form = $<HTMLFormElement>("leadForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setStatus("Отправка…", "info");

    const serviceSelect = $<HTMLSelectElement>("serviceSelect");
    if (serviceSelect.disabled || !serviceSelect.value) {
      setStatus("Выберите услугу.", "error");
      return;
    }

    const behavior = collector.snapshot();
    const payload: LeadApplicationCreate = {
      first_name: $<HTMLInputElement>("first_name").value.trim(),
      last_name: $<HTMLInputElement>("last_name").value.trim(),
      middle_name: textOrNull($<HTMLInputElement>("middle_name").value),
      business_info: textOrNull($<HTMLTextAreaElement>("business_info").value),
      budget_label: textOrNull($<HTMLInputElement>("budgetLabel").value),
      preferred_contact_method: textOrNull($<HTMLSelectElement>("preferred_contact_method").value),
      comments: textOrNull($<HTMLTextAreaElement>("comments").value),
      business_niche: textOrNull($<HTMLInputElement>("business_niche").value),
      company_size: textOrNull($<HTMLInputElement>("company_size").value),
      task_scope: textOrNull($<HTMLInputElement>("task_scope").value),
      role_type: textOrNull($<HTMLSelectElement>("role_type").value),
      business_scale: textOrNull($<HTMLInputElement>("business_scale").value),
      need_scope: textOrNull($<HTMLInputElement>("need_scope").value),
      result_deadline: textOrNull($<HTMLInputElement>("result_deadline").value),
      task_category: textOrNull($<HTMLInputElement>("task_category").value),
      product_interest: textOrNull($<HTMLInputElement>("product_interest").value),
      convenient_contact_time: textOrNull($<HTMLInputElement>("convenient_contact_time").value),
      behavior,
    };

    try {
      await apiPost<unknown>("/applications", payload);
      setStatus("Принято. Мы свяжемся с вами.", "ok");
      form.reset();
      syncBudgetFromSlider();
      await loadServices();
    } catch (err) {
      console.error(err);
      setStatus(err instanceof Error ? err.message : "Ошибка отправки", "error");
    }
  });
}

void main();
