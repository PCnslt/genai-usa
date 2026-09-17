/* ---- CONFIG (filled during deploy) ---- */
const CONFIG = {
  cognitoDomain: "https://genai-usa-auth.auth.us-east-2.amazoncognito.com",
  clientId: "532f118f0hllb65dammopv9lgv",
  redirectUri: window.location.origin + window.location.pathname,
  apiUrl: "https://fj2i0k2wvg.execute-api.us-east-2.amazonaws.com",
};

/* ---- auth (Cognito hosted UI, implicit grant) ---- */
function login() {
  const url =
    `${CONFIG.cognitoDomain}/oauth2/authorize` +
    `?client_id=${CONFIG.clientId}` +
    `&response_type=token` +
    `&scope=openid+email+profile` +
    `&redirect_uri=${encodeURIComponent(CONFIG.redirectUri)}`;
  window.location.href = url;
}

function parseHash() {
  const p = new URLSearchParams(window.location.hash.substring(1));
  if (p.get("id_token")) {
    localStorage.setItem(
      "gai_tokens",
      JSON.stringify({ id: p.get("id_token"), access: p.get("access_token") })
    );
    history.replaceState(null, "", window.location.pathname);
  }
}

function tokens() {
  try { return JSON.parse(localStorage.getItem("gai_tokens")); } catch (_) { return null; }
}

function decodeJwt(token) {
  try { return JSON.parse(atob(token.split(".")[1])); } catch (_) { return {}; }
}

function logout() {
  localStorage.removeItem("gai_tokens");
  window.location.href =
    `${CONFIG.cognitoDomain}/logout` +
    `?client_id=${CONFIG.clientId}` +
    `&logout_uri=${encodeURIComponent(window.location.origin + "/app/")}`;
}

async function api(path, opts = {}) {
  const t = tokens();
  const res = await fetch(CONFIG.apiUrl + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + (t && t.access),
      ...(opts.headers || {}),
    },
  });
  return res.json();
}

