import 'dart:convert';
import 'dart:io';

class PartitionService {
  PartitionService._();
  static final PartitionService instance = PartitionService._();

  Future<List<Map<String, dynamic>>> getPartitions(String diskName) async {
    List<Map<String, dynamic>> partitionList = [];
    
    // Eğer seçilen disk bizim laboratuvar diskimiz ise (Sanal Disk)
    if (diskName == '/dev/RoASD_Safe_Disk') {
       return [
         {"name": "/dev/sda1", "type": "fat32", "sizeBytes": 512 * 1024 * 1024, "mount": "/boot/efi", "flags": "boot, esp", "isFreeSpace": false, "isPlanned": false},
         {"name": "/dev/sda2", "type": "ext4", "sizeBytes": 50 * 1024 * 1024 * 1024, "mount": "/", "flags": "", "isFreeSpace": false, "isPlanned": false},
         {"name": "Free Space", "type": "unallocated", "sizeBytes": 69 * 1024 * 1024 * 1024, "mount": "unmounted", "flags": "", "isFreeSpace": true, "isPlanned": false},
       ];
    }

    try {
      final result = await Process.run('lsblk', ['-J', '-b', '-o', 'NAME,FSTYPE,SIZE,MOUNTPOINT,PARTFLAGS', diskName]);
      if (result.exitCode == 0) {
        final Map<String, dynamic> parsed = jsonDecode(result.stdout.toString());
        if (parsed.containsKey('blockdevices')) {
          final devices = parsed['blockdevices'] as List<dynamic>;
          if (devices.isNotEmpty) {
             final diskSize = devices.first['size'] is int ? devices.first['size'] as int : int.tryParse(devices.first['size'].toString()) ?? 0;
             int usedSpace = 0;

             if (devices.first.containsKey('children')) {
                 final children = devices.first['children'] as List<dynamic>;
                 for (var child in children) {
                    final int sizeBytes = child['size'] is int ? child['size'] as int : int.tryParse(child['size'].toString()) ?? 0;
                    usedSpace += sizeBytes;
                    
                    String mountPointStr = "";
                    if (child.containsKey('mountpoints') && child['mountpoints'] != null) {
                       final mpList = child['mountpoints'] as List<dynamic>;
                       if (mpList.isNotEmpty && mpList.first != null) {
                          mountPointStr = mpList.join(', ');
                       }
                    } else if (child.containsKey('mountpoint') && child['mountpoint'] != null) {
                       mountPointStr = child['mountpoint'].toString();
                    }
                    
                    partitionList.add({
                      'name': '/dev/${child['name']}',
                      'type': child['fstype'] ?? 'unknown',
                      'sizeBytes': sizeBytes,
                      'mount': mountPointStr.isEmpty ? 'unmounted' : mountPointStr,
                      'flags': child['partflags'] ?? '',
                      'isPlanned': false,
                      'isFreeSpace': false,
                    });
                 }
             }
             
             // Geriye kalan disk alanı varsa (10 MB tolerans) sona Free Space ekle
             int freeBytes = diskSize - usedSpace;
             if (freeBytes > 10 * 1024 * 1024) {
                 partitionList.add({
                    'name': 'Free Space',
                    'type': 'unallocated',
                    'sizeBytes': freeBytes,
                    'mount': 'unmounted',
                    'flags': '',
                    'isPlanned': false,
                    'isFreeSpace': true,
                 });
             }

             // Eğer hiç children yoksa (Ham disk) hepsini boş alan yap
             if (partitionList.isEmpty && diskSize > 0) {
                 partitionList.add({
                    'name': 'Free Space',
                    'type': 'unallocated',
                    'sizeBytes': diskSize,
                    'mount': 'unmounted',
                    'flags': '',
                    'isPlanned': false,
                    'isFreeSpace': true,
                 });
             }
          }
        }
      }
    } catch (e) {
      // Hata durumu
    }

    return partitionList;
  }
}
