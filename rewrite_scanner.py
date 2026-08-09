import re

with open('lib/features/scanner/screens/scanner_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace imports
code = code.replace("import 'package:mobile_scanner/mobile_scanner.dart';", 
"""import 'package:camera/camera.dart';
import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';
import 'package:flutter/foundation.dart';
import '../services/realtime_ocr_service.dart';
import '../models/annotated_block.dart';
import '../widgets/ar_overlay_painter.dart';""")

# Add state variables
state_vars = """
  CameraController? _ctrl;
  final _realtimeOcrService = RealtimeOcrService();
  final _barcodeScanner = BarcodeScanner();
  bool _arOverlayEnabled = false;
  List<AnnotatedBlock> _arBlocks = [];
  bool _isProcessingBarcode = false;
  Size _imageSize = Size.zero;
"""
code = re.sub(r'  MobileScannerController\?\s*_ctrl;', state_vars, code)

# Update initState and dispose
init_state_replacement = """  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _realtimeOcrService.initialize();
    _realtimeOcrService.arStream.listen((blocks) {
      if (mounted && _arOverlayEnabled) {
        setState(() => _arBlocks = blocks);
      }
    });
    _checkPermission();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _ctrl?.dispose();
    _realtimeOcrService.dispose();
    _barcodeScanner.close();
    super.dispose();
  }"""
code = re.sub(r'  @override\s+void initState\(\) \{.*?\n  \}', init_state_replacement, code, flags=re.DOTALL)

# Remove the old dispose
code = re.sub(r'\n  @override\s+void dispose\(\) \{.*?super\.dispose\(\);\n  \}', '', code, flags=re.DOTALL)

# Update AppLifecycleState handling
code = code.replace('_ctrl?.start();', """
      if (_ctrl != null && !_ctrl!.value.isStreamingImages) {
        _startCameraStream();
      }""")

# Replace _initScanner
init_scanner_replacement = """  Future<void> _initScanner() async {
    if (kIsWeb) return; // Web fallback handled in build
    try {
      final cameras = await availableCameras();
      final backCamera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      
      final controller = CameraController(
        backCamera, 
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
      );
      
      await controller.initialize();
      if (!mounted) return;
      
      setState(() => _ctrl = controller);
      _startCameraStream();
    } catch (e) {
      debugPrint('Camera init error: $e');
    }
  }

  void _startCameraStream() {
    _ctrl?.startImageStream((image) {
      final inputImage = _inputImageFromCameraImage(image);
      if (inputImage == null) return;
      
      _imageSize = Size(image.width.toDouble(), image.height.toDouble());

      if (!_isProcessingBarcode) {
        _processBarcodeLive(inputImage);
      }
      
      if (_arOverlayEnabled) {
        _realtimeOcrService.processImage(inputImage);
      } else if (_arBlocks.isNotEmpty) {
        setState(() => _arBlocks = []);
      }
    });
  }

  InputImage? _inputImageFromCameraImage(CameraImage image) {
    if (_ctrl == null) return null;
    final camera = _ctrl!.description;
    final sensorOrientation = camera.sensorOrientation;
    
    InputImageRotation? rotation = InputImageRotationValue.fromRawValue(sensorOrientation);
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null || (Platform.isAndroid && format != InputImageFormat.nv21) || (Platform.isIOS && format != InputImageFormat.bgra8888)) {
      return null;
    }

    if (image.planes.isEmpty) return null;
    
    final bytes = Platform.isAndroid 
        ? image.planes.first.bytes 
        : Uint8List.fromList(image.planes.expand((plane) => plane.bytes).toList());

    return InputImage.fromBytes(
      bytes: bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: image.planes.first.bytesPerRow,
      ),
    );
  }

  Future<void> _processBarcodeLive(InputImage image) async {
    _isProcessingBarcode = true;
    try {
      final barcodes = await _barcodeScanner.processImage(image);
      if (barcodes.isNotEmpty) {
        final barcode = barcodes.first.rawValue;
        if (barcode != null && barcode.isNotEmpty) {
          final now = DateTime.now();
          if (_lastDetect == null || now.difference(_lastDetect!) > const Duration(seconds: 3)) {
             _lastDetect = now;
             await ref.read(scanProvider.notifier).onBarcodeDetected(barcode);
          }
        }
      }
    } finally {
      _isProcessingBarcode = false;
    }
  }"""
code = re.sub(r'  void _initScanner\(\) \{.*?\n  \}', init_scanner_replacement, code, flags=re.DOTALL)

# Remove the old _onDetect
code = re.sub(r'\n  void _onDetect\(BarcodeCapture capture\) async \{.*?\n  \}', '', code, flags=re.DOTALL)

# Update torch toggle
code = code.replace('_ctrl?.toggleTorch();', "_ctrl?.setFlashMode(_torchOn ? FlashMode.torch : FlashMode.off);")

# Remove analyzeImage logic from _processImageFile since we don't have mobile_scanner anymore
process_image_replacement = """  Future<void> _processImageFile(File file) async {
    // With image picker, we just directly do OCR
    if (!mounted) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    _showProcessingSnackbar('Reading ingredient label via OCR…');

    final result = await extractFromLabelImage(file);

    if (!mounted) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();

    if (result != null) {
      ref.read(scanProvider.notifier).onOcrResult(result);
    } else {
      _showErrorSnackbar(
          'Could not read this image. Try "Type" to paste the ingredient list.');
    }
  }"""
code = re.sub(r'  Future<void> _processImageFile\(File file\) async \{.*?\n  \}', process_image_replacement, code, flags=re.DOTALL)

# Replace MobileScanner widget with CameraPreview and AR overlay
camera_layer_replacement = """  Widget _buildCameraLayer() {
    if (kIsWeb) {
      return const Center(
        child: Text('AR available on Android/iOS\\nCamera feed disabled on Web', 
          textAlign: TextAlign.center, 
          style: TextStyle(color: Colors.white, fontSize: 16)),
      );
    }
    if (_checkingPermission) {
      return const Center(
          child: CircularProgressIndicator(color: Colors.white));
    }
    if (!_permissionGranted) {
      return _NoCameraPermissionView(onRetry: _checkPermission);
    }
    if (_ctrl == null || !_ctrl!.value.isInitialized) {
      return Container(color: const Color(0xFF1A2820));
    }
    
    // Calculate rotation enum for AR Painter
    final sensorOrientation = _ctrl!.description.sensorOrientation;
    InputImageRotation rotation = InputImageRotationValue.fromRawValue(sensorOrientation) ?? InputImageRotation.rotation90deg;

    return Stack(
      fit: StackFit.expand,
      children: [
        CameraPreview(_ctrl!),
        if (_arOverlayEnabled && _arBlocks.isNotEmpty)
          CustomPaint(
            painter: AROverlayPainter(_arBlocks, _imageSize, rotation),
          ),
      ],
    );
  }"""
code = re.sub(r'  Widget _buildCameraLayer\(\) \{.*?\n  \}', camera_layer_replacement, code, flags=re.DOTALL)

# Add AR toggle button and "Live analysis" pill
top_bar_replacement = """  Widget _buildTopBar(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _CircleButton(
                  icon: Icons.arrow_back_ios_new_rounded,
                  onTap: () =>
                      context.canPop() ? context.pop() : context.go('/'),
                ),
                const Text(
                  'NutriScan',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                    shadows: [Shadow(blurRadius: 8, color: Colors.black54)],
                  ),
                ),
                Row(
                  children: [
                    _CircleButton(
                      icon: _arOverlayEnabled ? Icons.visibility_rounded : Icons.visibility_off_rounded,
                      onTap: () => setState(() => _arOverlayEnabled = !_arOverlayEnabled),
                    ),
                    const SizedBox(width: 8),
                    _CircleButton(
                      icon: _torchOn
                          ? Icons.flash_on_rounded
                          : Icons.flash_off_rounded,
                      onTap: () {
                        setState(() => _torchOn = !_torchOn);
                        _ctrl?.setFlashMode(_torchOn ? FlashMode.torch : FlashMode.off);
                      },
                    ),
                  ],
                ),
              ],
            ),
            if (_arOverlayEnabled)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.darkGreen.withOpacity(0.8),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.auto_awesome, color: Colors.amber, size: 16),
                      SizedBox(width: 6),
                      Text('Live AR Analysis', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }"""
code = re.sub(r'  Widget _buildTopBar\(BuildContext context\) \{.*?\n  \}', top_bar_replacement, code, flags=re.DOTALL)

with open('lib/features/scanner/screens/scanner_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated ScannerScreen.dart")
