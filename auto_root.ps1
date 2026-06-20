# ============================================================
#  GM 5 Plus (shamrock) - OTOMATIK ROOT
#  Magisk'li (dm-verity KAPALI) boot uretir ve flashlar.
#  Cihazin KENDI boot.img'ini cektigi icin build'den bagimsizdir.
# ============================================================
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$adb  = Join-Path $root "adb.exe"
$fb   = Join-Path $root "fastboot.exe"
$twrp = Join-Path $root "twrp-3.7.0_9-0-shamrock.img"
$apk  = Join-Path $root "Magisk-v30.7.apk"
$mp   = Join-Path $root "magisk_patch"

function Say($m,$c="White"){ Write-Host $m -ForegroundColor $c }
function Get-State { try { (& $adb get-state) 2>$null } catch { "" } }
function In-Fastboot { ((& $fb devices) 2>$null) -match "fastboot" }
function Wait-For($cond,[int]$sec,$label){
  Say "Bekleniyor: $label ..." Yellow
  for($i=0;$i -lt [int]($sec/2);$i++){ Start-Sleep 2; if(& $cond){ return $true } }
  return $false
}

Say "========================================================" Cyan
Say " GM 5 Plus (shamrock) OTOMATIK ROOT" Cyan
Say "========================================================" Cyan
Say ""
Say "ON KOSUL: Bootloader ZATEN ACIK olmali (fastboot flashing unlock)." Red
Say "Acik degilse once OKU-BENI.txt'deki 'BOOTLOADER ACMA' adimini yap." Red
Say "(Bootloader acmak telefonu TAMAMEN SILER - bu script silmez.)" Red
Say ""
$go = Read-Host "Bootloader acik ve devam etmek istiyor musun? (E/H)"
if ($go -notmatch "^[EeYy]") { Say "Iptal."; exit }

# --- adb/fastboot var mi ---
if (-not (Test-Path $adb) -or -not (Test-Path $fb)) { Say "adb/fastboot bulunamadi!" Red; exit 1 }

# --- 1) Cihaz nerede? Android ise Magisk app kur + bootloader'a gec ---
& $adb kill-server *> $null; & $adb start-server *> $null
$st = Get-State
if ($st -match "device") {
  Say "Android'de. Magisk app kuruluyor..." Green
  try { & $adb install -r $apk } catch { Say "APK kurulamadi (devam ediliyor)" Yellow }
  Say "Bootloader'a geciliyor..." Green
  & $adb reboot bootloader
}
elseif ($st -match "recovery") { Say "Recovery'de. Bootloader'a geciliyor..." Green; & $adb reboot bootloader }

# --- 2) Fastboot'u bekle (surucu kontrolu) ---
if (-not (Wait-For { In-Fastboot } 60 "fastboot")) {
  Say "" ; Say "FASTBOOT CIHAZI GORMUYOR = surucu eksik." Red
  Say "Cozum: Gm5Driver\Install.ps1'e sag tikla > PowerShell ile calistir (yonetici)." Yellow
  Say "Sonra telefonu cikar-tak ve bu script'i tekrar baslat." Yellow
  exit 1
}
Say "Fastboot OK." Green

# --- 3) TWRP'yi GECICI baslat (flashlamaz) ---
Say "TWRP gecici baslatiliyor..." Green
& $fb boot $twrp
& $adb kill-server *> $null
if (-not (Wait-For { (Get-State) -match "recovery" } 40 "recovery (adb)")) {
  Say "Recovery adb gelmedi. Telefon ekraninda TWRP/OrangeFox acildi mi?" Red; exit 1
}
Say "Recovery OK." Green

# --- 4) Cihazin KENDI boot.img'ini cek + Magisk binarylerini yukle ---
Say "boot partition cekiliyor + Magisk dosyalari yukleniyor..." Green
& $adb shell "mkdir -p /tmp/mp"
& $adb push "$mp\." /tmp/mp | Out-Null
& $adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/tmp/mp/boot_stock.img"
# PC'ye yedek (kurtarma icin)
& $adb pull /tmp/mp/boot_stock.img "$root\boot_stock_BUDEVICE.img" | Out-Null

# --- 5) Magisk patch (verity KAPALI) ---
Say "Magisk patch uygulaniyor (dm-verity kaldiriliyor)..." Green
& $adb shell "cd /tmp/mp && chmod 755 magisk magiskboot magiskinit magiskpolicy busybox init-ld && KEEPVERITY=false KEEPFORCEENCRYPT=false sh boot_patch.sh boot_stock.img 2>&1"
$has = (& $adb shell "[ -f /tmp/mp/new-boot.img ] && echo OK") 2>$null
if ($has -notmatch "OK") { Say "Patch basarisiz - new-boot.img olusmadi." Red; exit 1 }
& $adb pull /tmp/mp/new-boot.img "$root\magisk_patched_BUDEVICE.img" | Out-Null

# --- 6) Patched boot'u yaz + sisteme don ---
Say "Patched boot yaziliyor..." Green
& $adb shell "dd if=/tmp/mp/new-boot.img of=/dev/block/bootdevice/by-name/boot"
Say "Sisteme yeniden baslatiliyor..." Green
& $adb reboot
& $adb kill-server *> $null

# --- 7) Dogrula ---
if (Wait-For { (& $adb shell getprop sys.boot_completed 2>$null) -match "1" } 150 "Android acilisi") {
  $v = (& $adb shell "magisk -v" 2>$null)
  Say ""
  Say "========================================================" Green
  Say " ROOT TAMAM!  Magisk: $v" Green
  Say "========================================================" Green
  Say "Termux'ta:  pkg install tsu  &&  sudo htop" Cyan
  Say "Yedekler: boot_stock_BUDEVICE.img (orijinal) / magisk_patched_BUDEVICE.img" Cyan
} else {
  Say "Android acilmadi. Telefon ekranina bak; gerekirse:" Red
  Say "  fastboot flash boot boot_stock_BUDEVICE.img   (orijinali geri yukler)" Yellow
}
Read-Host "Kapatmak icin Enter"
