/* Detay NDT — site davranışları (bağımlılık yok) */
(function () {
  "use strict";

  var doc = document.documentElement;
  var body = document.body;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  doc.classList.remove("no-js");

  /* ---- Açılış başlığı: satır satır belirme ---- */
  requestAnimationFrame(function () {
    requestAnimationFrame(function () { body.classList.add("is-ready"); });
  });

  /* ---- Üstbilgi: kaydırınca katılaşır, aşağı inerken gizlenir ---- */
  var header = document.querySelector(".header");
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    if (!header) return;
    header.classList.toggle("is-scrolled", y > 24);
    if (!body.classList.contains("menu-open")) {
      header.classList.toggle("is-hidden", y > 420 && y > lastY + 2);
      if (y < lastY - 2) header.classList.remove("is-hidden");
    }
    lastY = y;
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---- Mobil menü ---- */
  var burger = document.querySelector(".burger");
  var drawer = document.getElementById("drawer");
  function setMenu(open) {
    body.classList.toggle("menu-open", open);
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Menüyü kapat" : "Menüyü aç");
    drawer.setAttribute("aria-hidden", String(!open));
    if (open) header.classList.remove("is-hidden");
  }
  if (burger && drawer) {
    burger.addEventListener("click", function () { setMenu(!body.classList.contains("menu-open")); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && body.classList.contains("menu-open")) { setMenu(false); burger.focus(); }
    });
    drawer.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    window.addEventListener("resize", function () { if (window.innerWidth > 1080) setMenu(false); });
  }

  /* ---- Görünme animasyonları ---- */
  var revealEls = document.querySelectorAll(".reveal, .phases");
  if (reduce || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .08 });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* ---- Sayaçlar ---- */
  function fmt(n) { return Math.round(n).toLocaleString("tr-TR"); }
  function runCounter(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    if (reduce) { el.textContent = fmt(target); return; }
    var start = null, dur = 1800;
    function tick(t) {
      if (start === null) start = t;
      var p = Math.min((t - start) / dur, 1);
      el.textContent = fmt(target * (1 - Math.pow(1 - p, 4)));
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  var counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    if (!("IntersectionObserver" in window)) {
      counters.forEach(function (el) { el.textContent = fmt(parseFloat(el.getAttribute("data-count"))); });
    } else {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { runCounter(en.target); cio.unobserve(en.target); }
        });
      }, { threshold: .4 });
      counters.forEach(function (el) { cio.observe(el); });
    }
  }

  /* ---- Yıl ---- */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---- Teklif formu doğrulaması ---- */
  var form = document.getElementById("quoteForm");
  if (form) {
    var ok = document.getElementById("formOk");
    var rules = {
      name: function (v) { return v.trim().length >= 3 || "Lütfen adınızı ve soyadınızı yazın."; },
      company: function (v) { return v.trim().length >= 2 || "Firma adını yazın."; },
      email: function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) || "Geçerli bir e-posta adresi yazın."; },
      phone: function (v) { return v.replace(/\D/g, "").length >= 10 || "Telefon numarası en az 10 haneli olmalı."; },
      service: function (v) { return v !== "" || "Bir hizmet seçin."; },
      message: function (v) { return v.trim().length >= 20 || "Projenizi birkaç cümleyle anlatın (en az 20 karakter)."; }
    };
    function check(input) {
      var rule = rules[input.name];
      if (!rule) return true;
      var res = rule(input.value);
      var field = input.closest(".field");
      var err = field.querySelector(".field__err");
      var bad = res !== true;
      field.classList.toggle("is-invalid", bad);
      input.setAttribute("aria-invalid", String(bad));
      if (err) err.textContent = bad ? res : "";
      return !bad;
    }
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!rules[el.name]) return;
      el.addEventListener("blur", function () { check(el); });
      el.addEventListener("input", function () {
        if (el.closest(".field").classList.contains("is-invalid")) check(el);
      });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault(); // Form servisine bağlanınca kaldırın (bkz. README)
      var firstBad = null;
      Array.prototype.forEach.call(form.elements, function (el) {
        if (rules[el.name] && !check(el) && !firstBad) firstBad = el;
      });
      if (firstBad) { firstBad.focus(); return; }
      ok.classList.add("is-shown");
      ok.focus();
      form.reset();
    });
  }
})();
