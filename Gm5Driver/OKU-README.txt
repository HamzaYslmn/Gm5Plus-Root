================================================================
 GM 5 PLUS - FASTBOOT SURUCU PAKETI
================================================================

SORUN
-----
General Mobile GM 5 Plus bootloader/fastboot modunda Windows'ta
"fastboot devices" bos doner. Cunku cihazin USB kimligi
VID_18D1 PID_D00D (Google fastboot) Google'in resmi
android_winusb.inf'inde KAYITLI DEGIL ve adb/fastboot'un aradigi
Android arayuz GUID'i atanmaz.

================================================================
 YONTEM 0 (EN KOLAY - ONERILEN): Install.ps1
================================================================
Zadig YOK, imza kapatma YOK. Imzali surucu paketi.

1) Telefonu fastboot moduna al:   adb reboot bootloader
   (Ekranda "fastboot mode" yazmali, USB takili kalsin.)
2) Install.ps1'e SAG TIKLA > "PowerShell ile calistir".
   Yonetici istegi cikar -> Evet.
   (Sertifikayi guvenilirlere ekler + surucuyu kurar.)
3) Telefonu USB'den CIKAR-TAK.
4) Kontrol:   fastboot devices    ->  seri no gorunmeli.

Icindekiler bu yontem icin: Install.ps1 + gm5_winusb.inf
+ gm5_winusb.cat (imzali katalog) + gm5_cert.cer (sertifika)

----------------------------------------------------------------
 YONTEM 1 (ALTERNATIF): Zadig + GUID duzeltme scripti
----------------------------------------------------------------
1) Zadig (https://zadig.akeo.ie) > Options > List All Devices.
2) Telefon fastboot modunda. Listeden "18D1 D00D" cihazini sec.
3) WinUSB sec > Install Driver.
4) Fix-Gm5Fastboot.ps1'i YONETICI PowerShell'de calistir.
5) Telefonu cikar-tak > fastboot devices.

----------------------------------------------------------------
 YONTEM 2 (ALTERNATIF): INF'i elle, imza kapatarak
----------------------------------------------------------------
Imza zorlamasini kapat (Ayarlar > Sistem > Kurtarma > Gelismis
baslatma > Sorun giderme > Gelismis secenekler > Baslangic
Ayarlari > Yeniden baslat > F7), sonra Aygit Yoneticisi'nden
gm5_winusb.inf'i "Have Disk" ile kur.

================================================================
 BOOTLOADER ACMA (surucu calistiktan sonra)
================================================================
!!! DIKKAT: Bootloader kilidini acmak telefonu TAMAMEN SILER
!!! (fabrika sifirlamasi). Bu bir guvenlik onlemidir, kacinilmaz.
!!! Once Google hesabi yedegini ve onemli dosyalari al.

Telefonda: Gelistirici Secenekler > "OEM unlocking" acik olmali.

  fastboot flashing unlock      (olmazsa: fastboot oem unlock)

Telefonda ses tuslariyla "Yes/Unlock" sec, Power ile onayla.

================================================================
 ICINDEKILER
================================================================
  Install.ps1          - Yontem 0: tek tik imzali kurulum
  gm5_winusb.inf       - surucu tanimi
  gm5_winusb.cat       - imzali katalog (Install.ps1 kullanir)
  gm5_cert.cer         - kendinden imzali sertifika
  Fix-Gm5Fastboot.ps1  - Yontem 1: Zadig sonrasi GUID duzeltme
  OKU-README.txt       - bu dosya

Not: gm5_cert.cer "GM5 Community Driver" adli kendinden imzali bir
sertifikadir; sadece bu surucu paketini imzalamak icindir.
================================================================
