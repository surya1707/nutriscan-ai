import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              Text(
                'HISTORY',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: AppColors.textMuted,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              Text('Scan history', style: Theme.of(context).textTheme.headlineMedium),
              const Expanded(child: _EmptyHistoryState()),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyHistoryState extends StatelessWidget {
  const _EmptyHistoryState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.lightGreen,
              borderRadius: BorderRadius.circular(32),
            ),
            child: const Icon(Icons.history, color: AppColors.mediumGreen, size: 30),
          ),
          const SizedBox(height: 18),
          const Text(
            'Nothing scanned yet',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Your scans will appear here for quick\nreview.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          GestureDetector(
            onTap: () => context.push('/scanner'),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 15),
              decoration: BoxDecoration(
                color: AppColors.darkGreen,
                borderRadius: BorderRadius.circular(30),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _BracketIcon(),
                  const SizedBox(width: 10),
                  const Text(
                    'Start scanning',
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
        ],
      ),
    );
  }
}

class _BracketIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(18, 18),
      painter: _BracketPainter(),
    );
  }
}

class _BracketPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final c = size.width * 0.28;
    final w = size.width;
    final h = size.height;
    canvas.drawPath(Path()..moveTo(0, c)..lineTo(0, 0)..lineTo(c, 0), paint);
    canvas.drawPath(Path()..moveTo(w - c, 0)..lineTo(w, 0)..lineTo(w, c), paint);
    canvas.drawPath(Path()..moveTo(0, h - c)..lineTo(0, h)..lineTo(c, h), paint);
    canvas.drawPath(Path()..moveTo(w - c, h)..lineTo(w, h)..lineTo(w, h - c), paint);
  }

  @override
  bool shouldRepaint(_BracketPainter old) => false;
}
