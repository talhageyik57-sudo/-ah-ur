# US Small-Cap Breakout Botu

NASDAQ / NYSE'de işlem gören yüksek volatiliteli, düşük piyasa değerli
(small-cap / penny stock) hisseler için **Telegram'a hazır "Hacimli Mum &
Breakout Notu"** üreten bot.

Hisse kodunu, fiyatı, değişim oranını ve haberi yazarsınız; bot direnç,
destek, kırılım alım seviyesi, TP1/TP2 ve stop-loss seviyelerini hesaplayıp
kopyala-yapıştır hazır gönderiyi döndürür.

```
🇺🇸 🚀 US SMALL-CAP | HACİMLİ MUM & HEDEF BÖLGELERİ 🚀

📌 Ticker: $RKLB
💰 Son Fiyat: $4.25 (%+32)
⚡ Katalizör / Haber: Uydu sözleşmesi haberi (RVOL ~8.0x)
...
🔴 İlk Direnç: $4.50      🟢 İlk Destek: $4.00
🎯 TP1: $4.75             🚀 TP2: $5.40        🛑 Stop: $3.90
```

## Kurulum

```bash
cd smallcap-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # TELEGRAM_BOT_TOKEN değerini doldurun
python3 run.py
```

Token'ı Telegram'da [@BotFather](https://t.me/BotFather) üzerinden
`/newbot` komutuyla alırsınız.

## Kullanım

Bota özel mesajdan doğrudan girdi yazabilir ya da komut kullanabilirsiniz.

```
RKLB 4.25 %32 FDA onayı sonrası hacim patlaması
```

| Komut | İşlevi |
|---|---|
| `/analiz <girdi>` | Gönderiyi üretir |
| `/detay <girdi>` | Seviyelerin hesap gerekçesi, birim risk ve R/R oranı |
| `/gonder <girdi>` | Gönderiyi üretip doğrudan hedef kanala atar |
| `/ornek` | Örnek gönderi |
| `/yardim` | Kullanım bilgisi |

Gruplarda gürültü olmaması için komutsuz mesajlara yalnızca `$` ile
başlıyorsa yanıt verilir (`$RKLB 4.25 %32 haber`).

### Girdi biçimi

```
<HİSSE> <FİYAT> <%DEĞİŞİM> <haber metni>
```

İlk kelime hisse kodu (`RKLB` veya `$RKLB`), ardından gelen sayı son fiyat,
`%` ya da işaret taşıyan sayı yüzde değişim, kalan metin katalizördür.
Ondalık ayırıcı olarak nokta da virgül de kabul edilir.

Seviyeleri keskinleştirmek için `anahtar=değer` çiftleri eklenebilir —
metnin herhangi bir yerinde bulunabilirler:

| Anahtar | Karşılığı | Türkçe alternatifleri |
|---|---|---|
| `hod=` | gün içi tepe | `tepe=` `yuksek=` `zirve=` |
| `lod=` | gün içi dip | `dip=` `dusuk=` `taban=` |
| `pm=` | pre-market tepesi | `premarket=` |
| `pc=` | önceki kapanış | `onceki=` `kapanis=` |
| `vol=` | hacim | `hacim=` |
| `avgvol=` | ortalama hacim | `ortalama=` |
| `float=` | float | `dolasim=` |
| `short=` | short oranı (%) | `si=` |
| `haber=` | katalizör metni | `katalizor=` `news=` |

Hacim değerleri `48M`, `850K`, `1.2B` biçiminde yazılabilir.

```
$ABCD 0.4523 +118% hod=0.52 lod=0.31 float=14M short=%24 haber=Ortaklık duyurusu
```

`hod`/`lod` verilmezse seviyeler yüzde değişimden tahmin edilir; verilirse
gerçek gün içi bant kullanıldığı için sonuç belirgin biçimde isabetli olur.

### Terminalden kullanım

Telegram olmadan da çalışır:

```bash
python3 -m smallcap.cli "RKLB 4.25 %32 FDA onayı"
python3 -m smallcap.cli --detay "RKLB 4.25 %32 hod=4.48 lod=3.10"
python3 -m smallcap.cli --format html "SOUN 12.40 -3.2 Nvidia ortaklığı"
```

## Seviye metodolojisi

| Seviye | Kural |
|---|---|
| **İlk Direnç** | Gün içi tepe (HOD) veya pre-market tepesi. Verilmezse son fiyatın %1.5 üzeri. |
| **İlk Destek** | Gün içi dip (LOD). Gün içi bant %15'ten genişse dip yerine %38.2 Fibonacci düzeltme pivotu — momentum hissesinde dip çok uzakta kaldığı için retest bölgesi daha yakındır. Dip yoksa günün hareketinin %50 düzeltmesi. |
| **Kırılım alım** | İlk direncin bir tick + %1 üzeri (ör. direnç `$5.00` → `$5.05`). |
| **TP1** | Direncin %7 üzeri (%5–10 bandı), temiz rakama oturtulur. |
| **TP2** | Direncin %20 üzeri (%15–25 bandı). |
| **Stop-Loss** | İlk desteğin %2.5 altı (%2–3 bandı). |

Tüm seviyeler fiyat bandına göre "temiz" rakamlara yuvarlanır (`$4.4912`
yerine `$4.50`), ancak yuvarlama seviyeyi %1.5'ten fazla kaydırmaz. Sıralama
her girdi için garantilidir: `stop < destek < fiyat < direnç < kırılım < TP1 < TP2`.

Hacim ve float verildiğinde katalizör satırına RVOL ve squeeze notu eklenir
(float ≤ 20M **ve** short ≥ %15 → squeeze adayı).

`/detay` çıktısı hangi kuralın uygulandığını, birim riski ve R/R oranını
gösterir — seviyeleri paylaşmadan önce gözden geçirmek için kullanın.

## Kanala gönderme

Analizi görüp onayladıktan sonra kanala iletmek için iki yol var:

- Üretilen her gönderinin altındaki **📢 Kanala Gönder** butonu — önce
  seviyeleri gözden geçirir, beğenirseniz tek dokunuşla atarsınız
- `/gonder <girdi>` — analizi üretip doğrudan kanala atar

Açmak için `.env` dosyasında **iki** alan da dolu olmalıdır:

```ini
TELEGRAM_ALLOWED_CHAT_IDS=5418325557      # sizin kullanıcı ID'niz
TELEGRAM_TARGET_CHAT_ID=-1001234567890    # kanalın ID'si
```

Beyaz liste boşken kanala gönderim **kasıtlı olarak kapalıdır**: aksi halde
botu bulan herkes kanalınıza gönderi attırabilirdi.

**Kanal ID'si nasıl bulunur?** Kanal ID'leri `-100` ile başlar ve kullanıcı
ID'lerinden farklıdır. Kanaldan bir mesajı [@userinfobot](https://t.me/userinfobot)
adlı bota iletin, ID'yi size yazsın. Herkese açık kanallarda `@kanaladi`
biçimi de kullanılabilir. **Bot kanalda yönetici olmalıdır**, aksi halde
Telegram gönderimi reddeder ve bot size hatayı bildirir.

Kendi kullanıcı ID'nizi öğrenmek için de aynı bota `/start` yazmanız yeterli.

## Canlı veri (isteğe bağlı)

`AUTO_FETCH=1` iken bot eksik alanları canlı veriden tamamlamaya çalışır;
yalnızca hisse kodu yazmanız (`/analiz RKLB`) yeterli olur.

- **Finnhub** — `FINNHUB_API_KEY` tanımlıysa kullanılır, ek paket gerektirmez.
- **yfinance** — kuruluysa yedek sağlayıcı olarak denenir (`pip install yfinance`).

Elle girilen değerler her zaman canlı veriyi ezer: API'nin bilmediği bir
pre-market tepesini siz verebilirsiniz. Sağlayıcı yanıt vermezse bot hata
vermez, manuel girdiyle çalışmaya devam eder.

## Yapılandırma

Tüm ayarlar ortam değişkeni ya da `.env` dosyası ile verilir:

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | **Zorunlu.** BotFather token'ı |
| `TELEGRAM_PARSE_MODE` | `html` | `html` \| `markdownv2` \| `plain` |
| `TELEGRAM_ALLOWED_CHAT_IDS` | boş | Boşsa herkese açık; virgüllü ID listesi ile kısıtlanır. Kanala gönderim için zorunlu |
| `TELEGRAM_TARGET_CHAT_ID` | boş | Gönderilerin atılacağı kanal/grup ID'si (`-100...`) veya `@kanaladi` |
| `AUTO_FETCH` | `1` | Canlı veri denemesi |
| `FINNHUB_API_KEY` | boş | Finnhub anahtarı |
| `REQUEST_TIMEOUT` | `10` | Canlı veri zaman aşımı (sn) |
| `LOG_LEVEL` | `INFO` | Günlük seviyesi |
| `TELEGRAM_API_BASE_URL` | boş | Kendi Bot API sunucunuzun adresi; boşsa resmî API kullanılır |

`html` biçimi önerilir: Telegram MarkdownV2'de `.`, `-`, `!` gibi
karakterlerin kaçışı gerekir ve haber metni bunları sık içerir.

## Testler

```bash
python3 -m unittest discover
```

Testler yalnızca standart kütüphaneyi kullanır; Telegram katmanı
kuruluysa handler testleri de çalışır, kurulu değilse atlanır.

## Dosya yapısı

```
smallcap-bot/
├── run.py                  Botu başlatan giriş noktası
├── requirements.txt
├── .env.example
├── smallcap/
│   ├── models.py           Quote (girdi) ve Levels (çıktı) veri yapıları
│   ├── numbers.py          Tick bandı, psikolojik yuvarlama, biçimlendirme
│   ├── levels.py           Seviye hesaplama motoru
│   ├── template.py         Telegram gönderi şablonu
│   ├── markup.py           Kanonik işaretleme → HTML / MarkdownV2 / düz metin
│   ├── parser.py           Serbest metin girdisi çözümleyici
│   ├── market_data.py      Finnhub / yfinance canlı veri (isteğe bağlı)
│   ├── service.py          Girdi → gönderi akışı (bot ve CLI ortak)
│   ├── config.py           Ortam değişkeni yapılandırması
│   ├── cli.py              Terminal arayüzü
│   └── app.py              Telegram handler'ları
└── tests/                  125 birim testi (yalnızca stdlib)
```

## Sürekli çalıştırma

`systemd` ile örnek servis tanımı:

```ini
[Unit]
Description=US Small-Cap Breakout Telegram Botu
After=network-online.target

[Service]
WorkingDirectory=/opt/smallcap-bot
ExecStart=/opt/smallcap-bot/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Uyarı

Bot teknik seviye hesaplayan bir **şablon üreticisidir**; yatırım tavsiyesi
vermez. Small-cap piyasalarda slippage ve oynaklık yüksektir — üretilen her
gönderiyi paylaşmadan önce kendi kontrolünüzden geçirin.
