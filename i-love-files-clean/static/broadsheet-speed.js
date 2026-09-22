/* ============================================================================
   I LOVE FILES — Returning-user speed layer
   Adds a "RECENT DISPATCHES" strip above the tool grid for 1-click repeat.
   Non-invasive: wraps the existing global selectQuickTool() without altering it.
   Data is stored locally in the browser (no server calls).
   ============================================================================ */
(function () {
  "use strict";
  var KEY = "ilovefiles_recent_v1";
  var MAX = 6;

  /* Notion tag color lookup matching iconic database multi-select colors */
  var PALETTE = {
    "icon-blue":   { bg: "rgba(211, 229, 239, 0.7)", fg: "#0b6e99", bd: "rgba(11, 110, 153, 0.25)" },
    "icon-green":  { bg: "rgba(219, 237, 219, 0.7)", fg: "#0f7b6c", bd: "rgba(15, 123, 108, 0.25)" },
    "icon-orange": { bg: "rgba(250, 222, 201, 0.7)", fg: "#d9730d", bd: "rgba(217, 115, 13, 0.25)" },
    "icon-purple": { bg: "rgba(232, 222, 238, 0.7)", fg: "#6940a5", bd: "rgba(105, 64, 165, 0.25)" },
    "icon-teal":   { bg: "rgba(211, 229, 239, 0.7)", fg: "#0b6e99", bd: "rgba(11, 110, 153, 0.25)" },
    "icon-red":    { bg: "rgba(251, 228, 228, 0.7)", fg: "#e03e3e", bd: "rgba(224, 62, 62, 0.25)" },
    "icon-dark":   { bg: "rgba(206, 205, 202, 0.5)", fg: "#37352f", bd: "rgba(55, 53, 47, 0.16)" }
  };

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX))); } catch (e) {}
  }

  /* Pull tool metadata (badge text, colour class, label) straight from the
     existing DOM card so we never hardcode or duplicate the icon design. */
  function toolMeta(toolId) {
    var card = document.querySelector('.tool-card[data-tool="' + toolId + '"]') ||
               document.getElementById('card-' + toolId);
    var meta = { badge: "?", cls: "icon-dark", label: toolId, ext: "" };
    if (!card) return meta;
    var wrap = card.querySelector('.tool-icon-wrap');
    if (wrap) {
      var span = wrap.querySelector('span');
      if (span) meta.badge = span.textContent.trim();
      wrap.classList.forEach(function (c) { if (PALETTE[c]) meta.cls = c; });
    }
    var lab = card.querySelector('.tool-label');
    if (lab) meta.label = lab.textContent.trim();
    meta.ext = card.getAttribute('data-ext') || "";
    return meta;
  }

  function remember(toolId, title, ext) {
    if (!toolId) return;
    var list = read().filter(function (x) { return x.id !== toolId; });
    list.unshift({ id: toolId, title: title || toolId, ext: ext || "", t: Date.now() });
    write(list);
    render();
  }

  function timeAgo(ts) {
    var s = Math.floor((Date.now() - ts) / 1000);
    if (s < 60) return "just now";
    var m = Math.floor(s / 60); if (m < 60) return m + "m ago";
    var h = Math.floor(m / 60); if (h < 24) return h + "h ago";
    var d = Math.floor(h / 24); return d + "d ago";
  }

  function ensureContainer() {
    var host = document.getElementById('ilf-recent');
    if (host) return host;
    var grid = document.getElementById('tools-catalog-grid');
    if (!grid) return null;
    // place the strip above the filter pills if present, else above the grid
    var anchor = document.querySelector('.hub-filter-pills') || grid;
    host = document.createElement('div');
    host.id = 'ilf-recent';
    host.className = 'recent-dispatch';
    host.style.display = 'none';
    anchor.parentNode.insertBefore(host, anchor);
    return host;
  }

  function render() {
    var host = ensureContainer();
    if (!host) return;
    var list = read();
    if (!list.length) { host.style.display = 'none'; return; }
    host.style.display = 'block';

    var chips = list.map(function (item) {
      var m = toolMeta(item.id);
      var p = PALETTE[m.cls] || PALETTE["icon-dark"];
      var safeTitle = (item.title || m.label).replace(/"/g, '&quot;');
      var safeExt = (item.ext || m.ext || '').replace(/"/g, '&quot;');
      return '' +
        '<div class="recent-chip" role="button" tabindex="0" ' +
             'data-id="' + item.id + '" data-title="' + safeTitle + '" data-ext="' + safeExt + '">' +
          '<span class="recent-chip-badge" style="background:' + p.bg + ';color:' + p.fg + ';border:1px solid ' + p.bd + '">' + m.badge + '</span>' +
          '<span class="recent-chip-body">' +
            '<span class="recent-chip-tool">' + safeTitle + '</span>' +
            '<span class="recent-chip-meta">' + timeAgo(item.t) + '</span>' +
          '</span>' +
          '<span class="recent-chip-go">&rsaquo;</span>' +
        '</div>';
    }).join('');

    host.innerHTML =
      '<div class="recent-dispatch-head">' +
        '<span class="recent-dispatch-title">Jump Back In · Recently Used</span>' +
        '<button class="recent-clear" type="button">Clear</button>' +
      '</div>' +
      '<div class="recent-row">' + chips + '</div>';

    host.querySelector('.recent-clear').addEventListener('click', function () {
      write([]); render();
    });
    Array.prototype.forEach.call(host.querySelectorAll('.recent-chip'), function (chip) {
      function go() {
        if (typeof window.switchTab === 'function') window.switchTab('convert');
        if (typeof window.selectQuickTool === 'function') {
          window.selectQuickTool(chip.dataset.id, chip.dataset.title, chip.dataset.ext);
        }
      }
      chip.addEventListener('click', go);
      chip.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
      });
    });
  }

  /* Wrap the existing global without changing its behaviour */
  function hook() {
    if (typeof window.selectQuickTool !== 'function') return false;
    if (window.__ilfHooked) return true;
    var original = window.selectQuickTool;
    window.selectQuickTool = function (toolId, title, ext) {
      try { remember(toolId, title, ext); } catch (e) {}
      return original.apply(this, arguments);
    };
    window.__ilfHooked = true;
    return true;
  }

  function boot() {
    var tries = 0;
    (function attempt() {
      var ok = hook();
      render();
      if (!ok && tries++ < 40) setTimeout(attempt, 150); // wait for app.js globals
    })();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
