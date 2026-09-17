/* ---- CONFIG ---- */
const CONFIG = {
  apiUrl: "https://fj2i0k2wvg.execute-api.us-east-2.amazonaws.com",
};

/* ---- Cognito (custom auth UI via amazon-cognito-identity-js) ---- */
const userPool = new AmazonCognitoIdentity.CognitoUserPool({
  UserPoolId: "us-east-2_Ft3gk0RP8",
  ClientId: "532f118f0hllb65dammopv9lgv",
});

function decodeJwt(token) {
  try { return JSON.parse(atob(token.split(".")[1])); } catch (_) { return {}; }
}

function currentCognitoUser() { return userPool.getCurrentUser(); }

function getSession() {
  return new Promise((resolve, reject) => {
    const u = currentCognitoUser();
    if (!u) return reject(new Error("not logged in"));
    u.getSession((err, session) => (err ? reject(err) : resolve(session)));
  });
}

async function getAccessToken() {
  const s = await getSession();
  return s.getAccessToken().getJwtToken();
}

function signIn(email, password) {
  return new Promise((resolve, reject) => {
    const details = new AmazonCognitoIdentity.AuthenticationDetails({ Username: email, Password: password });
    new AmazonCognitoIdentity.CognitoUser({ Username: email, Pool: userPool })
      .authenticateUser(details, {
        onSuccess: resolve,
        onFailure: reject,
        newPasswordRequired: () => reject(new Error("Password change required — contact support.")),
      });
  });
}

function signUp(email, password) {
  return new Promise((resolve, reject) => {
    userPool.signUp(email, password, [{ Name: "email", Value: email }], null,
      (err, result) => (err ? reject(err) : resolve(result)));
  });
}

function confirmSignUp(email, code) {
  return new Promise((resolve, reject) => {
    new AmazonCognitoIdentity.CognitoUser({ Username: email, Pool: userPool })
      .confirmRegistration(code, true, (err, result) => (err ? reject(err) : resolve(result)));
  });
}

function forgotPassword(email) {
  return new Promise((resolve, reject) => {
    new AmazonCognitoIdentity.CognitoUser({ Username: email, Pool: userPool })
      .forgotPassword({ onSuccess: resolve, onFailure: reject });
  });
}

function confirmNewPassword(email, code, newPassword) {
  return new Promise((resolve, reject) => {
    new AmazonCognitoIdentity.CognitoUser({ Username: email, Pool: userPool })
      .confirmPassword(code, newPassword, { onSuccess: resolve, onFailure: reject });
  });
}

function logout() {
  const u = currentCognitoUser();
  if (u) u.signOut();
  showAuth();
}

