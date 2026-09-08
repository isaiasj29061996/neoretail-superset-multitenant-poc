import { embedDashboard } from "@superset-ui/embedded-sdk";

const $ = (selector) => document.querySelector(selector);

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.action || body.detail || body.error || `Erro HTTP ${response.status}`);
  return body;
}

async function loginPage() {
  const form = $("#login-form");
  if (!form) return false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const error = $("#login-error");
    error.textContent = "";
    try {
      await jsonFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ username: form.username.value, password: form.password.value }),
      });
      window.location.assign("/portal");
    } catch (reason) {
      error.textContent = reason.message;
    }
  });
  return true;
}

function renderModules(modules) {
  document.querySelectorAll("[data-module]").forEach((element) => {
    element.hidden = !modules.includes(element.dataset.module);
  });
}

function showSetup(message) {
  $("#dashboard-loading").hidden = true;
  $("#setup-state").hidden = false;
  $("#setup-message").textContent = message;
}

async function portalPage() {
  const mountPoint = $("#superset-container");
  if (!mountPoint) return;

  let identity;
  try {
    identity = await jsonFetch("/api/session");
  } catch {
    window.location.assign("/login");
    return;
  }

  $("#user-name").textContent = identity.displayName;
  $("#tenant-name").textContent = identity.customerName;
  $("#tenant-badge").textContent = identity.idCustomer;
  const selector = $("#customer-select");
  for (const customer of identity.availableCustomers) {
    const option = document.createElement("option");
    option.value = String(customer.idCustomer);
    option.textContent = `${customer.name} (${customer.idCustomer})`;
    option.selected = customer.idCustomer === identity.idCustomer;
    selector.append(option);
  }
  selector.addEventListener("change", async () => {
    selector.disabled = true;
    try {
      await jsonFetch("/api/context", {
        method: "POST",
        body: JSON.stringify({ idCustomer: Number(selector.value) }),
      });
      window.location.reload();
    } catch (reason) {
      showSetup(reason.message);
      selector.disabled = false;
    }
  });
  $("#analytics-state").textContent = identity.analyticsMode === "local_postgres"
    ? "PostgreSQL Analytics ativo"
    : "Analytics pendente";
  $("#analytics-state").classList.toggle("online", identity.analyticsMode === "local_postgres");
  renderModules(identity.modules);

  $("#logout").addEventListener("click", async () => {
    await jsonFetch("/api/logout", { method: "POST" });
    window.location.assign("/login");
  });

  if (!identity.dashboardConfigured) {
    showSetup("O portal local está pronto. Falta habilitar o dashboard no Superset e preencher SUPERSET_EMBEDDED_DASHBOARD_ID no .env.");
    return;
  }

  try {
    await embedDashboard({
      id: identity.dashboardId,
      supersetDomain: identity.publicSupersetUrl,
      mountPoint,
      fetchGuestToken: async () => (await jsonFetch("/api/guest-token", { method: "POST" })).token,
      dashboardUiConfig: {
        hideTitle: true,
        hideTab: true,
        hideChartControls: true,
        filters: { visible: true, expanded: false },
        urlParams: { standalone: 3 },
      },
    });
    $("#dashboard-loading").hidden = true;
  } catch (reason) {
    showSetup(reason.message);
  }
}

(async () => {
  if (await loginPage()) return;
  await portalPage();
})();
