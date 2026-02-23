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
        
        self.status_signal.emit(f"Kullanıcı ayarları yapılandırılıyor: {user_name}...")
        self.log_signal.emit(f"[*] Chroot işlemlerine başlanıyor. Kullanıcı: {user_name}")
        
        # Pseudo filesystems bind mount
        self.run_cmd(f"mount --bind /dev {self.target_mount}/dev")
        self.run_cmd(f"mount --bind /proc {self.target_mount}/proc")
        self.run_cmd(f"mount --bind /sys {self.target_mount}/sys")

        # Chroot Komutları
        chroot_base = f"chroot {self.target_mount} /bin/bash -c "
        
        # Kullanıcı oluşturma
        self.run_cmd(chroot_base + f"'useradd -m -s /bin/bash {user_name}'")
        
        if sudo:
            self.run_cmd(chroot_base + f"'usermod -aG wheel {user_name}'")
            self.log_signal.emit(f"    - {user_name} sudo (wheel) grubuna eklendi.")
            
        # ro-repo vb. (Örnek)
        self.log_signal.emit("    - ro-repo ve ro-theme yapılandırılıyor...")
        self.run_cmd(chroot_base + "'cp -r /etc/skel/. /home/" + user_name + "/'")
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
