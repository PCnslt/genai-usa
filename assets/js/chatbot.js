/* Generative AI — public sales chatbot widget (marketing site).
   Self-contained: injects its own CSS + DOM, talks to POST /chat-public. */
(function () {
  var API = "https://fj2i0k2wvg.execute-api.us-east-2.amazonaws.com";

  var CSS =
    ".gai-launcher{position:fixed;right:22px;bottom:22px;z-index:9998;width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;" +
    "background:linear-gradient(120deg,#4f7cff,#9b5cff);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 30px rgba(79,124,255,.4);transition:transform .15s}" +
    ".gai-launcher:hover{transform:scale(1.07)}" +
    ".gai-panel{position:fixed;right:22px;bottom:88px;z-index:9999;width:340px;max-width:92vw;height:480px;max-height:70vh;display:none;flex-direction:column;" +
    "background:#0d0a18;border:1px solid rgba(155,92,255,.28);border-radius:16px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5);font-family:'Roboto',-apple-system,sans-serif}" +
    ".gai-panel.open{display:flex}" +
    ".gai-head{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:linear-gradient(120deg,#4f7cff,#9b5cff);color:#fff}" +
    ".gai-title{font-weight:500;font-size:14px}" +
    ".gai-close{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;line-height:1}" +
    ".gai-log{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}" +
    ".gai-msg{max-width:82%;padding:9px 13px;border-radius:14px;font-size:13.5px;line-height:1.5;color:#f4f3fb;white-space:normal}" +
    ".gai-msg.ai{align-self:flex-start;background:rgba(255,255,255,.06);border:1px solid rgba(155,92,255,.25);border-bottom-left-radius:4px}" +
    ".gai-msg.user{align-self:flex-end;background:linear-gradient(120deg,#4f7cff,#9b5cff);border-bottom-right-radius:4px}" +
    ".gai-form{display:flex;gap:8px;padding:12px;border-top:1px solid rgba(155,92,255,.2)}" +
    ".gai-form input{flex:1;background:transparent;border:1px solid rgba(155,92,255,.3);border-radius:9px;padding:10px 12px;color:#f4f3fb;font-family:inherit;font-size:14px;outline:none}" +
    ".gai-form input:focus{border-color:#9b5cff}" +
    ".gai-form button{background:linear-gradient(120deg,#4f7cff,#9b5cff);border:none;border-radius:9px;color:#fff;padding:0 16px;cursor:pointer;font-size:13px}" +
    ".gai-foot{text-align:center;padding:8px;font-size:11px;color:#8b87a6}";

  var style = document.createElement("style");
  style.textContent = CSS;
  document.head.appendChild(style);

  var launcher = document.createElement("button");
  launcher.className = "gai-launcher";
  launcher.setAttribute("aria-label", "Chat with us");
  launcher.innerHTML =
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

  var panel = document.createElement("div");
  panel.className = "gai-panel";
  panel.innerHTML =
    '<div class="gai-head"><div class="gai-title">Ask our AI</div><button class="gai-close" aria-label="Close">×</button></div>' +
    '<div class="gai-log"></div>' +
    '<form class="gai-form"><input placeholder="Ask about pricing, chatbots, plans…" autocomplete="off"><button type="submit">Send</button></form>' +
    '<div class="gai-foot">Generative Artificial Intelligence</div>';

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  var log = panel.querySelector(".gai-log");

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function bubble(text, cls) {
    var d = document.createElement("div");
    d.className = "gai-msg " + cls;
    d.innerHTML = esc(text).replace(/\n/g, "<br>").replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    log.appendChild(d);
    log.scrollTop = 1e9;
  }

  var SESSION_KEY = "gai_session";
  function sessionId() {
    try {
      var id = localStorage.getItem(SESSION_KEY);
      if (!id) { id = "web-" + Math.random().toString(36).slice(2, 10); localStorage.setItem(SESSION_KEY, id); }
      return id;
    } catch (e) { return "web-" + Math.random().toString(36).slice(2, 10); }
  }

  launcher.addEventListener("click", function () { panel.classList.toggle("open"); });
  panel.querySelector(".gai-close").addEventListener("click", function () { panel.classList.remove("open"); });

  bubble("Hi! I can help you pick the right AI system or plan. What are you trying to automate?", "ai");

  panel.querySelector("form").addEventListener("submit", async function (e) {
    e.preventDefault();
    var input = panel.querySelector("input");
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    bubble(q, "user");
    try {
      var r = await fetch(API + "/chat-public", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q, session_id: sessionId() }),
      });
      var j = await r.json();
      if (j.session_id) { try { localStorage.setItem(SESSION_KEY, j.session_id); } catch (e) {} }
      bubble(j.answer || "Sorry, I couldn't answer that — email hello@genai-usa.com.", "ai");
    } catch (err) {
      bubble("Sorry, I'm having trouble connecting. Email hello@genai-usa.com.", "ai");
    }
  });
})();
