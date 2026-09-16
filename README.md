# Detay NDT — Kurumsal Web Sitesi

Doğal gaz iletim/dağıtım hatlarında tahribatsız muayene (NDT) hizmeti veren **Detay NDT**
için hazırlanmış, kurulum gerektirmeyen statik kurumsal web sitesi.

- **Teknoloji:** saf HTML + CSS + JavaScript (framework, derleme adımı ve npm bağımlılığı yok)
- **Dil:** Türkçe
- **Tema:** koyu endüstriyel — alacakaranlık atmosferi, safety-orange (`#ff7a1a`) ve cyan (`#22d3ee`) vurgular
- **Kahraman görsel:** yer altı boru hattı, kaynak muayene düğümleri, iş makinesi ve saha ekibini
  gösteren, tamamı kodla üretilmiş animasyonlu izometrik SVG sahne + canlı telemetri katmanı

## Çalıştırma

Dosyayı çift tıklayıp tarayıcıda açmak yeterlidir:

```bash
open index.html        # macOS
xdg-open index.html    # Linux
```

Yerel sunucu tercih ederseniz:

```bash
python3 -m http.server 8000     # http://localhost:8000
```

## Dosya yapısı

```
.
├── index.html          Ana sayfa (izometrik sahne, hizmetler, süreç, projeler, CTA)
├── hizmetler.html      Muayene yöntemleri (RT, UT, PAUT/TOFD, MT, PT, VT, PMI, basınç testi) + SSS
├── projeler.html       Referans projeler
├── kurumsal.html       Hakkımızda, kalite/belgeler, İSG, değerler
├── iletisim.html       Teklif formu, iletişim bilgileri, konum görseli
└── assets/
    ├── css/
    │   ├── style.css   Tüm tasarım (değişkenler, bileşenler, animasyonlar, duyarlı düzen)
    │   └── fonts.css   Yerel @font-face tanımları
    ├── fonts/          Inter, Space Grotesk, JetBrains Mono (woff2, latin + latin-ext)
    ├── img/favicon.svg
    └── js/main.js      Menü, kaydırma animasyonları, sayaçlar, telemetri, SSS, form doğrulama
```

Yazı tipleri siteyle birlikte geldiği için dış bir CDN'e (Google Fonts) istek yapılmaz;
site çevrimdışı da doğru görünür ve ziyaretçi verisi üçüncü tarafa gitmez.

## İçeriği özelleştirme

### 1. Firma bilgileri (önce bunları değiştirin)

Aşağıdaki değerler **örnek/temsilî**dir; gerçek bilgilerle değiştirilmelidir. Tümü beş HTML
dosyasında düz metin olarak geçer, arayıp değiştirmeniz yeterlidir:

| Alan | Şu anki örnek değer |
|---|---|
| Telefon | `+90 312 000 00 00` (`tel:+903120000000`) |
| Saha destek hattı | `+90 500 000 00 00` |
| E-posta | `info@detayndt.com`, `teklif@detayndt.com` |
| Adres | `OSTİM OSB, 1234. Cadde No: 00 — Yenimahalle / Ankara` |
| Sayısal veriler | 18 yıl, 2.400 km, 128.000+ kaynak, %99,1 kabul, 46 proje |
| Belgeler | EN ISO 9712, ISO 9001:2015, TS EN ISO/IEC 17020, API 1104, ASME B31.8, ISO 45001 |
| Referans projeler | `projeler.html` içindeki dört kart |

Örnek toplu değişiklik:

```bash
grep -rl "+90 312 000 00 00" *.html | xargs sed -i 's/+90 312 000 00 00/+90 312 123 45 67/g'
```

> Belge ve sertifika satırlarını yalnızca firmanın gerçekten sahip olduğu belgelerle
> doldurun; sahip olunmayan akreditasyonların sitede yer alması yanıltıcı olur.

### 2. Renkler ve tipografi

Tüm tasarım değişkenleri `assets/css/style.css` dosyasının başındaki `:root` bloğundadır:

```css
--orange: #ff7a1a;   /* birincil vurgu  */
--cyan:   #22d3ee;   /* dijital/telemetri vurgusu */
--bg:     #070a10;   /* sayfa zemini */
```

### 3. Menü, üstbilgi ve altbilgi

Üstbilgi ve altbilgi her sayfada aynı şekilde tekrarlanır (derleme adımı olmadığı için).
Menüye sayfa ekler veya iletişim bilgisini değiştirirseniz **beş HTML dosyasında da**
güncelleyin. Aktif menü öğesi ilgili sayfada `class="nav__link is-active"` ile işaretlidir.

### 4. Teklif formunu çalışır hâle getirme

`iletisim.html` içindeki form şu anda yalnızca tarayıcı tarafında doğrulama yapar ve
başarı mesajı gösterir — **veri hiçbir yere gönderilmez**. Sunucu tarafı olmadan çalıştırmak
için bir form servisine bağlamak yeterlidir:

```html
<!-- iletisim.html -->
<form class="form" id="quoteForm" action="https://formspree.io/f/XXXXXXX" method="POST">
```

Ardından `assets/js/main.js` içindeki `form.addEventListener("submit", ...)` bloğunda
`e.preventDefault()` satırını kaldırın (doğrulama kodu olduğu gibi kalabilir). Kendi
sunucunuz varsa `action` alanına kendi uç noktanızı yazın.

## Yayına alma

Statik bir site olduğu için herhangi bir sunucuya kopyalamanız yeterlidir.
GitHub Pages ile yayınlamak için: depo ayarlarından **Settings → Pages → Source: Deploy from
a branch** seçip yayınlanacak dalı ve `/ (root)` klasörünü işaretleyin.

Yayına almadan önce yapılması önerilenler:

- Gerçek alan adına göre `<meta property="og:url">` ve bir `og:image` görseli ekleyin
- Google Analytics / Search Console gibi araçları ekleyin (KVKK aydınlatma metniyle birlikte)
- Gerçek saha fotoğrafları eklenecekse `assets/img/` altına koyup ilgili SVG görselleri
  `<img>` ile değiştirin

## Erişilebilirlik ve performans notları

- Klavye ile tam gezinilebilir; odak halkaları ve "İçeriğe geç" bağlantısı mevcut
- `prefers-reduced-motion` açıkken tüm animasyonlar devre dışı kalır
- Tüm görseller SVG olduğu için sayfa ağırlığı düşüktür; resim optimizasyonu gerekmez
- Mobil, tablet ve masaüstü için ayrı kırılım noktaları tanımlıdır (900px ve 620px)
