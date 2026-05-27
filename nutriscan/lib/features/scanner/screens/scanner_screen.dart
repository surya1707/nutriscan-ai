import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_barcode_scanning/google_mlkit_barcode_scanning.dart';
import 'package:flutter/foundation.dart';
import '../services/realtime_ocr_service.dart';
import '../models/annotated_block.dart';
import '../widgets/ar_overlay_painter.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/providers/scan_provider.dart';
import '../../../core/services/ocr_service.dart';
import '../models/scan_result_model.dart';
import '../widgets/scan_viewfinder.dart';

class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key});

  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen>
    with WidgetsBindingObserver {

  CameraController? _ctrl;
  final _realtimeOcrService = RealtimeOcrService();
  final _barcodeScanner = BarcodeScanner();
  bool _arOverlayEnabled = false;
  List<AnnotatedBlock> _arBlocks = [];
  bool _isProcessingBarcode = false;
  Size _imageSize = Size.zero;

  bool _permissionGranted = false;
  bool _checkingPermission = true;
  bool _torchOn = false;

  // Debounce: ignore repeated detections within 3 s
  DateTime? _lastDetect;
  // True while gallery/capture processing is running
  bool _galleryBusy = false;
  // One-shot hook for gallery barcode capture
  void Function(String)? _onNextBarcode;

  @override
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
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Resume scanner when returning from Settings
    if (state == AppLifecycleState.resumed && _permissionGranted) {
      
      if (_ctrl != null && !_ctrl!.value.isStreamingImages) {
        _startCameraStream();
      }
    }
  }

  // ── Permission ────────────────────────────────────────────────────────────────

  Future<void> _checkPermission() async {
    final status = await Permission.camera.request();
    final granted = status == PermissionStatus.granted;
    if (!mounted) return;
    setState(() {
      _permissionGranted = granted;
      _checkingPermission = false;
    });
    if (granted) _initScanner();
  }

  Future<void> _initScanner() async {
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
  }

  // ── Live barcode detection ────────────────────────────────────────────────────


  // ── Shutter / Capture button ─────────────────────────────────────────────────
  // Uses ImagePicker(camera) → try barcode → fall back to OCR.
  // This is the most reliable path on devices where continuous scan struggles.

  Future<void> _capturePhoto() async {
    if (_galleryBusy) return;
    setState(() => _galleryBusy = true);

    try {
      final picker = ImagePicker();
      final picked = await picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 90,
        preferredCameraDevice: CameraDevice.rear,
      );
      if (picked == null || !mounted) return;

      _showProcessingSnackbar('Analysing photo…');
      await _processImageFile(File(picked.path));
    } finally {
      if (mounted) setState(() => _galleryBusy = false);
    }
  }

  // ── Gallery button ────────────────────────────────────────────────────────────

  Future<void> _pickFromGallery() async {
    if (_galleryBusy) return;
    setState(() => _galleryBusy = true);

    try {
      final picker = ImagePicker();
      final picked =
          await picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
      if (picked == null || !mounted) return;

      _showProcessingSnackbar('Analysing image…');
      await _processImageFile(File(picked.path));
    } finally {
      if (mounted) setState(() => _galleryBusy = false);
    }
  }

  // ── Shared image processing: barcode first → OCR fallback ────────────────────

  Future<void> _processImageFile(File file) async {
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
  }

  // ── Manual type input ────────────────────────────────────────────────────────

  void _showTypeDialog() {
    final controller = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _TypeIngredientSheet(
        controller: controller,
        onSubmit: (text) {
          Navigator.pop(context);
          final result = buildResultFromText(text);
          ref.read(scanProvider.notifier).onOcrResult(result);
        },
      ),
    );
  }

  // ── Snackbars ─────────────────────────────────────────────────────────────────

  void _showProcessingSnackbar(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Row(children: [
        const SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
        ),
        const SizedBox(width: 12),
        Flexible(child: Text(msg)),
      ]),
      duration: const Duration(seconds: 15),
      behavior: SnackBarBehavior.floating,
    ));
  }

  void _showErrorSnackbar(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: AppColors.flaggedRed,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ));
  }

  // ── Build ─────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    ref.listen<ScanState>(scanProvider, (_, next) {
      if (next.status == ScanStatus.found && next.result != null) {
        _lastDetect = null;
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ref.read(scanProvider.notifier).reset();
        if (mounted) context.push('/results', extra: next.result);
      } else if (next.status == ScanStatus.notFound) {
        _lastDetect = null;
        _showErrorSnackbar(
            'Product not in database. Try the "Capture" button or paste ingredients.');
      } else if (next.status == ScanStatus.error) {
        _lastDetect = null;
        _showErrorSnackbar(next.errorMessage ?? 'Scan failed. Please try again.');
      }
    });

    final isLoading = ref.watch(scanProvider).status == ScanStatus.loading;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          _buildCameraLayer(),
          _buildOverlay(context),
          _buildTopBar(context),
          if (isLoading) _buildLoadingOverlay(),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: _buildBottomSheet(context, isLoading),
          ),
        ],
      ),
    );
  }

  // ── Layer builders ─────────────────────────────────────────────────────────

  Widget _buildCameraLayer() {
    if (kIsWeb) {
      return Container(
        color: AppColors.background,
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.web, size: 64, color: AppColors.primary),
                const SizedBox(height: 16),
                const Text(
                  'Web Scanner Mode',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Camera AR is only available on Mobile.',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 32),
                ElevatedButton.icon(
                  onPressed: () {
                    // TODO: Implement image upload and pass to backend OCR
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Image OCR coming soon! Use manual text for now.')),
                    );
                  },
                  icon: const Icon(Icons.upload_file),
                  label: const Text('Upload Label Image'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () {
                    _showManualTextDialog();
                  },
                  icon: const Icon(Icons.edit_note),
                  label: const Text('Enter Ingredients Manually'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.primary,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    side: const BorderSide(color: AppColors.primary),
                  ),
                ),
              ],
            ),
          ),
        ),
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
  }

  Widget _buildOverlay(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final boxSize = size.width * 0.72;
    return CustomPaint(
        painter: _ScanOverlayPainter(boxSize: boxSize, screenSize: size));
  }

  Widget _buildTopBar(BuildContext context) {
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
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: Colors.black54,
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 16),
            Text('Looking up product…',
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500)),
            SizedBox(height: 6),
            Text('Checking Open Food Facts',
                style: TextStyle(color: Colors.white60, fontSize: 13)),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomSheet(BuildContext context, bool isLoading) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 24,
        right: 24,
        bottom: MediaQuery.of(context).padding.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Auto-scans barcodes · or tap capture to scan manually',
            textAlign: TextAlign.center,
            style: TextStyle(
                color: AppColors.textSecondary, fontSize: 12, height: 1.4),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Type button
              _BottomActionButton(
                icon: Icons.edit_outlined,
                label: 'Type',
                onTap: isLoading ? null : _showTypeDialog,
              ),

              // ── Centre shutter button (primary CTA) ──────────────────────
              GestureDetector(
                onTap: isLoading ? null : _capturePhoto,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 76,
                  height: 76,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isLoading
                        ? AppColors.mediumGreen.withOpacity(0.4)
                        : AppColors.darkGreen,
                    boxShadow: isLoading
                        ? null
                        : [
                            BoxShadow(
                              color: AppColors.darkGreen.withOpacity(0.4),
                              blurRadius: 20,
                              spreadRadius: 2,
                            ),
                          ],
                  ),
                  child: isLoading
                      ? const Center(
                          child: SizedBox(
                              width: 28,
                              height: 28,
                              child: CircularProgressIndicator(
                                  color: Colors.white, strokeWidth: 2.5)))
                      : const Icon(Icons.camera_alt_rounded,
                          color: Colors.white, size: 34),
                ),
              ),

              // Gallery button
              _BottomActionButton(
                icon: Icons.image_outlined,
                label: 'Gallery',
                onTap: isLoading ? null : _pickFromGallery,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '📷 Tap camera button to capture & scan',
            style: TextStyle(
                color: AppColors.textMuted, fontSize: 11, height: 1.4),
          ),
        ],
      ),
    );
  }
}

