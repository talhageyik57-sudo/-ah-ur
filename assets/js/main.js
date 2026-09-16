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

/* ==========================================================================
   Sinematik açılış — kaydırma konumunu sahne durumuna çevirir
   Perdeler: 01 kazı · 02 boru indirme · 03 kaynak · 04 geri dolgu
   ========================================================================== */
(function () {
  "use strict";

  var section = document.getElementById("cinema");
  if (!section) return;

  var svg = document.getElementById("cinemaSvg");
  if (!svg) return;

  var el = function (id) { return document.getElementById(id); };
  var undug     = el("undugRect");
  var backfill  = el("backfillRect");
  var excWrap   = el("excavatorWrap");
  var boom      = el("excBoom");
  var stick     = el("excStick");
  var bucket    = el("excBucket");
  var dust      = el("excDust");
  var digFace   = el("digFace");
  var pipe      = el("pipeGroup");
  var slings    = el("slings");
  var bead      = el("weldBead");
  var welder    = el("welderGroup");
  var weldFx    = el("weldFx");
  var marker    = el("markerPost");
  var sky       = el("skyLayer");
  var hills     = el("hillLayer");
  var hint      = el("cinemaHint");
  var acts      = Array.prototype.slice.call(document.querySelectorAll(".act"));
  var rail      = Array.prototype.slice.call(document.querySelectorAll(".cinema__rail li"));

  // perde aralıkları (0–1 arası genel ilerleme)
  var RANGES = [[0, .30], [.30, .54], [.54, .80], [.80, 1]];
  var STATE  = ["is-dig", "is-lay", "is-weld", "is-fill"];

  var clamp = function (v, a, b) { return v < a ? a : (v > b ? b : v); };
  var span  = function (p, a, b) { return clamp((p - a) / (b - a), 0, 1); };
  var ease  = function (t) { return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; };

  var lastAct = -1;
  var lastState = "";

  function render(p) {
    var dig  = span(p, RANGES[0][0], RANGES[0][1]);
    var lay  = span(p, RANGES[1][0], RANGES[1][1]);
    var weld = span(p, RANGES[2][0], RANGES[2][1]);
    var fill = span(p, RANGES[3][0], RANGES[3][1]);

    var eDig = ease(dig), eLay = ease(lay), eFill = ease(fill);

    // --- kazı: kazılmamış zemin soldan sağa açılır
    var digFront = -190 + 1790 * eDig;
    if (undug) undug.setAttribute("x", digFront.toFixed(1));
    if (digFace) {
      digFace.setAttribute("transform", "translate(" + digFront.toFixed(1) + " 0)");
      digFace.setAttribute("opacity", (dig > 0 && dig < .995 ? 1 : 0).toString());
    }

    // --- geri dolgu: toprak sağdan sola hattın üzerini örter
    var fillFront = 1590 - 1790 * eFill;
    if (backfill) {
      backfill.setAttribute("x", fillFront.toFixed(1));
      backfill.setAttribute("width", fill > 0 ? "1750" : "0");
    }

    // --- ekskavatör: kazarken sağa, dolgu yaparken sola ilerler
    var tx;
    if (fill > 0)      tx = 1160 - 1780 * eFill;
    else if (dig < 1)  tx = -620 + 1780 * eDig;
    else               tx = 1160;
    if (excWrap) excWrap.setAttribute("transform", "translate(" + tx.toFixed(1) + " 500) scale(.86)");

    // kol hareketi (kazı ve dolgu sırasında döngü)
    var working = (dig > 0 && dig < 1) || (fill > 0 && fill < 1);
    var phase = working ? (dig > 0 && dig < 1 ? dig : fill) * Math.PI * 2 * 7 : 0;
    var swing = working ? Math.sin(phase) : 0;
    var swing2 = working ? Math.sin(phase + 1.1) : 0;
    if (boom)   boom.setAttribute("transform", "rotate(" + (-4 + swing * 7).toFixed(2) + " 116 -150)");
    if (stick)  stick.setAttribute("transform", "rotate(" + (6 + swing2 * 13).toFixed(2) + " 292 -262)");
    if (bucket) bucket.setAttribute("transform", "rotate(" + (-8 - swing2 * 20).toFixed(2) + " 360 -140)");
    if (dust)   dust.setAttribute("opacity", working ? "1" : "0");

    // --- boru: hendeğe iner
    if (pipe) {
      pipe.setAttribute("transform", "translate(0 " + (-340 * (1 - eLay)).toFixed(1) + ")");
      pipe.setAttribute("opacity", lay > 0 ? "1" : "0");
    }
    if (slings) {
      var sl = lay <= 0 ? 0 : (lay < .8 ? Math.min(1, lay * 5) : Math.max(0, (1 - lay) / .2));
      slings.setAttribute("opacity", sl.toFixed(2));
    }

    // --- kaynak
    if (bead) {
      var b = span(weld, .14, .62);
      bead.setAttribute("opacity", b.toFixed(2));
      bead.classList.toggle("is-cool", weld > .8);
    }
    if (weldFx) {
      var fx = weld <= .04 ? 0 : (weld < .78 ? Math.min(1, (weld - .04) * 8) : Math.max(0, (.95 - weld) / .17));
      weldFx.setAttribute("opacity", clamp(fx, 0, 1).toFixed(2));
    }
    if (welder) {
      var w = p < RANGES[1][1] - .012 ? 0 : (weld < .92 ? 1 : Math.max(0, (1 - weld) / .08));
      welder.setAttribute("opacity", w.toFixed(2));
    }
    if (marker) marker.setAttribute("opacity", span(fill, .55, .95).toFixed(2));

    // --- derinlik hissi
    if (sky)   sky.setAttribute("transform", "translate(0 " + (-56 + p * 26).toFixed(1) + ")");
    if (hills) hills.setAttribute("transform", "translate(0 " + (-42 + p * 14).toFixed(1) + ")");

    // --- metin ve şerit
    var index = p >= RANGES[3][0] ? 3 : p >= RANGES[2][0] ? 2 : p >= RANGES[1][0] ? 1 : 0;
    if (index !== lastAct) {
      acts.forEach(function (a, i) { a.classList.toggle("is-active", i === index); });
      rail.forEach(function (r, i) {
        r.classList.toggle("is-active", i === index);
        r.classList.toggle("is-done", i < index);
      });
      lastAct = index;
    }
    var state = STATE[index];
    if (state !== lastState) {
      STATE.forEach(function (s) { section.classList.remove(s); });
      section.classList.add(state);
      lastState = state;
    }
    if (hint) hint.classList.toggle("is-hidden", p > .04);
  }

  function fitScene() {
    // dar ekranda sahneyi kırpmak yerine 16:9 şerit olarak göster
    var narrow = window.innerWidth <= 760;
    svg.setAttribute("preserveAspectRatio", narrow ? "xMidYMid meet" : "xMidYMid slice");
    section.classList.toggle("is-banded", narrow);
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var rect = section.getBoundingClientRect();
      var travel = section.offsetHeight - window.innerHeight;
      var p = travel > 0 ? clamp(-rect.top / travel, 0, 1) : 0;
      render(p);
      ticking = false;
    });
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    // hareket azaltma: sabit kare — hat serilmiş, kaynak tamamlanmış hâli
    fitScene();
    render(.78);
    return;
  }

  fitScene();
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", function () { fitScene(); onScroll(); });
})();
