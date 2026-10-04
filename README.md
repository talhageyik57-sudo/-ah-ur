# Detay NDT — Kurumsal Web Sitesi

Doğal gaz iletim/dağıtım hatlarında tahribatsız muayene (NDT) hizmeti veren **Detay NDT**
için hazırlanmış, kurulum gerektirmeyen statik kurumsal web sitesi.

- **Teknoloji:** saf HTML + CSS + JavaScript (framework, derleme adımı ve npm bağımlılığı yok)
- **Dil:** Türkçe
- **Tarz:** premium / editoryal — fildişi kâğıt zemin, espresso koyu bantlar, pirinç (`#9c7a43`)
  vurgu, serif başlıklar (Cormorant Garamond) ve Inter gövde metni
- **Görseller:** fotoğraf yerine mühendislik çizimi ("levha") estetiğinde, elle çizilmiş ince çizgi
  SVG'ler — boru kesiti ve kaynak detayı, panoramik radyografi, darbe–yankı UT, faz dizili tarama

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
├── index.html          Ana sayfa (levha çizimli açılış, yaklaşım, hizmetler, süreç, projeler, CTA)
├── kurumsal.html       Hakkımızda, sertifikalı personel, kalite/belgeler, İSG, değerler
├── hizmetler.html      RT, UT, PAUT/TOFD bölümleri + MT, PT, VT, PMI, basınç testi + SSS
├── surec.html          Kazıdan devreye almaya 10 adım, örnek kaynak kaydı, ekipman, standartlar
├── projeler.html       Sayaçlar ve dört referans proje
├── iletisim.html       Teklif formu ve iletişim bilgileri
└── assets/
    ├── css/
    │   ├── style.css   Tüm tasarım (değişkenler, bileşenler, duyarlı düzen)
    │   └── fonts.css   Yerel @font-face tanımları
    ├── fonts/          Cormorant Garamond, Inter (woff2, latin + latin-ext)
    ├── img/favicon.svg
    └── js/main.js      Üstbilgi, mobil menü, görünme animasyonları, sayaçlar, form doğrulama