async function api(path, opts = {}) {
  const token = await getAccessToken();
  const res = await fetch(CONFIG.apiUrl + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
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
  (thread || []).forEach((c) => {
    const d = document.createElement("div");
    d.className = "sup " + c.status;
    const msgs = (c.messages || []).map((m) =>
      `<div class="sup-msg ${m.sender}"><span class="sup-alias">${esc(m.alias)}</span><p>${esc(m.body)}</p></div>`
    ).join("");
    d.innerHTML =
      `<div class="sup-head"><b>${esc(c.subject || "Support")}</b> <span class="status">${esc(c.status)}</span></div>` +
      msgs +
      (c.status === "open" ? `<p class="muted small">${esc(c.manager)} will reply here.</p>` : "");
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
  if (!list || !list.length) { box.innerHTML = '<p class="muted">No open conversations.</p>'; return; }
  list.forEach((c) => {
    const d = document.createElement("div");
    d.className = "ops-row";
    const msgs = (c.messages || []).slice(-3).map((m) =>
      `<div class="muted small"><b>${esc(m.alias)}</b>: ${esc(m.body)}</div>`
    ).join("");
    d.innerHTML =
      `<div class="ops-main"><b>${esc(c.customer_alias)}</b><span class="muted small">${esc(c.subject || "Support")}${c.manager_name ? " · " + esc(c.manager_name) : " · unassigned"}</span><div class="ops-msgs">${msgs}</div></div>` +
      `<div class="ops-side"><textarea class="reply" placeholder="Reply…"></textarea><div class="ops-actions"><button class="btn small" data-mid="${esc(c.conversation_id)}">Reply</button><button class="btn ghost small" data-res="${esc(c.conversation_id)}">Resolve</button></div></div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-mid]").forEach((b) =>
    b.addEventListener("click", async () => {
      const ta = b.closest(".ops-row").querySelector(".reply");
      if (!ta.value.trim()) { alert("Type a reply."); return; }
      await api(`/ops/support/${b.dataset.mid}/reply`, { method: "POST", body: JSON.stringify({ reply: ta.value }) });
      loadOps();
    }));
  box.querySelectorAll("[data-res]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/support/${b.dataset.res}/resolve`, { method: "POST" });
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
        <button class="btn ghost small" data-role="${esc(u.username)}" data-g="contractors">+ contractor</button>
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

function renderOpsLeads(list) {
  const box = el("opsLeadsList");
  box.innerHTML = "";
  const flow = ["new", "contacted", "qualified", "won"];
  (list || []).forEach((l) => {
    const cur = l.status || "new";
    const i = Math.max(0, flow.indexOf(cur));
    const next = flow[Math.min(i + 1, flow.length - 1)];
    const when = new Date((l.created_at || 0) * 1000).toLocaleDateString();
    const d = document.createElement("div");
    d.className = "ops-row";
    d.innerHTML =
      `<div class="ops-main"><b>${esc(l.name)}</b><span class="muted small">${esc(l.email)}${l.company ? " · " + esc(l.company) : ""} · ${when} · ${esc(l.interest || "")}</span>${l.message ? `<div class="muted small" style="margin-top:4px">${esc(l.message)}</div>` : ""}</div>` +
      `<div class="ops-side"><span class="status">${esc(cur)}</span>` +
      (next !== cur ? `<button class="btn ghost small" data-lid="${esc(l.lead_id)}" data-next="${next}">→ ${next}</button>` : "") +
      (cur !== "lost" ? `<button class="btn ghost small" data-lost="${esc(l.lead_id)}">lost</button>` : "") +
      `</div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-lid]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/leads/${b.dataset.lid}/status`, { method: "POST", body: JSON.stringify({ status: b.dataset.next }) });
      loadOps();
    }));
  box.querySelectorAll("[data-lost]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/leads/${b.dataset.lost}/status`, { method: "POST", body: JSON.stringify({ status: "lost" }) });
      loadOps();
    }));
}

function renderAnalytics(a) {
  const box = el("opsAnalyticsBox");
  box.innerHTML = "";
  const card = (num, lbl) => `<div class="an-card"><div class="an-num">${num}</div><div class="an-lbl">${lbl}</div></div>`;
  const byStatus = (obj) => Object.entries(obj || {}).map(([k, v]) => `${esc(k)}: ${v}`).join(" · ") || "—";
  box.innerHTML =
    `<div class="an-grid">
      ${card(money(a.revenue_cents), "Revenue")}
      ${card(a.charges, "Charges")}
      ${card(a.orders.total, "Orders")}
      ${card(a.leads.total, "Leads")}
      ${card(a.contractors.total, "Contractors")}
      ${card(a.support_open, "Open tickets")}
    </div>
    <div class="an-sec"><h3>Orders</h3><div class="muted small">${byStatus(a.orders.by_status)} · fulfillment: ${byStatus(a.orders.by_fulfillment)}</div></div>
    <div class="an-sec"><h3>Leads</h3><div class="muted small">${byStatus(a.leads.by_status)}</div></div>
    <div class="an-sec"><h3>Contractors</h3><div class="muted small">${byStatus(a.contractors.by_status)}</div></div>
    <div class="an-sec"><h3>Revenue by provider</h3><div class="muted small">${Object.entries(a.by_provider_cents || {}).map(([k, v]) => `${esc(k)}: ${money(v)}`).join(" · ") || "—"}</div></div>`;
}

let SUPPLY_ROLES = {};

function renderSupply(data, roster) {
  const box = el("opsSupplyBox");
  box.innerHTML = "";
  const roles = data.roles || {};
  SUPPLY_ROLES = roles;
  // populate the role dropdown for the add form
  const sel = el("roRole");
  if (sel) {
    sel.innerHTML = "";
    Object.entries(roles).forEach(([k, r]) => {
      const o = document.createElement("option");
      o.value = k;
      o.textContent = r.title;
      sel.appendChild(o);
    });
  }
  // coverage: count roster by role + status
  const coverage = {};
  (roster || []).forEach((c) => {
    coverage[c.role] = coverage[c.role] || { hired: 0, assigned: 0, interviewing: 0 };
    if (coverage[c.role][c.status] != null) coverage[c.role][c.status]++;
  });
  (data.supply || []).forEach((g) => {
    const sec = document.createElement("div");
    sec.className = "supply-sec";
    const head = document.createElement("div");
    head.className = "supply-cat";
    head.textContent = g.category;
    sec.appendChild(head);
    (g.items || []).forEach((it) => {
      const row = document.createElement("div");
      row.className = "supply-row";
      const roleHtml = (it.roles || []).map((rk) => {
        const r = roles[rk] || {};
        const cost = (r.fiverr && r.fiverr !== "—") ? r.fiverr : (r.upwork || "");
        const cov = coverage[rk];
        const parts = [];
        if (cov) {
          if (cov.hired) parts.push(cov.hired + " hired");
          if (cov.assigned) parts.push(cov.assigned + " assigned");
          if (cov.interviewing) parts.push(cov.interviewing + " interviewing");
        }
        const covHtml = parts.length ? `<span class="cov">${parts.join(" · ")}</span>` : "";
        return `<span class="supply-role"><b>${esc(r.title || rk)}</b><span>${esc(r.gig || "")}</span><span class="cost">${esc(cost)}</span>${covHtml}</span>`;
      }).join("");
      row.innerHTML =
        `<div class="supply-item"><b>${esc(it.name)}</b><span class="sell">${esc(it.sell || "")}</span></div>` +
        `<div class="supply-roles">${roleHtml}</div>`;
      sec.appendChild(row);
    });
    box.appendChild(sec);
  });
}

function renderRoster(roster) {
  const box = el("opsRosterBox");
  box.innerHTML = "";
  if (!roster || !roster.length) {
    box.innerHTML = '<p class="muted small">No contractors yet — add one above, then advance it from interviewing → hired → assigned.</p>';
    return;
  }
  const flow = ["interviewing", "hired", "assigned"];
  roster.forEach((c) => {
    const cur = c.status || "interviewing";
    const i = flow.indexOf(cur);
    const next = flow[Math.min(i + 1, flow.length - 1)];
    const roleTitle = (SUPPLY_ROLES[c.role] || {}).title || c.role;
    const d = document.createElement("div");
    d.className = "roster-row";
    d.innerHTML =
      `<div class="roster-main"><b>${esc(c.name)}</b><span class="muted small">${esc(roleTitle)} · ${esc(c.platform)} · ${esc(c.price)}${c.notes ? " · " + esc(c.notes) : ""}</span></div>` +
      `<div class="roster-side"><span class="st st-${cur}">${esc(cur)}</span>` +
      (next !== cur ? `<button class="btn ghost small" data-rid="${esc(c.contractor_id)}" data-next="${next}">→ ${next}</button>` : "") +
      `<button class="btn ghost small" data-rdel="${esc(c.contractor_id)}">×</button></div>`;
    box.appendChild(d);
  });
  box.querySelectorAll("[data-rid]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/roster/${b.dataset.rid}/status`, { method: "POST", body: JSON.stringify({ status: b.dataset.next }) });
      refreshSupply();
    }));
  box.querySelectorAll("[data-rdel]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/ops/roster/${b.dataset.rdel}`, { method: "DELETE" });
      refreshSupply();
    }));
}

