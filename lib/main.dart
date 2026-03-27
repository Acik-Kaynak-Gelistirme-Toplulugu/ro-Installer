import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme/app_theme.dart';
import 'state/installer_state.dart';
import 'widgets/installer_layout.dart';
import 'screens/welcome_screen.dart';
import 'screens/theme_screen.dart';
import 'screens/location_screen.dart';
import 'screens/network_screen.dart';
import 'screens/account_screen.dart';
import 'screens/type_screen.dart';
import 'screens/disk_selection_screen.dart';
import 'screens/manual_partition_screen.dart';
import 'screens/kernel_screen.dart';
import 'screens/installing_screen.dart';

void main() async {
  // ═══════════════════════════════════════════════════
  // ROOT YETKİ KONTROLÜ
  // Disk yazma, mount, mkfs, sgdisk gibi tüm komutlar
  // root yetkisi gerektirir. Root değilse pkexec ile
  // kendini yeniden başlatır.
  // ═══════════════════════════════════════════════════
  
  // Mevcut kullanıcı root mu kontrol et
  final uid = int.tryParse(Platform.environment['UID'] ?? 
      (await Process.run('id', ['-u'])).stdout.toString().trim()) ?? -1;
  
  if (uid != 0) {
    // Root değiliz — pkexec ile yeniden başlat
    print('[ro-Installer] Root yetkisi gerekiyor (UID: $uid). pkexec ile yükseltiliyor...');
    
    // Kendi çalıştırılabilir dosyamızın yolunu bul
    final execPath = Platform.resolvedExecutable;
    
    try {
      final result = await Process.run('pkexec', [execPath, ...Platform.executableArguments]);
      // pkexec bittiğinde (kullanıcı iptal etti veya uygulama kapandı)
      exit(result.exitCode);
    } catch (e) {
      print('[ro-Installer] pkexec başlatılamadı: $e');
      print('[ro-Installer] Lütfen uygulamayı "sudo ro-installer" ile başlatın.');
      exit(1);
    }
  }

  print('[ro-Installer] Root yetkisi doğrulandı (UID: $uid). Başlatılıyor...');

  runApp(
    ChangeNotifierProvider(
      create: (_) => InstallerState(),
      child: const RoInstallerApp(),
    ),
  );
}

class RoInstallerApp extends StatelessWidget {
  const RoInstallerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<InstallerState>(
      builder: (context, state, child) {
        return MaterialApp(
          title: 'Ro-ASD OS Installer',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: state.themeMode == 'dark' ? ThemeMode.dark : ThemeMode.light,
          debugShowCheckedModeBanner: false,
          home: const MainScreenWrapper(),
        );
      },
    );
  }
}

class MainScreenWrapper extends StatelessWidget {
  const MainScreenWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final state = Provider.of<InstallerState>(context);
    
    // Dinamik olarak adımlara göre ekran getirme
    String stepName = state.steps[state.currentStep];
    Widget currentScreen;
    
    switch (stepName) {
      case "Welcome":
        currentScreen = const WelcomeScreen();
        break;
      case "Theme":
        currentScreen = const ThemeScreen();
        break;
      case "Location":
        currentScreen = const LocationScreen();
        break;
      case "Network":
        currentScreen = const NetworkScreen();
        break;
      case "Account":
        currentScreen = const AccountScreen();
        break;
      case "Type":
        currentScreen = const TypeScreen();
        break;
      case "Disk":
        currentScreen = const DiskSelectionScreen();
        break;
      case "Partitions":
        currentScreen = const ManualPartitionScreen();
        break;
      case "Kernel":
        currentScreen = const KernelScreen();
        break;
      case "Install":
        currentScreen = const InstallingScreen();
        break;
      default:
        currentScreen = const Center(child: Text("Sayfa Bulunamadı"));
    }

    return InstallerLayout(child: currentScreen);
  }
}