```

Yazı tipleri siteyle birlikte geldiği için dış bir CDN'e (Google Fonts) istek yapılmaz;
site çevrimdışı da doğru görünür ve ziyaretçi verisi üçüncü tarafa gitmez. Her iki yazı tipi de
SIL Open Font License ile dağıtılır.

## İçeriği özelleştirme

### 1. Firma bilgileri (önce bunları değiştirin)

Aşağıdaki değerler **örnek/temsilî**dir; gerçek bilgilerle değiştirilmelidir. Tümü HTML
dosyalarında düz metin olarak geçer, arayıp değiştirmeniz yeterlidir:

| Alan | Şu anki örnek değer |
|---|---|
| Telefon | `+90 312 000 00 00` (`tel:+903120000000`) |
| Saha destek hattı | `+90 500 000 00 00` |
| E-posta | `info@detayndt.com`, `teklif@detayndt.com` |
| Adres | `OSTİM OSB, 1234. Cadde No: 00 — Yenimahalle / Ankara` |
| Kuruluş yılı | `2008` (ana sayfa açılışı) |
| Sayısal veriler | 18 yıl, 2.400 km, 128.000+ kaynak, %99,1 kabul, 46 proje, 12 ekip |
| Belgeler | EN ISO 9712, ISO 9001:2015, TS EN ISO/IEC 17020, API 1104, ASME B31.8, ISO 45001 |
| Referans projeler | `projeler.html` içindeki dört proje, ana sayfadaki iki vitrin kartı |

Örnek toplu değişiklik:

```bash
grep -rl "+90 312 000 00 00" *.html | xargs sed -i 's/+90 312 000 00 00/+90 312 123 45 67/g'
```

> Belge ve sertifika satırlarını yalnızca firmanın gerçekten sahip olduğu belgelerle
> doldurun; sahip olunmayan akreditasyonların sitede yer alması yanıltıcı olur.

Sayaçlar `data-count` niteliğinden okunur; bir rakamı değiştirirken hem `data-count`
değerini hem de etiketin içindeki metni güncelleyin.

### 2. Renkler ve tipografi

Tüm tasarım değişkenleri `assets/css/style.css` dosyasının başındaki `:root` bloğundadır:

```css
--ivory: #f4efe5;   /* sayfa zemini */
--night: #15120f;   /* koyu bantlar ve altbilgi */
--gold:  #9c7a43;   /* açık zeminde vurgu */
--gold-2:#c8a66b;   /* koyu zeminde vurgu */
--serif: 'Cormorant Garamond', ...;
--sans:  'Inter', ...;
```

### 3. Menü, üstbilgi ve altbilgi

Üstbilgi, mobil menü ve altbilgi her sayfada aynı şekilde tekrarlanır (derleme adımı olmadığı
için). Menüye sayfa ekler veya iletişim bilgisini değiştirirseniz **altı HTML dosyasında da**
güncelleyin. Aktif menü öğesi ilgili sayfada `class="nav__link is-active"` ve
`aria-current="page"` ile işaretlidir.

### 4. Teklif formunu çalışır hâle getirme

`iletisim.html` içindeki form şu anda yalnızca tarayıcı tarafında doğrulama yapar ve
başarı mesajı gösterir — **veri hiçbir yere gönderilmez**. Sunucu tarafı olmadan çalıştırmak
için bir form servisine bağlamak yeterlidir:

```html
<!-- iletisim.html -->
<form class="form" id="quoteForm" action="https://formspree.io/f/XXXXXXX" method="POST" novalidate>
```

Ardından `assets/js/main.js` içindeki `form.addEventListener("submit", ...)` bloğunda
`e.preventDefault()` satırını yalnızca doğrulama hatası olduğunda çalışacak şekilde düzenleyin
(veya `fetch` ile gönderin). Kendi sunucunuz varsa `action` alanına kendi uç noktanızı yazın.

### 5. Gerçek fotoğraf eklemek

Çizimler sitenin kimliğinin parçasıdır, ancak gerçek saha fotoğrafı eklemek isterseniz
dosyaları `assets/img/` altına koyup `.chapter__art` veya `.case__art` içindeki `<svg>` yerine
`<img>` kullanabilirsiniz. Premium görünümü korumak için sıcak tonlu, düşük doygunluklu ve
aynı en-boy oranında (kare / 16:10) fotoğraflar tercih edin.

## Yayına alma

Statik bir site olduğu için herhangi bir sunucuya kopyalamanız yeterlidir.
GitHub Pages ile yayınlamak için: depo ayarlarından **Settings → Pages → Source: Deploy from
a branch** seçip yayınlanacak dalı ve `/ (root)` klasörünü işaretleyin.

Yayına almadan önce yapılması önerilenler:

- Gerçek alan adına göre `<meta property="og:url">` ve bir `og:image` görseli ekleyin
- Google Analytics / Search Console gibi araçları ekleyin (KVKK aydınlatma metniyle birlikte)

## Erişilebilirlik ve performans notları

- Klavye ile tam gezinilebilir; odak halkaları, "İçeriğe geç" bağlantısı ve Esc ile kapanan
  mobil menü mevcut
- Form hataları alan altında metinle gösterilir ve `aria-invalid` ile işaretlenir
- `prefers-reduced-motion` açıkken tüm animasyonlar kapanır, içerik doğrudan görünür
- JavaScript kapalıyken tüm içerik görünür kalır (animasyonlar `no-js` sınıfıyla devre dışı)
- Görseller satır içi SVG olduğu için sayfa ağırlığı düşüktür; yazı tipleri toplam ~360 KB
- Mobil, tablet ve masaüstü için kırılım noktaları: 1080px, 900px ve 620px
