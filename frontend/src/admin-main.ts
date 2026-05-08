import "./styles/admin.css";
import {
  apiDelete,
  apiPatch,
  apiPost,
  authLogin,
  authLogout,
  authMe,
  fetchAdminSettingsAll,
} from "./api";
import type { AdminSetting } from "./types";

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

function showLogin() {
  $<HTMLElement>("loginPanel").hidden = false;
  $<HTMLElement>("adminApp").hidden = true;
}

function showApp() {
  $<HTMLElement>("loginPanel").hidden = true;
  $<HTMLElement>("adminApp").hidden = false;
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

    const mkTd = (html: string) => {
      const td = document.createElement("td");
      td.innerHTML = html;
      return td;
    };

    tr.appendChild(mkTd(`<span class="mono">${row.id}</span>`));
    tr.appendChild(mkTd(`${escapeHtml(row.service_title)}`));
    tr.appendChild(mkTd(`${escapeHtml(row.budget_range)}`));
    tr.appendChild(mkTd(`<span class="mono">${row.sort_order}</span>`));
    tr.appendChild(
      mkTd(`${row.is_active ? `<span class="chip chip--on">активна</span>` : `<span class="chip">выкл</span>`}`),
    );

    const actions = document.createElement("td");
    actions.className = "inline";

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

    actions.appendChild(tBtn);
    actions.appendChild(dBtn);
    tr.appendChild(actions);

    body.appendChild(tr);
  }
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
        $("settingsBody").innerHTML = `<tr><td colspan="6">Войдите снова.</td></tr>`;
      })();
    },
    { passive: true },
  );

  $<HTMLFormElement>("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      setAdminStatus("Создание…", "info");
      await apiPost<AdminSetting>("/admin/settings", {
        service_title: $<HTMLInputElement>("c_title").value.trim(),
        budget_range: $<HTMLInputElement>("c_budget").value.trim(),
        sort_order: Number($<HTMLInputElement>("c_order").value || 0),
        is_active: $<HTMLInputElement>("c_active").checked,
      });
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

  try {
    const me = await authMe();
    if (!me.authenticated) {
      showLogin();
      $("settingsBody").innerHTML = `<tr><td colspan="6">Требуется вход.</td></tr>`;
      return;
    }
    showApp();
    await reload();
  } catch (err) {
    console.error(err);
    showLogin();
    setLoginStatus(err instanceof Error ? err.message : "Ошибка", true);
    $("settingsBody").innerHTML = "";
  }
}

void main();
