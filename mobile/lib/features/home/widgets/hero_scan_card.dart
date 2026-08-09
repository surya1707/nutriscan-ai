import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class HeroScanCard extends StatelessWidget {
  final VoidCallback onTap;
  const HeroScanCard({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.darkGreen,
        borderRadius: BorderRadius.circular(20),
      ),
      clipBehavior: Clip.hardEdge,
      child: Stack(
        children: [
          // Background texture hint (subtle leaf image placeholder)
          Positioned(
            right: -10,
            bottom: -10,
            child: Opacity(
              opacity: 0.15,
              child: Container(
                width: 140,
                height: 140,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.mediumGreen,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SCAN INGREDIENTS',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Colors.white54,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Decode what\nyou eat.',
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(
                    color: Colors.white,
                    fontSize: 30,
                    height: 1.15,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Point at any label. We translate E-codes,\nclassify NOVA tier, and flag ingredients\nmatched to your profile.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white70,
                    height: 1.55,
                  ),
                ),
                const SizedBox(height: 20),
                GestureDetector(
                  onTap: onTap,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: Colors.white24, width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _ScanBracketIcon(size: 18, color: Colors.white),
                        const SizedBox(width: 10),
                        const Text(
                          'Start Scan',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 4),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ScanBracketIcon extends StatelessWidget {
  final double size;
  final Color color;
  const _ScanBracketIcon({required this.size, required this.color});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(size, size),
      painter: _BracketPainter(color: color),
    );
  }
}

class _BracketPainter extends CustomPainter {
  final Color color;
  const _BracketPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final corner = size.width * 0.28;
    final w = size.width;
    final h = size.height;

    // Top-left
    canvas.drawPath(Path()..moveTo(0, corner)..lineTo(0, 0)..lineTo(corner, 0), paint);
    // Top-right
    canvas.drawPath(Path()..moveTo(w - corner, 0)..lineTo(w, 0)..lineTo(w, corner), paint);
    // Bottom-left
    canvas.drawPath(Path()..moveTo(0, h - corner)..lineTo(0, h)..lineTo(corner, h), paint);
    // Bottom-right
    canvas.drawPath(Path()..moveTo(w - corner, h)..lineTo(w, h)..lineTo(w, h - corner), paint);
  }

  @override
  bool shouldRepaint(_BracketPainter old) => old.color != color;
}
