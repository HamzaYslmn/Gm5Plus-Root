# GM 5 Plus fastboot surucusu - TEK TIK KURULUM (Zadig yok, imza kapatma yok)
# Kullanim: bu dosyaya sag tikla > "PowerShell ile calistir"  (yonetici istegi cikar, Evet de)
# On kosul: telefon fastboot modunda + USB takili olsun.

# --- yonetici degilse kendini yukselt ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "1/2  Sertifika guvenilirlere ekleniyor..." -ForegroundColor Cyan
certutil -addstore -f Root            "$here\gm5_cert.cer" | Out-Null
certutil -addstore -f TrustedPublisher "$here\gm5_cert.cer" | Out-Null

Write-Host "2/2  Surucu kuruluyor..." -ForegroundColor Cyan
pnputil /add-driver "$here\gm5_winusb.inf" /install

Write-Host ""
Write-Host "Bitti. Telefonu USB'den cikar-tak, sonra:" -ForegroundColor Green
Write-Host "    .\fastboot devices"
Write-Host ""
Read-Host "Kapatmak icin Enter"
