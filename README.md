# Gm5Plus-Root

**General Mobile GM 5 Plus** (kod adı: `shamrock`, Android 8.0.0) için **tek tıkla otomatik root** paketi.
Çift tıkla, gerisini bırak — Magisk ile root, **bootloop yok**.

> Bu paket, biz root atarken takıldığımız her tuzağı (fastboot sürücüsü, dm-verity bootloop, veri kaybı) hazır çözümüyle içerir. Başkaları aynı hataları yaşamasın diye.

---

## Ne yapar?

Telefonun **kendi** `boot.img`'ini çekip Magisk'le yamalar (**dm-verity kapalı**), geri yazar ve Magisk uygulamasını kurar.
Cihazın kendi boot'unu kullandığı için **build/sürüm fark etmez** ve bootloop'a girmez.

## Hızlı başlangıç

| # | Adım | Komut / İşlem |
|---|------|----------------|
| 0 | **Yedek al** | Bootloader açmak telefonu **tamamen siler** (güvenlik gereği, kaçınılmaz) |
| 1 | Geliştirici ayarları | *OEM kilidini aç* + *USB hata ayıklama* → AÇIK |
| 2 | Fastboot sürücüsü | `Gm5Driver\Install.ps1` → sağ tık → *PowerShell ile çalıştır* |
| 3 | Bootloader aç | `adb reboot bootloader` → `fastboot flashing unlock` |
| 4 | **Root at** | **`ROOTLA.bat`'a çift tıkla** → "ROOT TAMAM" |

Ayrıntılı anlatım: [`OKU-BENI.txt`](OKU-BENI.txt)

## İçindekiler

```
ROOTLA.bat            → Çift tıkla, otomatik root (asıl iş: auto_root.ps1)
Gm5Driver\            → Fastboot sürücüsü (imzalı .inf — Zadig'siz)
magisk_patch\         → magiskboot + binaryler (32-bit / armeabi-v7a)
Magisk-v30.7.apk      → Magisk
twrp-...-shamrock.img → Geçici recovery (flash'lanmaz, sadece boot edilir)
adb.exe / fastboot.exe→ Araçlar (DLL'lerle)
scrcpy\               → Kırık dokunmatik için PC'den kontrol (aşağıda)
termux-*.apk          → Termux + API + Boot (GitHub sürümleri)
setup_ssh.sh          → Termux'ta SSH kurar
```

## Çözülen tuzaklar

- **`fastboot devices` boş dönüyor** → GM 5 Plus bootloader'da USB kimliği `VID_18D1 PID_D00D`'dir ve Windows'un hazır sürücüsünde kayıtlı değildir. `Gm5Driver\Install.ps1` imzalı sürücüyü kurar.
- **Recovery'de bootloop (GM logosu → fastboot)** → dm-verity. Magisk yaması `KEEPVERITY=false` ile bunu kapatır, hem root verir hem bootloop'u çözer.
- **Verilerim gitti** → Bootloader kilidini açmak fabrika sıfırlamasıdır; **önceden yedek al**.

## scrcpy — PC'den kontrol (kırık dokunmatik için)

`scrcpy\` klasöründeki .bat'lar:

| Dosya | İş |
|-------|-----|
| `1-Ekrani-Goster.bat` | Telefon ekranını PC'de göster + fareyle kontrol |
| `2-Ekran-Kapali-Kontrol.bat` | Telefon ekranı kapalı, PC'den kontrol |
| `3-Ekran-Goruntusu-Al.bat` | Ekran görüntüsü al |
| `4-TV-Tam-Ekran.bat` | PC TV'ye bağlıyken tam ekran yansıtma |

## Kullanım (root sonrası)

```bash
pkg install tsu        # Termux
sudo htop              # ilk sudo'da Magisk "izin ver?" → Grant
```

---

## ⚠️ Sorumluluk reddi

Root atmak garantini düşürebilir ve **bootloader açmak tüm veriyi siler**. Tüm işlemleri **kendi sorumluluğunda** yaparsın. Yanlış adımdan doğacak hasardan paket sahibi sorumlu değildir. Yalnızca GM 5 Plus (`shamrock`) içindir.
