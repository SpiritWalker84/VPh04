import "./styles/admin.css";
import {
  apiDelete,
  apiPatch,
  apiPost,
  authCheckRegistration,
  authLogin,
  authLogout,
  authMe,
  authRegister,
  fetchAdminSettingsAll,
  fetchApplicationAdmin,
  fetchApplicationsAdmin,
  fetchApplicationsDashboard,
  fetchBehaviorStats,
} from "./api";
import type {
  AdminSetting,
  ApplicationDashboardResponse,
  LeadApplicationAdminDetail,
  LeadApplicationAdminListItem,
} from "./types";

let editingId: number | null = null;
let applicationsSort: "priority" | "recent" = "priority";

function goToCatalog(): void {
  $<HTMLElement>("adminPanelServices").hidden = false;
  $<HTMLElement>("adminPanelLeads").hidden = true;
  $<HTMLButtonElement>("navCatalogBtn").classList.add("is-active");
  $<HTMLButtonElement>("navLeadsBtn").classList.remove("is-active");
}

function goToLeadsSummary(): void {
  $<HTMLElement>("adminPanelServices").hidden = true;
  $<HTMLElement>("adminPanelLeads").hidden = false;
  $<HTMLButtonElement>("navCatalogBtn").classList.remove("is-active");
  $<HTMLButtonElement>("navLeadsBtn").classList.add("is-active");
  void reloadApplications();
}

const $ = <T extends HTMLElement>(id: string) => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`#${id} not found`);
  return el as T;
};

function setAdminStatus(message: string, kind: "info" | "error" | "ok" = "info") {
  const node = $("adminStatus");
  node.textContent = message;
  node.classList.remove("err", "ok");
  if (kind === "error") node.classList.add("err");
  if (kind === "ok") node.classList.add("ok");
}

function setLoginStatus(message: string, err = false) {
  const node = $("loginStatus");
  node.textContent = message;
  node.classList.toggle("err", err);
}

function showLoginForms(mode: "login" | "register") {
  $<HTMLFormElement>("loginForm").hidden = mode !== "login";
  $<HTMLFormElement>("registerForm").hidden = mode !== "register";
}

function showLogin() {
  $<HTMLElement>("loginPanel").hidden = false;
  $<HTMLElement>("adminApp").hidden = true;
  showLoginForms("login");
}

function showApp() {
  $<HTMLElement>("loginPanel").hidden = true;
  $<HTMLElement>("adminApp").hidden = false;
}

async function refreshRegistrationUi() {
  try {
    const { registration_open } = await authCheckRegistration();
    $<HTMLButtonElement>("toRegisterBtn").hidden = !registration_open;
  } catch (err) {
    console.error(err);
    $<HTMLButtonElement>("toRegisterBtn").hidden = true;
  }
}

function formatAvgDuration(sec: number): string {
  if (sec == null || Number.isNaN(sec)) return "—";
  if (sec < 0.5) return "нет данных";
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return m ? `${m} мин ${s} с (≈${sec.toFixed(0)} с)` : `≈${sec.toFixed(1)} с`;
}

