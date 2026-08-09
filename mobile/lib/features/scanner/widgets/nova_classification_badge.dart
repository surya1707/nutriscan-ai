import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';

class NovaClassificationBadge extends StatelessWidget {
  final NovaGroup group;

  const NovaClassificationBadge({super.key, required this.group});

  @override
  Widget build(BuildContext context) {
    final config = _novaConfig(group);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      decoration: BoxDecoration(
        color: config.bgColor,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: config.accentColor.withOpacity(0.18),
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
          BoxShadow(
            color: Colors.white.withOpacity(0.75),
            blurRadius: 1,
            offset: const Offset(0, -1),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Row(
          children: [
            // NOVA badge pill
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: config.accentColor,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: config.accentColor.withOpacity(0.45),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'NOVA',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
                  ),
                  Text(
                    '${_groupNumber(group)}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      height: 1.0,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 16),

            // Description
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    config.title,
                    style: TextStyle(
                      color: config.accentColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    config.description,
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                      height: 1.45,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  int _groupNumber(NovaGroup g) {
    switch (g) {
      case NovaGroup.group1: return 1;
      case NovaGroup.group2: return 2;
      case NovaGroup.group3: return 3;
      case NovaGroup.group4: return 4;
    }
  }

  _NovaConfig _novaConfig(NovaGroup g) {
    switch (g) {
      case NovaGroup.group1:
        return _NovaConfig(
          bgColor: const Color(0xFFF0FBF5),
          accentColor: const Color(0xFF1E8C4A),
          title: 'Unprocessed / Natural',
          description: 'Foods in their natural state. Eat freely and enjoy.',
        );
      case NovaGroup.group2:
        return _NovaConfig(
          bgColor: const Color(0xFFF4FBF0),
          accentColor: const Color(0xFF5BAD5B),
          title: 'Processed Culinary Ingredients',
          description:
              'Simple ingredients like oils, flours, or spices. Use in moderation.',
        );
      case NovaGroup.group3:
        return _NovaConfig(
          bgColor: const Color(0xFFFFF8EC),
          accentColor: const Color(0xFFD98B2A),
          title: 'Processed Foods',
          description:
              'Contains added salt, sugar, or oils. Limit your intake frequency.',
        );
      case NovaGroup.group4:
        return _NovaConfig(
          bgColor: const Color(0xFFFFF1F0),
          accentColor: const Color(0xFFD94F3D),
          title: 'Ultra-Processed',
          description:
              'Industrial formulations with additives. Avoid frequent consumption.',
        );
    }
  }
}

class _NovaConfig {
  final Color bgColor;
  final Color accentColor;
  final String title;
  final String description;

  const _NovaConfig({
    required this.bgColor,
    required this.accentColor,
    required this.title,
    required this.description,
  });
}
