import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';

class HeroScoreHeader extends StatefulWidget {
  final int score; // 0–100
  final String productName;
  final String brand;

  const HeroScoreHeader({
    super.key,
    required this.score,
    required this.productName,
    required this.brand,
  });

  @override
  State<HeroScoreHeader> createState() => _HeroScoreHeaderState();
}

class _HeroScoreHeaderState extends State<HeroScoreHeader>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _progressAnimation;
  late Animation<double> _numberAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1400),
      vsync: this,
    );
    final curve = CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic);
    _progressAnimation = Tween<double>(begin: 0, end: widget.score / 100).animate(curve);
    _numberAnimation = Tween<double>(begin: 0, end: widget.score.toDouble()).animate(curve);
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color _scoreColor(double progress) {
    // Interpolate: emerald green (good) → amber → deep red (poor)
    if (progress > 0.6) {
      // green zone
      return Color.lerp(const Color(0xFFE5A020), AppColors.safeGreen,
          ((progress - 0.6) / 0.4).clamp(0.0, 1.0))!;
    } else {
      // red zone
      return Color.lerp(AppColors.flaggedRed, const Color(0xFFE5A020),
          (progress / 0.6).clamp(0.0, 1.0))!;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final progress = _progressAnimation.value;
        final color = _scoreColor(progress);
        final displayScore = _numberAnimation.value.round();

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(24, 28, 24, 32),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.darkGreen,
                AppColors.mediumGreen.withOpacity(0.85),
              ],
            ),
          ),
          child: Column(
            children: [
              // Product info
              Text(
                widget.brand.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white54,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                widget.productName,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 28),

              // Circular gauge
              SizedBox(
                width: 160,
                height: 160,
                child: CustomPaint(
                  painter: _GaugePainter(progress: progress, color: color),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '$displayScore',
                          style: TextStyle(
                            color: color,
                            fontSize: 52,
                            fontWeight: FontWeight.w800,
                            height: 1,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Health Score',
                          style: TextStyle(
                            color: Colors.white60,
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // Score descriptor label
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: color.withOpacity(0.4), width: 1),
                ),
                child: Text(
                  _scoreLabel(widget.score),
                  style: TextStyle(
                    color: color,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  String _scoreLabel(int score) {
    if (score >= 75) return '✅ Great Choice';
    if (score >= 50) return '⚠️ Consume Moderately';
    if (score >= 25) return '🔴 Poor Nutritional Quality';
    return '🚫 Avoid — Very Unhealthy';
  }
}

class _GaugePainter extends CustomPainter {
  final double progress;
  final Color color;

  const _GaugePainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 8;
    const startAngle = math.pi * 0.75;
    const sweepFull = math.pi * 1.5;

    // Track (background arc)
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepFull,
      false,
      Paint()
        ..color = Colors.white.withOpacity(0.12)
        ..strokeWidth = 12
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round,
    );

    // Progress arc
    if (progress > 0) {
      final sweepAngle = sweepFull * progress;
      final gradient = SweepGradient(
        startAngle: startAngle,
        endAngle: startAngle + sweepFull,
        colors: [
          color.withOpacity(0.5),
          color,
        ],
      );
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepAngle,
        false,
        Paint()
          ..shader = gradient.createShader(
              Rect.fromCircle(center: center, radius: radius))
          ..strokeWidth = 12
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round,
      );

      // Glowing tip dot
      final endAngle = startAngle + sweepAngle;
      final tipX = center.dx + radius * math.cos(endAngle);
      final tipY = center.dy + radius * math.sin(endAngle);
      canvas.drawCircle(
        Offset(tipX, tipY),
        7,
        Paint()
          ..color = color
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4),
      );
      canvas.drawCircle(
        Offset(tipX, tipY),
        4,
        Paint()..color = Colors.white,
      );
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) =>
      old.progress != progress || old.color != color;
}
