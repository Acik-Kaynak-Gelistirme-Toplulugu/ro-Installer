import os
import subprocess

def run_in_chroot(target_mount: str, command: list):
    """
    Hedef sisteme chroot ile bağlanıp verilen komutu çalıştırır.
    Gerçek kodlama (Execution phase) sırasında KPMcore partitionlar ayrıldıktan
    sonra hedef /mnt/ro-ASD altına mount edilir ve komutlar oraya itilir.
    """
    chroot_cmd = ["chroot", target_mount] + command
    print(f"[Backend] Chroot komutu çalıştırılıyor: {' '.join(chroot_cmd)}")
    
    # process = subprocess.run(chroot_cmd, capture_output=True, text=True)
    # return process.stdout

def setup_ro_repo(target_mount: str):
    print("[Backend/ro-repo] Açık Kaynak Geliştirme Topluluğu ro-repo sisteme kuruluyor...")
    # ro-repo kurulum simülasyonu
    run_in_chroot(target_mount, ["curl", "-sSL", "https://raw.githubusercontent.com/Acik-Kaynak-Gelistirme-Toplulugu/ro-repo/main/install.sh", "|", "bash"])
    print("[Backend/ro-repo] Başarı: Repo eklendi ve dnf cache güncellendi.")

def setup_ro_theme(target_mount: str):
    print("[Backend/ro-theme] ro-theme sisteme kuruluyor ve varsayılan yapılıyor...")
    # ro-theme kurulum simülasyonu
    run_in_chroot(target_mount, ["curl", "-sSL", "https://raw.githubusercontent.com/Acik-Kaynak-Gelistirme-Toplulugu/ro-theme/main/install.sh", "|", "bash"])
    print("[Backend/ro-theme] Başarı: Tema eklendi (/etc/skel).")

def install_kernel(target_mount: str, kernel_type: str):
    if kernel_type == "standart":
        print("[Backend/Kernel] Standart Fedora Kerneli dnf ile indiriliyor...")
        run_in_chroot(target_mount, ["dnf", "-y", "install", "kernel", "kernel-core", "kernel-modules"])
    else:
        print("[Backend/Kernel] ro-Yamalı kernel yerel opt/ klasöründen kuruluyor...")
        run_in_chroot(target_mount, ["rpm", "-ivh", "/opt/installer-kernels/ro-kernel*.rpm"])
        
    # GRUB Güncellemesi
    run_in_chroot(target_mount, ["grub2-mkconfig", "-o", "/boot/grub2/grub.cfg"])
    print("[Backend/Kernel] Başarı: Kernel kuruldu ve GRUB güncellendi.")

if __name__ == "__main__":
    # Test Modülü
    print("--- RO-INSTALLER BACKEND TEST ---")
    TARGET = "/mnt/ro-target"
    
    install_kernel(TARGET, "deneysel")
    setup_ro_repo(TARGET)
    setup_ro_theme(TARGET)
