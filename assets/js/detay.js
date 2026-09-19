/* Detay NDT — ortak arayüz davranışları */
(function(){
  var hdr = document.querySelector('.hdr');
  var nav = document.getElementById('nav');
  var burger = document.getElementById('burger');

  if (hdr){
    var onScroll = function(){ hdr.classList.toggle('is-stuck', window.scrollY > 30); };
    window.addEventListener('scroll', onScroll, { passive:true });
    onScroll();
  }
  if (burger && nav){
    burger.addEventListener('click', function(){
      var open = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function(e){
      if (e.target.tagName === 'A'){ nav.classList.remove('is-open'); burger.setAttribute('aria-expanded','false'); }
    });
  }

  /* kaydırmayla beliren bloklar */
  var items = document.querySelectorAll('.rv');
  if (items.length){
    if (!('IntersectionObserver' in window)){
      items.forEach(function(el){ el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(en){
          if (en.isIntersecting){ en.target.classList.add('is-in'); io.unobserve(en.target); }
        });
      }, { rootMargin:'0px 0px -12% 0px', threshold:0.08 });
      items.forEach(function(el, i){
        el.style.transitionDelay = (Math.min(i % 4, 3) * 70) + 'ms';
        io.observe(el);
      });
    }
  }

  /* sayaçlar */
  var nums = document.querySelectorAll('[data-count]');
  if (nums.length && 'IntersectionObserver' in window){
    var io2 = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if (!en.isIntersecting) return;
        var el = en.target, to = parseFloat(el.getAttribute('data-count')), t0 = null;
        var step = function(ts){
          if (!t0) t0 = ts;
          var k = Math.min(1, (ts - t0) / 1400);
          var e = 1 - Math.pow(1 - k, 3);
          el.textContent = (to % 1 ? (to * e).toFixed(1) : Math.round(to * e)).toString();
          if (k < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        io2.unobserve(el);
      });
    }, { threshold:0.4 });
    nums.forEach(function(el){ io2.observe(el); });
  }

  /* yıl */
  var y = document.getElementById('yil');
  if (y) y.textContent = new Date().getFullYear();

  /* iletişim formu — sunucusuz demo */
  var form = document.getElementById('teklifForm');
  if (form){
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var ok = document.getElementById('formOk');
      if (ok){ ok.hidden = false; ok.scrollIntoView({ behavior:'smooth', block:'center' }); }
      form.reset();
    });
  }
})();