async function refreshSupply() {
  const [sup, roster] = await Promise.all([api("/ops/supply"), api("/ops/roster")]);
  renderSupply(sup, roster);
  renderRoster(roster);
}

el("roAdd").addEventListener("click", async () => {
  const name = el("roName").value.trim();
  const role = el("roRole").value;
  if (!name || !role) { alert("name and role required"); return; }
  await api("/ops/roster", { method: "POST", body: JSON.stringify({
    name, role, platform: el("roPlatform").value.trim(),
    price: el("roPrice").value.trim(), notes: el("roNotes").value.trim(),
  }) });
  ["roName", "roPlatform", "roPrice", "roNotes"].forEach((id) => (el(id).value = ""));
  refreshSupply();
});

async function loadOps() {
  if (role === "contractor") {
    const support = await api("/ops/support");
    renderOpsSupport(support);
    return;
  }
  const [orders, support, contracts, products, users, finance, leads] = await Promise.all([
    api("/ops/orders"), api("/ops/support"), api("/ops/contracts"),
    api("/products"), api("/ops/users"), api("/ops/finance"), api("/ops/leads"),
  ]);
  renderOpsOrders(orders);
  renderOpsSupport(support);
  renderOpsContracts(contracts);
  renderOpsProducts(products.products || products);
  renderOpsUsers(users.users || []);
  renderOpsFinance(finance);
  renderOpsLeads(leads);
  if (role === "admin") {
    renderAnalytics(await api("/ops/analytics"));
    await refreshSupply();
  }
}

