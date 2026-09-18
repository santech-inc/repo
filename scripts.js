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

  function formatSize(bytes) {
    if (!bytes) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    var d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  }

  function buildDetailPanel(app) {
    var panel = document.createElement("div");
    panel.className = "app-detail-panel";

    var html = "";

    // Screenshots
    var screenshots = app.screenshotURLs || [];
    if (screenshots.length > 0) {
      html += '<div class="detail-screenshots">';
      for (var s = 0; s < screenshots.length; s++) {
        var src = resolveUrl(screenshots[s]);
        html += '<img src="' + escapeAttr(src) + '" alt="Screenshot ' + (s + 1) + '" loading="lazy">';
      }
      html += "</div>";
    }

    // Description
    var desc = app.localizedDescription || "";
    if (desc) {
      html += '<div class="detail-description">' + escapeHtml(desc).replace(/\n/g, "<br>") + "</div>";
    }

    // Version info
    var versions = app.versions || [];
    if (versions.length > 0) {
      var latest = versions[0];
      html += '<div class="detail-version-info">';
      html += '<div class="detail-info-grid">';
      html += '<div class="detail-info-item"><span class="detail-info-label">Version</span><span class="detail-info-value">' + escapeHtml(latest.version || "") + "</span></div>";
      html += '<div class="detail-info-item"><span class="detail-info-label">Build</span><span class="detail-info-value">' + escapeHtml(latest.buildVersion || "") + "</span></div>";
      if (latest.size) {
        html += '<div class="detail-info-item"><span class="detail-info-label">Size</span><span class="detail-info-value">' + formatSize(latest.size) + "</span></div>";
      }
      if (latest.minOSVersion) {
        html += '<div class="detail-info-item"><span class="detail-info-label">Requires</span><span class="detail-info-value">iOS ' + escapeHtml(latest.minOSVersion) + "</span></div>";
      }
      if (latest.date) {
        html += '<div class="detail-info-item"><span class="detail-info-label">Released</span><span class="detail-info-value">' + formatDate(latest.date) + "</span></div>";
      }
      html += "</div>";
      html += "</div>";
    }

    // Changelog
    if (versions.length > 0) {
      html += '<div class="detail-changelog">';
      html += '<h4 class="detail-changelog-title">What\'s New</h4>';
      html += '<div class="detail-changelog-list">';
      for (var v = 0; v < versions.length; v++) {
        var ver = versions[v];
        var notes = ver.localizedDescription || "";
        html += '<div class="detail-changelog-entry">';
        html += '<div class="detail-changelog-header">';
        html += '<span class="detail-changelog-version">v' + escapeHtml(ver.version || "") + "</span>";
        if (ver.date) {
          html += '<span class="detail-changelog-date">' + formatDate(ver.date) + "</span>";
        }
        html += "</div>";
        if (notes) {
          html += '<div class="detail-changelog-notes">' + escapeHtml(notes).replace(/\n/g, "<br>") + "</div>";
        }
        html += "</div>";
      }
      html += "</div>";
      html += "</div>";
    }

    panel.innerHTML = html;
    return panel;
  }

  function toggleAppDetail(card, app) {
    var existing = card.querySelector(".app-detail-panel");
    if (existing) {
      collapseCard(card);
      return;
    }

    // Collapse any other expanded card
    var allCards = document.querySelectorAll(".app-card.expanded");
    for (var i = 0; i < allCards.length; i++) {
      collapseCard(allCards[i]);
    }

    card.classList.add("expanded");
    var panel = buildDetailPanel(app);
    card.appendChild(panel);

    // Force reflow then animate
    panel.offsetHeight;
    panel.classList.add("open");
  }

  function collapseCard(card) {
    var panel = card.querySelector(".app-detail-panel");
    if (panel) {
      panel.classList.remove("open");
      card.classList.remove("expanded");
      var p = panel;
      setTimeout(function () {
        if (p.parentNode) p.parentNode.removeChild(p);
      }, 300);
    } else {
      card.classList.remove("expanded");
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
      (app.versions && app.versions[0] && app.versions[0].downloadURL
        ? '<a class="btn btn-download" href="' + resolveUrl(app.versions[0].downloadURL) + '" download>Download IPA</a>'
        : "") +
      "</div>";

    // Click handler for expanding details (not on action buttons)
    card.addEventListener("click", function (e) {
      if (e.target.closest(".app-actions")) return;
      toggleAppDetail(card, app);
    });

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
