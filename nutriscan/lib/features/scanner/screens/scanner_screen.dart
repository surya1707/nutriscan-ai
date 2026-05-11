import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
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

class _ScannerScreenState extends ConsumerState<ScannerScreen> {
  MobileScannerController? _scanController;
  bool _permissionGranted = false;
  bool _checkingPermission = true;
  bool _torchOn = false;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  Future<void> _checkPermission() async {
    final status = await Permission.camera.request();
    final granted = status == PermissionStatus.granted;
    if (mounted) {
      setState(() {
        _permissionGranted = granted;
        _checkingPermission = false;
      });
      if (granted) _initScanner();
    }
  }

  void _initScanner() {
    setState(() {
      _scanController = MobileScannerController(
        detectionSpeed: DetectionSpeed.normal,
        facing: CameraFacing.back,
        formats: const [
          BarcodeFormat.ean13,
          BarcodeFormat.ean8,
          BarcodeFormat.upcA,
          BarcodeFormat.upcE,
          BarcodeFormat.code128,
          BarcodeFormat.code39,
          BarcodeFormat.qrCode,
        ],
        returnImage: false,
      );
    });
  }

  @override
  void dispose() {
    _scanController?.dispose();
    super.dispose();
  }

  // ── Barcode detected ─────────────────────────────────────────────────────────

  void _onDetect(BarcodeCapture capture) async {
    if (_isProcessing) return;
    final barcode = capture.barcodes.firstOrNull?.rawValue;
    if (barcode == null || barcode.isEmpty) return;
    _isProcessing = true;
    await ref.read(scanProvider.notifier).onBarcodeDetected(barcode);
  }

  // ── Gallery / OCR path ───────────────────────────────────────────────────────

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null || !mounted) return;

    await _scanController?.stop();
    _showProcessingSnackbar('Running OCR on label…');

    final result = await extractFromLabelImage(File(picked.path));
    if (!mounted) return;

    if (result != null) {
      ref.read(scanProvider.notifier).onOcrResult(result);
    } else {
      _showErrorSnackbar('Could not extract ingredients from image.');
      await _scanController?.start();
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

  void _showProcessingSnackbar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(children: [
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.white,
            ),
          ),
          const SizedBox(width: 12),
          Text(msg),
        ]),
        duration: const Duration(seconds: 10),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showErrorSnackbar(String msg) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: AppColors.flaggedRed,
        behavior: SnackBarBehavior.floating,
      ));
  }

  // ── Build ─────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    // Listen for scan state changes
    ref.listen<ScanState>(scanProvider, (_, next) async {
      if (next.status == ScanStatus.found && next.result != null) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ref.read(scanProvider.notifier).reset();
        if (mounted) context.push('/results', extra: next.result);
      } else if (next.status == ScanStatus.notFound) {
        _showErrorSnackbar('Product not found in database. Try "Type" or gallery.');
        await _scanController?.start();
      } else if (next.status == ScanStatus.error) {
        _showErrorSnackbar(next.errorMessage ?? 'Scan failed.');
        await _scanController?.start();
      }
    });

    final scanState = ref.watch(scanProvider);

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Camera feed or placeholder ──────────────────────────────
          _buildCameraLayer(),

          // ── Dark overlay with viewfinder cutout ─────────────────────
          _buildOverlay(context),

          // ── Top bar ─────────────────────────────────────────────────
          _buildTopBar(context),

          // ── Loading overlay ──────────────────────────────────────────
          if (scanState.status == ScanStatus.loading)
            _buildLoadingOverlay(),

          // ── Bottom action sheet ──────────────────────────────────────
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: _buildBottomSheet(context),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraLayer() {
    if (_checkingPermission) {
      return const Center(child: CircularProgressIndicator(color: Colors.white));
    }
    if (!_permissionGranted) {
      return _NoCameraPermissionView(onRetry: _checkPermission);
    }
    if (_scanController == null) {
      return Container(color: const Color(0xFF1A2820));
    }
    return MobileScanner(
      controller: _scanController!,
      onDetect: _onDetect,
    );
  }

  Widget _buildOverlay(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final boxSize = size.width * 0.72;
    return CustomPaint(
      painter: _ScanOverlayPainter(
        boxSize: boxSize,
        screenSize: size,
      ),
    );
  }

  Widget _buildTopBar(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _CircleButton(
              icon: Icons.arrow_back_ios_new_rounded,
              onTap: () => context.canPop() ? context.pop() : context.go('/'),
            ),
            const Text(
              'Scan Barcode or Label',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
                shadows: [Shadow(blurRadius: 8, color: Colors.black54)],
              ),
            ),
            _CircleButton(
              icon: _torchOn ? Icons.flash_on_rounded : Icons.flash_off_rounded,
              onTap: () {
                setState(() => _torchOn = !_torchOn);
                _scanController?.toggleTorch();
              },
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
            Text(
              'Looking up product…',
              style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomSheet(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
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
            'Point camera at a barcode or ingredient label',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary, fontSize: 13, height: 1.4),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _BottomActionButton(
                icon: Icons.edit_outlined,
                label: 'Type',
                onTap: _showTypeDialog,
              ),
              // Centre big scan-ring button (decorative — scanner is always active)
              GestureDetector(
                onTap: () {},
                child: Container(
                  width: 68,
                  height: 68,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.mediumGreen, width: 2.5),
                  ),
                  child: Center(
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.lightGreen.withOpacity(0.45),
                      ),
                      child: ScanViewfinder(size: 32),
                    ),
                  ),
                ),
              ),
              _BottomActionButton(
                icon: Icons.image_outlined,
                label: 'Gallery',
                onTap: _pickFromGallery,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Type input sheet ──────────────────────────────────────────────────────────

class _TypeIngredientSheet extends StatelessWidget {
  final TextEditingController controller;
  final ValueChanged<String> onSubmit;

  const _TypeIngredientSheet({required this.controller, required this.onSubmit});

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
          const Text(
            'Paste ingredient list',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Copy the ingredient text from the back of the package',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            maxLines: 6,
            autofocus: true,
            decoration: InputDecoration(
              hintText: 'e.g. Water, Sugar, Modified Starch, Citric Acid…',
              hintStyle: TextStyle(color: AppColors.textMuted, fontSize: 13),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: AppColors.divider),
              ),
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
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: const Text(
                'Analyse Ingredients',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Helper to build result from typed text ────────────────────────────────────

ScanResult buildResultFromText(String text) {
  // Reuse the OCR-based extraction logic
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
  };

  final parts = text.split(RegExp(r'[,;]')).map((s) => s.trim()).where((s) => s.length > 1).toList();
  final ingredients = parts.map((ingredient) {
    final lower = ingredient.toLowerCase();
    String? reason;
    for (final e in flagged.entries) {
      if (lower.contains(e.key)) { reason = e.value; break; }
    }
    return IngredientItem(name: ingredient, isFlagged: reason != null, flagReason: reason);
  }).toList();

  // NOVA estimate
  final lower = text.toLowerCase();
  const markers = ['syrup', 'flavor', 'colour', 'modified starch', 'preservative', 'emulsifier'];
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

  return ScanResult(
    productName: 'Typed Ingredients',
    brand: 'Manual Entry',
    healthScore: score.round().clamp(0, 100),
    novaGroup: nova,
    nutrients: const [
      NutrientInfo(name: 'Calories', value: '—', unit: 'kcal', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Sugar', value: '—', unit: 'g', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Fat', value: '—', unit: 'g', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Sodium', value: '—', unit: 'mg', level: NutritionLevel.moderate),
    ],
    ingredients: ingredients,
    alternatives: const [],
  );
}

// ── Shared small widgets ──────────────────────────────────────────────────────

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
          color: Colors.black38,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
    );
  }
}

