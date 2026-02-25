import os
import time
import json
import subprocess
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QThread

# GÜVENLİK AYARI: Gerçek disk formatlamayı önlemek için DRY_RUN = True
# Eğer bu False yapılırsa tüm komutlar sisteme harfiyen uygulanır!
DRY_RUN = True

class InstallWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.target_mount = "/mnt/ro-target"
        
        # Determine language from locale config
        loc = self.config.get('locale', 'tr_TR.UTF-8')
        self.lang = 'en' if 'en_US' in loc else 'tr'
        
        # Localization Dictionary
        self.i18n = {
            'tr': {
                'prepare_status': "Disk yapılandırılıyor ({} - {})...",
                'prepare_log1': "[*] Disk Hazırlığı Başladı. Tür: {}, FS: {}",
                'prepare_log2': "    {} diski tamamen siliniyor (GPT Parti tablosu)...",
                'prepare_log3': "    EFI Boot bölümü (512MB) oluşturuluyor...",
                'prepare_log4': "    Swap bölümü (4GB) oluşturuluyor...",
                'prepare_log_shrink': "    Disk küçültme ve yeni alan açma komutları hesaplanıyor...",
                'mount_status': "Yeni disk bölümleri sisteme bağlanıyor (Mount)...",
                'mount_log': "[*] Disk bölümleri {} altına bağlanıyor.",
                'copy_status': "İşletim sistemi hedef diske yazılıyor (RootFS Kopyalama)...",
                'copy_log1': "[*] Bu işlem diske ve USB hızına bağlı olarak 5-15 dakika sürebilir.",
                'copy_log2': "[+] Sistem imajı başarıyla kopyalandı.",
                'chroot_status': "Sistem ayarları ve kullanıcı yapılandırılıyor: {}...",
                'chroot_log1': "[*] Chroot işlemlerine başlanıyor. Bölge: {}, Dil: {}",
                'chroot_log2': "    - Bölge ve Zaman Dilimi ayarlanıyor...",
                'chroot_log3': "    - Sistem dili (Locale) ayarlanıyor...",
                'chroot_log4': "    - Klavye düzeni ayarlanıyor...",
                'chroot_log5': "    - {} sudo (wheel) grubuna eklendi.",
                'chroot_log6': "    - Root (Su) şifresi ayrı olarak ayarlandı.",
                'chroot_log7': "    - Skeleton (/etc/skel) şablonları kopyalanıyor...",
                'kernel_status': "Kurulum Modu: {} Çekirdek (Kernel) işleniyor...",
                'kernel_log': "[*] Kernel Modu: {}",
                'bootloader_status': "Önyükleyici (Bootloader) kuruluyor...",
                'bootloader_log1': "[*] Sistemin boot edebilmesi için GRUB2-EFI ayarları yapılıyor...",
                'bootloader_log2': "    - Bootloader kurulumu başarıyla tamamlandı.",
                'finish_status1': "Son işlem ve temizlik yapılıyor...",
                'finish_log1': "[*] Kurulum aracı hedef sistemden siliniyor (Self-Destruct)...",
                'finish_log2': "[*] Dağıtım bağlanma noktaları (mount) sökülüyor...",
                'finish_status2': "Kurulum başarıyla tamamlandı!",
                'finish_log3': "[BAŞARILI] Tüm sistem başarıyla kuruldu ve yapılandırıldı.",
                'finish_emit1': "Kurulum tamamlandı",
                'start_log': "--- Kurulum İşlemi Başladı (DRY_RUN={}) ---",
                'error_status': "Kurulum Başarısız: {}",
                'error_log': "[KRİTİK HATA] Kurulum durduruldu: {}"
            },
            'en': {
                'prepare_status': "Configuring disk ({} - {})...",
                'prepare_log1': "[*] Disk Preparation Started. Type: {}, FS: {}",
                'prepare_log2': "    {} disk is being completely erased (GPT Partition table)...",
                'prepare_log3': "    Creating EFI Boot partition (512MB)...",
                'prepare_log4': "    Creating Swap partition (4GB)...",
                'prepare_log_shrink': "    Calculating disk shrinking and new space commands...",
                'mount_status': "Mounting new disk partitions to the system...",
                'mount_log': "[*] Disk partitions are being mounted under {}.",
                'copy_status': "Writing Operating System to target disk (RootFS Copy)...",
                'copy_log1': "[*] This process may take 5-15 minutes depending on disk and USB speed.",
                'copy_log2': "[+] System image successfully copied.",
                'chroot_status': "Configuring system settings and user: {}...",
                'chroot_log1': "[*] Starting Chroot operations. Region: {}, Locale: {}",
                'chroot_log2': "    - Configuring Region and Timezone...",
                'chroot_log3': "    - Configuring System language (Locale)...",
                'chroot_log4': "    - Configuring Keyboard layout...",
                'chroot_log5': "    - Added {} to sudo (wheel) group.",
                'chroot_log6': "    - Root (Su) password set separately.",
                'chroot_log7': "    - Copying Skeleton (/etc/skel) templates...",
                'kernel_status': "Installation Mode: Processing {} Kernel...",
                'kernel_log': "[*] Kernel Mode: {}",
                'bootloader_status': "Installing Bootloader...",
                'bootloader_log1': "[*] Configuring GRUB2-EFI settings for system boot...",
                'bootloader_log2': "    - Bootloader installation completed successfully.",
                'finish_status1': "Performing final operations and cleanup...",
                'finish_log1': "[*] Removing installer tool from the target system (Self-Destruct)...",
                'finish_log2': "[*] Unmounting distribution points...",
                'finish_status2': "Installation completed successfully!",
                'finish_log3': "[SUCCESS] The entire system has been successfully installed and configured.",
                'finish_emit1': "Installation completed",
                'start_log': "--- Installation Process Started (DRY_RUN={}) ---",
                'error_status': "Installation Failed: {}",
                'error_log': "[CRITICAL ERROR] Installation stopped: {}"
            }
        }
        
    def t(self, key, *args):
        """Helper for translating log messages."""
        return self.i18n[self.lang].get(key, "").format(*args)

    def run_cmd(self, cmd, shell=True):
        """Yardımcı Metot: Komut çalıştırıcı (Dry-Run opsiyonlu)"""
        self.log_signal.emit(f"    [CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        
        if DRY_RUN:
            time.sleep(0.5) # Simüle gecikmesi
            return 0, "DRY RUN MODE"
        
        try:
            result = subprocess.run(cmd, shell=shell, text=True, capture_output=True, check=True)
            return result.returncode, result.stdout
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"    [HATA] Komut Başarısız: {e.stderr}")
            raise Exception(f"Komut Hatası: {e.stderr}")

    def prepare_disk(self):
        disk_type = self.config.get('diskType', 'Tamamen')
        fs_type = self.config.get('fsType', 'ext4')
        
        self.status_signal.emit(self.t('prepare_status', disk_type, fs_type))
        self.log_signal.emit(self.t('prepare_log1', disk_type, fs_type))

        target_hdd = self.config.get('targetDisk', '/dev/sda')
        
        if disk_type in ['Tamamen', 'Erase Entire Disk']:
            self.log_signal.emit(self.t('prepare_log2', target_hdd))
            # 1. GPT Partition Table
            self.run_cmd(f"parted -s {target_hdd} mklabel gpt")
            
            # 2. EFI System Partition (FAT32, ~512MB)
            self.log_signal.emit(self.t('prepare_log3'))
            self.run_cmd(f"parted -s {target_hdd} mkpart primary fat32 1MiB 513MiB")
            self.run_cmd(f"parted -s {target_hdd} set 1 boot on")
            self.run_cmd(f"parted -s {target_hdd} set 1 esp on")
            
            # 3. Swap Partition (Linux-swap, ~4GB)
            self.log_signal.emit(self.t('prepare_log4'))
            self.run_cmd(f"parted -s {target_hdd} mkpart primary linux-swap 513MiB 4609MiB")
            
            # 4. Root Partition (Kalan Tüm Alan)
            self.log_signal.emit(f"    Root bölümü ({fs_type}) oluşturuluyor...")
            self.run_cmd(f"parted -s {target_hdd} mkpart primary {fs_type} 4609MiB 100%")
            
            # === FORMATLAMA (MKFS) ===
            self.status_signal.emit("Disk bölümleri biçimlendiriliyor (Format)...")
            self.run_cmd(f"mkfs.fat -F32 {target_hdd}1")
            self.run_cmd(f"mkswap {target_hdd}2")
            
            if fs_type == 'ext4':
                self.run_cmd(f"mkfs.ext4 -F {target_hdd}3")
            elif fs_type == 'btrfs':
                self.run_cmd(f"mkfs.btrfs -f {target_hdd}3")
            elif fs_type == 'xfs':
                self.run_cmd(f"mkfs.xfs -f {target_hdd}3")
                
        elif disk_type in ['Yanına', 'Install Alongside']:
            self.log_signal.emit(self.t('prepare_log_shrink'))
            self.run_cmd(f"parted -s {target_hdd} resizepart ...") # Simülasyon
        
        self.progress_signal.emit(25)

    def mount_target(self):
        target_hdd = self.config.get('targetDisk', '/dev/sda')
        self.status_signal.emit(self.t('mount_status'))
        self.log_signal.emit(self.t('mount_log', self.target_mount))
        
        self.run_cmd(f"mkdir -p {self.target_mount}")
        self.run_cmd(f"mount {target_hdd}3 {self.target_mount}") # ROOT Mount
        
        self.run_cmd(f"mkdir -p {self.target_mount}/boot/efi")
        self.run_cmd(f"mount {target_hdd}1 {self.target_mount}/boot/efi") # ESP Mount
        
        self.run_cmd(f"swapon {target_hdd}2") # Swap Aktif
        
        self.progress_signal.emit(35)

    def copy_system(self):
        self.status_signal.emit(self.t('copy_status'))
        self.log_signal.emit(self.t('copy_log1'))
        
        # Gerçek rsync komutu (Canlı sistemin RAM harici tüm kalıcı sistem bloklarını hedef diske aktarır)
        rsync_cmd = (
            f"rsync -aAXv "
            f"--exclude='/dev/*' "
            f"--exclude='/proc/*' "
            f"--exclude='/sys/*' "
            f"--exclude='/tmp/*' "
            f"--exclude='/run/*' "
            f"--exclude='/mnt/*' "
            f"--exclude='/media/*' "
            f"--exclude='/lost+found' "
            f"/ {self.target_mount}/"
        )
        self.run_cmd(rsync_cmd)
        
        for i in range(40, 75, 5):
            time.sleep(0.3)
            self.progress_signal.emit(i)
        
        self.log_signal.emit(self.t('copy_log2'))

    def chroot_configure(self):
        user_name = self.config.get('username', 'ro-user')
        sudo = self.config.get('sudo', False)
        
        region = self.config.get('region', 'Europe/Istanbul')
        locale = self.config.get('locale', 'tr_TR.UTF-8')
        keyboard = self.config.get('keyboard', 'tr')
        
        self.status_signal.emit(self.t('chroot_status', user_name))
        self.log_signal.emit(self.t('chroot_log1', region, locale))
        
        # Pseudo filesystems bind mount
        self.run_cmd(f"mount --bind /dev {self.target_mount}/dev")
        self.run_cmd(f"mount --bind /proc {self.target_mount}/proc")
        self.run_cmd(f"mount --bind /sys {self.target_mount}/sys")

        # Chroot Komutları
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        
        # Zaman Dilimi, Saat ve Dil (Locale) Ayarları
        self.log_signal.emit(self.t('chroot_log2'))
        self.run_cmd(chroot_base + f"'ln -sf /usr/share/zoneinfo/{region} /etc/localtime'")
        self.run_cmd(chroot_base + "'hwclock --systohc --utc'")
        
        self.log_signal.emit(self.t('chroot_log3'))
        self.run_cmd(chroot_base + f"'echo \"LANG={locale}\" > /etc/locale.conf'")
        self.run_cmd(chroot_base + f"'echo \"{locale} UTF-8\" >> /etc/locale.gen'")
        self.run_cmd(chroot_base + "'locale-gen'")
        
        self.log_signal.emit(self.t('chroot_log4'))
        self.run_cmd(chroot_base + f"'echo \"KEYMAP={keyboard}\" > /etc/vconsole.conf'")
        self.run_cmd(chroot_base + f"'localectl set-x11-keymap {keyboard}'")

        # Kullanıcı oluşturma
        self.run_cmd(chroot_base + f"'useradd -m -U -s /bin/bash -c \"{self.config.get('name', '')} {self.config.get('surname', '')}\" {user_name}'")
        
        # Şifre ataması (Şifreler düz metin olarak geliyor, chpasswd ile besliyoruz)
        user_pass = self.config.get('password', '1234')
        self.run_cmd(f"echo '{user_name}:{user_pass}' | chroot {self.target_mount} chpasswd")
        
        if sudo:
            self.run_cmd(chroot_base + f"'usermod -aG wheel {user_name}'")
            self.log_signal.emit(self.t('chroot_log5', user_name))
        else:
            root_pass = self.config.get('rootPassword', '1234')
            self.run_cmd(f"echo 'root:{root_pass}' | chroot {self.target_mount} chpasswd")
            self.log_signal.emit(self.t('chroot_log6'))
            
        # ro-repo vb. (Örnek)
        self.log_signal.emit(self.t('chroot_log7'))
        # (useradd -m ile skel zaten kopyalandı ama tema vs. için ekstra izinleri yenileyebiliriz)
        self.run_cmd(chroot_base + f"'chown -R {user_name}:{user_name} /home/{user_name}'")
        
        self.progress_signal.emit(85)

    def install_kernel(self):
        kernel_type = self.config.get('kernelType', 'Standart')
        self.status_signal.emit(self.t('kernel_status', kernel_type))
        self.log_signal.emit(self.t('kernel_log', kernel_type))
        
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        
        if kernel_type == 'Standart':
            self.run_cmd(chroot_base + "'dnf install -y kernel kernel-core kernel-modules'")
        else:
            self.run_cmd(chroot_base + "'dnf install -y /opt/ro-packages/*.rpm'") # Deneysel local rpmler
            
        self.progress_signal.emit(90)

    def setup_bootloader(self):
        self.status_signal.emit(self.t('bootloader_status'))
        self.log_signal.emit(self.t('bootloader_log1'))
        
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        self.run_cmd(chroot_base + "'grub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ro-ASD --recheck'")
        self.run_cmd(chroot_base + "'grub2-mkconfig -o /boot/grub2/grub.cfg'")
        
        self.log_signal.emit(self.t('bootloader_log2'))
        self.progress_signal.emit(95)

    def finish_and_umount(self):
        self.status_signal.emit(self.t('finish_status1'))
        self.log_signal.emit(self.t('finish_log1'))
        
        # Self-destruct: Kurulum bittiğinde aracı hedef sistemden kaldır.
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        self.run_cmd(chroot_base + "'dnf remove -y ro-installer'")

        self.log_signal.emit(self.t('finish_log2'))
        
        self.run_cmd(f"umount {self.target_mount}/dev")
        self.run_cmd(f"umount {self.target_mount}/proc")
        self.run_cmd(f"umount {self.target_mount}/sys")
        self.run_cmd(f"umount {self.target_mount}/boot/efi")
        self.run_cmd(f"umount {self.target_mount}")
        
        self.progress_signal.emit(100)
        self.status_signal.emit(self.t('finish_status2'))
        self.log_signal.emit(self.t('finish_log3'))
        self.finished_signal.emit(True, self.t('finish_emit1'))

    def run(self):
        try:
            self.log_signal.emit(self.t('start_log', DRY_RUN))
            self.progress_signal.emit(5)
            
            self.prepare_disk()
            self.mount_target()
            self.copy_system()
            self.chroot_configure()
            self.install_kernel()
            self.setup_bootloader()
            self.finish_and_umount()

        except Exception as e:
            self.status_signal.emit(self.t('error_status', str(e)))
            self.log_signal.emit(self.t('error_log', str(e)))
            self.progress_signal.emit(0)
            self.finished_signal.emit(False, str(e))

