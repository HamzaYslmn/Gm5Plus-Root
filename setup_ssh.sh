#!/data/data/com.termux/files/usr/bin/bash
exec > /data/data/com.termux/files/home/ssh_setup.log 2>&1
echo "=== START ==="
yes | pkg install -y openssh termux-auth
echo "INSTALL_EXIT:$?"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
# sshd'yi baslat (Termux varsayilan port 8022)
pkill sshd 2>/dev/null
sshd
echo "SSHD_EXIT:$?"
sleep 1
echo "=== whoami / port ==="
whoami
cat $PREFIX/etc/ssh/sshd_config | grep -i port
echo "ALLDONE"
