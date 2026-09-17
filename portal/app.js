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

/* ---- API ---- */
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

/* ---- render ---- */
function renderEntitlements(ents) {
  const ul = document.getElementById("entitlements");
  ul.innerHTML = "";
  if (!ents || !ents.length) {
    ul.innerHTML = '<li class="muted">No purchases yet.</li>';
    return;
  }
  ents.forEach((e) => {
    const li = document.createElement("li");
    li.className = "ent";
    li.innerHTML = `<span class="dot"></span>${e.product_id}`;
    ul.appendChild(li);
  });
}

function renderOrders(orders) {
  const ul = document.getElementById("orders");
  ul.innerHTML = "";
  if (!orders || !orders.length) {
    ul.innerHTML = '<li class="muted">No orders yet.</li>';
    return;
  }
  orders.forEach((o) => {
    const li = document.createElement("li");
    li.className = "order";
    li.innerHTML = `<span>${o.order_id}</span><span class="status">${o.status || "pending"}</span>`;
    ul.appendChild(li);
  });
}

function renderBilling(b) {
  const el = document.getElementById("billing");
  const link = document.getElementById("portalLink");
  if (b && b.portal_url) {
    el.textContent = "Manage invoices, payment methods, and subscriptions.";
    link.style.display = "inline-flex";
    link.href = b.portal_url;
  } else {
    el.textContent = "Billing portal will appear once a payment provider is connected.";
  }
}

function bubble(html, cls) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.innerHTML = html;
  document.getElementById("chatlog").appendChild(d);
  document.getElementById("chatlog").scrollTop = 1e9;
}

/* ---- init ---- */
async function init() {
  parseHash();
  const t = tokens();
  if (!t) { login(); return; }
  const claims = decodeJwt(t.id);
  document.getElementById("whoami").textContent = claims.email || claims["cognito:username"] || "";
  const groups = claims["cognito:groups"] || ["customers"];
  const role = groups.includes("admins") ? "admin" : groups.includes("employees") ? "employee" : "customer";
  document.getElementById("roleBadge").textContent = role;

  const [ents, orders, billing] = await Promise.all([
    api("/entitlements"), api("/orders"), api("/billing"),
  ]);
  renderEntitlements(ents);
  renderOrders(orders);
  renderBilling(billing);

  bubble("Hi — I'm your assistant. Ask me anything about your purchase or our services.", "ai");
}

document.getElementById("chatform").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chatinput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  bubble(q, "user");
  const r = await api("/chat", { method: "POST", body: JSON.stringify({ message: q }) });
  bubble(r.answer || "Sorry, something went wrong.", "ai");
});

document.getElementById("logout").addEventListener("click", logout);

init();
