/* reveal.js — scroll reveal for .reveal sections (paired with motion_kit.css) */
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("active");
    });
    return;
  }

  function revealOnScroll() {
    var reveals = document.querySelectorAll(".reveal");
    var windowHeight = window.innerHeight;
    for (var i = 0; i < reveals.length; i++) {
      var elementTop = reveals[i].getBoundingClientRect().top;
      if (elementTop < windowHeight - 100) {
        reveals[i].classList.add("active");
      }
    }
  }

  window.addEventListener("scroll", revealOnScroll, { passive: true });
  window.addEventListener("load", revealOnScroll);
  revealOnScroll();
})();
