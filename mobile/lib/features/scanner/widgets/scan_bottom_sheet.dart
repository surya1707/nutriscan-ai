import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class ScanBottomSheet extends StatelessWidget {
  final bool cameraAvailable;
  const ScanBottomSheet({super.key, required this.cameraAvailable});

  @override
  Widget build(BuildContext context) {
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
          if (!cameraAvailable) ...[
            Text(
              'Camera unavailable here. Use "Type ingredients" or pick a label image from gallery.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Action row: Type | Scan | Gallery
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Type button
              _ActionButton(
                icon: Icons.edit_outlined,
                label: 'Type',
                onTap: () {/* type mode */},
              ),

              // Centre scan button (larger, ringed)
              GestureDetector(
                onTap: () {/* scan */},
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
                        color: AppColors.lightGreen.withOpacity(0.4),
                      ),
                      child: CustomPaint(
                        painter: _SmallBracketPainter(color: AppColors.darkGreen),
                      ),
                    ),
                  ),
                ),
              ),

              // Gallery button
              _ActionButton(
                icon: Icons.image_outlined,
                label: 'Gallery',
                onTap: () {/* gallery picker */},
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionButton({
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

class _SmallBracketPainter extends CustomPainter {
  final Color color;
  const _SmallBracketPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final c = size.width * 0.22;
    final w = size.width;
    final h = size.height;

    canvas.drawPath(Path()..moveTo(0, c)..lineTo(0, 0)..lineTo(c, 0), paint);
    canvas.drawPath(Path()..moveTo(w - c, 0)..lineTo(w, 0)..lineTo(w, c), paint);
    canvas.drawPath(Path()..moveTo(0, h - c)..lineTo(0, h)..lineTo(c, h), paint);
    canvas.drawPath(Path()..moveTo(w - c, h)..lineTo(w, h)..lineTo(w, h - c), paint);
  }

  @override
  bool shouldRepaint(_SmallBracketPainter old) => old.color != color;
}
