/* R3.2.1 — UX Polish: back-to-top (Business / Premium).
   Respects prefers-reduced-motion. Basic tier does not load this file.
*/
(function () {
  var btn = document.querySelector(".back-to-top");
  if (!btn) return;

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var SHOW_AFTER = 480;

  function sync() {
    var y = window.scrollY || document.documentElement.scrollTop || 0;
    if (y >= SHOW_AFTER) {
      btn.classList.add("is-visible");
      btn.setAttribute("aria-hidden", "false");
    } else {
      btn.classList.remove("is-visible");
      btn.setAttribute("aria-hidden", "true");
    }
  }

  btn.addEventListener("click", function (e) {
    e.preventDefault();
    if (reduce) {
      window.scrollTo(0, 0);
      return;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  window.addEventListener("scroll", sync, { passive: true });
  window.addEventListener("load", sync);
  sync();
})();
