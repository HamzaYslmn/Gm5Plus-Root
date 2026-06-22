#!/data/data/com.termux/files/usr/bin/sh
# GM5 Plus arka cift-LED flas. Root gerekir. (Onflas YOK = ekran flasi, donanim degil.)
# Kullanim: flash on [1-200] | off | toggle | blink [adet]
L=/sys/class/leds
on(){ su -c "echo ${1:-100} > $L/led:torch_0/brightness; echo ${1:-100} > $L/led:torch_1/brightness; echo 2 > $L/led:switch/brightness"; }
off(){ su -c "echo 0 > $L/led:switch/brightness; echo 0 > $L/led:torch_0/brightness; echo 0 > $L/led:torch_1/brightness"; }
case "$1" in
  on) on "$2"; echo "arka flas ACIK (${2:-100}/200)";;
  off) off; echo "arka flas KAPALI";;
  toggle) [ "$(su -c "cat $L/led:switch/brightness")" != "0" ] && { off; echo KAPALI; } || { on; echo ACIK; };;
  blink) n=${2:-3}; while [ "$n" -gt 0 ]; do on 150; sleep 0.25; off; sleep 0.25; n=$((n-1)); done; echo "blink x${2:-3}";;
  *) echo "flash on [1-200] | off | toggle | blink [adet]";;
esac
