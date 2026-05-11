import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';

class NutrientInsightGrid extends StatelessWidget {
  final List<NutrientInfo> nutrients;

  const NutrientInsightGrid({super.key, required this.nutrients});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionHeader(context, 'Nutrient Breakdown'),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.45,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            children: nutrients.map((n) => _NutrientTile(nutrient: n)).toList(),
          ),
        ],
      ),
    );
  }
}

class _NutrientTile extends StatelessWidget {
  final NutrientInfo nutrient;

  const _NutrientTile({required this.nutrient});

  @override
  Widget build(BuildContext context) {
    final colors = _levelColors(nutrient.level);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(color: AppColors.divider, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Nutrient name + traffic light dot
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                nutrient.name,
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.3,
                ),
              ),
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: colors.dot,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: colors.dot.withOpacity(0.5),
                      blurRadius: 6,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Value
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                nutrient.value,
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  height: 1,
                ),
              ),
              const SizedBox(width: 4),
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  nutrient.unit,
                  style: TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),

          // Status label
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: colors.bg,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              _levelLabel(nutrient.level),
              style: TextStyle(
                color: colors.label,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _levelLabel(NutritionLevel l) {
    switch (l) {
      case NutritionLevel.good: return 'HEALTHY';
      case NutritionLevel.moderate: return 'MODERATE';
      case NutritionLevel.poor: return 'HIGH';
    }
  }

  _TrafficColors _levelColors(NutritionLevel l) {
    switch (l) {
      case NutritionLevel.good:
        return _TrafficColors(
          dot: AppColors.safeGreen,
          bg: const Color(0xFFEAF7F0),
          label: AppColors.safeGreen,
        );
      case NutritionLevel.moderate:
        return _TrafficColors(
          dot: AppColors.cautionAmber,
          bg: const Color(0xFFFFF7E6),
          label: AppColors.cautionAmber,
        );
      case NutritionLevel.poor:
        return _TrafficColors(
          dot: AppColors.flaggedRed,
          bg: const Color(0xFFFFF0EF),
          label: AppColors.flaggedRed,
        );
    }
  }
}

class _TrafficColors {
  final Color dot;
  final Color bg;
  final Color label;
  const _TrafficColors({required this.dot, required this.bg, required this.label});
}

Widget _sectionHeader(BuildContext context, String title) {
  return Text(
    title,
    style: const TextStyle(
      color: AppColors.textPrimary,
      fontSize: 17,
      fontWeight: FontWeight.w700,
    ),
  );
}