/* ---- helpers ---- */
const money = (c) => "$" + (Number(c || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const el = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* ---- state ---- */
let role = "customer";
let acceptedVersion = null;
let checkoutItem = null;
let catalog = [];

/* ---- role ---- */
function groupsOf(claims) {
  const g = claims["cognito:groups"] || ["customers"];
  return Array.isArray(g) ? g : [g];
}

/* ---- customer view ---- */
function renderEntitlements(ents) {
  const ul = el("entitlements");
  ul.innerHTML = "";
  if (!ents || !ents.length) {
    ul.innerHTML = '<li class="muted">No purchases yet.</li>';
    return;
  }
  const names = {};
  catalog.forEach((p) => (names[p.product_id] = p.name));
  ents.forEach((e) => {
    const li = document.createElement("li");
    li.className = "ent";
    li.innerHTML = `<span class="dot"></span>${esc(names[e.product_id] || e.product_id)}`;
    ul.appendChild(li);
  });
}

function renderOrders(orders) {
  const ul = el("orders");
  ul.innerHTML = "";
  if (!orders || !orders.length) {
    ul.innerHTML = '<li class="muted">No orders yet.</li>';
    return;
  }
  orders.forEach((o) => {
    const li = document.createElement("li");
    li.className = "order";
    li.innerHTML =
      `<span>${esc(o.order_id)} · ${money(o.amount_cents)}</span>` +
      `<span class="status">${esc(o.status || "pending")}${o.fulfillment_status ? " · " + esc(o.fulfillment_status) : ""}</span>`;
    ul.appendChild(li);
  });
}

function renderBilling(b) {
  const box = el("billing");
  const link = el("portalLink");
  if (b && b.portal_url) {
    box.textContent = "Manage invoices, payment methods, and subscriptions.";
    link.style.display = "inline-flex";
    link.href = b.portal_url;
  } else {
    box.textContent = "Billing portal appears once a payment provider is connected.";
    link.style.display = "none";
  }
}

function renderShop() {
  const grid = el("shop");
  grid.innerHTML = "";
  const kinds = { product: "Product", service: "Service", plan: "Plan" };
  (catalog || []).forEach((p) => {
    const d = document.createElement("div");
    d.className = "shop-item";
    const monthly = Number(p.monthly_cents || 0);
    const priceLine = money(p.price_cents) + (monthly ? " + " + money(monthly) + "/mo" : "");
    d.innerHTML =
      `<div class="ptag">${esc(kinds[p.kind] || p.kind)}</div>` +
      `<h4>${esc(p.name)}</h4>` +
      `<p class="muted small">${esc(p.description || "")}</p>` +
      `<div class="price">${priceLine}</div>` +
      `<button class="btn buy" data-id="${esc(p.product_id)}">Buy</button>`;
    grid.appendChild(d);
  });
  grid.querySelectorAll(".buy").forEach((b) =>
    b.addEventListener("click", () => openCheckout(b.dataset.id)));
}

async function renderTerms() {
  const latest = await api("/contracts/latest");
  el("termsText").textContent = latest.text || "";
  acceptedVersion = latest.version;
  const mine = await api("/contracts");
  const ok = (mine || []).some((c) => c.version === acceptedVersion);
  el("termsStatus").textContent = ok
    ? `✓ You accepted version ${acceptedVersion}.`
    : `You have not accepted version ${acceptedVersion}.`;
  el("acceptTerms").style.display = ok ? "none" : "inline-flex";
  return ok;
}

async function refreshCustomer() {
  const [ents, orders, billing] = await Promise.all([
    api("/entitlements"), api("/orders"), api("/billing"),
  ]);
  renderEntitlements(ents);
  renderOrders(orders);
  renderBilling(billing);
}

/* ---- checkout ---- */
function openCheckout(productId) {
  const p = catalog.find((x) => x.product_id === productId);
  if (!p) return;
  checkoutItem = p;
  const monthly = Number(p.monthly_cents || 0);
  const priceLine = money(p.price_cents) + (monthly ? " + " + money(monthly) + "/mo" : "");
  const needTerms = !acceptedVersion;
  el("modalTitle").textContent = "Checkout";
  el("modalBody").innerHTML =
    `<p><b>${esc(p.name)}</b> — ${priceLine}</p>` +
    (needTerms
      ? `<label class="agree"><input type="checkbox" id="agreeChk"> I agree to the <b>Terms of Service &amp; Service Agreement</b> (version ${esc(acceptedVersion)})</label>`
      : `<p class="muted small">Terms version ${esc(acceptedVersion)} already accepted.</p>`);
  el("modal").style.display = "flex";
}

function closeCheckout() {
  el("modal").style.display = "none";
  checkoutItem = null;
}

async function completePurchase() {
  if (!checkoutItem) return;
  const chk = el("agreeChk");
  if (chk && !chk.checked) { alert("Please accept the terms to continue."); return; }
  const btn = el("modalConfirm");
  btn.disabled = true;
  try {
    if (chk) { await api("/contracts/accept", { method: "POST", body: JSON.stringify({ type: "terms" }) }); }
    const here = window.location.origin + window.location.pathname;
    const order = await api("/orders", {
      method: "POST",
      body: JSON.stringify({
        items: [{ product_id: checkoutItem.product_id, qty: 1 }],
        success_url: here, cancel_url: here,
        recurring: !!checkoutItem.recurring,
      }),
    });
    if (order.error) { alert(order.error); return; }
    if (order.checkout_url && order.checkout_url.includes("mock")) {
      // mock provider: simulate a successful payment webhook round-trip
      await fetch(CONFIG.apiUrl + "/webhooks/payments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "payment.succeeded", order_id: order.order_id,
          amount_cents: order.amount_cents, event_id: "mock_" + order.order_id,
        }),
      });
      closeCheckout();
      await refreshCustomer();
      renderTerms();
      alert("Purchase complete (mock payment). See your orders + purchases.");
    } else {
      window.location.href = order.checkout_url; // real provider checkout
    }
  } catch (e) {
    alert("Checkout failed: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

/* ---- chat ---- */
function bubble(html, cls) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.innerHTML = html;
  el("chatlog").appendChild(d);
  el("chatlog").scrollTop = 1e9;
}

/* ---- support (customer) ---- */
async function refreshSupport() {
  const thread = await api("/support");
  const box = el("supportThread");
  box.innerHTML = "";
  (thread || []).forEach((m) => {
    const d = document.createElement("div");
    d.className = "sup " + m.status;
    d.innerHTML =
      `<div class="sup-head"><b>${esc(m.subject || "Support request")}</b> <span class="status">${esc(m.status)}</span></div>` +
      `<p class="muted small">${esc(m.body)}</p>` +
      (m.reply ? `<p class="sup-reply">→ ${esc(m.reply)}</p>` : `<p class="muted small">Awaiting reply…</p>`);
    box.appendChild(d);
  });
}

/* ---- ops view ---- */
function showPanel(name) {
  document.querySelectorAll(".panel").forEach((p) => (p.style.display = "none"));
  el(name).style.display = "";
  document.querySelectorAll("#opsNav li").forEach((li) => li.classList.toggle("active", li.dataset.panel === name));
}

function renderOpsOrders(list) {
  const box = el("opsOrdersList");
  box.innerHTML = "";
  const flow = ["pending", "in_progress", "delivered"];
  (list || []).forEach((o) => {
    const cur = o.fulfillment_status || "pending";
    const i = Math.max(0, flow.indexOf(cur));
    const next = flow[Math.min(i + 1, flow.length - 1)];
    const d = document.createElement("div");
    d.className = "ops-row";
    d.innerHTML =
      `<div class="ops-main"><b>${esc(o.order_id)}</b><span class="muted small">${esc(o.customer_id)} · ${money(o.amount_cents)} · ${esc(o.status)}</span></div>` +
      `<div class="ops-side"><span class="status">${esc(cur)}</span>` +
      (next !== cur ? `<button class="btn ghost small" data-fid="${esc(o.order_id)}" data-next="${next}">→ ${next}</button>` : "") +
      `</div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-fid]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/orders/${b.dataset.fid}/fulfill`, { method: "POST", body: JSON.stringify({ status: b.dataset.next }) });
      loadOps();
    }));
}

