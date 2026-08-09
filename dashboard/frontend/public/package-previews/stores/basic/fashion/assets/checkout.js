/* AI Store Checkout 1.0 */
(function () {
  var TOKEN_KEY = "store_buyer_token_v1";
  var CART_KEY = "store_cart_v1";

  function cfg() {
    var s = window.__VIRTUS_STORE__ || {};
    var orderId = s.orderId || "";
    if (!orderId) {
      var m = (location.pathname || "").match(/\/stores\/([^\/]+)\/live/);
      if (m) orderId = m[1];
    }
    var apiBase = s.apiBase || (orderId ? "/api/store/" + orderId : "");
    return { orderId: orderId, apiBase: apiBase };
  }
  function token() {
    try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; }
  }
  function setToken(t) {
    try {
      if (t) localStorage.setItem(TOKEN_KEY, t);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {}
  }
  function cart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY) || "[]"); } catch (e) { return []; }
  }
  function clearCart() {
    try { localStorage.setItem(CART_KEY, "[]"); } catch (e) {}
  }

  async function api(path, opts) {
    opts = opts || {};
    var c = cfg();
    var headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    var res = await fetch(c.apiBase + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
    var body = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      var err = new Error((body && (body.detail || body.message)) || "request_failed");
      err.status = res.status;
      throw err;
    }
    return body;
  }

  function field(label, name, type, value) {
    return (
      '<label style="display:block;margin:.55rem 0;font-size:.85rem">' + label +
      '<input name="' + name + '" type="' + (type || "text") + '" value="' +
      String(value == null ? "" : value).replace(/"/g, "&quot;") +
      '" style="display:block;width:100%;margin-top:.3rem;padding:.65rem .75rem;border-radius:.75rem;border:1px solid rgba(0,0,0,.12)" /></label>'
    );
  }

  var state = {
    step: "cart",
    options: null,
    address: { country: "DE" },
    shipping_method_id: "",
    payment_method_id: "",
    buyer: null,
  };

  function money(n) { return "€" + Number(n || 0).toFixed(2); }

  function cartTotal() {
    return cart().reduce(function (s, it) {
      return s + Number(it.price || 0) * Number(it.qty || 1);
    }, 0);
  }

  async function ensureOptions() {
    if (!state.options) state.options = await api("/checkout/options");
    return state.options;
  }

  async function render(root) {
    var items = cart();
    if (!items.length && state.step !== "done") {
      root.innerHTML = '<p class="muted">Cart is empty. <a href="catalog.html">Browse catalog</a></p>';
      return;
    }

    if (state.step === "cart") {
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem">' +
        "<h2>1 · Cart</h2>" +
        items.map(function (it) {
          return "<p>" + (it.name || it.id) + " × " + (it.qty || 1) + " — " + money(it.price) + "</p>";
        }).join("") +
        "<p><strong>Subtotal: " + money(cartTotal()) + "</strong></p>" +
        '<button type="button" class="btn" id="ck-next" style="width:100%">Continue</button></div>';
      root.querySelector("#ck-next").onclick = async function () {
        if (token()) {
          try {
            var me = await api("/account/me");
            state.buyer = me.buyer;
            if (me.addresses && me.addresses[0]) state.address = Object.assign({}, me.addresses[0]);
            state.step = "address";
          } catch (e) {
            state.step = "auth";
          }
        } else state.step = "auth";
        await render(root);
      };
      return;
    }

    if (state.step === "auth") {
      root.innerHTML =
        '<div class="cart-layout"><div class="cart-summary"><h2>2 · Sign in</h2>' +
        '<form id="ck-login">' + field("Email", "email", "email") + field("Password", "password", "password") +
        '<button class="btn" type="submit" style="width:100%">Sign in</button></form></div>' +
        '<div class="cart-summary"><h2>Register</h2>' +
        '<form id="ck-reg">' + field("First name", "first_name") + field("Last name", "last_name") +
        field("Email", "email", "email") + field("Password (min 8)", "password", "password") +
        '<button class="btn" type="submit" style="width:100%">Create account</button></form></div></div>';
      async function after(body) {
        setToken(body.token);
        state.buyer = body.buyer;
        state.step = "address";
        await render(root);
      }
      root.querySelector("#ck-login").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        try {
          await after(await api("/account/login", { method: "POST", body: { email: fd.get("email"), password: fd.get("password") } }));
        } catch (err) { alert(err.message); }
      };
      root.querySelector("#ck-reg").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        try {
          await after(await api("/account/register", { method: "POST", body: {
            first_name: fd.get("first_name"), last_name: fd.get("last_name"),
            email: fd.get("email"), password: fd.get("password")
          }}));
        } catch (err) { alert(err.message); }
      };
      return;
    }

    if (state.step === "address") {
      var a = state.address || {};
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>3 · Address</h2>' +
        '<form id="ck-addr">' +
        field("Full name", "full_name", "text", a.full_name || "") +
        field("Street", "line1", "text", a.line1 || "") +
        field("City", "city", "text", a.city || "") +
        field("Postal code", "postal_code", "text", a.postal_code || "") +
        field("Country", "country", "text", a.country || "DE") +
        field("Phone", "phone", "text", a.phone || "") +
        '<button class="btn" type="submit" style="width:100%">Continue to shipping</button></form></div>';
      root.querySelector("#ck-addr").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        state.address = {
          full_name: fd.get("full_name"), line1: fd.get("line1"), city: fd.get("city"),
          postal_code: fd.get("postal_code"), country: fd.get("country"), phone: fd.get("phone")
        };
        state.step = "shipping";
        await render(root);
      };
      return;
    }

    if (state.step === "shipping") {
      var opt = await ensureOptions();
      var methods = opt.shipping_methods || [];
      if (!methods.length) {
        root.innerHTML =
          '<div class="cart-summary" style="max-width:36rem"><h2>4 · Shipping</h2>' +
          '<p class="muted">Этот магазин пока не может отправлять товары — доставка не подключена.</p>' +
          '<button type="button" class="btn btn-ghost" id="ck-back-addr">Back</button></div>';
        root.querySelector("#ck-back-addr").onclick = async function () {
          state.step = "address";
          await render(root);
        };
        return;
      }
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>4 · Shipping</h2>' +
        methods.map(function (m) {
          var checked = state.shipping_method_id === m.id ? " checked" : "";
          return (
            '<label style="display:block;margin:.5rem 0;padding:.75rem;border:1px solid rgba(0,0,0,.1);border-radius:.75rem">' +
            '<input type="radio" name="ship" value="' + m.id + '"' + checked + ' /> ' +
            "<strong>" + (m.label || m.id) + "</strong> — " +
            (m.days_min || 0) + "–" + (m.days_max || 0) + " days · " + money(m.price_eur) +
            "</label>"
          );
        }).join("") +
        '<button type="button" class="btn" id="ck-ship" style="width:100%;margin-top:.75rem">Continue</button></div>';
      if (!state.shipping_method_id && methods[0]) state.shipping_method_id = methods[0].id;
      root.querySelectorAll('input[name="ship"]').forEach(function (r) {
        r.onchange = function () { state.shipping_method_id = r.value; };
      });
      root.querySelector("#ck-ship").onclick = async function () {
        if (!state.shipping_method_id) { alert("Select shipping"); return; }
        state.step = "payment";
        await render(root);
      };
      return;
    }

    if (state.step === "payment") {
      var opt2 = await ensureOptions();
      var pays = opt2.payment_methods || [];
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>5 · Payment</h2>' +
        '<p class="muted" style="font-size:.8rem">Checkout 1.0 stores the order — live card charge comes later.</p>' +
        pays.map(function (p) {
          var checked = state.payment_method_id === p.id ? " checked" : "";
          return (
            '<label style="display:block;margin:.5rem 0;padding:.75rem;border:1px solid rgba(0,0,0,.1);border-radius:.75rem">' +
            '<input type="radio" name="pay" value="' + p.id + '"' + checked + ' /> ' +
            "<strong>" + (p.label || p.id) + "</strong><br/><span class=\"muted\">" + (p.note || "") + "</span></label>"
          );
        }).join("") +
        '<button type="button" class="btn" id="ck-pay" style="width:100%;margin-top:.75rem">Review order</button></div>';
      if (!state.payment_method_id && pays[0]) state.payment_method_id = pays[0].id;
      root.querySelectorAll('input[name="pay"]').forEach(function (r) {
        r.onchange = function () { state.payment_method_id = r.value; };
      });
      root.querySelector("#ck-pay").onclick = async function () {
        if (!state.payment_method_id) { alert("Select payment"); return; }
        state.step = "confirm";
        await render(root);
      };
      return;
    }

    if (state.step === "confirm") {
      var opt3 = await ensureOptions();
      var ship = (opt3.shipping_methods || []).find(function (m) { return m.id === state.shipping_method_id; }) || {};
      var pay = (opt3.payment_methods || []).find(function (p) { return p.id === state.payment_method_id; }) || {};
      var sub = cartTotal();
      var shipPrice = Number(ship.price_eur || 0);
      if (opt3.free_shipping_from_eur != null && sub >= Number(opt3.free_shipping_from_eur)) shipPrice = 0;
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>6 · Confirm</h2>' +
        "<p>Items: " + money(sub) + "</p>" +
        "<p>Shipping (" + (ship.label || "") + "): " + money(shipPrice) + "</p>" +
        "<p>Payment: " + (pay.label || "") + "</p>" +
        "<p><strong>Total: " + money(sub + shipPrice) + "</strong></p>" +
        '<button type="button" class="btn" id="ck-place" style="width:100%">Place order</button>' +
        '<p id="ck-msg" class="muted"></p></div>';
      root.querySelector("#ck-place").onclick = async function () {
        var btn = root.querySelector("#ck-place");
        btn.disabled = true;
        try {
          var out = await api("/checkout/place", {
            method: "POST",
            body: {
              items: cart(),
              address: state.address,
              shipping_method_id: state.shipping_method_id,
              payment_method_id: state.payment_method_id,
              save_address: true,
            },
          });
          clearCart();
          state.step = "done";
          state.lastOrder = out.order;
          state.lastEmail = out.email;
          await render(root);
        } catch (err) {
          btn.disabled = false;
          root.querySelector("#ck-msg").textContent = err.message || "Failed";
        }
      };
      return;
    }

    if (state.step === "done") {
      var o = state.lastOrder || {};
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>Order placed</h2>' +
        "<p><strong>" + (o.id || "") + "</strong></p>" +
        "<p>Status: " + (o.status || "") + " · Total " + money(o.total_eur) + "</p>" +
        '<p class="muted">Confirmation queued' +
        (state.lastEmail && state.lastEmail.delivery ? " (" + state.lastEmail.delivery + ")" : "") +
        ".</p>" +
        '<p><a class="btn" href="account.html#orders">Open my orders</a> ' +
        '<a class="btn btn-ghost" href="catalog.html">Continue shopping</a></p></div>';
    }
  }

  async function boot() {
    var root = document.getElementById("checkout-root");
    if (!root) return;
    if (!cfg().orderId) {
      root.innerHTML = '<p class="muted">Open checkout via the live shop URL.</p>';
      return;
    }
    await render(root);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
