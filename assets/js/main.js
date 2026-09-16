/* ==========================================================================
   Detay NDT — arayüz davranışları
   Bağımlılık yok; tüm modüller ilgili element yoksa sessizce atlanır.
   ========================================================================== */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- 1. Yapışkan başlık ---- */
  var header = document.getElementById("siteHeader");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- 2. Mobil menü ---- */
  var toggle = document.getElementById("navToggle");
  var list = document.getElementById("navList");
  if (toggle && list) {
    toggle.addEventListener("click", function () {
      var open = list.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    list.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        list.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && list.classList.contains("is-open")) {
        list.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ---- 3. Kaydırmayla görünürlük ---- */
  var revealables = document.querySelectorAll(".reveal");
  if (revealables.length) {
    if (!("IntersectionObserver" in window) || reduceMotion) {
      revealables.forEach(function (el) { el.classList.add("is-visible"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });
      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---- 4. Sayaçlar ---- */
  function formatNumber(value, decimals, sep) {
    var text = decimals ? value.toFixed(decimals) : String(Math.round(value));
    if (!sep) return text;
    var parts = text.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return parts.join(",");
  }

  function runCounter(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    var decimals = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var sep = el.hasAttribute("data-sep");
    if (isNaN(target)) return;
    if (reduceMotion) { el.textContent = formatNumber(target, decimals, sep); return; }

    var duration = 1500;
    var start = null;
    function frame(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = formatNumber(target * eased, decimals, sep);
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  var counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    if (!("IntersectionObserver" in window)) {
      counters.forEach(runCounter);
    } else {
      var co = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            runCounter(entry.target);
            co.unobserve(entry.target);
          }
        });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { co.observe(el); });
    }
  }

  /* ---- 5. Telemetri göstergeleri (hero HUD) ---- */
  var tickers = document.querySelectorAll("[data-ticker]");
  if (tickers.length && !reduceMotion) {
    setInterval(function () {
      if (document.hidden) return;
      tickers.forEach(function (el) {
        var min = parseFloat(el.getAttribute("data-min"));
        var max = parseFloat(el.getAttribute("data-max"));
        var unit = el.querySelector("small");
        var digits = parseInt(el.getAttribute("data-decimals") || "1", 10);
        var value = (min + Math.random() * (max - min)).toFixed(digits);
        el.textContent = value.replace(".", ",");
        if (unit) el.appendChild(unit);
      });
    }, 2600);
  }

  /* ---- 6. SSS akordiyonu ---- */
  document.querySelectorAll(".faq__q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var item = btn.closest(".faq__item");
      var open = item.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", String(open));
    });
  });

  /* ---- 7. Teklif formu doğrulaması ---- */
  var form = document.getElementById("quoteForm");
  if (form) {
    var success = document.getElementById("formSuccess");

    var setError = function (field, message) {
      var wrap = field.closest(".field");
      var box = wrap.querySelector(".field__error");
      wrap.classList.toggle("field--error", Boolean(message));
      field.setAttribute("aria-invalid", message ? "true" : "false");
      if (box) box.textContent = message || "";
    };

    var validate = function (field) {
      var value = field.value.trim();
      if (field.required && !value) { setError(field, "Bu alan zorunludur."); return false; }
      if (field.type === "email" && value && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) {
        setError(field, "Geçerli bir e-posta adresi girin."); return false;
      }
      if (field.type === "tel" && value && value.replace(/\D/g, "").length < 10) {
        setError(field, "Telefon numarası eksik görünüyor."); return false;
      }
      setError(field, "");
      return true;
    };

    form.querySelectorAll("input, select, textarea").forEach(function (field) {
      field.addEventListener("blur", function () { validate(field); });
      field.addEventListener("input", function () {
        if (field.closest(".field").classList.contains("field--error")) validate(field);
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fields = Array.prototype.slice.call(form.querySelectorAll("input, select, textarea"));
      var valid = fields.map(validate).every(Boolean);
      if (!valid) {
        var firstError = form.querySelector(".field--error input, .field--error select, .field--error textarea");
        if (firstError) firstError.focus();
        return;
      }
      // Not: sunucu tarafı henüz bağlı değil — README'deki adımlarla form servisine yönlendirin.
      if (success) {
        success.classList.add("is-visible");
        success.setAttribute("role", "status");
      }
      form.reset();
    });
  }

  /* ---- 8. Yıl bilgisi ---- */
  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