function renderOpsSupport(list) {
  const box = el("opsSupportList");
  box.innerHTML = "";
  if (!list || !list.length) { box.innerHTML = '<p class="muted">No open messages.</p>'; return; }
  list.forEach((m) => {
    const d = document.createElement("div");
    d.className = "ops-row";
    d.innerHTML =
      `<div class="ops-main"><b>${esc(m.subject || "Support request")}</b><span class="muted small">${esc(m.email)} · ${esc(m.customer_id)}</span><p class="muted small">${esc(m.body)}</p></div>` +
      `<div class="ops-side"><textarea class="reply" placeholder="Reply…"></textarea><button class="btn small" data-mid="${esc(m.message_id)}">Reply</button></div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-mid]").forEach((b) =>
    b.addEventListener("click", async () => {
      const ta = b.parentElement.querySelector(".reply");
      if (!ta.value.trim()) { alert("Type a reply."); return; }
      await api(`/ops/support/${b.dataset.mid}/reply`, { method: "POST", body: JSON.stringify({ reply: ta.value }) });
      loadOps();
    }));
}

function renderOpsContracts(list) {
  const box = el("opsContractsList");
  box.innerHTML = "";
  if (!list || !list.length) { box.innerHTML = '<p class="muted">No contracts yet.</p>'; return; }
  list.forEach((c) => {
    const d = document.createElement("div");
    d.className = "ops-row";
    const when = new Date((c.accepted_at || 0) * 1000).toLocaleString();
    d.innerHTML =
      `<div class="ops-main"><b>${esc(c.customer_id)}</b><span class="muted small">${esc(c.contract_type)} v${esc(c.version)} · ${when} · ${esc(c.ip)}</span></div>`;
    box.appendChild(d);
  });
}

function renderOpsProducts(list) {
  const box = el("opsProductsList");
  box.innerHTML = "";
  (list || []).forEach((p) => {
    const d = document.createElement("div");
    d.className = "ops-row";
    const monthly = Number(p.monthly_cents || 0);
    d.innerHTML =
      `<div class="ops-main"><b>${esc(p.name)}</b><span class="muted small">${esc(p.product_id)} · ${esc(p.kind)} · ${money(p.price_cents)}${monthly ? " + " + money(monthly) + "/mo" : ""}</span></div>` +
      `<div class="ops-side"><button class="btn ghost small" data-del="${esc(p.product_id)}">Delete</button></div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/products/${b.dataset.del}`, { method: "DELETE" });
      loadOps();
    }));
}

function renderOpsUsers(list) {
  const box = el("opsUsersList");
  box.innerHTML = "";
  (list || []).forEach((u) => {
    const d = document.createElement("div");
    d.className = "ops-row";
    d.innerHTML =
      `<div class="ops-main"><b>${esc(u.email || u.username)}</b><span class="muted small">${esc(u.username)} · ${esc(u.status)}</span></div>` +
      `<div class="ops-side">
        <button class="btn ghost small" data-role="${esc(u.username)}" data-g="employees">+ employee</button>
        <button class="btn ghost small" data-role="${esc(u.username)}" data-g="admins">+ admin</button>
        <button class="btn ghost small" data-role="${esc(u.username)}" data-g="customers">+ customer</button>
      </div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-role]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/users/${encodeURIComponent(b.dataset.role)}/role`, {
        method: "POST", body: JSON.stringify({ group: b.dataset.g, action: "add" }),
      });
      alert("Role assigned.");
    }));
}

function renderOpsFinance(f) {
  el("opsFinanceBox").innerHTML =
    `<p>Total charges: <b>${f.total_charges}</b></p>` +
    `<p>Total revenue: <b>${money(f.total_revenue_cents)}</b></p>` +
    `<p>By provider: ${Object.entries(f.by_provider_cents || {}).map(([k, v]) => `${esc(k)} ${money(v)}`).join(" · ") || "—"}</p>`;
}

async function loadOps() {
  const [orders, support, contracts, products, users, finance] = await Promise.all([
    api("/ops/orders"), api("/ops/support"), api("/ops/contracts"),
    api("/products"), api("/ops/users"), api("/ops/finance"),
  ]);
  renderOpsOrders(orders);
  renderOpsSupport(support);
  renderOpsContracts(contracts);
  renderOpsProducts(products.products || products);
  renderOpsUsers(users.users || []);
  renderOpsFinance(finance);
}

/* ---- view switching ---- */
function setView(view) {
  const ops = view === "ops";
  el("customerView").style.display = ops ? "none" : "";
  el("opsView").style.display = ops ? "" : "none";
  el("opsToggle").textContent = ops ? "My account" : "Ops console";
}

/* ---- init ---- */
async function init() {
  parseHash();
  const t = tokens();
  if (!t) { login(); return; }
  const claims = decodeJwt(t.id);
  el("whoami").textContent = claims.email || claims["cognito:username"] || "";
  const groups = groupsOf(claims);
  role = groups.includes("admins") ? "admin" : groups.includes("employees") ? "employee" : "customer";
  el("roleBadge").textContent = role;

  const isOps = role === "admin" || role === "employee";
  el("opsToggle").style.display = isOps ? "" : "none";
  document.querySelectorAll(".adminOnly").forEach((n) => (n.style.display = role === "admin" ? "" : "none"));

  // catalog (shared)
  const prod = await api("/products");
  catalog = prod.products || [];

  renderShop();
  await renderTerms();
  await refreshCustomer();
  await refreshSupport();
  bubble("Hi — I'm your assistant. Ask me anything about your purchase or our services.", "ai");

  if (isOps) {
    setView("customer");
    await loadOps();
  }
}

/* ---- event wiring ---- */
el("chatform").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = el("chatinput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  bubble(esc(q), "user");
  const r = await api("/chat", { method: "POST", body: JSON.stringify({ message: q }) });
  bubble(esc(r.answer || "Sorry, something went wrong."), "ai");
});

el("supportForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = el("supportInput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  await api("/support", { method: "POST", body: JSON.stringify({ subject: "Support request", message: q }) });
  refreshSupport();
});

el("acceptTerms").addEventListener("click", async () => {
  await api("/contracts/accept", { method: "POST", body: JSON.stringify({ type: "terms" }) });
  renderTerms();
});

el("productForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    product_id: el("pfId").value.trim(),
    name: el("pfName").value.trim(),
    price_cents: Math.round(Number(el("pfPrice").value || 0) * 100),
    monthly_cents: Math.round(Number(el("pfMonthly").value || 0) * 100),
    kind: el("pfKind").value,
    description: "",
    recurring: Number(el("pfMonthly").value || 0) > 0,
  };
  if (!body.product_id || !body.name) { alert("product_id and name required"); return; }
  await api("/ops/products", { method: "POST", body: JSON.stringify(body) });
  ["pfId", "pfName", "pfPrice", "pfMonthly"].forEach((id) => (el(id).value = ""));
  loadOps();
});

el("opsToggle").addEventListener("click", () => {
  const toOps = el("opsToggle").textContent === "Ops console";
  setView(toOps ? "ops" : "customer");
});

el("opsNav").addEventListener("click", (e) => {
  const li = e.target.closest("li");
  if (li && li.dataset.panel) showPanel(li.dataset.panel);
});

el("modalCancel").addEventListener("click", closeCheckout);
el("modalConfirm").addEventListener("click", completePurchase);
el("modal").addEventListener("click", (e) => { if (e.target === el("modal")) closeCheckout(); });
el("logout").addEventListener("click", logout);

init();
