# Undertaker — Ministry 1998–1999 — v1

[**SFC + SRAM içeren paketi indir**](https://github.com/necaticturk-rwf/superfirex/raw/refs/heads/raw-ring-v1/downloads/raw-ministry-undertaker-v1.zip)

SFC ve aynı adlı SRM birlikte kullanılır. SRM'yi Snes9x'in SRAM/Battery kayıt klasörüne koyup yeni SFC'yi normal açılıştan başlatın. **DREAM MATCH → EDIT → TAKER**. Eski save state'i yüklemeyin. Önceki kayıtlarınızı bu yeni SRM ile değiştirmeyin.

Tombstone, Chokeslam, Big Boot ve Flying Clothesline; siyah kıyafet/botlar, güç/dayanıklılık ayarları ve CPU bitirici tercihleri dahil. Kabul edilen RAW ring v3 korunur. Görünüm mevcut SNES Undertaker modeline dayanır; dövme/göğüs sembolü birebir değildir.

[Kurulum ve profil notları](UNDERTAKER_MINISTRY_V1.md) · [Profil verileri](undertaker-profile.json) · [Test sonucu](undertaker-validation.json)

![Gerçek oyun kaydı](undertaker-gameplay.gif)

![Kayıttan yüklenen edit karakteri](undertaker-loaded-edit.png)

[Tombstone demosu](undertaker-tombstone.gif) · [Chokeslam demosu](undertaker-chokeslam.gif)

---

# RAW IS WAR ring — v3

**Güncel sürüm v3'tür. V1'de renk, v2'de ip animasyonu hatası vardır; eski paketleri kullanmayın.**

[ROM, IPS, test kaydı ve kaynak araçları içeren V3 ZIP'i indir](https://github.com/necaticturk-rwf/superfirex/raw/refs/heads/raw-ring-v1/downloads/raw-is-war-v3.zip)

ZIP'i yeni bir klasöre çıkarın. Snes9x'te **raw-is-war-v3.sfc** dosyasını açıp yeni maç başlatın. Eski maç içi save state'i kullanmayın; SRAM ilerlemesini silmek gerekmez. Hazır SFC'ye ayrıca IPS uygulamayın.

İp animasyonunun sabit grafik numaraları korunur; apron artık bu alanları kullanmaz. HWA/HWF/RANDOM aynı RAW tasarımını yükler. Açık gri mat, kırmızı ipler ve siyah/kırmızı/beyaz apron korunmuştur.

## Gerçek sekme testi kaydı

![İplere koşma, sekme ve devamı — Snes9x 1.62.3 emülasyon kaydı](rope-rebound-v3.gif)

## Sekme sonrası

![Sekme sonrası görünüm](rope-settled-v3.png)

Snes9x 1.62.3 Linux libretro çekirdeğinde HWA, HWF ve RANDOM için dört yönde koşma/bekleme dizileri denendi. Her seçimde 2.160 kare ve 6 animasyon başlangıcı boyunca kullanılan dinamik grafikler özgün ip/köşe grafikleriyle bayt düzeyinde karşılaştırıldı. Bilgisayar maçında 16.178 oyun karesi de kontrol edildi. Windows arayüzü burada çalıştırılmadı.

[Doğrulama sonuçları](raw-is-war-v3-validation.json) · [Teknik notlar](RAW_RING_V3.md)

IPS yalnızca özgün Sydra v7 İngilizce çeviri ROM'una uygulanır; v1/v2 üzerine uygulanmaz.

ZIP SHA-256: `b5ffbcb2527a53f31230407ac442a33eb20c65a44544cf8da258e27d382cef23`.
ROM SHA-256: `f3a6e07c10d3494b398d9c0c0883736f0e47f84f75113bd64adfb2629be62474`.
