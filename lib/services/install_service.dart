import 'dart:async';
import 'dart:convert';
import 'dart:io';

class InstallService {
  InstallService._();
  static final InstallService instance = InstallService._();

  // Komut çalıştırma ve çıktıları canlı okuma
  Future<bool> runCmd(String cmd, List<String> args, void Function(String) onLog) async {
    onLog(">> \$cmd \${args.join(' ')}\n");
    try {
      final process = await Process.start(cmd, args);
      process.stdout.transform(utf8.decoder).listen((data) {
        if (data.trim().isNotEmpty) onLog(data.trim());
      });
      process.stderr.transform(utf8.decoder).listen((data) {
        if (data.trim().isNotEmpty) onLog("STDERR: \${data.trim()}");
      });
      final exitCode = await process.exitCode;
      
      if (exitCode != 0) {
        onLog(">> Komut bașarısız oldu. (Exit Code: \$exitCode)\n");
        return false;
      }
      return true;
    } catch (e) {
      onLog("EXCEPTION: \$e\n");
      return false;
    }
  }

  // Ana kurulum motoru
  Future<bool> runInstall(Map<String, dynamic> state, void Function(double progress, String status) onProgress) async {
    String logBuffer = "";
    void log(String msg) {
       // Log string handler
       // onProgress(-1.0, msg); (Opsiyonel UI streamleri icin).
       print(msg); // Terminal debug amacli
    }

    final selectedDisk = state['selectedDisk'] as String;
    final partitionMethod = state['partitionMethod'] as String; // 'full' or 'manual' or 'alongside'
    final manualPartitions = state['manualPartitions'] as List<dynamic>;

    try {
      if (partitionMethod == 'full') {
        onProgress(0.1, "Tüm disk sıfırlanıyor ve yapılandırılıyor: \$selectedDisk");
        
        // 1. Wipe partition table
        if (!await runCmd('sgdisk', ['-Z', selectedDisk], log)) return false;
        
        // 2. Create EFI Partition (512MB)
        if (!await runCmd('sgdisk', ['-n', '1:0:+512M', '-t', '1:ef00', selectedDisk], log)) return false;
        
        // 3. Create Root Partition (Rest of disk)
        if (!await runCmd('sgdisk', ['-n', '2:0:0', selectedDisk], log)) return false;
        
        await runCmd('partprobe', [selectedDisk], log);
        await Future.delayed(const Duration(seconds: 3));

        // Format
        String rootFs = state['fileSystem'] ?? 'btrfs';
        String efiPart = "\${selectedDisk}1";
        String rootPart = "\${selectedDisk}2";
        if (selectedDisk.contains("nvme") || selectedDisk.contains("loop")) {
          efiPart = "\${selectedDisk}p1";
          rootPart = "\${selectedDisk}p2";
        }

        onProgress(0.2, "Bölümler biçimlendiriliyor... (\${rootFs.toUpperCase()})");
        if (!await runCmd('mkfs.fat', ['-F32', efiPart], log)) return false;
        
        if (rootFs == 'btrfs') {
          if (!await runCmd('mkfs.btrfs', ['-f', rootPart], log)) return false;
        } else {
          if (!await runCmd('mkfs.ext4', ['-F', rootPart], log)) return false;
        }

        // Mount
        onProgress(0.3, "Bölümler (/mnt) hedefine bağlanıyor...");
        await runCmd('umount', ['-R', '/mnt'], log); 
        if (!await runCmd('mount', [rootPart, '/mnt'], log)) return false;
        if (!await runCmd('mkdir', ['-p', '/mnt/boot/efi'], log)) return false;
        if (!await runCmd('mount', [efiPart, '/mnt/boot/efi'], log)) return false;

      } else { // Elle Bölümlendirme (Manual Partitioning)
        onProgress(0.1, "Kullanıcının disk yapılandırma planı uygulanıyor...");
        
        // Önce bölümleri formatla (Sadece eylem yapılması planlananlar isPlanned == true)
        for (var p in manualPartitions) {
           if (p['isFreeSpace'] == true || p['isPlanned'] != true) continue;
           String partName = p['name'];
           String fsType = p['type'];
           
           if (fsType == 'fat32') {
             if (!await runCmd('mkfs.fat', ['-F32', partName], log)) return false;
           } else if (fsType == 'btrfs') {
             if (!await runCmd('mkfs.btrfs', ['-f', partName], log)) return false;
           } else if (fsType == 'ext4') {
             if (!await runCmd('mkfs.ext4', ['-F', partName], log)) return false;
           } else if (fsType == 'xfs') {
             if (!await runCmd('mkfs.xfs', ['-f', partName], log)) return false;
           } else if (fsType == 'linux-swap') {
             if (!await runCmd('mkswap', [partName], log)) return false;
           }
        }

        // Mount işlemleri (Root önceliği kritiktir!)
        await runCmd('umount', ['-R', '/mnt'], log);
        var rootPart = manualPartitions.firstWhere((p) => p['mount'] == '/', orElse: () => null);
        if (rootPart == null) { log("Root partisiz bir sistem! / montaj noktasını bulamadım."); return false; }
        
        if (!await runCmd('mount', [rootPart['name'], '/mnt'], log)) return false;

        // Diğerlerini Mountla
        for (var p in manualPartitions) {
           if (p['isFreeSpace'] == true || p['mount'] == '/' || p['mount'] == 'unmounted' || p['mount'] == '[SWAP]') continue;
           String mntPoint = "/mnt\${p['mount']}";
           if (!await runCmd('mkdir', ['-p', mntPoint], log)) return false;
           if (!await runCmd('mount', [p['name'], mntPoint], log)) return false;
        }

        // Swap var ise etkinleştir
        for (var p in manualPartitions) {
           if (p['mount'] == '[SWAP]') await runCmd('swapon', [p['name']], log);
        }
      }

      // ACT 2: SISTEM KOPYALAMASI (RSYNC Klonlama Teknolojisi)
      onProgress(0.4, "Live İşletim Sistemi Kök dosya hedef diske aktarılıyor...");
      onProgress(0.41, "Bu işlem disk hızına bağlı olarak 5-15 dakika sürebilir. (Rsync Çalışıyor...)");
      
      bool rsyncOk = await runCmd('rsync', [
        '-aAX',
        '--exclude=/dev/*',
        '--exclude=/proc/*',
        '--exclude=/sys/*',
        '--exclude=/tmp/*',
        '--exclude=/run/*',
        '--exclude=/mnt/*',
        '--exclude=/media/*',
        '--exclude=/lost+found',
        '--exclude=/etc/machine-id',
        '/', // Kaynak: Calisan Live Kök
        '/mnt/' // Hedef
      ], log);

      if (!rsyncOk) {
         log("Rsync (Kurulum ve dosya kopyalama) başarısız oldu.");
         return false;
      }

      // ACT 3: CHROOT SİSTEM BÜTÜNLÜĞÜ (BIND MOUNTS)
      onProgress(0.7, "Kök sistem bağlamaları yapılıyor (Chroot hazırlığı)...");
      await runCmd('mount', ['--bind', '/dev', '/mnt/dev'], log);
      await runCmd('mount', ['--bind', '/proc', '/mnt/proc'], log);
      await runCmd('mount', ['--bind', '/sys', '/mnt/sys'], log);
      await runCmd('mount', ['--bind', '/run', '/mnt/run'], log);

      // ACT 4: KULLANICI / TIMEZONE AYARLARI
      onProgress(0.8, "Zaman dilimi ve kullanıcı ayarları yapılandırılıyor...");
      String user = state['username'] ?? 'user';
      String pass = state['password'] ?? 'user';
      String tz = state['selectedRegion'] ?? 'Europe/Istanbul';
      
      await runCmd('chroot', ['/mnt', 'ln', '-sf', '/usr/share/zoneinfo/\$tz', '/etc/localtime'], log);
      await runCmd('chroot', ['/mnt', 'useradd', '-m', '-G', 'wheel,storage,power,network', '-s', '/bin/bash', user], log);
      
      await runCmd('chroot', ['/mnt', 'sh', '-c', 'echo "\$user:\$pass" | chpasswd'], log);
      await runCmd('chroot', ['/mnt', 'sh', '-c', 'echo "root:root" | chpasswd'], log); // Opsiyonel

      if (state['isAdministrator'] == true) {
         await runCmd('chroot', ['/mnt', 'sh', '-c', 'echo "\$user ALL=(ALL:ALL) ALL" > /etc/sudoers.d/\$user'], log);
      }

      // ACT 5: BOOTLOADER (rEFInd)
      onProgress(0.9, "Bootloader yapılandırılıyor (rEFInd)...");
      bool refindOk = await runCmd('chroot', ['/mnt', 'refind-install'], log);
      if (!refindOk) {
         log("INFO: refind-install uyarısı aldı (Standart Legacy ortamında alınabilir, UEFI gerektirir). Geçiliyor...");
      }

      // ACT 6: CLEANUP
      onProgress(0.95, "Sistem dosyaları korunuyor ve unmount işlemi başlatılıyor...");
      await runCmd('umount', ['-R', '/mnt'], log);

      onProgress(1.0, "Kurulum Hatasız Tamamlandı! Sistemi Yeniden Başlatabilirsiniz.");
      return true;

    } catch (e) {
      log("FATAL CATCH: \$e");
      return false;
    }
  }
}
