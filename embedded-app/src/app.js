import { embedDashboard } from "@superset-ui/embedded-sdk";

const $ = (selector) => document.querySelector(selector);
const page = document.body.dataset.page;

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.action || body.detail || body.error || `Erro HTTP ${response.status}`);
  return body;
}

function initials(name) {
  return String(name || "NR").split(/\s+/).filter(Boolean).slice(0, 2)
    .map((part) => part[0]).join("").toUpperCase();
}

async function authenticatedSession() {
  try {
    return await jsonFetch("/api/session");
  } catch {
    window.location.assign("/login");
    return null;
  }
}

async function logout() {
  await jsonFetch("/api/logout", { method: "POST" });
  window.location.assign("/login");
}

function configureIndustryModal(identity, onConfirm) {
  const modal = $("#industry-modal");
  const selector = $("#industry-select");
  const options = $("#industry-options");
  selector.replaceChildren();
  for (const customer of identity.availableCustomers) {
    const option = document.createElement("option");
    option.value = String(customer.idCustomer);
    option.textContent = customer.name;
    option.selected = customer.idCustomer === identity.idCustomer;
    selector.append(option);
  }

  function selectCustomer(idCustomer) {
    selector.value = String(idCustomer);
    options?.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("selected", Number(button.dataset.customer) === idCustomer);
    });
  }

  if (options) {
    options.replaceChildren();
    for (const customer of identity.availableCustomers) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.customer = String(customer.idCustomer);
      button.innerHTML = `<span>${initials(customer.name)}</span><strong>${customer.name}</strong><small>ID ${customer.idCustomer}</small>`;
      button.addEventListener("click", () => selectCustomer(customer.idCustomer));
      options.append(button);
    }
  }
  selectCustomer(identity.idCustomer);
  selector.addEventListener("change", () => selectCustomer(Number(selector.value)));

  const open = () => {
    selectCustomer(identity.idCustomer);
    modal.hidden = false;
    document.body.classList.add("modal-open");
    selector.focus();
  };
  const close = () => {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
  };
  modal.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", close));
  modal.addEventListener("click", (event) => { if (event.target === modal) close(); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !modal.hidden) close(); });
  $("#confirm-industry").addEventListener("click", async () => {
    const button = $("#confirm-industry");
    button.disabled = true;
    try {
      await jsonFetch("/api/context", {
        method: "POST",
        body: JSON.stringify({ idCustomer: Number(selector.value) }),
      });
      await onConfirm(Number(selector.value));
      close();
    } finally {
      button.disabled = false;
    }
  });
  return { open, close };
}

function loginPage() {
  const form = $("#login-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const error = $("#login-error");
    const button = form.querySelector("button");
    error.textContent = "";
    button.disabled = true;
    try {
      await jsonFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ username: form.username.value, password: form.password.value }),
      });
      window.location.assign("/portal");
    } catch (reason) {
      error.textContent = reason.message;
      button.disabled = false;
    }
  });
}

async function portalPage() {
  const identity = await authenticatedSession();
  if (!identity) return;
  const catalog = await jsonFetch("/api/catalog");
  $("#portal-user-name").textContent = identity.displayName;
  $("#portal-first-name").textContent = identity.displayName.split(/\s+/)[0];
  $("#portal-initials").textContent = initials(identity.displayName);
  $("#portal-logout").addEventListener("click", logout);
  const modal = configureIndustryModal(identity, async () => {
    window.location.assign(`/app?dashboard=${encodeURIComponent(identity.defaultDashboard)}`);
  });
  $("#solution-access").addEventListener("click", modal.open);
  document.querySelector(".solution-count").textContent = `${catalog.dashboards.length} análises`;
}

function showDashboardError(message) {
  $("#dashboard-loading").hidden = true;
  $("#setup-state").hidden = false;
  $("#setup-message").textContent = message;
}

function renderNavigation(catalog, activeKey, selectDashboard) {
  const navigationRoot = $("#product-navigation");
  navigationRoot.replaceChildren();
  for (const section of catalog.navigation) {
    const group = document.createElement("div");
    group.className = `nav-group ${section.items.some((item) => item.key === activeKey) ? "active" : ""}`;
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "nav-trigger";
    trigger.innerHTML = `${section.label}<span>⌄</span>`;
    const menu = document.createElement("div");
    menu.className = "nav-menu";
    for (const item of section.items) {
      const link = document.createElement("button");
      link.type = "button";
      link.className = item.key === activeKey ? "selected" : "";
      link.innerHTML = `<span>${item.menuLabel}</span>${item.key === activeKey ? "<i>✓</i>" : "<i>→</i>"}`;
      link.addEventListener("click", () => selectDashboard(item.key));
      menu.append(link);
    }
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      document.querySelectorAll(".nav-group.open").forEach((item) => {
        if (item !== group) item.classList.remove("open");
      });
      group.classList.toggle("open");
    });
    group.append(trigger, menu);
    navigationRoot.append(group);
  }
}

async function productPage() {
  let identity = await authenticatedSession();
  if (!identity) return;
  let catalog = await jsonFetch("/api/catalog");
  $("#tenant-name").textContent = identity.customerName;
  $("#user-initials").textContent = initials(identity.displayName);
  $("#logout").addEventListener("click", logout);
  document.addEventListener("click", () => document.querySelectorAll(".nav-group.open")
    .forEach((item) => item.classList.remove("open")));

  let activeKey = new URLSearchParams(window.location.search).get("dashboard") || identity.defaultDashboard;
  if (!catalog.dashboards.some((item) => item.key === activeKey)) activeKey = identity.defaultDashboard;

  async function loadDashboard(key) {
    const dashboard = catalog.dashboards.find((item) => item.key === key);
    if (!dashboard) return showDashboardError("A análise selecionada não está disponível para este perfil.");
    activeKey = key;
    history.replaceState({}, "", `/app?dashboard=${encodeURIComponent(key)}`);
    renderNavigation(catalog, key, loadDashboard);
    $("#dashboard-title").textContent = dashboard.title;
    $("#breadcrumb").textContent = `NeoRetail / ${dashboard.section === "tasks" ? "Tarefas do dia" : "Análises"}`;
    $("#setup-state").hidden = true;
    $("#dashboard-loading").hidden = false;
    const mountPoint = $("#superset-container");
    mountPoint.replaceChildren();
    try {
      await embedDashboard({
        id: dashboard.embeddedId,
        supersetDomain: identity.publicSupersetUrl,
        mountPoint,
        fetchGuestToken: async () => (await jsonFetch("/api/guest-token", {
          method: "POST",
          body: JSON.stringify({ dashboardKey: key }),
        })).token,
        dashboardUiConfig: {
          hideTitle: true,
          hideTab: true,
          hideChartControls: true,
          filters: { visible: true, expanded: false },
          urlParams: { standalone: 3 },
        },
        referrerPolicy: "strict-origin-when-cross-origin",
      });
      $("#dashboard-loading").hidden = true;
    } catch (reason) {
      showDashboardError(reason.message);
    }
  }

  const industryModal = configureIndustryModal(identity, async () => {
    identity = await jsonFetch("/api/session");
    catalog = await jsonFetch("/api/catalog");
    $("#tenant-name").textContent = identity.customerName;
    await loadDashboard(activeKey);
  });
  $("#active-industry").addEventListener("click", industryModal.open);
  $("#retry-dashboard").addEventListener("click", () => loadDashboard(activeKey));
  await loadDashboard(activeKey);
}

if (page === "login") loginPage();
if (page === "portal") portalPage();
if (page === "product") productPage();
