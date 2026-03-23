#!/bin/bash

set -euo pipefail

# Root kontrolu
if [ "$EUID" -ne 0 ]; then
  echo "Birader bu scripti root olarak calistir (sudo ./build.sh)"
  exit
fi

echo "--- Ortamdaki SELinux Gevsetiliyor ---"
# Anaconda'nin chroot icinde takilmamasi icin gecici permissive yapiyoruz
setenforce 0

echo "--- Gerekli XDG dizinleri ayarlaniyor ---"
mkdir -p /var/tmp/xdg
chmod 0700 /var/tmp/xdg
chown root:root /var/tmp/xdg

echo "--- Lorax Installer yamasi yapiliyor ---"
# Eger bu dosya /tmp altinda yoksa burasi hata verir, gecici kaldirabilirsin.
# cp /tmp/installer.py /usr/lib/python3.14/site-packages/pylorax/installer.py 2>/dev/null || true

echo "--- Asili Kalan Eski Mountlar Zorla Temizleniyor ---"
# Bir onceki patlayan kurulumdan kalan "busy" klasorlerin agzina siciyoruz
umount -l /var/tmp/ro-asd-iso/* 2>/dev/null || true
rm -rf /var/tmp/ro-asd-iso
rm -f livemedia.log

if [ ! -d /var/tmp/ro-asd-repo/repodata ]; then
  echo "/var/tmp/ro-asd-repo/repodata bulunamadi"
  exit 1
fi

PROXY_ARG=()
if [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARG+=( "--proxy=${HTTP_PROXY}" )
elif [ -n "${http_proxy:-}" ]; then
  PROXY_ARG+=( "--proxy=${http_proxy}" )
fi

echo "--- Ro-ASD ISO Basimi Basliyor. Kemerleri bagla amk! ---"
env -i PATH="/usr/sbin:/usr/bin:/sbin:/bin" XDG_RUNTIME_DIR=/var/tmp/xdg HOME=/root \
livemedia-creator \
  --ks linux/packaging/ro-asd-live.ks \
  --no-virt \
  --resultdir /var/tmp/ro-asd-iso \
  --project "Ro-ASD" \
  --make-iso \
  --volid "RoASD_Live" \
  --iso-only \
  --iso-name Ro-ASD-Beta.iso \
  "${PROXY_ARG[@]}"

echo "--- SELinux Tekrar Aktif Ediliyor ---"
setenforce 1

echo "--- İŞLEM TAMAM ŞEFİM! ---"
