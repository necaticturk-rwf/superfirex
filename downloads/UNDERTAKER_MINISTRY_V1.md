# Undertaker — Ministry, 1998–1999 — v1

Bu paket, kabul edilen RAW ring v3'e ayrı bir **UNDERTAKER** edit karakteri
ekler. Uzun adı UNDERTAKER, kısa adı TAKER; konumu **EDIT → TAKER**, edit kayıt
numarası **No001**. WC grubundaki özgün Undertaker ve diğer yerleşik güreşçiler
korunur. Yeni karakter ROM'a yeni bir roster satırı olarak işlenmez: oyunun
yerleşik edit sistemi ve normal `.srm` kaydı kullanılır.

## Görünüm

Oyunun mevcut Undertaker yüzü/gövdesi, uzun saç, siyah kıyafet ve siyah botlar
kullanılır. Soluk gri kollar referanstaki genel görünümü yaklaştırır. Bu ilk
sürüm, gönderilen modern Fire Pro görselinin birebir sprite aktarımı değildir:
dövme desenleri, göğüsteki Ministry sembolü ve yeni bir portre çizilmemiştir.
Animasyonların tamamı mevcut SNES gövdesiyle çalışır.

Pozlar: boğaz kesme hareketi, tek diz üzerinde kol kaldırma ve iki kolu kaldırma.
Giriş kıyafeti/şapka ve özgün WWF giriş müziği eklenmemiştir.

## Yetenekler

- Stil: ORTHODOX; karşılık verme: POWER.
- Recovery: FAST; kesiklerden toparlanma: NORM.
- Hız: NORM; köşeye tırmanma: MED SLOW.
- Critical: yalnız bitirici; bitirici: **TOMBSTONE**.
- Ring dışı sayım karakter ayarı: 10; rope stop kapalı.
- Edit puanı: **84**. ROM'daki 80/100/150 edit sınırları bu sürümde **180**
  yapılır; diğer edit karakterlerinde de bu sınır geçerlidir.

Oyundaki nitelik ölçeği **1–5**'tir.

| Hücum | Puan | Savunma | Puan |
| --- | --- | --- | --- |
| THRUST | 4 | HIT | 5 |
| KICK | 3 | KICK | 4 |
| THROW | 5 | BASIC | 5 |
| JOINT | 2 | JOINT | 3 |
| SUBMIS | 2 | SUBMIS | 3 |
| FLYING | 3 | FLYING | 3 |
| RUSH | 4 | TOUGH | 5 |
| ARM | 5 | LARIAT | 5 |
| TECH | 3 | TECH | 4 |
| RUFF | 5 | RUFF | 5 |
| | | NK | 5 |
| | | UPPER | 5 |

## Hareketler

Başlıca seçimler: Tombstone Piledriver, Chokeslam, Big Boot için oyunun
KENKA KICK animasyonu, Flying Clothesline, DDT, gecikmeli vertical suplex,
sidewalk slam için SIDE BUSTER, body slam, gorilla slam, leg drop ve stomplar.
Moonsault, Tiger Driver, Dragon/German Suplex ve Figure Four gibi varsayılan
profile ait uygunsuz seçimler kaldırılır. Last Ride ve Hell's Gate yoktur.
Old School için birebir ip üstünde yürüme animasyonu eklenmemiştir.

Ön grapple seçenekleri Bear Hug, Chokeslam, Front Rush ve Rev Tombstone'u
içerir; **Y+B = Tombstone** ve bitirici işareti taşır.
Oyunun kontrol düzeni esas alınır; emülatörde tuşlara atanmış klavye harfleri
farklı olabilir. Tam 57 girişin sayısal dökümü profil JSON'undadır.

CPU'nun normal yaklaşım tercihleri %55 grapple / %35 vuruş / %10 bekleme;
ikinci yaklaşım tablosu %60 / %35 / %5'tir. Son grapple aşamasında Y/B/A/X/Y+B
ağırlıkları %5 / %10 / %20 / %0 / %65'tir; böylece yorgun rakibe karşı
Tombstone tercih edilir. Diğer CPU tabloları oyunun varsayılan dağılımını
kullanır. Bu, tüm maçlarda aynı bitiricinin gerçekleşeceği anlamına gelmez.

## Snes9x 1.62.3 kurulumu

1. ZIP'i yeni bir klasöre çıkarın.
2. `raw-ministry-undertaker-v1.sfc` dosyasını açın.
3. Yanındaki aynı adlı `.srm` dosyasını Snes9x'in **SRAM/Battery** kayıt
   klasörüne koyun. Bu klasör ROM klasörü olarak ayarlıysa dosyaları birlikte
   tutmak yeterlidir. Emülatör kapalıyken kopyalayın.
4. Oyunu normal açılıştan başlatın. Önceki maçın save state'ini yüklemeyin.
5. DREAM MATCH karakter seçiminde L/R ile **EDIT** grubuna geçin ve **TAKER**
   seçin. WC grubundaki TAKER özgün karakterdir.

Bu `.srm` yalnız No001 Undertaker kaydını içerir; mevcut ilerleme ve edit
kayıtlarınızı bu dosyayla değiştirmeyin. Ayrı ROM dosya adı, eski ring sürümünün
aynı adlı kaydıyla çakışmayı önler. Hazır `.sfc` dosyasına ayrıca IPS uygulamayın.

## Üretim ve doğrulama

`tools/build_undertaker.py`, SHA-256 ile doğruladığı RAW ring v3 ROM'unda üç
edit sınırı sabitini ve SNES checksum'unu değiştirir. Ring, güreşçi sprite'ları,
hareket animasyonları ve oyun kodunun geri kalanı aynıdır. ROM v3'e göre yalnız
7 bayt değişir. 380 baytlık profil, normal açılıştan edit menüsüne gidilerek
oyunun SAVE işlemiyle SRAM No001'e yazılır; save state dağıtılmaz.

`tools/smoke_undertaker.py`, verilen SRAM'ı sıfırdan yükler, oyunun LOAD menüsüyle
No001'i geri okur ve 380 baytı kaynak profille karşılaştırır. Nitelik ekranı,
Chokeslam/Tombstone hareket demoları, EDIT seçimi ve gerçek CPU maçını kaydeder.
Maçtaki dinamik ip tile'ları özgün grafiklerle bayt düzeyinde karşılaştırılır.
Ölçülen sonuçlar `undertaker-validation.json` dosyasındadır.

Test çekirdeği resmî Snes9x 1.62.3 kaynaklarından derlenen Linux libretro'dur;
Windows arayüzü bu ortamda çalıştırılmadı. Maç kayıtları emülatörün gerçek
görüntüleridir; fotoğraf düzenlemesi veya konsept çizim değildir.

```bash
python tools/build_undertaker.py --base-rom build/raw-is-war-v3.sfc \
  --core /path/to/snes9x_libretro.so --output-dir build/undertaker-v1
python tools/smoke_undertaker.py \
  --rom build/undertaker-v1/raw-ministry-undertaker-v1.sfc \
  --sram build/undertaker-v1/raw-ministry-undertaker-v1.srm \
  --core /path/to/snes9x_libretro.so --output-dir research/undertaker/final
```

`*-from-raw-v3.ips`, yalnız RAW ring v3 ROM'una edit sınırı değişikliğini uygular;
güreşçiyi eklemek için beraberindeki `.srm` de gerekir.
