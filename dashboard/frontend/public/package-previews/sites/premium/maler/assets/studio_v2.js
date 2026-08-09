/* Virtus Core Studio Renderer 2.0 */
(function () {
  document.documentElement.classList.add('studio-v2');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function markBands() {
    var map = [
      ['#about', 'studio-band--story'],
      ['.about', 'studio-band--story'],
      ['#services', 'studio-band--services'],
      ['.services', 'studio-band--services'],
      ['#gallery', 'studio-band--gallery'],
      ['.gallery', 'studio-band--gallery'],
      ['#team', 'studio-band--team'],
      ['.team', 'studio-band--team'],
      ['#process', 'studio-band--process'],
      ['.process', 'studio-band--process'],
      ['#contact', 'studio-band--contact'],
      ['.contact', 'studio-band--contact'],
      ['#reviews', 'studio-band--reviews'],
      ['.reviews', 'studio-band--reviews'],
      ['.testimonials', 'studio-band--reviews']
    ];
    map.forEach(function (pair) {
      document.querySelectorAll(pair[0]).forEach(function (el) {
        if (el.tagName === 'SECTION' || el.classList.contains('section') || el.id) {
          el.classList.add('studio-band', pair[1]);
        }
      });
    });
    document.querySelectorAll('section').forEach(function (sec) {
      if (!sec.classList.contains('hero') && !sec.classList.contains('studio-band')) {
        sec.classList.add('studio-band');
      }
    });
  }

  function mouseLight() {
    if (reduce || !(window.matchMedia && window.matchMedia('(pointer: fine)').matches)) return;
    var el = document.createElement('div');
    el.className = 'studio-mouse-light';
    el.setAttribute('aria-hidden', 'true');
    document.body.appendChild(el);
    window.addEventListener('pointermove', function (e) {
      el.style.transform = 'translate3d(' + e.clientX + 'px,' + e.clientY + 'px,0)';
    }, { passive: true });
  }

  function bootLenisGsap() {
    if (reduce) return;
    var LenisCtor = window.Lenis;
    var gsap = window.gsap;
    var ScrollTrigger = window.ScrollTrigger;
    if (LenisCtor) {
      var lenis = new LenisCtor({ lerp: 0.09, smoothWheel: true });
      function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
      if (gsap && ScrollTrigger) {
        gsap.registerPlugin(ScrollTrigger);
        lenis.on('scroll', ScrollTrigger.update);
      }
    }
    if (gsap && ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      gsap.utils.toArray('.studio-band, .svc-card, .exp-reveal, .gallery img, .studio-gallery-grid img').forEach(function (node) {
        gsap.fromTo(node, { autoAlpha: 0, y: 28 }, {
          autoAlpha: 1, y: 0, duration: 0.85, ease: 'power2.out',
          scrollTrigger: { trigger: node, start: 'top 88%', toggleActions: 'play none none none' }
        });
      });
      var hero3d = document.getElementById('virtus-3d-hero');
      if (hero3d) {
        gsap.to(hero3d, {
          yPercent: 12, ease: 'none',
          scrollTrigger: { trigger: hero3d, start: 'top top', end: 'bottom top', scrub: true }
        });
      }
    }
  }

  function expandGallery() {
    var host = document.querySelector('#gallery .gallery-grid, #gallery .grid, .gallery-grid, [data-studio-gallery]');
    if (!host) return;
    var existing = host.querySelectorAll('img').length;
    if (existing >= 8) return;
    host.classList.add('studio-gallery-grid');
    for (var i = existing + 1; i <= 18; i++) {
      var img = document.createElement('img');
      img.src = 'assets/gallery_' + i + '.jpg';
      img.alt = 'Galerie ' + i;
      img.loading = 'lazy';
      img.onerror = function () { this.remove(); };
      host.appendChild(img);
    }
  }

  function boot() {
    markBands();
    mouseLight();
    expandGallery();
    bootLenisGsap();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  window.addEventListener('load', function () { setTimeout(bootLenisGsap, 80); });
})();