// ── Type input bottom sheet ───────────────────────────────────────────────────

class _TypeIngredientSheet extends StatelessWidget {
  final TextEditingController controller;
  final ValueChanged<String> onSubmit;

  const _TypeIngredientSheet(
      {required this.controller, required this.onSubmit});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        top: 24,
        left: 24,
        right: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Paste ingredient list',
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 6),
          const Text(
              'Copy the ingredient text from the back of the package',
              style:
                  TextStyle(color: AppColors.textSecondary, fontSize: 13)),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            maxLines: 6,
            autofocus: true,
            decoration: InputDecoration(
              hintText: 'e.g. Sugar, Fruit Pulp, Citric Acid, Pectin…',
              hintStyle:
                  const TextStyle(color: AppColors.textMuted, fontSize: 13),
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.divider)),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                final text = controller.text.trim();
                if (text.isNotEmpty) onSubmit(text);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.darkGreen,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
              ),
              child: const Text('Analyse Ingredients',
                  style: TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Build result from typed text ──────────────────────────────────────────────

ScanResult buildResultFromText(String text) {
  const flagged = <String, String>{
    'high-fructose corn syrup': 'Linked to metabolic disorders',
    'hfcs': 'High-fructose corn syrup',
    'partially hydrogenated': 'Trans fat source',
    'sodium benzoate': 'Artificial preservative',
    'aspartame': 'Artificial sweetener',
    'monosodium glutamate': 'Flavor enhancer',
    'msg': 'Monosodium glutamate',
    'artificial flavor': 'Synthetic flavoring',
    'artificial flavour': 'Synthetic flavoring',
    'artificial color': 'Synthetic coloring',
    'carrageenan': 'May cause gut inflammation',
    'bha': 'Potential endocrine disruptor',
    'bht': 'Potential endocrine disruptor',
    'sodium nitrate': 'Carcinogenic risk',
    'sodium nitrite': 'Carcinogenic risk',
    'red 40': 'Synthetic dye',
    'yellow 5': 'Synthetic dye',
    'yellow 6': 'Synthetic dye',
    'sugar': 'Primary ingredient — high sugar content',
    'corn syrup': 'High-sugar sweetener',
    'glucose syrup': 'High-glycemic sweetener',
    'dextrose': 'Added sugar',
    'maltose': 'Added sugar',
    'fructose': 'Added sugar',
  };

  final parts = text
      .split(RegExp(r'[,;]'))
      .map((s) => s.trim())
      .where((s) => s.length > 1)
      .toList();

  final ingredients = parts.map((ingredient) {
    final lower = ingredient.toLowerCase();
    String? reason;
    for (final e in flagged.entries) {
      if (lower.contains(e.key)) {
        reason = e.value;
        break;
      }
    }
    return IngredientItem(
        name: ingredient, isFlagged: reason != null, flagReason: reason);
  }).toList();

  final lower = text.toLowerCase();
  const markers = [
    'syrup', 'flavor', 'colour', 'modified starch',
    'preservative', 'emulsifier', 'sugar', 'glucose',
  ];
  final hits = markers.where((m) => lower.contains(m)).length;
  final nova = hits >= 3
      ? NovaGroup.group4
      : hits >= 1
          ? NovaGroup.group3
          : NovaGroup.group2;

  final flaggedCount = ingredients.where((i) => i.isFlagged).length;
  double score = 85;
  if (nova == NovaGroup.group4) score -= 30;
  else if (nova == NovaGroup.group3) score -= 15;
  score -= (flaggedCount * 8).clamp(0, 25).toDouble();

  // Extra penalty if sugar is the first/primary ingredient
  final firstIngredient = parts.isNotEmpty ? parts.first.toLowerCase() : '';
  if (firstIngredient.contains('sugar') ||
      firstIngredient.contains('glucose') ||
      firstIngredient.contains('syrup')) {
    score -= 15;
  }

  return ScanResult(
    productName: 'Typed Ingredients',
    brand: 'Manual Entry',
    healthScore: score.round().clamp(0, 100),
    novaGroup: nova,
    nutrients: const [
      NutrientInfo(name: 'Calories', value: '—', unit: 'kcal', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Sugar', value: '—', unit: 'g', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Fat', value: '—', unit: 'g', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Sodium', value: '—', unit: 'mg', level: NutritionLevel.unknown),
    ],
    ingredients: ingredients,
    alternatives: const [],
  );
}

// ── Small reusable widgets ────────────────────────────────────────────────────

class _CircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _CircleButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
            color: Colors.black38, borderRadius: BorderRadius.circular(20)),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
    );
  }
}

