/* AI Store R3.2 — Store Customer Account */
(function () {
  var TOKEN_KEY = "store_buyer_token_v1";
  var WISH_KEY = "store_wish_v1";
  var L = { login: "Anmelden", register: "Registrieren" };

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

  async function api(path, opts) {
    opts = opts || {};
    var c = cfg();
    var headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    var res = await fetch(c.apiBase + "/account" + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
    var body = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      var err = new Error((body && body.detail) || "request_failed");
      err.status = res.status;
      err.body = body;
      throw err;
    }
    return body;
  }

  function el(html) {
    var d = document.createElement("div");
    d.innerHTML = html.trim();
    return d.firstChild;
  }

  function field(label, name, type, value) {
    type = type || "text";
    value = value == null ? "" : value;
    return (
      '<label style="display:block;margin:.6rem 0;font-size:.85rem">' +
      label +
      '<input name="' + name + '" type="' + type + '" value="' + String(value).replace(/"/g, "&quot;") +
      '" style="display:block;width:100%;margin-top:.35rem;padding:.65rem .75rem;border-radius:.75rem;border:1px solid rgba(0,0,0,.12)" />' +
      "</label>"
    );
  }

  function renderAuth(root) {
    root.innerHTML =
      '<div class="cart-layout" style="margin-top:1rem">' +
      '<div class="cart-summary" id="login"><h2 style="margin-top:0">Anmelden</h2>' +
      '<form id="login-form">' +
      field("Email", "email", "email") +
      field("Password", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">Anmelden</button>' +
      '</form><p class="muted" style="font-size:.8rem;margin-top:1rem"><a href="#forgot" id="goto-forgot">Forgot password?</a></p></div>' +
      '<div class="cart-summary" id="register"><h2 style="margin-top:0">Registrieren</h2>' +
      '<form id="reg-form">' +
      field("First name", "first_name") +
      field("Last name", "last_name") +
      field("Email", "email", "email") +
      field("Password (min 8)", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">Registrieren</button>' +
      "</form></div></div>" +
      '<div id="forgot-box" style="display:none;margin-top:1rem" class="cart-summary">' +
      "<h2>Reset password</h2>" +
      '<form id="forgot-form">' +
      field("Email", "email", "email") +
      '<button class="btn btn-ghost" type="submit">Request reset</button></form>' +
      '<form id="reset-form" style="margin-top:1rem">' +
      field("Email", "email", "email") +
      field("Reset token", "token") +
      field("New password", "password", "password") +
      '<button class="btn" type="submit">Set new password</button></form>' +
      '<p id="auth-msg" class="muted"></p></div>';

    root.querySelector("#goto-forgot").onclick = function (e) {
      e.preventDefault();
      root.querySelector("#forgot-box").style.display = "block";
    };

    async function afterAuth(body) {
      setToken(body.token);
      try {
        var localWish = JSON.parse(localStorage.getItem(WISH_KEY) || "[]");
        if (localWish && localWish.length) {
          await api("/wishlist", {
            method: "PUT",
            body: {
              items: localWish.map(function (w) {
                return {
                  product_id: w.id || w.product_id,
                  title: w.name || w.title,
                  price: w.price,
                  image: w.image,
                };
              }),
            },
          });
        }
      } catch (e) {}
      await renderCabinet(root);
    }

    root.querySelector("#login-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/login", {
          method: "POST",
          body: { email: fd.get("email"), password: fd.get("password") },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Login failed");
      }
    };
    root.querySelector("#reg-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/register", {
          method: "POST",
          body: {
            first_name: fd.get("first_name"),
            last_name: fd.get("last_name"),
            email: fd.get("email"),
            password: fd.get("password"),
          },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Register failed");
      }
    };
    root.querySelector("#forgot-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/forgot-password", {
          method: "POST",
          body: { email: fd.get("email") },
        });
        var msg = body.message || "OK";
        if (body.dev_reset_token) {
          msg += " · token: " + body.dev_reset_token;
          var rt = root.querySelector('#reset-form input[name="token"]');
          var re = root.querySelector('#reset-form input[name="email"]');
          if (rt) rt.value = body.dev_reset_token;
          if (re) re.value = fd.get("email");
        }
        root.querySelector("#auth-msg").textContent = msg;
      } catch (err) {
        alert(err.message || "Failed");
      }
    };
    root.querySelector("#reset-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/reset-password", {
          method: "POST",
          body: {
            email: fd.get("email"),
            token: fd.get("token"),
            password: fd.get("password"),
          },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Reset failed");
      }
    };
  }

  async function renderCabinet(root) {
    var me;
    try {
      me = await api("/me");
    } catch (err) {
      setToken("");
      renderAuth(root);
      return;
    }
    var b = me.buyer || {};
    var addrs = me.addresses || [];
    var wish = me.wishlist || [];
    var orders = me.orders || [];

    root.innerHTML =
      '<div style="display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0">' +
      '<button type="button" class="btn btn-sm" data-tab="profile">Profile</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="addresses">Addresses</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="wishlist">Wishlist</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="orders">Orders</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" id="logout-btn">Sign out</button>' +
      '</div><div id="tab-body"></div>';

    function show(tab) {
      var box = root.querySelector("#tab-body");
      if (tab === "profile") {
        box.innerHTML =
          '<form id="profile-form" class="cart-summary" style="max-width:28rem">' +
          field("First name", "first_name", "text", b.first_name) +
          field("Last name", "last_name", "text", b.last_name) +
          field("Phone", "phone", "text", b.phone) +
          field("New password (optional)", "password", "password", "") +
          '<p class="muted" style="font-size:.8rem">Email: ' +
          (b.email || "") +
          " (login)</p>" +
          '<button class="btn" type="submit">Save profile</button></form>';
        box.querySelector("#profile-form").onsubmit = async function (e) {
          e.preventDefault();
          var fd = new FormData(e.target);
          var payload = {
            first_name: fd.get("first_name"),
            last_name: fd.get("last_name"),
            phone: fd.get("phone"),
          };
          if (fd.get("password")) payload.password = fd.get("password");
          try {
            var out = await api("/me", { method: "PATCH", body: payload });
            b = out.buyer || b;
            alert("Saved");
          } catch (err) {
            alert(err.message || "Save failed");
          }
        };
      } else if (tab === "addresses") {
        var list = addrs
          .map(function (a) {
            return (
              '<div class="wish-line"><div><strong>' +
              (a.label || "Address") +
              "</strong><br/>" +
              (a.full_name || "") +
              "<br/>" +
              (a.line1 || "") +
              ", " +
              (a.postal_code || "") +
              " " +
              (a.city || "") +
              " (" +
              (a.country || "") +
              ')</div><button type="button" class="btn btn-ghost btn-sm" data-del-addr="' +
              a.id +
              '">Remove</button></div>'
            );
          })
          .join("");
        box.innerHTML =
          (list || '<p class="muted">No addresses yet.</p>') +
          '<form id="addr-form" class="cart-summary" style="margin-top:1rem;max-width:28rem">' +
          "<h3>Add address</h3>" +
          field("Label", "label", "text", "Home") +
          field("Full name", "full_name") +
          field("Street", "line1") +
          field("City", "city") +
          field("Postal code", "postal_code") +
          field("Country", "country", "text", "DE") +
          '<button class="btn" type="submit">Save address</button></form>';
        box.querySelectorAll("[data-del-addr]").forEach(function (btn) {
          btn.onclick = async function () {
            try {
              var out = await api("/addresses/" + btn.getAttribute("data-del-addr"), {
                method: "DELETE",
              });
              addrs = out.addresses || [];
              show("addresses");
            } catch (err) {
              alert(err.message || "Failed");
            }
          };
        });
        box.querySelector("#addr-form").onsubmit = async function (e) {
          e.preventDefault();
          var fd = new FormData(e.target);
          try {
            var out = await api("/addresses", {
              method: "POST",
              body: {
                label: fd.get("label"),
                full_name: fd.get("full_name"),
                line1: fd.get("line1"),
                city: fd.get("city"),
                postal_code: fd.get("postal_code"),
                country: fd.get("country"),
                is_default: true,
              },
            });
            addrs = out.addresses || [];
            show("addresses");
          } catch (err) {
            alert(err.message || "Failed");
          }
        };
      } else if (tab === "wishlist") {
        box.innerHTML =
          wish.length === 0
            ? '<p class="muted">Wishlist is empty. Save items while browsing, then sign in to sync.</p>'
            : wish
                .map(function (w) {
                  return (
                    '<div class="wish-line"><div><strong>' +
                    (w.title || w.product_id) +
                    "</strong><br/>€" +
                    Number(w.price || 0).toFixed(2) +
                    "</div></div>"
                  );
                })
                .join("");
      } else {
        box.innerHTML =
          '<p class="muted">Order history will appear here after Commerce (R3.3).</p>' +
          (orders.length
            ? "<pre>" + JSON.stringify(orders, null, 2) + "</pre>"
            : "<p>No orders yet.</p>");
      }
    }

    root.querySelectorAll("[data-tab]").forEach(function (btn) {
      btn.onclick = function () {
        show(btn.getAttribute("data-tab"));
      };
    });
    root.querySelector("#logout-btn").onclick = function () {
      setToken("");
      renderAuth(root);
    };
    show("profile");
  }

  async function boot() {
    var root = document.getElementById("account-panels");
    if (!root) return;
    if (!cfg().orderId) {
      root.innerHTML =
        '<p class="muted">Open this page via the live shop URL so your store id is known.</p>';
      return;
    }
    if (token()) await renderCabinet(root);
    else {
      renderAuth(root);
      var h = (location.hash || '').toLowerCase();
      if (h.indexOf('register') >= 0) {
        var r = document.getElementById('register');
        if (r) r.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else if (h.indexOf('login') >= 0) {
        var l = document.getElementById('login');
        if (l) l.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
