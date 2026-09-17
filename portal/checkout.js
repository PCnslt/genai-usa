/* ---- checkout (white-label mock payment + rich signup) ---- */
const API = "https://fj2i0k2wvg.execute-api.us-east-2.amazonaws.com";
const money = (c) => "$" + (Number(c || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const $ = (id) => document.getElementById(id);

const params = new URLSearchParams(location.search);
const productId = params.get("product") || "";
let product = null;

function renderProduct() {
  $("coName").textContent = product.name;
  $("coTag").textContent = product.category || (product.kind === "plan" ? "Retainer" : product.kind === "service" ? "Service" : "Product");
  $("coDesc").textContent = product.description || "";
  const monthly = Number(product.monthly_cents || 0);
  const line = monthly
    ? `${money(product.price_cents)} one-time + ${money(monthly)}/month`
    : `${money(product.price_cents)}${product.recurring ? "/month" : " one-time"}`;
  $("coPrice").textContent = line;
  $("coPayAmount").textContent = money(product.price_cents) + (monthly ? " + " + money(monthly) + "/mo" : "");
}

function showError(msg) {
  const e = $("coError");
  e.textContent = msg;
  e.style.display = msg ? "block" : "none";
}

async function init() {
  if (!productId) {
    $("coName").textContent = "No product selected";
    $("coDesc").textContent = "Pick a service, product, or plan from the site first.";
    return;
  }
  try {
    const r = await fetch(API + "/catalog");
    const data = await r.json();
    const list = data.products || [];
    product = list.find((p) => p.product_id === productId);
    if (!product) {
      $("coName").textContent = "Product not found";
      $("coDesc").textContent = "That product no longer exists. Browse the site for current offerings.";
      $("coSubmit").disabled = true;
      return;
    }
    renderProduct();
    $("coSubmit").disabled = false;
  } catch (err) {
    $("coName").textContent = "Couldn't load product";
    $("coDesc").textContent = "Network error — refresh to try again.";
  }
}

$("checkoutForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!product) return;
  showError("");

  const email = $("coEmail").value.trim();
  const password = $("coPassword").value;
  const name = $("coName").value.trim();
  const card = $("coCard").value.trim();
  const exp = $("coExp").value.trim();
  const cvc = $("coCvc").value.trim();

  if (!email || !/@/.test(email)) return showError("Enter a valid email.");
  if (password.length < 8) return showError("Password must be at least 8 characters.");
  if (!$("coAgree").checked) return showError("Please accept the Terms of Service to continue.");
  // mock card validation (kept light on purpose)
  if (!card || card.replace(/\D/g, "").length < 12) return showError("Enter a valid card number.");
  if (!exp || !/^\d{2}\s*\/\s*\d{2}$/.test(exp)) return showError("Enter expiry as MM / YY.");
  if (!cvc || !/^\d{3,4}$/.test(cvc)) return showError("Enter a valid CVC.");

  const btn = $("coSubmit");
  btn.disabled = true;
  btn.textContent = "Processing…";
  try {
    const r = await fetch(API + "/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: product.product_id,
        email, password,
        name,
        company: $("coCompany").value.trim(),
        phone: $("coPhone").value.trim(),
        role: $("coRole").value.trim(),
        needs: $("coNeeds").value.trim(),
        agree: true,
      }),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      showError(data.error || "Checkout failed — try again.");
      btn.disabled = false;
      btn.innerHTML = 'Pay <span id="coPayAmount">' + $("coPayAmount").textContent + "</span>";
      return;
    }
    // success
    $("coFormCard").style.display = "none";
    $("coSuccess").style.display = "block";
    $("coSuccessMsg").textContent =
      `Order ${data.order_id} placed for ${data.product}. ` +
      `Your account for ${data.email} is ready — sign in with the password you just created.`;
    $("coSignin").href = "/app/?email=" + encodeURIComponent(data.email);
  } catch (err) {
    showError("Network error — please try again.");
    btn.disabled = false;
  }
});

init();
