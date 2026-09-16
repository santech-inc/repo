(function () {
  "use strict";

  var SOURCE_JSON = "./sources.json";
  var CLASIC_JSON = "./clasic.sources.json";
  var PAL_JSON = "./pal.sources.json";

  var baseUrl = resolveBaseUrl();

  function resolveBaseUrl() {
    var loc = window.location;
    var path = loc.pathname;
    if (path.endsWith("/")) return loc.origin + path;
    return loc.origin + path.substring(0, path.lastIndexOf("/") + 1);
  }

  function resolveUrl(relative) {
    if (!relative) return "";
    if (relative.startsWith("http://") || relative.startsWith("https://")) return relative;
    return new URL(relative, baseUrl).href;
  }

  function copyText(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { showCopied(btn); });
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showCopied(btn);
    }
  }

  function showCopied(btn) {
    var original = btn.textContent;
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(function () {
      btn.textContent = original;
      btn.classList.remove("copied");
    }, 1500);
  }

  function initLinks() {
    var allUrl = resolveUrl(SOURCE_JSON);
    var classicUrl = resolveUrl(CLASIC_JSON);
    var palUrl = resolveUrl(PAL_JSON);

    var btnAll = document.getElementById("btn-all");
    var btnClassic = document.getElementById("btn-classic");
    var btnPal = document.getElementById("btn-pal");
    if (btnAll) btnAll.href = "altstore://source?url=" + encodeURIComponent(allUrl);
    if (btnClassic) btnClassic.href = "altstore-classic://source?url=" + encodeURIComponent(classicUrl);
    if (btnPal) btnPal.href = "altstore-pal://source?url=" + encodeURIComponent(palUrl);

    var urlAll = document.getElementById("url-all");
    var urlClassic = document.getElementById("url-classic");
    var urlPal = document.getElementById("url-pal");
    if (urlAll) urlAll.textContent = allUrl;
    if (urlClassic) urlClassic.textContent = classicUrl;
    if (urlPal) urlPal.textContent = palUrl;

    var copyBtns = document.querySelectorAll(".copy-btn[data-copy-path]");
    for (var i = 0; i < copyBtns.length; i++) {
      copyBtns[i].addEventListener("click", function () {
        var path = this.getAttribute("data-copy-path");
        if (path) copyText(path, this);
      });
    }
  }

  function createAppCard(app, distribution) {
    var card = document.createElement("div");
    card.className = "app-card";

    var iconSrc = app.iconURL ? resolveUrl(app.iconURL) : "";
    var metaParts = [];
    if (app.version) metaParts.push("v" + app.version);
    if (app.developerName) metaParts.push(app.developerName);
    if (distribution) metaParts.push(distribution.toUpperCase());
    var desc = app.localizedDescription || app.subtitle || "";

    card.innerHTML =
      (iconSrc
        ? '<img src="' + escapeAttr(iconSrc) + '" alt="' + escapeAttr(app.name) + '" width="56" height="56" loading="lazy">'
        : '<img src="" alt="" width="56" height="56" style="display:none">') +
      '<div class="app-info">' +
      "<h3>" + escapeHtml(app.name || "Unknown App") + "</h3>" +
      (metaParts.length ? '<div class="app-meta">' + escapeHtml(metaParts.join(" · ")) + "</div>" : "") +
      (desc ? '<div class="app-desc">' + escapeHtml(desc) + "</div>" : "") +
      "</div>" +
      '<div class="app-actions">' +
      (distribution !== "pal"
        ? '<a class="btn btn-small-classic" href="altstore-classic://source?url=' +
          encodeURIComponent(resolveUrl(CLASIC_JSON)) + '">Classic</a>'
        : "") +
      (distribution !== "classic"
        ? '<a class="btn btn-small-pal" href="altstore-pal://source?url=' +
          encodeURIComponent(resolveUrl(PAL_JSON)) + '">PAL</a>'
        : "") +
      "</div>";

    return card;
  }

  function renderApps(data) {
    var container = document.getElementById("apps-list");
    if (!container) return;

    if (!data || !data.apps || data.apps.length === 0) {
      container.innerHTML = '<p class="empty">No apps available yet.</p>';
      return;
    }

    container.innerHTML = "";
    var seen = {};
    for (var i = 0; i < data.apps.length; i++) {
      var app = data.apps[i];
      var key = app.bundleIdentifier || app.name;
      if (seen[key]) continue;
      seen[key] = true;
      container.appendChild(createAppCard(app, app.distribution || ""));
    }
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return str.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function loadApps() {
    fetch(SOURCE_JSON)
      .then(function (res) {
        if (!res.ok) throw new Error("Failed to load sources");
        return res.json();
      })
      .then(renderApps)
      .catch(function () {
        var container = document.getElementById("apps-list");
        if (container) container.innerHTML = '<p class="empty">Could not load apps. Please try again later.</p>';
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initLinks();
    loadApps();
  });
})();
