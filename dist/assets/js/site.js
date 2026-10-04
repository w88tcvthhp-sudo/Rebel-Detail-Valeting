/* Rebel Detail & Valeting: progressive enhancement only. Everything works without this file. */
(function () {
  "use strict";
  var cfg = window.REBEL || {};

  /* Mobile navigation */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    };
    toggle.addEventListener("click", function () { setOpen(toggle.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) { setOpen(false); toggle.focus(); }
    });
    window.matchMedia("(min-width: 64rem)").addEventListener("change", function (m) { if (m.matches) setOpen(false); });
  }

  /* Before/after sliders */
  document.querySelectorAll("[data-ba]").forEach(function (fig) {
    var frame = fig.querySelector(".ba-frame");
    var range = fig.querySelector(".ba-range");
    if (!frame || !range) return;
    var update = function () { frame.style.setProperty("--pos", range.value + "%"); };
    range.addEventListener("input", update);
    update();
  });

  /* Contact form: preselect service from ?service= and stop past dates */
  var form = document.querySelector(".quote-form");
  if (form) {
    var svc = new URLSearchParams(location.search).get("service");
    if (svc === "detailing") svc = "polishing";
    if (svc) {
      var radio = form.querySelector('input[name="service"][value="' + CSS.escape(svc) + '"]');
      if (radio) radio.checked = true;
    }
    var date = form.querySelector('input[type="date"]');
    if (date) date.min = new Date().toISOString().slice(0, 10);
    form.addEventListener("submit", function () {
      var chosen = form.querySelector('input[name="service"]:checked');
      track("quote_submit", { service: chosen ? chosen.value : "" });
    });
  }

  /* Mobile action bar: parked while the hero buttons are on screen, hidden while typing */
  var bar = document.querySelector(".actionbar");
  var heroActions = document.querySelector(".hero-actions");
  if (bar && heroActions && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      bar.classList.toggle("is-parked", entries[0].isIntersecting);
    }).observe(heroActions);
  }
  if (bar) {
    document.addEventListener("focusin", function (e) { if (e.target.matches("input, textarea, select")) bar.classList.add("is-hidden"); });
    document.addEventListener("focusout", function () { bar.classList.remove("is-hidden"); });
  }

  /* Conversion tracking: sends GA4 events only when analytics is enabled and consented */
  function track(name, params) {
    if (typeof window.gtag === "function") window.gtag("event", name, params || {});
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-track]");
    if (a) track(a.getAttribute("data-track"), { label: a.getAttribute("data-label") || "", link_url: a.href || "" });
  });

  /* Consent + GA4: only when a measurement ID is configured */
  var KEY = "rebel-consent";
  function loadGA() {
    if (!cfg.gaId || window.gtag) return;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(cfg.gaId);
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", cfg.gaId, { anonymize_ip: true });
  }
  function getChoice() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function setChoice(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function showBanner() {
    if (document.querySelector(".consent")) return;
    var box = document.createElement("div");
    box.className = "consent";
    box.setAttribute("role", "region");
    box.setAttribute("aria-label", "Cookie choice");
    box.innerHTML = '<p>Can we use analytics cookies to see how people use this site? We don\'t use advertising cookies. <a href="/cookies/">Cookie policy</a></p>' +
      '<div class="consent-actions"><button class="btn btn-primary btn-sm" type="button" data-c="yes">Accept</button>' +
      '<button class="btn btn-outline btn-sm" type="button" data-c="no">Reject</button></div>';
    box.addEventListener("click", function (e) {
      var b = e.target.closest("[data-c]");
      if (!b) return;
      setChoice(b.getAttribute("data-c"));
      if (b.getAttribute("data-c") === "yes") loadGA();
      box.remove();
    });
    document.body.appendChild(box);
  }
  if (cfg.gaId) {
    var choice = getChoice();
    if (choice === "yes") loadGA();
    else if (choice !== "no") showBanner();
    document.querySelectorAll("[data-cookie-reset]").forEach(function (b) {
      b.addEventListener("click", function () { try { localStorage.removeItem(KEY); } catch (e) {} showBanner(); });
    });
  }
})();
