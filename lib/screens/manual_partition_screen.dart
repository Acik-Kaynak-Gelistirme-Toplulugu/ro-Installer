import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../state/installer_state.dart';
import '../services/partition_service.dart';

class ManualPartitionScreen extends StatefulWidget {
  const ManualPartitionScreen({super.key});

  @override
  State<ManualPartitionScreen> createState() => _ManualPartitionScreenState();
}

class _ManualPartitionScreenState extends State<ManualPartitionScreen> {
  int? _selectedIndex;
  bool _isLoading = true;
  String? _loadedDisk;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final state = Provider.of<InstallerState>(context);
    if (_loadedDisk != state.selectedDisk) {
       _loadedDisk = state.selectedDisk;
       _loadPartitions();
    }
  }

  void _loadPartitions() {
    WidgetsBinding.instance.addPostFrameCallback((_) async {
       if (!mounted) return;
       final state = Provider.of<InstallerState>(context, listen: false);
       setState(() => _isLoading = true);
       
       if (state.manualPartitions.isEmpty && state.selectedDisk.isNotEmpty) {
          final realParts = await PartitionService.instance.getPartitions(state.selectedDisk);
          if (mounted) {
             state.manualPartitions = realParts;
          }
       }
       if (mounted) setState(() => _isLoading = false);
    });
  }

  String _formatBytes(int bytes) {
    if (bytes >= 1024 * 1024 * 1024) {
      return "${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB";
    } else {
      return "${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB";
    }
  }

  void _openAddDialog(BuildContext context, InstallerState state) {
    if (_selectedIndex == null || _selectedIndex! >= state.manualPartitions.length) return;
    
    final part = state.manualPartitions[_selectedIndex!];
    if (part['isFreeSpace'] != true) return;

    final maxMb = (part['sizeBytes'] as int) ~/ (1024 * 1024);
    int inputMb = maxMb;
    
    String tempFormat = 'btrfs';
    String tempMount = '/';

    final textController = TextEditingController(text: inputMb.toString());

    showDialog(
       context: context,
       builder: (c) {
          return StatefulBuilder(builder: (c, setDialogState) {
             return AlertDialog(
                title: const Text("Yeni Bölüm Oluştur"),
                content: Column(
                   mainAxisSize: MainAxisSize.min,
                   children: [
                      const Text("DİKKAT: İşlem planlanacaktır, hemen uygulanmaz.", style: TextStyle(color: Colors.orange, fontSize: 12)),
                      const SizedBox(height: 16),
                      TextField(
                         controller: textController,
                         keyboardType: TextInputType.number,
                         inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                         decoration: InputDecoration(
                            labelText: 'Boyut (MB) [Maksimum: $maxMb MB]',
                         ),
                         onChanged: (v) {
                            int? parsed = int.tryParse(v);
                            if (parsed != null && parsed > maxMb) {
                               textController.text = maxMb.toString();
                            }
                         },
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                         value: tempFormat,
                         decoration: const InputDecoration(labelText: 'Dosya Sistemi (File System)'),
                         items: ['btrfs', 'ext4', 'xfs', 'fat32', 'linux-swap'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                         onChanged: (v) {
                             setDialogState(() {
                                 tempFormat = v!;
                                 if (tempFormat == 'fat32') tempMount = '/boot/efi';
                             });
                         },
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                         value: tempMount,
                         decoration: const InputDecoration(labelText: 'Bağlama Noktası (Mount Point)'),
                         items: ['/', '/home', '/boot', '/boot/efi', '[SWAP]', 'unmounted'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                         onChanged: (v) => setDialogState(() => tempMount = v!),
                      ),
                   ],
                ),
                actions: [
                   TextButton(onPressed: () => Navigator.pop(c), child: const Text("İptal")),
                   ElevatedButton(
                      onPressed: () {
                         int chosenMb = int.tryParse(textController.text) ?? maxMb;
                         if (chosenMb <= 0) return;
                         if (chosenMb > maxMb) chosenMb = maxMb;
                         
                         int newBytes = chosenMb * 1024 * 1024;
                         int remainingBytes = (part['sizeBytes'] as int) - newBytes;

                         setState(() {
                            state.manualPartitions.insert(_selectedIndex!, {
                               'name': 'New Partition',
                               'type': tempFormat,
                               'sizeBytes': newBytes,
                               'mount': tempMount,
                               'flags': (tempMount == '/boot/efi' || tempFormat == 'fat32') ? 'boot, esp' : '',
                               'isFreeSpace': false,
                               'isPlanned': true
                            });

                            if (remainingBytes > 10 * 1024 * 1024) {
                               state.manualPartitions[_selectedIndex! + 1]['sizeBytes'] = remainingBytes;
                            } else {
                               state.manualPartitions.removeAt(_selectedIndex! + 1);
                            }
                            _selectedIndex = null;
                         });
                         Navigator.pop(c);
                      }, 
                      child: const Text("Oluştur")
                   )
                ]
             );
          });
       }
    );
  }

  void _actionDelete(InstallerState state) {
    if (_selectedIndex == null || _selectedIndex! >= state.manualPartitions.length) return;
    final part = state.manualPartitions[_selectedIndex!];
    if (part['isFreeSpace'] == true) return; // Zaten boşluk olanı silinmez

    setState(() {
       part['isFreeSpace'] = true;
       part['type'] = 'unallocated';
       part['name'] = 'Free Space';
       part['mount'] = 'unmounted';
       part['flags'] = '';
       part['isPlanned'] = true;

       // Merge Free Spaces (Yukarıdan Aşağıya)
       for (int i = 0; i < state.manualPartitions.length - 1; i++) {
          if (state.manualPartitions[i]['isFreeSpace'] == true && state.manualPartitions[i+1]['isFreeSpace'] == true) {
             state.manualPartitions[i]['sizeBytes'] = (state.manualPartitions[i]['sizeBytes'] as int) + (state.manualPartitions[i+1]['sizeBytes'] as int);
             state.manualPartitions.removeAt(i+1);
             i--; // Yinelenen döngü kontrolü
          }
       }
       _selectedIndex = null;
    });
  }

  void _openFormatDialog(BuildContext context, InstallerState state) {
    if (_selectedIndex == null || _selectedIndex! >= state.manualPartitions.length) return;
    
    final part = state.manualPartitions[_selectedIndex!];
    if (part['isFreeSpace'] == true) return; // Free space formatlanmaz, bölüm oluşturulur

    String tempFormat = ['btrfs', 'ext4', 'xfs', 'fat32', 'linux-swap', 'unallocated'].contains(part['type']) 
        ? part['type'] : 'btrfs';
    String tempMount = ['/', '/home', '/boot', '/boot/efi', '[SWAP]', 'unmounted'].contains(part['mount']) 
        ? part['mount'] : 'unmounted';
    
    showDialog(
       context: context,
       builder: (c) {
          return StatefulBuilder(builder: (c, setDialogState) {
             return AlertDialog(
                title: Text("Bölümü Formatla: ${part['name']}"),
                content: Column(
                   mainAxisSize: MainAxisSize.min,
                   children: [
                      const Text("DİKKAT: İşlem planlanacaktır, hemen uygulanmaz.", style: TextStyle(color: Colors.orange, fontSize: 12)),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                         value: tempFormat,
                         decoration: const InputDecoration(labelText: 'Dosya Sistemi (File System)'),
                         items: ['btrfs', 'ext4', 'xfs', 'fat32', 'linux-swap', 'unallocated'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                         onChanged: (v) => setDialogState(() => tempFormat = v!),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                         value: tempMount,
                         decoration: const InputDecoration(labelText: 'Bağlama Noktası (Mount Point)'),
                         items: ['/', '/home', '/boot', '/boot/efi', '[SWAP]', 'unmounted'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                         onChanged: (v) => setDialogState(() => tempMount = v!),
                      ),
                   ],
                ),
                actions: [
                   TextButton(onPressed: () => Navigator.pop(c), child: const Text("İptal")),
                   ElevatedButton(
                      onPressed: () {
                         setState(() {
                            part['type'] = tempFormat;
                            part['mount'] = tempMount;
                            if (tempMount == '/boot/efi' || tempFormat == 'fat32') part['flags'] = 'boot, esp';
                            part['isPlanned'] = true; // Sisteme format atılacağı bildiriliyor
                         });
                         Navigator.pop(c);
                      }, 
                      child: const Text("Format Planla")
                   )
                ]
             );
          });
       }
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = Provider.of<InstallerState>(context);
    final theme = Theme.of(context);
    final isDark = state.themeMode == 'dark';
    final textColor = isDark ? Colors.white : Colors.black87;

    bool isSelectedFreeSpace = false;
    bool hasSelection = _selectedIndex != null && _selectedIndex! < state.manualPartitions.length;
    if (hasSelection) {
       isSelectedFreeSpace = state.manualPartitions[_selectedIndex!]['isFreeSpace'] == true;
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 10, bottom: 20),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: theme.colorScheme.primary.withOpacity(0.5)),
                ),
                child: Text(
                  state.t('part_badge'),
                  style: TextStyle(
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                    letterSpacing: 1.2,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                state.t('part_title'),
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: textColor,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                state.selectedDisk.isEmpty 
                    ? state.t('part_desc') 
                    : "${state.t('part_desc')}\nSeçilen Hedef Disk: ${state.selectedDisk}",
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: textColor.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ),

        // Partition Table
        Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.cardColor.withOpacity(isDark ? 0.3 : 0.6),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: Column(
              children: [
                // Table Header
                Padding(
                  padding: const EdgeInsets.only(bottom: 12, left: 16, right: 16),
                  child: Row(
                    children: [
                      Expanded(flex: 2, child: Text("BÖLÜM (DEVICE)", style: _headerStyle(textColor))),
                      Expanded(flex: 2, child: Text("FORMAT (TYPE)", style: _headerStyle(textColor))),
                      Expanded(flex: 2, child: Text("BOYUT (SIZE)", style: _headerStyle(textColor))),
                      Expanded(flex: 3, child: Text("BAĞLANTI (MOUNT POINT)", style: _headerStyle(textColor))),
                      Expanded(flex: 2, child: Text("DURUM (FLAGS)", style: _headerStyle(textColor))),
                    ],
                  ),
                ),
                const Divider(color: Colors.white24, height: 1),
                const SizedBox(height: 12),
                
                // Table Body
                Expanded(
                  child: _isLoading 
                    ? const Center(child: CircularProgressIndicator()) 
                    : ListView.builder(
                    itemCount: state.manualPartitions.length,
                    itemBuilder: (context, index) {
                      final part = state.manualPartitions[index];
                      final isSelected = _selectedIndex == index;
                      final isPlanned = part['isPlanned'] == true;
                      final isFreeSpace = part['isFreeSpace'] == true;
                      
                      return GestureDetector(
                        onTap: () => setState(() => _selectedIndex = index),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
                          decoration: BoxDecoration(
                            color: isSelected 
                                ? theme.colorScheme.primary.withOpacity(0.3) 
                                : (isPlanned && !isFreeSpace ? theme.colorScheme.secondary.withOpacity(0.1) : Colors.transparent),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: isSelected ? theme.colorScheme.primary : (isFreeSpace ? Colors.grey.withOpacity(0.3) : Colors.transparent),
                            ),
                          ),
                          child: Row(
                            children: [
                              Expanded(flex: 2, child: Text(part["name"], style: TextStyle(color: isFreeSpace ? Colors.grey : textColor, fontStyle: isFreeSpace ? FontStyle.italic : FontStyle.normal, fontWeight: isFreeSpace ? FontWeight.normal : FontWeight.bold))),
                              Expanded(flex: 2, child: Text(part["type"], style: TextStyle(color: _getTypeColor(part["type"])))),
                              Expanded(flex: 2, child: Text(_formatBytes(part["sizeBytes"]), style: TextStyle(color: textColor.withOpacity(0.8)))),
                              Expanded(flex: 3, child: Text(part["mount"] ?? '-', style: TextStyle(color: textColor.withOpacity(isFreeSpace ? 0.3 : 0.8)))),
                              Expanded(flex: 2, child: Text(
                                isPlanned && !isFreeSpace ? "Planlandı ⚠️" : (part["flags"] ?? ''), 
                                style: TextStyle(color: isPlanned ? Colors.orange : Colors.grey, fontSize: 12, fontWeight: isPlanned ? FontWeight.bold : FontWeight.normal)
                              )),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                
                // Partition Actions
                const SizedBox(height: 20),
                const Divider(color: Colors.white24, height: 1),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _actionBtn(context, state.t('part_add'), Icons.add, isSelectedFreeSpace ? () => _openAddDialog(context, state) : null),
                    _actionBtn(context, state.t('part_delete'), Icons.remove, (!isSelectedFreeSpace && hasSelection) ? () => _actionDelete(state) : null),
                    _actionBtn(context, state.t('part_format'), Icons.build, (!isSelectedFreeSpace && hasSelection) ? () => _openFormatDialog(context, state) : null),
                  ],
                ),
              ],
            ),
          ),
        ),

        // Navigation
        Padding(
          padding: const EdgeInsets.only(top: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              TextButton.icon(
                onPressed: () => state.previousStep(),
                icon: const Icon(Icons.arrow_back),
                label: Text(state.t('prev')),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  foregroundColor: textColor.withOpacity(0.7),
                ),
              ),
              ElevatedButton.icon(
                onPressed: () {
                   bool hasRoot = false;
                   bool hasEfi = false;
                   for (var p in state.manualPartitions) {
                      if (p['isFreeSpace'] == true) continue;
                      if (p['mount'] == '/') hasRoot = true;
                      if (p['mount'] == '/boot/efi') hasEfi = true;
                   }
                   if (!hasRoot || !hasEfi) {
                      ScaffoldMessenger.of(context).showSnackBar(
                         const SnackBar(
                           content: Text("Kuruluma devam etmek için tabloya en az bir Kök (/) ve EFI (/boot/efi) bölümü planlamanız gerekir!"), 
                           backgroundColor: Colors.red
                         )
                      );
                      return;
                   }
                   state.nextStep();
                },
                icon: const Icon(Icons.arrow_forward),
                label: Text(state.t('next')),
                style: theme.elevatedButtonTheme.style?.copyWith(
                  padding: const WidgetStatePropertyAll(
                    EdgeInsets.symmetric(horizontal: 32, vertical: 20),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  TextStyle _headerStyle(Color textColor) => TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
        color: textColor.withOpacity(0.5),
      );

  Color _getTypeColor(String type) {
    switch (type) {
      case 'ext4': return Colors.orange;
      case 'btrfs': return Colors.blue;
      case 'fat32': return Colors.green;
      case 'linux-swap': return Colors.redAccent;
      case 'unallocated': return Colors.grey;
      default: return Colors.grey;
    }
  }

  Widget _actionBtn(BuildContext context, String label, IconData icon, VoidCallback? onPressed) {
    final theme = Theme.of(context);
    final isDisabled = onPressed == null;
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: isDisabled ? Colors.grey : theme.colorScheme.primary,
        side: BorderSide(color: isDisabled ? Colors.grey.withOpacity(0.3) : theme.colorScheme.primary.withOpacity(0.5)),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      ),
    );
  }
}
