# RAW IS WAR ring v3 — ip animasyonu düzeltmesi

V2'nin grafik atlasını yeniden numaralandırması, oyunun sabit tile numaralarıyla
çalışan ip animasyonlarıyla uyumlu değildi. Koşup iplere çarpıldığında örneğin
BG1 `$14C` tile'ı çağrılıyor, fakat bu adreste artık apron yazısının bir parçası
bulunuyordu. Animasyon bitince kullanılan özgün şablonlar da yeni atlasla
uyuşmadığı için bozulma kalıcı olabiliyordu. Bu hata yerel emülatörde yeniden
üretildi; eski v2 aynı hareketin grafik doğrulamasında başarısız oldu.

## V3'te değişenler

- BG1'in `$0000..$3000` grafik alanı ve özgün tile numaraları korunur.
  İlk ekranda görünmeyen ip animasyon kareleri de bu kapsamdadır.
- Apron tasarımının 32 metatile'ı BG1'in eski apron logo alanına, kalan
  37 metatile'ı BG2'nin kullanılmayan mat logo alanına yerleştirilir.
- BG2 logo alanında köşelerin de kullandığı 11 blok ayrılmıştır; bu blokların
  numarası ve içeriği korunur. BG2'nin ilk `$2800` baytı da değiştirilmez.
- İki katmana ayrılan apron hücrelerinin arkasındaki ring geometrisi gerektiği
  yerde aynı hücreye işlenir. Karakterlerin önünde yeni bir yazı katmanı açılmaz;
  apron, normal arka plan önceliğinde kalır.
- Apron yazısının 144 × 25 piksel kaynak boyutu korunur. Birkaç kenar/zemin
  tonunda SNES'in ortak 16 renk paletine uygun yakın gri tonları kullanılır.
- HWA/HWF/RANDOM seçeneklerinin ayrı ve rastgele grafik kaynaklarını seçen
  dört yükleme komutu RAW/HWA düzenine yönlendirilir. İp animasyon kodu ve
  oyunun genel kaynak yükleyicisi değiştirilmez.
- V2'nin maç sırasında RAW renklerini koruyan palet düzeltmesi devam eder.

Bu sürümde ring seçenekleri aynı RAW tasarımını kullanır; HWF'nin eski köşe
tasarımını veya RANDOM'un rastgele görünümünü korumak hedeflenmez.

## Teknik yerleşim

`tools/ring_tiles.py`, eski tile adreslerini koruyarak apron hücrelerini
oluşturur. Yeni ham kaynaklar aşağıdaki dört kayda bağlanır:

| Kaynak kaydı | VRAM hedefi | Boyut | Yeni ROM konumu |
| --- | --- | --- | --- |
| `$15B940` | `$3000` | `$1000` | `$15DA20` |
| `$15B8C8` | `$A800` | `$1800` | `$15C220` |
| `$15B9A0` | `$7000` | `$0800` | `$15EA20` |
| `$15BA80` | `$7800` | `$0800` | `$15F220` |

Maç kurulumu içindeki dosya ofsetleri `$05C203`, `$05C20F`, `$05C21B`,
`$05C226` olan dört 16 bit yükleme, sırasıyla `$40E2`, `$40B1`, `$40C1`,
`$40A2` sabit kaynak kimliklerini yükler. Diğer kaynak yüklemeleri korunur.

Özgün BG2 temel varlığının SHA-256 değeri:
`64596a384cd0ca6cc3ea06598ff61061a67612bed833df1e2dd86f273bbf1b3d`.
Bu varlık aynı kaynak ROM'dan emülatör belleği aracılığıyla çıkarılmıştır.

## Doğrulama

Resmî Snes9x 1.62.3 kaynaklarından derlenen Linux libretro çekirdeği kullanıldı.
Windows arayüzü bu ortamda çalıştırılmadı.

- HWA, HWF ve RANDOM ayrı ayrı normal açılıştan başlatıldı.
- Her seçimde dört yönde koşma ve bekleme dizileri boyunca 2.160 oyun karesi
  denetlendi. Her koşuda 6 animasyon başlangıcı, 106 güncellenen hücre ve 69
  farklı dinamik grafik girişi görüldü. Her güncellenen girişin çağırdığı dört
  küçük tile, özgün HWA ip/köşe grafikleriyle bayt düzeyinde karşılaştırıldı.
- Bilgisayarın yönettiği bir maçta 16.178 oyun karesi ve sonuç ekranına geçişe
  kadar arka plan güncellemeleri kontrol edildi; dinamik grafik karşılaştırması
  geçti. Bu test bütün olası oyun hareketlerinin doğrulandığı anlamına gelmez.
- HWF ve RANDOM'da genel maç/hareket kontrolleri geçti. RANDOM ayrıca v1'den
  alınmış SRAM ile açıldı; kayıt ilerlemesini silmek gerekmedi.
- `rope-rebound.gif`, HWA sekme testinin 20 FPS ile alınmış gerçek emülatör
  kaydıdır; hayali bir ring çizimi veya görsel düzenleme değildir.
- IPS yeniden uygulama eşitliği, kaynak/çıktı hash'leri ve SNES checksum'u
  derleme sırasında doğrulanır.

Örnek, depo kökünden:

```sh
python3 -m pip install -r tools/requirements.txt
python3 tools/build_raw_ring.py --rom '/path/to/original-Sydra-v7.sfc'
python3 tools/rope_regression.py --rom build/raw-is-war-v3.sfc \
  --core /path/to/snes9x_libretro.so --ring HWA --record-gif \
  --output-dir build/rope-check
```

Çıktılar: `build/raw-is-war-v3.sfc`, `patches/raw-is-war-v3.ips`,
`patches/raw-is-war-v3.json`. Kaynak ROM'un SHA-256 değeri eski sürümlerle
aynıdır ve derleyici farklı ROM'ları reddeder. IPS özgün Sydra v7 ROM'una
uygulanır; v1/v2 üzerine uygulanmaz.

ZIP'teki hazır **raw-is-war-v3.sfc** dosyasını açıp yeni maç başlatın. Eski
maç içi save state'i kullanmayın; bu dosyalar eski VRAM içeriğini geri getirir.
SRAM ilerlemesini silmek gerekmez. Hazır SFC'ye ayrıca IPS uygulamayın.
