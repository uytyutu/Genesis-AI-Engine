/* AI Store R2.1 — cart, drawer, wishlist (localStorage) */
(function () {
  var CART_KEY = "store_cart_v1";
  var WISH_KEY = "store_wish_v1";
  var UI = {
    toastAdded: "Zum Warenkorb hinzugefügt",
    toastWishAdd: "Auf die Merkliste",
    toastWishRm: "Von der Merkliste entfernt",
    toastCheckout: "Demo-Kasse — Zahlungen folgen später",
    toastPromo: "Gutscheine aktivieren sich mit der Live-Kasse",
    remove: "Entfernen",
    wishEmpty: "Ihre Merkliste ist leer.",
    browse: "Zum Katalog"
  };

  function read(key) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }
  function write(key, val) {
    localStorage.setItem(key, JSON.stringify(val));
  }

  function cart() { return read(CART_KEY); }
  function setCart(items) {
    write(CART_KEY, items);
    updateBadge();
    renderCartPage();
  }

  function updateBadge() {
    var items = cart();
    var n = items.reduce(function (s, it) { return s + (it.qty || 1); }, 0);
    document.querySelectorAll("[data-cart-badge]").forEach(function (el) {
      el.textContent = String(n);
      el.setAttribute("data-count", String(n));
      el.classList.toggle("has-items", n > 0);
    });
  }

  function toast(msg) {
    var el = document.getElementById("store-toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.classList.remove("show"); }, 1800);
  }

  function addItem(payload, buyNow) {
    var items = cart();
    var found = items.find(function (x) { return x.id === payload.id; });
    if (found) found.qty = (found.qty || 1) + 1;
    else items.push({ id: payload.id, name: payload.name, price: payload.price, priceLabel: payload.priceLabel, qty: 1 });
    setCart(items);
    toast(UI.toastAdded);
    if (buyNow) window.location.href = "cart.html";
  }

  function toggleWish(id, name) {
    if (!id || id === "header") return;
    var list = read(WISH_KEY);
    var i = list.findIndex(function (x) { return x.id === id; });
    if (i >= 0) list.splice(i, 1);
    else list.push({ id: id, name: name });
    write(WISH_KEY, list);
    toast(i >= 0 ? UI.toastWishRm : UI.toastWishAdd);
    renderWishPage();
  }

  function renderWishPage() {
    var root = document.getElementById("wish-lines");
    if (!root) return;
    var list = read(WISH_KEY).filter(function (x) { return x && x.id && x.id !== "header"; });
    var empty = document.getElementById("wish-empty");
    if (!list.length) {
      root.innerHTML = "";
      if (empty) empty.style.display = "block";
      return;
    }
    if (empty) empty.style.display = "none";
    root.innerHTML = list.map(function (it) {
      return (
        '<div class="wish-line" data-wish-id="' + escapeHtml(it.id) + '">' +
          "<strong>" + escapeHtml(it.name || it.id) + "</strong>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-action="wish" data-id="' +
          escapeHtml(it.id) + '" data-name="' + escapeHtml(it.name || "") + '">' +
          escapeHtml(UI.remove) + "</button>" +
        "</div>"
      );
    }).join("");
  }

  function openDrawer(open) {
    var d = document.getElementById("nav-drawer");
    var o = document.getElementById("drawer-overlay");
    if (!d || !o) return;
    d.classList.toggle("open", open);
    o.classList.toggle("open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }

  function renderCartPage() {
    var root = document.getElementById("cart-lines");
    if (!root) return;
    var items = cart();
    var empty = document.getElementById("cart-empty");
    var summary = document.getElementById("cart-summary");
    if (!items.length) {
      root.innerHTML = "";
      if (empty) empty.style.display = "block";
      if (summary) summary.style.display = "none";
      return;
    }
    if (empty) empty.style.display = "none";
    if (summary) summary.style.display = "block";
    var total = 0;
    root.innerHTML = items.map(function (it) {
      var line = (it.price || 0) * (it.qty || 1);
      total += line;
      var letter = (it.name || "?").charAt(0).toUpperCase();
      return (
        '<article class="cart-line" data-id="' + it.id + '">' +
          '<div class="cart-thumb">' + letter + "</div>" +
          '<div><strong>' + escapeHtml(it.name) + "</strong>" +
          '<div class="muted">' + escapeHtml(it.priceLabel || "") + "</div>" +
          '<div class="qty-ctrl">' +
            '<button type="button" data-qty="-1" aria-label="−">−</button>' +
            "<span>" + (it.qty || 1) + "</span>" +
            '<button type="button" data-qty="1" aria-label="+">+</button>' +
          "</div></div>" +
          '<div><strong>€' + line.toFixed(2) + "</strong><br>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-remove style="margin-top:0.5rem">' +
          escapeHtml(UI.remove) + "</button></div>" +
        "</article>"
      );
    }).join("");
    var totalEl = document.getElementById("cart-total");
    if (totalEl) totalEl.textContent = "€" + total.toFixed(2);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function filterCatalog(q) {
    q = (q || "").trim().toLowerCase();
    var cards = document.querySelectorAll("[data-product-card]");
    if (!cards.length && q) {
      window.location.href = "catalog.html?q=" + encodeURIComponent(q);
      return;
    }
    cards.forEach(function (card) {
      var name = (card.getAttribute("data-name") || "").toLowerCase();
      card.style.display = !q || name.indexOf(q) >= 0 ? "" : "none";
    });
  }

  document.addEventListener("click", function (e) {
    var navLink = e.target.closest(".nav-drawer a");
    if (navLink) openDrawer(false);

    var t = e.target.closest("[data-action]");
    if (t) {
      var action = t.getAttribute("data-action");
      if (action === "drawer-open") openDrawer(true);
      if (action === "drawer-close") openDrawer(false);
      if (action === "add-cart" || action === "buy-now") {
        addItem({
          id: t.getAttribute("data-id"),
          name: t.getAttribute("data-name"),
          price: parseFloat(t.getAttribute("data-price") || "0"),
          priceLabel: t.getAttribute("data-price-label") || ""
        }, action === "buy-now");
      }
      if (action === "wish") {
        toggleWish(t.getAttribute("data-id"), t.getAttribute("data-name"));
      }
      if (action === "checkout") {
        var note = document.getElementById("checkout-note");
        if (note) note.classList.add("show");
        toast(UI.toastCheckout);
      }
    }
    var line = e.target.closest(".cart-line");
    if (line) {
      var id = line.getAttribute("data-id");
      var items = cart();
      if (e.target.closest("[data-remove]")) {
        setCart(items.filter(function (x) { return x.id !== id; }));
        return;
      }
      var qtyBtn = e.target.closest("[data-qty]");
      if (qtyBtn) {
        var delta = parseInt(qtyBtn.getAttribute("data-qty"), 10);
        items = items.map(function (x) {
          if (x.id !== id) return x;
          return Object.assign({}, x, { qty: Math.max(1, (x.qty || 1) + delta) });
        });
        setCart(items);
      }
    }
  });

  var overlay = document.getElementById("drawer-overlay");
  if (overlay) overlay.addEventListener("click", function () { openDrawer(false); });

  var search = document.getElementById("header-search");
  if (search) {
    var params = new URLSearchParams(window.location.search);
    var q0 = params.get("q");
    if (q0) {
      search.value = q0;
      filterCatalog(q0);
    }
    search.addEventListener("input", function () { filterCatalog(search.value); });
    search.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        filterCatalog(search.value);
      }
    });
  }

  var promo = document.getElementById("promo-apply");
  if (promo) {
    promo.addEventListener("click", function () {
      toast(UI.toastPromo);
    });
  }

  updateBadge();
  renderCartPage();
  renderWishPage();
})();
