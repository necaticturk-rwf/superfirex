# RAW IS WAR ring v2 — renk yükleme düzeltmesi

V1'deki apron grafikleri yüklenebilmesine rağmen başka bir ring paleti
seçildiğinde mat mavi kalabiliyor, ipler üç renge ve apron sarı/beyaza
dönebiliyordu. Kullanıcı bunu Windows Snes9x x64 1.62.3'te HWA seçili bir maçta
bildirdi. Eşdeğer renk bozulması burada Dream Match / HWF ile yeniden üretildi.
Kullanıcının HWA seçimine rağmen o paletin nasıl etkinleştiği tek başına
ekran görüntüsünden belirlenmedi; düzeltme yalnızca seçim adına dayanmaz.

## Değişiklik

- HWA'nın yanında HWF'nin `$01E17D..$01E1FD` ring paletleri de RAW renkleriyle
  güncellenir; seyirci ve güreşçi paletleri değiştirilmez.
- RANDOM renkleri RAM'de üretebildiği için yalnızca ROM tablosunu değiştirmek
  yeterli değildir. `$80D63C` adresindeki 5 baytlık DMA başlatma dizisi, boş
  `$D5FA20` alanında bulunan kısa bir 65816 yordamına yönlendirilir.
- Yordam, DMA hedefinin CGRAM, kaynak adresinin `$00059E`, boyutunun `$0200`
  ve arka plan renk işaretlerinin `$2528/$2549` olduğunu kontrol eder.
  Eşleştiğinde yalnızca arka plan paletleri 4–7'yi RAW renklerine çevirir.
  Sonra A/X/Y ve işlemci bayraklarını geri yükler, özgün DMA komutunu çalıştırır.
- SRAM dosyaları silinmez veya yamalanmaz. Menü renkleri ve sprite paletleri
  bu yordamın hedefi değildir.

Mat düz açık gri, apron siyah/kırmızı/beyaz, ipler kırmızı ve köşeler koyu renktir.
V1'in grafik düzeni, seyirci tile'ları ve ROM boyutu korunmuştur.

## Yeniden üretme

Depo kökünden, `tools/requirements.txt` bağımlılıkları kurulu olarak:

```sh
python3 tools/build_raw_ring.py \
  --rom 'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc'
```

Çıktılar: `build/raw-is-war-v2.sfc`, `patches/raw-is-war-v2.ips`,
`patches/raw-is-war-v2.json`. Kaynak ROM v1 ile aynıdır; derleyici SHA-256
kontrolü yapar. V2 IPS, v1'e değil **özgün Sydra v7 ROM'una** uygulanır.
Hazır ROM kullanılıyorsa ayrıca IPS uygulanmaz.

## Doğrulama

Ring seçimine izin veren **Dream Match** modunda, seçilen RING satırını da
gösteren `options.png` kaydedilir. Championship modu ring seçimini kilitlediği
için v1'deki ilk kontrol farklı ringleri doğrulamak için yeterli değildi.

- Resmî Snes9x `1.62.3` etiketi,
  `8b82d487937d9ea39f7229d280c6f6686c415fe7`, değiştirilmeden Linux libretro
  çekirdeği olarak derlendi. Windows arayüzü burada çalıştırılmadı.
- Bu çekirdekte HWA, HWF ve RANDOM ayrı ayrı normal açılıştan maç, hareket ve
  600 ek oyun karesine kadar kontrol edildi.
- V1'den kaydedilmiş SRAM ile v2 açılışı da kontrol edildi.
- Ek olarak güncel Snes9x libretro çekirdeğinde RANDOM kontrolü çalıştırıldı.
- V1/HWF regresyon kontrolü beklenen biçimde gri mat kontrolünde başarısız olur;
  v2 aynı koşulda geçer. Görüntü kontrolleri tam RAW mat ve yazı renklerini
  kontrol eder; genel bir gri/kırmızı piksel sayımına dayanmaz.
- Özgün ve v2 ROM'ların HWA maç ayarları ekranları piksel düzeyinde karşılaştırılır.
- IPS tekrar uygulaması, çıktı checksum'u ve derlemenin aynı çıktıyı üretmesi
  derleyicinin kendi kontrolleridir.

Örnek:

```sh
python3 tools/smoke_ring.py --rom build/raw-is-war-v2.sfc \
  --core /path/to/snes9x_libretro.so \
  --ring HWF --expect-raw --output-dir build/check-hwf
```

Ekran görüntüleri `research/screenshots/raw-v2-snes9x-1623-*` ve
`research/screenshots/raw-v2-existing-sram` altında saklanır.

## Kullanım

ZIP'teki **raw-is-war-v2.sfc** dosyasını Snes9x'te açıp yeni maç başlatın.
Eski maç içi save state'i yüklemeyin; state, ROM'dan bağımsız olarak eski
VRAM/palet içeriğini geri getirebilir. SRAM ilerlemesini silmek gerekmez.
