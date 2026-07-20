/** Inject client services from ?services= into demo #services (Premium order preview). */
(function () {
  try {
    var params = new URLSearchParams(window.location.search);
    var raw = params.get("services");
    if (!raw) return;
    var items = decodeURIComponent(raw)
      .split("|")
      .map(function (s) {
        return s.replace(/^[\s\-*•·]+/, "").trim();
      })
      .filter(function (s) {
        return s.length >= 2;
      })
      .slice(0, 8);
    if (!items.length) return;

    var root = document.getElementById("services");
    if (!root) return;

    var list = root.querySelector(".services");
    if (!list) return;

    list.innerHTML = items
      .map(function (name) {
        return (
          '<li class="service-card"><h3>' +
          name +
          "</h3><p class=\"service-desc\">Individuell für Ihr Unternehmen — wie besprochen.</p></li>"
        );
      })
      .join("");

    var showcase = document.querySelector(".showcase-services");
    if (showcase) {
      showcase.innerHTML = items
        .slice(0, 4)
        .map(function (name) {
          return "<li>" + name + "</li>";
        })
        .join("");
    }

    var hint = root.querySelector(".muted.client-services-hint");
    if (hint) hint.textContent = "Ihre Leistungen — aus Ihren Angaben im Bestellformular.";
  } catch (_e) {
    /* static demo — ignore */
  }
})();