function renderHeatmapSvg(svg: SVGSVGElement, cells: { x: number; y: number; count: number }[]) {
  const ns = "http://www.w3.org/2000/svg";
  svg.innerHTML = "";
  const maxC = Math.max(...cells.map((c) => c.count), 1);
  const maxX = Math.max(...cells.map((c) => c.x + 50), 520);
  const maxY = Math.max(...cells.map((c) => c.y + 50), 400);
  svg.setAttribute("viewBox", `0 0 ${maxX} ${maxY}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  for (const c of cells) {
    const t = Math.sqrt(c.count / maxC);
    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", String(c.x));
    circle.setAttribute("cy", String(c.y));
    circle.setAttribute("r", String(6 + 26 * t));
    circle.setAttribute("fill", `rgba(61, 107, 92, ${0.2 + 0.65 * t})`);
    circle.setAttribute("stroke", "rgba(20, 19, 18, 0.12)");
    circle.setAttribute("stroke-width", "1");
    svg.appendChild(circle);
  }
}

async function loadStatsModal() {
  const summary = $("statsSummary");
  const empty = $("statsHeatmapEmpty");
  const hint = $<HTMLParagraphElement>("statsEmptyHint");
  const el = document.getElementById("statsHeatmapSvg");
  if (!el || !(el instanceof SVGSVGElement)) throw new Error("#statsHeatmapSvg");
  const svg = el;
  summary.innerHTML = "";
  empty.hidden = true;
  hint.hidden = true;
  hint.textContent = "";
  svg.innerHTML = "";
  try {
    const s = await fetchBehaviorStats();
    if (s.stream_rows_last_30_days === 0) {
      hint.hidden = false;
      hint.textContent =
        "В базе пока нет потоковых метрик. Считается только с клиентской главной страницы (адрес /), не с админки: откройте её в другой вкладке, подержите 20–40 секунд (отправка раз в секунду), затем обновите это окно (закройте и снова нажмите «Статистика пользователей»).";
    }
    const lines: [string, string][] = [
      ["Записей потока за 30 суток", String(s.stream_rows_last_30_days)],
      ["Окно ~1 сутки (UTC): среднее дневных максимумов времени на странице", formatAvgDuration(s.avg_daily_max_seconds_day)],
      ["Последние 7 суток", formatAvgDuration(s.avg_daily_max_seconds_week)],
      ["Последние 30 суток", formatAvgDuration(s.avg_daily_max_seconds_month)],
    ];
    for (const [label, val] of lines) {
      const li = document.createElement("li");
      li.textContent = `${label}: ${val}`;
      summary.appendChild(li);
    }
    if (!s.heatmap.length) {
      empty.hidden = false;
      return;
    }
    renderHeatmapSvg(svg, s.heatmap);
  } catch (err) {
    const li = document.createElement("li");
    li.textContent = err instanceof Error ? err.message : "Ошибка загрузки";
    summary.appendChild(li);
    empty.hidden = false;
  }
}

function openStatsModal() {
  $<HTMLElement>("statsModal").hidden = false;
  void loadStatsModal();
}

function closeStatsModal() {
  $<HTMLElement>("statsModal").hidden = true;
}

function escHtml(s: string | null | undefined): string {
  if (s == null || s === "") return "—";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function formatShortDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function setApplicationsSortUi(): void {
  $<HTMLButtonElement>("applicationsSortPriority").classList.toggle("is-active", applicationsSort === "priority");
  $<HTMLButtonElement>("applicationsSortRecent").classList.toggle("is-active", applicationsSort === "recent");
}

function resetDashboardCards(): void {
  for (const id of ["dashTotal", "dashWeek", "dashHot", "dashWarm", "dashCold"]) {
    $(id).textContent = "—";
  }
  const meta = $<HTMLParagraphElement>("dashboardMeta");
  meta.hidden = true;
  meta.textContent = "";
}

function renderDashboard(d: ApplicationDashboardResponse): void {
  $("dashTotal").textContent = String(d.applications_total);
  $("dashWeek").textContent = String(d.new_last_7_days);
  $("dashHot").textContent = String(d.hot_count);
  $("dashWarm").textContent = String(d.warm_count);
  $("dashCold").textContent = String(d.cold_count);
  const meta = $<HTMLParagraphElement>("dashboardMeta");
  if (d.applications_total === 0) {
    meta.hidden = false;
    meta.textContent = "Заявок в базе пока нет — отправьте форму с лендинга или добавьте строки в pgAdmin.";
    return;
  }
  if (d.scoring_capped) {
    meta.hidden = false;
    meta.textContent = `Горячие, тёплые и холодные посчитаны по ${d.scored_for_breakdown} последним заявкам. Всего в базе: ${d.applications_total}.`;
    return;
  }
  meta.hidden = true;
  meta.textContent = "";
}

async function reloadDashboard(): Promise<void> {
  try {
    const d = await fetchApplicationsDashboard();
    renderDashboard(d);
  } catch (err) {
    console.error(err);
    resetDashboardCards();
    const meta = $<HTMLParagraphElement>("dashboardMeta");
    meta.hidden = false;
    meta.textContent = "Сводку заявок не удалось загрузить. Проверьте вход и что backend доступен.";
  }
}

function iceChipClass(t: string): string {
  if (t === "hot") return "ice-chip ice-chip--hot";
  if (t === "warm") return "ice-chip ice-chip--warm";
  return "ice-chip ice-chip--cold";
}

async function reloadApplications(): Promise<void> {
  const body = $("applicationsBody");
  body.innerHTML = `<tr><td colspan="11">Загрузка…</td></tr>`;
  try {
    const rows = await fetchApplicationsAdmin(0, 100, applicationsSort);
    renderApplicationsRows(rows);
  } catch (err) {
    body.innerHTML = `<tr><td colspan="11">${escHtml(err instanceof Error ? err.message : "Ошибка")}</td></tr>`;
  }
  await reloadDashboard();
}

function renderApplicationsRows(items: LeadApplicationAdminListItem[]): void {
  const body = $("applicationsBody");
  body.innerHTML = "";
  if (items.length === 0) {
    body.innerHTML = `<tr><td colspan="11">Заявок пока нет.</td></tr>`;
    return;
  }
  for (const r of items) {
    const tr = document.createElement("tr");
    const s = r.scoring;
    const name = [r.last_name, r.first_name, r.middle_name].filter(Boolean).join(" ");
    tr.innerHTML = `
      <td><span class="mono-pill">${s.priority_score}</span></td>
      <td><span class="${iceChipClass(s.temperature)}" title="${escHtml(s.temperature_label)}">${escHtml(s.temperature_label)}</span></td>
      <td>${escHtml(name)}</td>
      <td>${escHtml(r.business_niche ?? r.product_interest)}</td>
      <td>${escHtml(r.company_size)}</td>
      <td>${escHtml(r.budget_label)}</td>
      <td>${escHtml(s.recommended_department)}</td>
      <td>${s.personal_manager_recommended ? '<span class="ice-chip ice-chip--warm">Да</span>' : '<span class="ice-chip ice-chip--cold">Нет</span>'}</td>
      <td>${escHtml(r.preferred_contact_method)}</td>
      <td>${escHtml(formatShortDate(r.created_at))}</td>
      <td></td>`;
    const tdBtn = tr.lastElementChild as HTMLTableCellElement;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-sm";
    btn.textContent = "Просмотр";
    btn.addEventListener("click", () => void openApplicationModal(r.id), { passive: true });
    tdBtn.appendChild(btn);
    body.appendChild(tr);
  }
}

function closeApplicationModal(): void {
  $<HTMLElement>("applicationModal").hidden = true;
}

async function openApplicationModal(id: number): Promise<void> {
  const modal = $<HTMLElement>("applicationModal");
  const body = $("applicationModalBody");
  const title = $("applicationModalTitle");
  modal.hidden = false;
  title.textContent = `Заявка #${id}`;
  body.innerHTML = "<p>Загрузка…</p>";
  try {
    const d = await fetchApplicationAdmin(id);
    body.innerHTML = renderApplicationDetailHtml(d);
  } catch (e) {
    body.innerHTML = `<p class="err">${escHtml(e instanceof Error ? e.message : "Ошибка")}</p>`;
  }
}

function renderApplicationDetailHtml(d: LeadApplicationAdminDetail): string {
  const sc = d.scoring;
  const reasons = sc.reasons.length
    ? `<ul class="app-scoring-reasons">${sc.reasons.map((x) => `<li>${escHtml(x)}</li>`).join("")}</ul>`
    : "";
  const mgr = sc.personal_manager_recommended
    ? '<span class="ice-chip ice-chip--warm">Персональный менеджер — да</span>'
    : '<span class="ice-chip ice-chip--cold">Персональный менеджер — не обязателен</span>';
  const worth = sc.worth_pursuing
    ? "Имеет смысл выделить время на проработку."
    : "Ручная проработка может быть невыгодна — рассмотреть автоответ или длинный цикл.";

  const scoringBlock = `<div class="app-scoring-card">
      <div class="app-scoring-card__row">
        <span class="mono-pill">${sc.priority_score}</span>
        <span class="${iceChipClass(sc.temperature)}">${escHtml(sc.temperature_label)}</span>
        ${mgr}
      </div>
      <p>${escHtml(sc.summary)}</p>
      <p><strong>Рекомендуемый отдел:</strong> ${escHtml(sc.recommended_department)}</p>
      <p><strong>Окупаемость времени менеджера:</strong> ${worth}</p>
      ${reasons}
    </div>`;

  const blocks: Array<[string, string | null | undefined]> = [
    ["Имя", d.first_name],
    ["Фамилия", d.last_name],
    ["Отчество", d.middle_name],
    ["Способ связи", d.preferred_contact_method],
    ["Удобное время связи", d.convenient_contact_time],
    ["Ниша", d.business_niche],
    ["Размер компании", d.company_size],
    ["Роль", d.role_type],
    ["Масштаб бизнеса", d.business_scale],
    ["Интерес к продукту", d.product_interest],
    ["Категория задачи", d.task_category],
    ["Объём задачи", d.task_scope],
    ["Срок / результат", d.result_deadline],
    ["Охват потребности", d.need_scope],
    ["Бюджет (поле формы)", d.budget_label],
    ["Комментарий клиента", d.comments],
  ];

  const dl = blocks
    .map(([k, v]) => {
      const long = k === "Комментарий клиента" || k === "Объём задачи";
      const cls = long ? " class=\"biz-block\"" : "";
      return `<dt>${escHtml(k)}</dt><dd${cls}>${escHtml(v)}</dd>`;
    })
    .join("");

  const biz = d.business_info
    ? `<dt>О бизнесе</dt><dd class="biz-block">${escHtml(d.business_info)}</dd>`
    : "";

  let behavior = "";
  if (d.behavior) {
    behavior = `<dt>Метрики поведения (сырые)</dt><dd class="biz-block"><pre style="margin:0;font-size:0.78rem;white-space:pre-wrap">${escHtml(JSON.stringify(d.behavior, null, 2))}</pre></dd>`;
  }

  return `${scoringBlock}<dl class="app-detail-dl">${dl}${biz}${behavior}</dl>
    <p style="margin-top:1rem;font-size:var(--step--1);color:var(--ink-muted)">Создана: ${escHtml(formatShortDate(d.created_at))} · обновлена: ${escHtml(formatShortDate(d.updated_at))}</p>`;
}

function renderRows(items: AdminSetting[]) {
  const body = $("settingsBody");
  body.innerHTML = "";
  if (items.length === 0) {
    body.innerHTML = `<tr><td colspan="6">Пока нет записей.</td></tr>`;
    return;
  }

  for (const row of items) {
    const tr = document.createElement("tr");

    const mkTd = () => document.createElement("td");

    if (editingId === row.id) {
      const idTd = mkTd();
      idTd.innerHTML = `<span class="mono">${row.id}</span>`;
      tr.appendChild(idTd);

      const titleTd = mkTd();
      const titleIn = document.createElement("input");
      titleIn.type = "text";
      titleIn.className = "admin-table-field";
      titleIn.id = `edit-${row.id}-title`;
      titleIn.value = row.service_title;
      titleTd.appendChild(titleIn);
      tr.appendChild(titleTd);

      const budgetTd = mkTd();
      const budgetIn = document.createElement("input");
      budgetIn.type = "text";
      budgetIn.className = "admin-table-field";
      budgetIn.id = `edit-${row.id}-budget`;
      budgetIn.value = row.budget_range;
      budgetTd.appendChild(budgetIn);
      tr.appendChild(budgetTd);

      const orderTd = mkTd();
      const orderIn = document.createElement("input");
      orderIn.type = "number";
      orderIn.className = "admin-table-field";
      orderIn.id = `edit-${row.id}-order`;
      orderIn.value = String(row.sort_order);
      orderTd.appendChild(orderIn);
      tr.appendChild(orderTd);

      const statTd = mkTd();
      const lab = document.createElement("label");
      lab.className = "inline";
      lab.style.gap = "0.35rem";
      lab.style.alignItems = "center";
      const actCb = document.createElement("input");
      actCb.type = "checkbox";
      actCb.className = "admin-table-check";
      actCb.id = `edit-${row.id}-active`;
      actCb.checked = row.is_active;
      lab.appendChild(actCb);
      lab.appendChild(document.createTextNode("Активна"));
      statTd.appendChild(lab);
      tr.appendChild(statTd);

      const actTd = mkTd();
      actTd.className = "inline";
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "btn-sm";
      saveBtn.textContent = "Сохранить";
      saveBtn.addEventListener("click", () => void saveEdit(row.id), { passive: true });
      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.className = "btn-sm";
      cancelBtn.textContent = "Отмена";
      cancelBtn.addEventListener("click", () => cancelEdit(), { passive: true });
      actTd.appendChild(saveBtn);
      actTd.appendChild(cancelBtn);
      tr.appendChild(actTd);

      body.appendChild(tr);
      continue;
    }

    const idTd = mkTd();
    idTd.innerHTML = `<span class="mono">${row.id}</span>`;
    tr.appendChild(idTd);

    const titleTd = mkTd();
    titleTd.textContent = row.service_title;
    tr.appendChild(titleTd);

    const budgetTd = mkTd();
    budgetTd.textContent = row.budget_range;
    tr.appendChild(budgetTd);

    const orderTd = mkTd();
    orderTd.innerHTML = `<span class="mono">${row.sort_order}</span>`;
    tr.appendChild(orderTd);

    tr.appendChild(
      (() => {
        const td = mkTd();
        td.innerHTML = row.is_active
          ? `<span class="chip chip--on">активна</span>`
          : `<span class="chip">выкл</span>`;
        return td;
      })(),
    );

    const actions = mkTd();
    actions.className = "inline";

    const eBtn = document.createElement("button");
    eBtn.type = "button";
    eBtn.className = "btn-sm";
    eBtn.textContent = "Редактировать";
    eBtn.addEventListener(
      "click",
      () => {
        editingId = row.id;
        void reload();
      },
      { passive: true },
    );

    const tBtn = document.createElement("button");
    tBtn.type = "button";
    tBtn.className = "btn-sm";
    tBtn.textContent = row.is_active ? "Деактивировать" : "Включить";
    tBtn.addEventListener("click", () => void toggleActive(row.id, !row.is_active), { passive: true });

    const dBtn = document.createElement("button");
    dBtn.type = "button";
    dBtn.className = "btn-sm danger";
    dBtn.textContent = "Удалить";
    dBtn.addEventListener("click", () => void removeRow(row.id), { passive: true });

    actions.appendChild(eBtn);
    actions.appendChild(tBtn);
    actions.appendChild(dBtn);
    tr.appendChild(actions);

    body.appendChild(tr);
  }
}

function cancelEdit() {
  editingId = null;
  void reload();
}

async function saveEdit(id: number) {
  const titleEl = document.getElementById(`edit-${id}-title`) as HTMLInputElement | null;
  const budgetEl = document.getElementById(`edit-${id}-budget`) as HTMLInputElement | null;
  const orderEl = document.getElementById(`edit-${id}-order`) as HTMLInputElement | null;
  const activeEl = document.getElementById(`edit-${id}-active`) as HTMLInputElement | null;
  if (!titleEl || !budgetEl || !orderEl || !activeEl) return;

  const service_title = titleEl.value.trim();
  const budget_range = budgetEl.value.trim();
  if (!service_title || !budget_range) {
    setAdminStatus("Заполните услугу и диапазон бюджета.", "error");
    return;
  }

  try {
    setAdminStatus("Сохранение…", "info");
    await apiPatch<AdminSetting>(`/admin/settings/${id}`, {
      service_title,
      budget_range,
      sort_order: Number(orderEl.value || 0),
      is_active: activeEl.checked,
    });
    editingId = null;
    setAdminStatus("Сохранено.", "ok");
    await reload();
  } catch (err) {
    console.error(err);
    setAdminStatus(err instanceof Error ? err.message : "Ошибка", "error");
  }
}

async function reload() {
  const items = await fetchAdminSettingsAll();
  renderRows(items);
}

async function toggleActive(id: number, is_active: boolean) {
  try {
    setAdminStatus("Сохранение…", "info");
    await apiPatch<AdminSetting>(`/admin/settings/${id}`, { is_active });
    setAdminStatus("Готово.", "ok");
    await reload();
  } catch (err) {
    console.error(err);
    setAdminStatus(err instanceof Error ? err.message : "Ошибка", "error");
  }
}

async function removeRow(id: number) {
  if (!globalThis.confirm(`Удалить запись #${id}?`)) return;
  try {
    setAdminStatus("Удаление…", "info");
    await apiDelete(`/admin/settings/${id}`);
    setAdminStatus("Удалено.", "ok");
    await reload();
  } catch (err) {
    console.error(err);
    setAdminStatus(err instanceof Error ? err.message : "Ошибка", "error");
  }
}

async function main() {
  await refreshRegistrationUi();

  $<HTMLButtonElement>("toRegisterBtn").addEventListener(
    "click",
    () => {
      setLoginStatus("", false);
      showLoginForms("register");
    },
    { passive: true },
  );

  $<HTMLButtonElement>("cancelRegisterBtn").addEventListener(
    "click",
    () => {
      setLoginStatus("", false);
      showLoginForms("login");
    },
    { passive: true },
  );

  $<HTMLFormElement>("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    setLoginStatus("Регистрация…", false);
    try {
      await authRegister(
        $<HTMLInputElement>("registerUser").value.trim(),
        $<HTMLInputElement>("registerPass").value,
      );
      setLoginStatus("");
      $<HTMLInputElement>("registerPass").value = "";
      $<HTMLButtonElement>("toRegisterBtn").hidden = true;
      showApp();
      $<HTMLFormElement>("createForm").reset();
      $<HTMLInputElement>("c_order").value = "0";
      $<HTMLInputElement>("c_active").checked = true;
      await reload();
      goToCatalog();
    } catch (err) {
      console.error(err);
      setLoginStatus(err instanceof Error ? err.message : "Ошибка регистрации", true);
    }
  });

  $<HTMLFormElement>("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    setLoginStatus("Вход…", false);
    try {
      await authLogin($<HTMLInputElement>("loginUser").value.trim(), $<HTMLInputElement>("loginPass").value);
      setLoginStatus("");
      $<HTMLInputElement>("loginPass").value = "";
      showApp();
      $<HTMLFormElement>("createForm").reset();
      $<HTMLInputElement>("c_order").value = "0";
      $<HTMLInputElement>("c_active").checked = true;
      await reload();
      goToCatalog();
    } catch (err) {
      console.error(err);
      setLoginStatus(err instanceof Error ? err.message : "Неверные данные", true);
    }
  });

  $<HTMLButtonElement>("logoutBtn").addEventListener(
    "click",
    () => {
      void (async () => {
        try {
          await authLogout();
        } catch (e) {
          console.error(e);
        }
        showLogin();
        setAdminStatus("");
        editingId = null;
        goToCatalog();
        $("settingsBody").innerHTML = `<tr><td colspan="6">Войдите снова.</td></tr>`;
        $("applicationsBody").innerHTML = `<tr><td colspan="11">Войдите, чтобы загрузить заявки.</td></tr>`;
        resetDashboardCards();
        await refreshRegistrationUi();
      })();
    },
    { passive: true },
  );

  $<HTMLFormElement>("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      setAdminStatus("Создание…", "info");
      await apiPost<AdminSetting>(
        "/admin/settings",
        {
          service_title: $<HTMLInputElement>("c_title").value.trim(),
          budget_range: $<HTMLInputElement>("c_budget").value.trim(),
          sort_order: Number($<HTMLInputElement>("c_order").value || 0),
          is_active: $<HTMLInputElement>("c_active").checked,
        },
        { auth: true },
      );
      setAdminStatus("Создано.", "ok");
      $<HTMLFormElement>("createForm").reset();
      $<HTMLInputElement>("c_order").value = "0";
      $<HTMLInputElement>("c_active").checked = true;
      await reload();
    } catch (err) {
      console.error(err);
      setAdminStatus(err instanceof Error ? err.message : "Ошибка создания", "error");
    }
  });

  $<HTMLButtonElement>("navCatalogBtn").addEventListener("click", () => goToCatalog(), { passive: true });
  $<HTMLButtonElement>("navLeadsBtn").addEventListener("click", () => goToLeadsSummary(), { passive: true });

  $<HTMLButtonElement>("statsOpenBtn").addEventListener("click", () => openStatsModal(), { passive: true });
  $<HTMLButtonElement>("statsModalClose").addEventListener("click", () => closeStatsModal(), { passive: true });
  $<HTMLElement>("statsModalBackdrop").addEventListener("click", () => closeStatsModal(), { passive: true });

  $<HTMLButtonElement>("applicationsSortPriority").addEventListener(
    "click",
    () => {
      applicationsSort = "priority";
      setApplicationsSortUi();
      void reloadApplications();
    },
    { passive: true },
  );
  $<HTMLButtonElement>("applicationsSortRecent").addEventListener(
    "click",
    () => {
      applicationsSort = "recent";
      setApplicationsSortUi();
      void reloadApplications();
    },
    { passive: true },
  );
  $<HTMLButtonElement>("applicationsRefresh").addEventListener("click", () => void reloadApplications(), { passive: true });
  $<HTMLButtonElement>("applicationModalClose").addEventListener("click", () => closeApplicationModal(), {
    passive: true,
  });
  $<HTMLElement>("applicationModalBackdrop").addEventListener("click", () => closeApplicationModal(), {
    passive: true,
  });

  try {
    const me = await authMe();
    if (!me) {
      showLogin();
      $("settingsBody").innerHTML = `<tr><td colspan="6">Требуется вход.</td></tr>`;
      $("applicationsBody").innerHTML = `<tr><td colspan="11">Требуется вход.</td></tr>`;
      return;
    }
    showApp();
    goToCatalog();
    setApplicationsSortUi();
    await reload();
  } catch (err) {
    console.error(err);
    showLogin();
    setLoginStatus(err instanceof Error ? err.message : "Ошибка", true);
    $("settingsBody").innerHTML = "";
    $("applicationsBody").innerHTML = `<tr><td colspan="11">Ошибка загрузки.</td></tr>`;
  }
}

void main();
