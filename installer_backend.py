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
        
        self.status_signal.emit(f"Disk yapılandırılıyor ({disk_type} - {fs_type})...")
        self.log_signal.emit(f"[*] Disk Hazırlığı Başladı. Tür: {disk_type}, FS: {fs_type}")

        if disk_type == 'Tamamen':
            self.log_signal.emit("    Hedef diski silme komutları hesaplanıyor...")
            self.run_cmd("parted -s /dev/vda mklabel gpt") # Örnek disk (vda/sda)
            self.run_cmd("parted -s /dev/vda mkpart ESP fat32 1MiB 513MiB")
            self.run_cmd("parted -s /dev/vda set 1 boot on")
            self.run_cmd(f"parted -s /dev/vda mkpart primary {fs_type} 513MiB 100%")
            
            # Format
            self.run_cmd("mkfs.fat -F32 /dev/vda1")
            if fs_type == 'ext4':
                self.run_cmd("mkfs.ext4 -F /dev/vda2")
            elif fs_type == 'btrfs':
                self.run_cmd("mkfs.btrfs -f /dev/vda2")
            elif fs_type == 'xfs':
                self.run_cmd("mkfs.xfs -f /dev/vda2")
                
        elif disk_type == 'Yanına':
            self.log_signal.emit("    Disk küçültme ve yeni alan açma komutları hesaplanıyor...")
            self.run_cmd("parted -s /dev/vda resizepart ...") # Simülasyon
        
        self.progress_signal.emit(25)

    def mount_target(self):
        self.status_signal.emit("Hedef bağlama noktaları oluşturuluyor...")
        self.log_signal.emit(f"[*] Disk bölümleri {self.target_mount} altına bağlanıyor.")
        
        self.run_cmd(f"mkdir -p {self.target_mount}")
        self.run_cmd(f"mount /dev/vda2 {self.target_mount}")
        self.run_cmd(f"mkdir -p {self.target_mount}/boot/efi")
        self.run_cmd(f"mount /dev/vda1 {self.target_mount}/boot/efi")
        
        self.progress_signal.emit(35)

    def copy_system(self):
        self.status_signal.emit("Sistem dosyaları kopyalanıyor (SquashFS)...")
        self.log_signal.emit("[*] Live sistem hedef diske aktarılıyor...")
        
        # Gerçekte SquashFS'ten root ağacını rsync veya unsquashfs ile kopyalarız
        # Örn: rsync -aAXH --info=progress2 /run/initramfs/live/LiveOS/ /mnt/ro-target/
        self.run_cmd(f"rsync -aAXv --exclude='/dev/*' --exclude='/proc/*' --exclude='/sys/*' --exclude='/tmp/*' --exclude='/run/*' --exclude='/mnt/*' --exclude='/media/*' --exclude='/lost+found' / {self.target_mount}/")
        
        for i in range(40, 75, 5):
            time.sleep(0.3)
            self.progress_signal.emit(i)
        
        self.log_signal.emit("[+] Sistem imajı başarıyla kopyalandı.")

    def chroot_configure(self):
        user_name = self.config.get('username', 'ro-user')
        sudo = self.config.get('sudo', False)
        
        region = self.config.get('region', 'Europe/Istanbul')
        locale = self.config.get('locale', 'tr_TR.UTF-8')
        keyboard = self.config.get('keyboard', 'tr')
        
        self.status_signal.emit(f"Sistem ayarları ve kullanıcı yapılandırılıyor: {user_name}...")
        self.log_signal.emit(f"[*] Chroot işlemlerine başlanıyor. Bölge: {region}, Dil: {locale}")
        
        # Pseudo filesystems bind mount
        self.run_cmd(f"mount --bind /dev {self.target_mount}/dev")
        self.run_cmd(f"mount --bind /proc {self.target_mount}/proc")
        self.run_cmd(f"mount --bind /sys {self.target_mount}/sys")

        # Chroot Komutları
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        
        # Zaman Dilimi, Saat ve Dil (Locale) Ayarları
        self.log_signal.emit("    - Bölge ve Zaman Dilimi ayarlanıyor...")
        self.run_cmd(chroot_base + f"'ln -sf /usr/share/zoneinfo/{region} /etc/localtime'")
        self.run_cmd(chroot_base + "'hwclock --systohc --utc'")
        
        self.log_signal.emit("    - Sistem dili (Locale) ayarlanıyor...")
        self.run_cmd(chroot_base + f"'echo \"LANG={locale}\" > /etc/locale.conf'")
        self.run_cmd(chroot_base + f"'echo \"{locale} UTF-8\" >> /etc/locale.gen'")
        self.run_cmd(chroot_base + "'locale-gen'")
        
        self.log_signal.emit("    - Klavye düzeni ayarlanıyor...")
        self.run_cmd(chroot_base + f"'echo \"KEYMAP={keyboard}\" > /etc/vconsole.conf'")
        self.run_cmd(chroot_base + f"'localectl set-x11-keymap {keyboard}'")

        # Kullanıcı oluşturma
        self.run_cmd(chroot_base + f"'useradd -m -U -s /bin/bash -c \"{self.config.get('name', '')} {self.config.get('surname', '')}\" {user_name}'")
        
        # Şifre ataması (Şifreler düz metin olarak geliyor, chpasswd ile besliyoruz)
        user_pass = self.config.get('password', '1234')
        self.run_cmd(f"echo '{user_name}:{user_pass}' | chroot {self.target_mount} chpasswd")
        
        if sudo:
            self.run_cmd(chroot_base + f"'usermod -aG wheel {user_name}'")
            self.log_signal.emit(f"    - {user_name} sudo (wheel) grubuna eklendi.")
        else:
            root_pass = self.config.get('rootPassword', '1234')
            self.run_cmd(f"echo 'root:{root_pass}' | chroot {self.target_mount} chpasswd")
            self.log_signal.emit("    - Root (Su) şifresi ayrı olarak ayarlandı.")
            
        # ro-repo vb. (Örnek)
        self.log_signal.emit("    - Skeleton (/etc/skel) şablonları kopyalanıyor...")
        # (useradd -m ile skel zaten kopyalandı ama tema vs. için ekstra izinleri yenileyebiliriz)
        self.run_cmd(chroot_base + f"'chown -R {user_name}:{user_name} /home/{user_name}'")
        
        self.progress_signal.emit(85)

    def install_kernel(self):
        kernel_type = self.config.get('kernelType', 'Standart')
        self.status_signal.emit(f"Kurulum Modu: {kernel_type} Çekirdek (Kernel) işleniyor...")
        self.log_signal.emit(f"[*] Kernel Modu: {kernel_type}")
        
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        
        if kernel_type == 'Standart':
            self.run_cmd(chroot_base + "'dnf install -y kernel kernel-core kernel-modules'")
        else:
            self.run_cmd(chroot_base + "'dnf install -y /opt/ro-packages/*.rpm'") # Deneysel local rpmler
            
        self.progress_signal.emit(90)

    def setup_bootloader(self):
        self.status_signal.emit("Bootloader (GRUB2) kuruluyor...")
        self.log_signal.emit("[*] Sistem Önyükleyici kuruluyor...")
        
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        self.run_cmd(chroot_base + "'grub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ro-ASD'")
        self.run_cmd(chroot_base + "'grub2-mkconfig -o /boot/grub2/grub.cfg'")
        
        self.progress_signal.emit(95)

    def finish_and_umount(self):
        self.status_signal.emit("Son işlem ve temizlik yapılıyor...")
        self.log_signal.emit("[*] Kurulum aracı hedef sistemden siliniyor (Self-Destruct)...")
        
        # Self-destruct: Kurulum bittiğinde aracı hedef sistemden kaldır.
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        self.run_cmd(chroot_base + "'dnf remove -y ro-installer'")

        self.log_signal.emit("[*] Dağıtım bağlanma noktaları (mount) sökülüyor...")
        
        self.run_cmd(f"umount {self.target_mount}/dev")
        self.run_cmd(f"umount {self.target_mount}/proc")
        self.run_cmd(f"umount {self.target_mount}/sys")
        self.run_cmd(f"umount {self.target_mount}/boot/efi")
        self.run_cmd(f"umount {self.target_mount}")
        
        self.progress_signal.emit(100)
        self.status_signal.emit("Kurulum başarıyla tamamlandı!")
        self.log_signal.emit("[BAŞARILI] Tüm sistem başarıyla kuruldu ve yapılandırıldı.")
        self.finished_signal.emit(True, "Kurulum tamamlandı")

    def run(self):
        try:
            self.log_signal.emit(f"--- Kurulum İşlemi Başladı (DRY_RUN={DRY_RUN}) ---")
            self.progress_signal.emit(5)
            
            self.prepare_disk()
            self.mount_target()
            self.copy_system()
            self.chroot_configure()
            self.install_kernel()
            self.setup_bootloader()
            self.finish_and_umount()

        except Exception as e:
            self.status_signal.emit(f"Kurulum Başarısız: {str(e)}")
            self.log_signal.emit(f"[KRİTİK HATA] Kurulum durduruldu: {str(e)}")
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
    
    # Yeni eklendi: OS Prober Sinyali
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
