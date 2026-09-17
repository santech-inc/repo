(function () {
  "use strict";

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
    try {
      return new URL(relative, baseUrl).href;
    } catch (_) {
      return relative;
    }
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
    var classicUrl = resolveUrl(CLASIC_JSON);
    var palUrl = resolveUrl(PAL_JSON);

    var btnClassic = document.getElementById("btn-classic");
    var btnPal = document.getElementById("btn-pal");
    if (btnClassic) btnClassic.href = "altstore-classic://source?url=" + encodeURIComponent(classicUrl);
    if (btnPal) btnPal.href = "altstore-pal://source?url=" + encodeURIComponent(palUrl);

    var urlClassic = document.getElementById("url-classic");
    var urlPal = document.getElementById("url-pal");
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

  function createAppCard(app, dists) {
    var card = document.createElement("div");
    card.className = "app-card";

    var iconSrc = app.iconURL ? resolveUrl(app.iconURL) : "";
    var metaParts = [];
    if (app.developerName) metaParts.push(app.developerName);
    if (app.category) metaParts.push(app.category);
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
      (dists.classic
        ? '<a class="btn btn-small-classic" href="altstore-classic://source?url=' +
          encodeURIComponent(resolveUrl(CLASIC_JSON)) + '">Classic</a>'
        : "") +
      (dists.pal
        ? '<a class="btn btn-small-pal" href="altstore-pal://source?url=' +
          encodeURIComponent(resolveUrl(PAL_JSON)) + '">PAL</a>'
        : "") +
      "</div>";

    return card;
  }

  function mergeApps(classicData, palData) {
    var apps = {};

    if (classicData && classicData.apps) {
      for (var i = 0; i < classicData.apps.length; i++) {
        var app = classicData.apps[i];
        var key = app.bundleIdentifier || app.name;
        apps[key] = { app: app, dists: { classic: true, pal: false } };
      }
    }

    if (palData && palData.apps) {
      for (var j = 0; j < palData.apps.length; j++) {
        var palApp = palData.apps[j];
        var palKey = palApp.bundleIdentifier || palApp.name;
        if (apps[palKey]) {
          apps[palKey].dists.pal = true;
        } else {
          apps[palKey] = { app: palApp, dists: { classic: false, pal: true } };
        }
      }
    }

    return apps;
  }

  function renderApps(apps) {
    var container = document.getElementById("apps-list");
    if (!container) return;

    var keys = Object.keys(apps);
    var summary = document.getElementById("apps-summary");
    if (summary) {
      summary.textContent = keys.length === 1
        ? "1 app available from SanTech Inc."
        : keys.length + " apps available from SanTech Inc.";
    }
    if (keys.length === 0) {
      container.innerHTML = '<p class="empty">No apps available yet.</p>';
      return;
    }

    container.innerHTML = "";
    for (var i = 0; i < keys.length; i++) {
      var entry = apps[keys[i]];
      container.appendChild(createAppCard(entry.app, entry.dists));
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

  function fetchJson(url) {
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error("Failed to load " + url);
      return res.json();
    });
  }

  function loadApps() {
    Promise.all([fetchJson(CLASIC_JSON), fetchJson(PAL_JSON)])
      .then(function (results) {
        var apps = mergeApps(results[0], results[1]);
        renderApps(apps);
      })
      .catch(function () {
        var container = document.getElementById("apps-list");
        if (container) container.innerHTML = '<p class="empty">Could not load apps.</p>';
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initLinks();
    loadApps();
  });
})();