class _BottomActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const _BottomActionButton(
      {required this.icon, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    final disabled = onTap == null;
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: disabled ? 0.4 : 1.0,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 11),
          decoration: BoxDecoration(
            color: AppColors.lightGreen.withOpacity(0.5),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: AppColors.divider, width: 0.5),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: AppColors.darkGreen),
              const SizedBox(width: 6),
              Text(label,
                  style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: AppColors.darkGreen)),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Overlay painter ───────────────────────────────────────────────────────────

class _ScanOverlayPainter extends CustomPainter {
  final double boxSize;
  final Size screenSize;
  const _ScanOverlayPainter({required this.boxSize, required this.screenSize});

  @override
  void paint(Canvas canvas, Size size) {
    const cornerLen = 28.0;
    const cornerR = 6.0;
    const stroke = 3.5;

    final cx = size.width / 2;
    final cy = size.height * 0.42;
    final half = boxSize / 2;
    final l = cx - half, t = cy - half, r = cx + half, b = cy + half;

    final dark = Paint()..color = Colors.black.withOpacity(0.62);
    canvas.drawRect(Rect.fromLTRB(0, 0, size.width, t), dark);
    canvas.drawRect(Rect.fromLTRB(0, b, size.width, size.height), dark);
    canvas.drawRect(Rect.fromLTRB(0, t, l, b), dark);
    canvas.drawRect(Rect.fromLTRB(r, t, size.width, b), dark);

    final paint = Paint()
      ..color = Colors.white
      ..strokeWidth = stroke
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    void corner(double x, double y, double dx, double dy) {
      canvas.drawPath(
        Path()
          ..moveTo(x + dx * cornerLen, y)
          ..lineTo(x, y)
          ..lineTo(x, y + dy * cornerLen),
        paint,
      );
    }

    corner(l + cornerR, t + cornerR, 1, 1);
    corner(r - cornerR, t + cornerR, -1, 1);
    corner(l + cornerR, b - cornerR, 1, -1);
    corner(r - cornerR, b - cornerR, -1, -1);
  }

  @override
  bool shouldRepaint(_ScanOverlayPainter o) =>
      o.boxSize != boxSize || o.screenSize != screenSize;
}

// ── No permission view ────────────────────────────────────────────────────────

class _NoCameraPermissionView extends StatelessWidget {
  final VoidCallback onRetry;
  const _NoCameraPermissionView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.camera_alt_outlined,
                color: Colors.white54, size: 56),
            const SizedBox(height: 20),
            const Text('Camera access required',
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            const Text(
                'NutriScan needs camera access to scan barcodes and ingredient labels.',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: Colors.white60, fontSize: 14, height: 1.5)),
            const SizedBox(height: 28),
            ElevatedButton.icon(
              onPressed: openAppSettings,
              icon: const Icon(Icons.settings_outlined),
              label: const Text('Open Settings'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.mediumGreen,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
              ),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: onRetry,
              child: const Text('Try again',
                  style: TextStyle(color: Colors.white70)),
            ),
          ],
        ),
      ),
    );
  }
}