class BackendBridge(QObject):
    """HTML JS ile Python arasında köprü görevi görür"""
    
    progressChanged = pyqtSignal(int)
    logMessageSignal = pyqtSignal(str)
    statusChangedSignal = pyqtSignal(str)
    installFinished = pyqtSignal(bool, str)
    
    # Yeni eklendi: Wi-Fi tarama ve bağlantı sinyalleri
    wifiListSignal = pyqtSignal(str)
    wifiConnectStatus = pyqtSignal(bool, str)
    
    # Yeni eklendi: Disk ve OS Tespit sinyalleri
    diskListSignal = pyqtSignal(str)
    osDetectedSignal = pyqtSignal(bool, str)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.worker = None

    @pyqtSlot()
    def exitInstaller(self):
        print("[Backend] Sistem yeniden başlatılıyor...")
        self.main_window.close()

    @pyqtSlot(str)
    def logMessage(self, msg):
        print(f"[UI Log] {msg}")

    @pyqtSlot()
    def detectOS(self):
        """Diskteki kurulu işletim sistemlerini (Windows/Linux) tespit etmeye çalışır."""
        try:
            self.logMessageSignal.emit("Diskteki işletim sistemleri ve diskler taranıyor...")
            # blkid ile kurulu dosya sistemlerini basitçe analiz edelim
            result = subprocess.run(['blkid'], capture_output=True, text=True)
            output = result.stdout.lower()
            
            # Windows boot manager veya genel NTFS kontrolü
            if 'ntfs' in output or 'bitlocker' in output or 'vfat' in output and 'efi' in output:
                self.logMessageSignal.emit("[+] Windows (veya EFI bölüntülü başka bir OS) kurulumu tespit edildi!")
                self.osDetectedSignal.emit(True, "Windows (veya başka bir OS) tespit edildi.")
            # Diğer Linux dağıtımları
            elif 'ext4' in output or 'btrfs' in output or 'xfs' in output:
                self.logMessageSignal.emit("[+] Başka bir Linux / Dosya Sistemi tespit edildi!")
                self.osDetectedSignal.emit(True, "Başka bir dosya sistemi bulundu.")
            else:
                self.logMessageSignal.emit("[-] Yalnızca boş disk veya tanınmayan bölümler bulundu.")
                self.osDetectedSignal.emit(False, "")
                
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] İşletim sistemi taranırken hata: {str(e)}")
            self.osDetectedSignal.emit(False, "")

    @pyqtSlot()
    def scanWifi(self):
        """nmcli kullanarak çevredeki Wi-Fi ağlarını tarar ve JSON sinyali olarak yollar."""
        try:
            self.logMessageSignal.emit("Ağlar aranıyor...")
            # nmcli -t -f active,ssid,signal,security dev wifi list
            result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid,signal,security', 'dev', 'wifi', 'list'], 
                                    capture_output=True, text=True, check=True)
            
            networks = []
            for line in result.stdout.split('\n'):
                if not line.strip(): continue
                parts = line.split(':')
                if len(parts) >= 4:
                    active, ssid, signal, security = parts[0], parts[1], parts[2], parts[3]
                    if not ssid: continue # Gizli ağları atla
                    
                    networks.append({
                        'active': active == 'yes',
                        'ssid': ssid,
                        'signal': int(signal) if signal.isdigit() else 0,
                        'security': security
                    })
            
            # Aynı SSID'den gelen birden çok sinyali tekilleştir, en güçlüsünü tut
            unique_nets = {}
            for net in networks:
                if net['ssid'] not in unique_nets or net['signal'] > unique_nets[net['ssid']]['signal']:
                    unique_nets[net['ssid']] = net
                    
            sorted_nets = sorted(list(unique_nets.values()), key=lambda x: x['signal'], reverse=True)
            
            # Ethernet kontrolü (ethernet:connected var mı?)
            eth_active = False
            try:
                eth_res = subprocess.run(['nmcli', '-t', '-f', 'type,state', 'dev'], capture_output=True, text=True, check=True)
                if 'ethernet:connected' in eth_res.stdout:
                    eth_active = True
                    self.logMessageSignal.emit("[+] Ethernet bağlantısı tespit edildi.")
            except:
                pass

            response = {
                "ethernet_active": eth_active,
                "networks": sorted_nets
            }
            
            self.wifiListSignal.emit(json.dumps(response))
            
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] Wi-Fi tarama hatası: {str(e)}")
            self.wifiListSignal.emit(json.dumps({"ethernet_active": False, "networks": []}))

    @pyqtSlot()
    def scanDisks(self):
        """lsblk kullanarak sisteme bağlı tüm diskleri tarar."""
        try:
            self.logMessageSignal.emit("Disk sürücüleri aranıyor...")
            # Sadece cihazlar, root'suz da çalışabilen -J (JSON) output veren lsblk
            result = subprocess.run(
                ['lsblk', '-d', '-n', '-J', '-o', 'NAME,SIZE,MODEL,TYPE'], 
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            disks = []
            
            if 'blockdevices' in data:
                for dev in data['blockdevices']:
                    # loop, rom (cdrom), ram gibi hedefleri kurulum listesinden çıkart
                    if dev.get('type') == 'disk' and not dev.get('name', '').startswith(('loop', 'ram', 'sr', 'zram')):
                        name = f"/dev/{dev.get('name')}"
                        size = dev.get('size', 'Bilinmiyor')
                        model = dev.get('model', 'Model Bilinmiyor')
                        if model is None: model = 'Bilinmeyen Disk'
                        disks.append({'name': name, 'size': size, 'model': model.strip()})
                        
            self.diskListSignal.emit(json.dumps(disks))
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] Disk tarama hatası: {str(e)}")
            self.diskListSignal.emit("[]")

    @pyqtSlot(str, str)
    def connectWifi(self, ssid, password):
        """Kullanıcının girdiği şifre ile nmcli üzerinden Wi-Fi ağına bağlanır."""
        try:
            self.logMessageSignal.emit(f"'{ssid}' ağına bağlanılıyor...")
            
            # Eğer daha önce hatalı şifre girilmişse nmcli bunu önbelleğe alır ve yapılandırmayı bozar.
            # Live USB olduğumuz için bu bağlantı kimliğini (profile) silmek tamamen güvenlidir.
            subprocess.run(['nmcli', 'connection', 'delete', 'id', ssid], capture_output=True)
            
            cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
            if password:
                cmd.extend(['password', password])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logMessageSignal.emit(f"[++] Başarıyla '{ssid}' ağına bağlanıldı.")
                self.wifiConnectStatus.emit(True, ssid)
            else:
                raw_err = result.stderr.lower()
                self.logMessageSignal.emit(f"[--] Bağlantı başarısız: {raw_err}")
                
                if "gizli bilgiler" in raw_err or "secrets" in raw_err or "wireless-security" in raw_err:
                    user_err = "Girdiğiniz Wi-Fi şifresi yanlış veya ağ tarafından reddedildi. Lütfen kontrol edip tekrar deneyin."
                elif "not found" in raw_err or "bulunamadi" in raw_err:
                    user_err = "Belirtilen Wi-Fi ağı bulunamadı veya kapsama alanı dışında."
                else:
                    user_err = "Bağlantı hatası: Ağa bağlanılamadı. Lütfen şifreyi kontrol edin."
                    
                self.wifiConnectStatus.emit(False, user_err)
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] Wi-Fi bağlanma hatası: {str(e)}")
            self.wifiConnectStatus.emit(False, str(e))

    @pyqtSlot(str)
    def changeLiveKeyboard(self, val):
        """Live ISO üzerinde klavye dilini anında değiştirir."""
        try:
            self.logMessageSignal.emit(f"Klavye düzeni değiştiriliyor: {val}")
            # X11 için anında değişiklik
            subprocess.run(['setxkbmap', val], capture_output=True)
            # Eğer Wayland ise localectl ile de destekleyelim
            subprocess.run(['localectl', 'set-x11-keymap', val], capture_output=True)
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] Klavye değiştirme hatası: {str(e)}")

    @pyqtSlot(str)
    def startInstall(self, config_json):
        try:
            config = json.loads(config_json)
            self.logMessageSignal.emit("Python Backend: Kurulum komutu alındı.")
            
            self.worker = InstallWorker(config)
            self.worker.progress_signal.connect(self.progressChanged)
            self.worker.log_signal.connect(self.logMessageSignal)
            self.worker.status_signal.connect(self.statusChangedSignal)
            self.worker.finished_signal.connect(self.installFinished)
            
            self.worker.start()
            
        except Exception as e:
            self.logMessageSignal.emit(f"[HATA] Frontend bağlantı hatası: {str(e)}")