class _BottomActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _BottomActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
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
            Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: AppColors.darkGreen,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Scan overlay painter ──────────────────────────────────────────────────────

class _ScanOverlayPainter extends CustomPainter {
  final double boxSize;
  final Size screenSize;

  const _ScanOverlayPainter({required this.boxSize, required this.screenSize});

  @override
  void paint(Canvas canvas, Size size) {
    const cornerLen = 28.0;
    const cornerRadius = 6.0;
    const cornerStroke = 3.5;

    final cx = size.width / 2;
    final cy = size.height * 0.42;
    final half = boxSize / 2;

    final left = cx - half;
    final top = cy - half;
    final right = cx + half;
    final bottom = cy + half;

    // Dark overlay (two rects above and below, full width sides)
    final overlayPaint = Paint()..color = Colors.black.withOpacity(0.62);
    // top
    canvas.drawRect(Rect.fromLTRB(0, 0, size.width, top), overlayPaint);
    // bottom
    canvas.drawRect(Rect.fromLTRB(0, bottom, size.width, size.height), overlayPaint);
    // left
    canvas.drawRect(Rect.fromLTRB(0, top, left, bottom), overlayPaint);
    // right
    canvas.drawRect(Rect.fromLTRB(right, top, size.width, bottom), overlayPaint);

    // Corner brackets
    final cornerPaint = Paint()
      ..color = Colors.white
      ..strokeWidth = cornerStroke
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    void drawCorner(double x, double y, double dx, double dy) {
      final path = Path()
        ..moveTo(x + dx * cornerLen, y)
        ..lineTo(x, y)
        ..lineTo(x, y + dy * cornerLen);
      canvas.drawPath(path, cornerPaint);
    }

    drawCorner(left + cornerRadius, top + cornerRadius, 1, 1);
    drawCorner(right - cornerRadius, top + cornerRadius, -1, 1);
    drawCorner(left + cornerRadius, bottom - cornerRadius, 1, -1);
    drawCorner(right - cornerRadius, bottom - cornerRadius, -1, -1);
  }

  @override
  bool shouldRepaint(_ScanOverlayPainter old) =>
      old.boxSize != boxSize || old.screenSize != screenSize;
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
            const Icon(Icons.camera_alt_outlined, color: Colors.white54, size: 56),
            const SizedBox(height: 20),
            const Text(
              'Camera access required',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'NutriScan needs camera access to scan barcodes and ingredient labels.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white60, fontSize: 14, height: 1.5),
            ),
            const SizedBox(height: 28),
            ElevatedButton.icon(
              onPressed: () async {
                await openAppSettings();
              },
              icon: const Icon(Icons.settings_outlined),
              label: const Text('Open Settings'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.mediumGreen,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: onRetry,
              child: const Text(
                'Try again',
                style: TextStyle(color: Colors.white70),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