/* ---- view switching ---- */
function setView(view) {
  const ops = view === "ops";
  el("customerView").style.display = ops ? "none" : "";
  el("opsView").style.display = ops ? "" : "none";
  el("opsToggle").textContent = ops ? "My account" : "Ops console";
}

/* ---- auth UI ---- */
function showAuthForm(name) {
  ["signinForm", "confirmForm", "forgotForm", "resetForm"].forEach((id) => {
    el(id).style.display = (id === name) ? "" : "none";
  });
  el("authMsg").textContent = "";
}

function authMsg(msg, isErr) {
  el("authMsg").textContent = msg;
  el("authMsg").style.color = isErr ? "#ff7b9c" : "var(--muted)";
}

function showAuth() {
  el("authView").style.display = "flex";
  el("customerView").style.display = "none";
  el("opsView").style.display = "none";
  el("opsToggle").style.display = "none";
  showAuthForm("signinForm");
}

async function showApp(idToken) {
  el("authView").style.display = "none";
  el("customerView").style.display = "";
  el("opsView").style.display = "none";
  const claims = decodeJwt(idToken);
  el("whoami").textContent = claims.email || claims["cognito:username"] || "";
  const groups = groupsOf(claims);
  role = groups.includes("admins") ? "admin"
       : groups.includes("employees") ? "employee"
       : groups.includes("contractors") ? "contractor"
       : "customer";
  el("roleBadge").textContent = role;

  const isOps = role === "admin" || role === "employee" || role === "contractor";
  el("opsToggle").style.display = isOps ? "" : "none";
  document.querySelectorAll(".adminOnly").forEach((n) => (n.style.display = role === "admin" ? "" : "none"));
  document.querySelectorAll(".employeeOnly").forEach((n) => (n.style.display = (role === "admin" || role === "employee") ? "" : "none"));

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
    if (role === "contractor") { showPanel("opsSupport"); }
    await loadOps();
  }
}

