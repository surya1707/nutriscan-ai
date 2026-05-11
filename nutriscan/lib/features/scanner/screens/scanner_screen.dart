import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../widgets/scan_viewfinder.dart';
import '../widgets/scan_bottom_sheet.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  // Camera controller would go here in real implementation
  // For now we render the UI shell with camera unavailable state
  bool _cameraAvailable = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview area
          _cameraAvailable
              ? const Expanded(child: Placeholder()) // Replace with CameraPreview(controller)
              : Container(
                  width: double.infinity,
                  height: double.infinity,
                  color: const Color(0xFF4A5E58), // muted dark teal matching screenshot
                ),

          // Full screen layout
          Column(
            children: [
              // App bar
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      GestureDetector(
                        onTap: () => context.pop(),
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.black38,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(Icons.close, color: Colors.white, size: 20),
                        ),
                      ),
                      const Text(
                        'Scan label',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      GestureDetector(
                        onTap: () {/* gallery */},
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.black38,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(Icons.image_outlined, color: Colors.white, size: 20),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Viewfinder in center
              Expanded(
                child: Center(
                  child: ScanViewfinder(size: MediaQuery.of(context).size.width * 0.7),
                ),
              ),

              // Bottom sheet
              ScanBottomSheet(cameraAvailable: _cameraAvailable),
            ],
          ),
        ],
      ),
    );
  }
}
