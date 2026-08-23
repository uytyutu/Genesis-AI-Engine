/* reveal.js — R2.2c Premium Interactions (paired with motion_kit.css)
   Scroll reveal · light hero parallax · KPI counters.
   Exits early when prefers-reduced-motion: reduce.
*/
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function activateReveals() {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("active");
    });
  }

  if (reduce) {
    activateReveals();
    return;
  }

  function revealOnScroll() {
    var reveals = document.querySelectorAll(".reveal:not(.active)");
    var windowHeight = window.innerHeight;
    for (var i = 0; i < reveals.length; i++) {
      var top = reveals[i].getBoundingClientRect().top;
      if (top < windowHeight - 90) {
        reveals[i].classList.add("active");
      }
    }
  }

  /* Light parallax — only while hero is in view; tiny factor */
  var hero = document.querySelector(".hero.hero-parallax");
  function parallaxOnScroll() {
    if (!hero) return;
    var rect = hero.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) return;
    var y = Math.max(0, -rect.top) * 0.12;
    if (y > 48) y = 48;
    hero.style.setProperty("--parallax-y", y.toFixed(1) + "px");
  }

  /* KPI counters — animate once when visible */
  function parseTarget(text) {
    var t = (text || "").trim();
    var m = t.match(/^(\d+(?:[.,]\d+)?)(.*)$/);
    if (!m) return null;
    var num = parseFloat(m[1].replace(",", "."));
    if (isNaN(num)) return null;
    return { value: num, suffix: m[2] || "", decimals: (m[1].split(/[.,]/)[1] || "").length };
  }

  function runCounter(el) {
    if (el.getAttribute("data-vc-counted") === "1") return;
    var parsed = parseTarget(el.textContent);
    if (!parsed) return;
    el.setAttribute("data-vc-counted", "1");
    var start = 0;
    var duration = 900;
    var t0 = null;
    function frame(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / duration);
      var eased = 1 - Math.pow(1 - p, 3);
      var cur = start + (parsed.value - start) * eased;
      if (parsed.decimals > 0) {
        el.textContent = cur.toFixed(parsed.decimals) + parsed.suffix;
      } else {
        el.textContent = Math.round(cur) + parsed.suffix;
      }
      if (p < 1) {
        window.requestAnimationFrame(frame);
      } else {
        el.classList.add("vc-count-done");
      }
    }
    window.requestAnimationFrame(frame);
  }

  function countersOnScroll() {
    var nodes = document.querySelectorAll(
      ".hero-kpi strong, .stat strong, [data-count]"
    );
    var wh = window.innerHeight;
    for (var i = 0; i < nodes.length; i++) {
      var top = nodes[i].getBoundingClientRect().top;
      if (top < wh - 60) runCounter(nodes[i]);
    }
  }

  function onScroll() {
    revealOnScroll();
    parallaxOnScroll();
    countersOnScroll();
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("load", onScroll);
  onScroll();
})();