/* ---- init ---- */
async function init() {
  const qp = new URLSearchParams(location.search);
  if (qp.get("email")) el("siEmail").value = qp.get("email");
  const u = currentCognitoUser();
  if (!u) { showAuth(); return; }
  try {
    const s = await getSession();
    await showApp(s.getIdToken().getJwtToken());
  } catch (e) {
    showAuth();
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

el("inviteForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = el("invEmail").value.trim();
  const role = el("invRole").value;
  if (!email) { alert("Enter an email."); return; }
  const r = await api("/ops/users", { method: "POST", body: JSON.stringify({ email, role }) });
  if (r.error) { el("inviteResult").textContent = "Error: " + r.error; return; }
  el("inviteResult").innerHTML = `<b>${esc(r.email)}</b> (${esc(r.role)}) — password: <b>${esc(r.password)}</b>`;
  el("invEmail").value = "";
  loadOps();
});

el("opsToggle").addEventListener("click", () => {
  const toOps = el("opsToggle").textContent === "Ops console";
  setView(toOps ? "ops" : "customer");
});

el("opsChatform").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = el("opsChatinput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  const log = el("opsChatlog");
  const add = (html, cls) => {
    const d = document.createElement("div");
    d.className = "msg " + cls;
    d.innerHTML = html;
    log.appendChild(d);
    log.scrollTop = 1e9;
  };
  add(esc(q), "user");
  const r = await api("/staff-chat", { method: "POST", body: JSON.stringify({ message: q }) });
  add(esc(r.answer || "Sorry, something went wrong."), "ai");
});

el("opsNav").addEventListener("click", (e) => {
  const li = e.target.closest("li");
  if (li && li.dataset.panel) showPanel(li.dataset.panel);
});

el("modalCancel").addEventListener("click", closeCheckout);
el("modalConfirm").addEventListener("click", completePurchase);
el("modal").addEventListener("click", (e) => { if (e.target === el("modal")) closeCheckout(); });

/* ---- auth form handlers ---- */
el("signinForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = el("siEmail").value.trim();
  const pw = el("siPassword").value;
  if (!email || !pw) return;
  authMsg("Signing in…");
  try {
    await signIn(email, pw);
    const s = await getSession();
    await showApp(s.getIdToken().getJwtToken());
  } catch (err) {
    authMsg(err.message || "Sign-in failed.", true);
  }
});

el("confirmForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = el("cfEmail").value.trim();
  const code = el("cfCode").value.trim();
  if (!email || !code) return;
  authMsg("Verifying…");
  try {
    await confirmSignUp(email, code);
    el("siEmail").value = email;
    showAuthForm("signinForm");
    authMsg("Email verified — sign in.");
  } catch (err) {
    authMsg(err.message || "Confirmation failed.", true);
  }
});

el("forgotForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = el("fpEmail").value.trim();
  if (!email) return;
  authMsg("Sending code…");
  try {
    await forgotPassword(email);
    el("rsEmail").value = email;
    showAuthForm("resetForm");
    authMsg("Check your email for a reset code.");
  } catch (err) {
    authMsg(err.message || "Request failed.", true);
  }
});

el("resetForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = el("rsEmail").value.trim();
  const code = el("rsCode").value.trim();
  const pw = el("rsPassword").value;
  if (!email || !code || !pw) return;
  authMsg("Setting password…");
  try {
    await confirmNewPassword(email, code, pw);
    el("siEmail").value = email;
    showAuthForm("signinForm");
    authMsg("Password reset — sign in.");
  } catch (err) {
    authMsg(err.message || "Reset failed.", true);
  }
});

el("toForgot").addEventListener("click", (e) => { e.preventDefault(); showAuthForm("forgotForm"); });
["toSignin3", "toSignin4", "toSignin5"].forEach((id) =>
  el(id).addEventListener("click", (e) => { e.preventDefault(); showAuthForm("signinForm"); }));

el("logout").addEventListener("click", logout);

init();
