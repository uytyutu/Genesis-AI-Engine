"""Shared scroll-cinema player — rAF + transform progress (anti-jank).

Used by Factory exporters / package-previews so scroll does not
setState-style thrash: no per-scroll layout via width%, no full-list
class churn beyond the two active frames.
"""

from __future__ import annotations

# CSS snippet for progress bar (pair with cinema_scroll_script).
CINEMA_PROGRESS_CSS = """
.progress, #prog, #progress {
  width: 100% !important;
  transform: scaleX(0);
  transform-origin: left center;
  will-change: transform;
}
.seq img, #seq img {
  transition: opacity 0.06s linear;
  will-change: auto;
}
"""


def cinema_scroll_script(
    *,
    copies_js: str | None = None,
    copies_var: str = "copies",
    imgs_selector: str = "#seq img",
    pin_id: str = "cinemaPin",
    beat_id: str = "beatLine",
    meter_id: str = "meter",
    prog_id: str = "prog",
    meter_prefix: str = "FRAME",
) -> str:
    """Return IIFE script body (without outer <script> tags).

    If ``copies_js`` is set, inject ``var copies = <copies_js>;``
    else assume ``copies_var`` already exists in scope.
    """
    copies_line = (
        f"var copies = {copies_js};"
        if copies_js is not None
        else f"var copies = {copies_var};"
    )
    return f"""
(function(){{
  {copies_line}
  var imgs = Array.prototype.slice.call(document.querySelectorAll({imgs_selector!r}));
  var N = imgs.length;
  var pin = document.getElementById({pin_id!r});
  var beat = document.getElementById({beat_id!r});
  var meter = document.getElementById({meter_id!r});
  var prog = document.getElementById({prog_id!r});
  var last = -1;
  var pending = false;
  function paint(){{
    pending = false;
    if (!N || !pin) return;
    var rect = pin.getBoundingClientRect();
    var total = pin.offsetHeight - window.innerHeight;
    var scrolled = Math.min(Math.max(-rect.top, 0), total);
    var t = total > 0 ? scrolled / total : 0;
    var idx = Math.min(N - 1, Math.floor(t * N));
    if (idx !== last) {{
      if (last >= 0 && imgs[last]) imgs[last].classList.remove('is-on');
      if (last > 0 && imgs[last - 1]) imgs[last - 1].classList.remove('is-prev');
      if (imgs[idx]) imgs[idx].classList.add('is-on');
      if (idx > 0 && imgs[idx - 1]) imgs[idx - 1].classList.add('is-prev');
      if (beat) beat.textContent = copies[idx] || copies[copies.length - 1] || '';
      if (meter) meter.textContent = {meter_prefix!r} + ' ' + String(idx + 1).padStart(3, '0') + ' / ' + String(N).padStart(3, '0');
      last = idx;
    }}
    if (prog) prog.style.transform = 'scaleX(' + t.toFixed(4) + ')';
  }}
  function onScroll(){{
    if (pending) return;
    pending = true;
    requestAnimationFrame(paint);
  }}
  window.addEventListener('scroll', onScroll, {{passive:true}});
  window.addEventListener('resize', onScroll);
  paint();
}})();
""".strip()
