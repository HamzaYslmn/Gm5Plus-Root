# GM 5 Plus - fastboot surucu duzeltmesi (tasinabilir)
# Sorun: Zadig generic WinUSB kurunca cihaza kendi GUID'ini koyar; adb/fastboot
#        Android'e ozel GUID'i arar, eslesmez, "fastboot devices" bos doner.
# Cozum: Bu cihazin DeviceInterfaceGUIDs degerini Android GUID'iyle degistir.
#
# ON KOSUL: Telefon FASTBOOT modunda + uzerine Zadig ile WinUSB kurulu olmali.
# CALISTIRMA: PowerShell'i "Yonetici olarak" ac, bu dosyayi calistir:
#   powershell -ExecutionPolicy Bypass -File .\Fix-Gm5Fastboot.ps1

$ANDROID_GUID = "{F72FE0D4-CBCB-407d-8814-9ED673D0DD6B}"

$devs = Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match "VID_18D1&PID_D00D" }
if (-not $devs) {
    Write-Host "Cihaz bulunamadi." -ForegroundColor Red
    Write-Host "Telefonu fastboot moduna al (adb reboot bootloader) ve uzerine Zadig ile WinUSB kur, sonra tekrar calistir."
    exit 1
}

foreach ($d in $devs) {
    $p = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($d.InstanceId)\Device Parameters"
    try {
        Set-ItemProperty -Path $p -Name DeviceInterfaceGUIDs -Value @($ANDROID_GUID) -Type MultiString -ErrorAction Stop
        Write-Host ("OK  -> {0}" -f $d.InstanceId) -ForegroundColor Green
    } catch {
        # Enum anahtari kilitliyse once sahiplik al
        $sub = "SYSTEM\CurrentControlSet\Enum\$($d.InstanceId)\Device Parameters"
        $rk = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($sub,
              [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree,
              [System.Security.AccessControl.RegistryRights]::TakeOwnership)
        $acl = $rk.GetAccessControl()
        $acl.SetOwner([System.Security.Principal.NTAccount]"Administrators")
        $rk.SetAccessControl($acl)
        $acl.SetAccessRule((New-Object System.Security.AccessControl.RegistryAccessRule("Administrators","FullControl","Allow")))
        $rk.SetAccessControl($acl)
        Set-ItemProperty -Path $p -Name DeviceInterfaceGUIDs -Value @($ANDROID_GUID) -Type MultiString
        Write-Host ("OK (sahiplik alindi) -> {0}" -f $d.InstanceId) -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Bitti. Simdi telefonu USB'den CIKAR-TAK, sonra: fastboot devices" -ForegroundColor Cyan
