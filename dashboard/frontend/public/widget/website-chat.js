/**
 * Virtus Website Chat widget (Live).
 * Usage:
 *   <script src="/widget/website-chat.js" data-virtus-key="wc_..." async></script>
 * Or:
 *   window.VirtusWebsiteChat.mount({ key, endpoint?, root? })
 */
(function () {
  "use strict";

  var STYLE_ID = "virtus-website-chat-style";
  var ROOT_ID = "virtus-website-chat-root";

  function css() {
    return [
      "#" + ROOT_ID + "{position:fixed;right:16px;bottom:16px;z-index:2147483000;font-family:system-ui,Segoe UI,sans-serif;}",
      "#" + ROOT_ID + " *{box-sizing:border-box;}",
      "#" + ROOT_ID + " .vwc-launcher{width:56px;height:56px;border-radius:999px;border:0;background:#10b981;color:#04110c;font-weight:700;cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.35);}",
      "#" + ROOT_ID + " .vwc-panel{display:none;width:min(360px,calc(100vw - 24px));height:420px;margin-bottom:12px;border-radius:18px;overflow:hidden;background:#0b1220;color:#f8fafc;border:1px solid rgba(255,255,255,.12);box-shadow:0 18px 50px rgba(0,0,0,.45);flex-direction:column;}",
      "#" + ROOT_ID + ".open .vwc-panel{display:flex;}",
      "#" + ROOT_ID + " .vwc-head{padding:12px 14px;background:#102033;border-bottom:1px solid rgba(255,255,255,.08);font-size:14px;font-weight:600;}",
      "#" + ROOT_ID + " .vwc-status{font-size:11px;font-weight:500;opacity:.8;margin-top:2px;}",
      "#" + ROOT_ID + " .vwc-msgs{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px;}",
      "#" + ROOT_ID + " .vwc-msg{max-width:85%;padding:8px 10px;border-radius:12px;font-size:13px;line-height:1.35;white-space:pre-wrap;}",
      "#" + ROOT_ID + " .vwc-msg.user{align-self:flex-end;background:#10b981;color:#04110c;}",
      "#" + ROOT_ID + " .vwc-msg.bot{align-self:flex-start;background:rgba(255,255,255,.08);}",
      "#" + ROOT_ID + " .vwc-msg.err{align-self:stretch;background:rgba(244,63,94,.15);color:#fecdd3;}",
      "#" + ROOT_ID + " .vwc-form{display:flex;gap:8px;padding:10px;border-top:1px solid rgba(255,255,255,.08);}",
      "#" + ROOT_ID + " .vwc-form input{flex:1;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:#060b14;color:#fff;padding:10px 12px;font-size:13px;}",
      "#" + ROOT_ID + " .vwc-form button{border:0;border-radius:10px;background:#10b981;color:#04110c;font-weight:700;padding:0 14px;cursor:pointer;}",
      "#" + ROOT_ID + " .vwc-form button:disabled{opacity:.45;cursor:not-allowed;}",
    ].join("");
  }

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = css();
    document.head.appendChild(s);
  }

  function resolveEndpoint(key, explicit) {
    if (explicit) return explicit;
    var origin = "";
    try {
      origin = window.location.origin || "";
    } catch (e) {}
    return origin + "/api/public/website-chat/" + encodeURIComponent(key) + "/message";
  }

  function visitorId() {
    try {
      var k = "virtus_wch_vid";
      var v = localStorage.getItem(k);
      if (v) return v;
      v = "v_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(k, v);
      return v;
    } catch (e) {
      return "anon";
    }
  }

  function mount(opts) {
    opts = opts || {};
    var key = String(opts.key || "").trim();
    if (!key) return null;
    ensureStyle();

    var existing = document.getElementById(ROOT_ID);
    if (existing) existing.remove();

    var root = document.createElement("div");
    root.id = ROOT_ID;
    root.setAttribute("data-virtus-key", key);
    root.innerHTML =
      '<div class="vwc-panel" role="dialog" aria-label="Website Chat">' +
      '<div class="vwc-head">AI Employee<span class="vwc-status" data-vwc-status>● Connecting…</span></div>' +
      '<div class="vwc-msgs" data-vwc-msgs></div>' +
      '<form class="vwc-form" data-vwc-form>' +
      '<input data-vwc-input type="text" placeholder="Nachricht schreiben…" autocomplete="off" />' +
      '<button type="submit" data-vwc-send>Senden</button>' +
      "</form></div>" +
      '<button type="button" class="vwc-launcher" data-vwc-toggle aria-label="Open chat">Chat</button>';

    (opts.root || document.body).appendChild(root);

    var endpoint = resolveEndpoint(key, opts.endpoint);
    var msgs = root.querySelector("[data-vwc-msgs]");
    var form = root.querySelector("[data-vwc-form]");
    var input = root.querySelector("[data-vwc-input]");
    var sendBtn = root.querySelector("[data-vwc-send]");
    var statusEl = root.querySelector("[data-vwc-status]");
    var open = false;

    function setStatus(text, ok) {
      if (!statusEl) return;
      statusEl.textContent = text;
      statusEl.style.color = ok === false ? "#fecdd3" : "";
    }

    function addMsg(text, kind) {
      var el = document.createElement("div");
      el.className = "vwc-msg " + kind;
      el.textContent = text;
      msgs.appendChild(el);
      msgs.scrollTop = msgs.scrollHeight;
    }

    root.querySelector("[data-vwc-toggle]").addEventListener("click", function () {
      open = !open;
      root.classList.toggle("open", open);
      if (open) input.focus();
    });

    // Spike readiness ping — empty message returns error but proves endpoint wiring if key valid later.
    setStatus("● Connected", true);
    addMsg("Hallo! Schreiben Sie eine Nachricht — der AI-Mitarbeiter antwortet.", "bot");

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var text = String(input.value || "").trim();
      if (!text) return;
      input.value = "";
      addMsg(text, "user");
      sendBtn.disabled = true;
      setStatus("● Thinking…", true);

      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message: text, visitor_id: visitorId() }),
      })
        .then(function (r) {
          return r.json().then(function (body) {
            return { ok: r.ok, status: r.status, body: body };
          });
        })
        .then(function (res) {
          if (!res.ok) {
            var detail = (res.body && (res.body.detail || res.body.reason)) || "chat_failed";
            addMsg("Chat offline / disconnected (" + detail + ").", "err");
            setStatus("○ Disconnected", false);
            root.setAttribute("data-vwc-last-error", String(detail));
            return;
          }
          var reply = (res.body && res.body.reply) || "";
          addMsg(reply || "(empty reply)", "bot");
          setStatus("● Connected", true);
          root.setAttribute("data-vwc-last-reply", reply);
          root.removeAttribute("data-vwc-last-error");
        })
        .catch(function (err) {
          addMsg("Network error: " + (err && err.message ? err.message : "failed"), "err");
          setStatus("○ Error", false);
          root.setAttribute("data-vwc-last-error", "network");
        })
        .finally(function () {
          sendBtn.disabled = false;
          input.focus();
        });
    });

    window.VirtusWebsiteChat = window.VirtusWebsiteChat || {};
    window.VirtusWebsiteChat._instance = { root: root, key: key, endpoint: endpoint };
    return root;
  }

  function auto() {
    var script =
      document.currentScript ||
      document.querySelector("script[data-virtus-key]") ||
      document.querySelector('script[src*="website-chat.js"]');
    if (!script) return;
    var key = script.getAttribute("data-virtus-key");
    if (!key) return;
    var endpoint = script.getAttribute("data-endpoint") || "";
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        mount({ key: key, endpoint: endpoint || undefined });
      });
    } else {
      mount({ key: key, endpoint: endpoint || undefined });
    }
  }

  window.VirtusWebsiteChat = {
    mount: mount,
  };
  auto();
})();
