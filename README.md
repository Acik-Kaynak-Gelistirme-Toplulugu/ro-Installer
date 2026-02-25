# ro-Installer
**Created by minitheguitarist**

---

## Türkçe
ro-Installer, **ro-ASD** işletim sistemi için özel olarak tasarlanmış, modern bilgisayarlara yönelik yeni nesil bir sistem kurulum (Installer) aracıdır. Python (PyQt6 WebEngine) arka planı ve güncel Web Teknolojileri (HTML/CSS/JS) kullanılarak geliştirilmiş, "Glassmorphism" temalı şık ve sezgisel bir kullanıcı arayüzü sunar.

### Özellikler
- **Dinamik Disk Yönetimi:** `lsblk` üzerinden canlı disk taraması yaparak donanımlarınızı listeler, diskinizdeki boş/dolu alanı anlık hesaplayarak Dual-Boot (Yanına Kur) sınırlarını güvenliye alır.
- **Kurulum Tipleri:** Tüm diski silme veya mevcut sistemin yanına kurma (Dual Boot).
- **Dosya Sistemi Desteği:** EXT4, BTRFS ve XFS.
- **Canlı Ağ Entegrasyonu:** Wi-Fi ağlarını (NetworkManager üzerinden) arayüzde listeler ve kurulum sırasında internete bağlanmanızı sağlar.
- **Kişiselleştirme:** Bölge, Zaman Dilimi ve Klavye (TR/EN) düzeni seçimi. Kurulumda oluşturduğunuz kullanıcıyı hedef sisteme tam yetkili (`wheel`) şekilde aktarır.
- **Çoklu Dil Desteği:** Kurulum anında dilediğiniz zaman Türkçe ve İngilizce arasında geçiş yapabilirsiniz. Terminal logları dahi seçtiğiniz dile entegre çalışır.

---

## English
ro-Installer is a next-generation system installation tool designed specifically for the **ro-ASD** operating system. Powered by a Python (PyQt6 WebEngine) backend and modern Web Technologies (HTML/CSS/JS), it offers a sleek, intuitive, and Glassmorphism-themed user interface.

### Features
- **Dynamic Disk Management:** Performs live disk scanning via `lsblk`, safely calculating exact used/free space constraints for Dual-Boot configurations.
- **Installation Types:** Erase the entire disk or Install Alongside the current OS (Dual-Boot).
- **File System Support:** EXT4, BTRFS, and XFS.
- **Live Network Integration:** Scans and lists Wi-Fi networks (via NetworkManager) directly in the UI, allowing you to connect during the setup.
- **Personalization:** Region, Timezone, and Keyboard (TR/EN) layout selection. It perfectly creates and transfers your user profile (`wheel` authorized) into the target system.
- **Multi-language Support:** Seamlessly switch between Turkish and English at any point during the installation. Even backend installation logs adapt to your chosen locale.
