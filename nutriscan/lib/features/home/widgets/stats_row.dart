import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class StatsRow extends StatelessWidget {
  final int totalScans;
  final int safeCount;
  final int flaggedCount;

  const StatsRow({
    super.key,
    required this.totalScans,
    required this.safeCount,
    required this.flaggedCount,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _StatCard(
          icon: Icons.layers_outlined,
          iconColor: AppColors.textSecondary,
          value: totalScans.toString(),
          label: 'Total\nscans',
        )),
        const SizedBox(width: 10),
        Expanded(child: _StatCard(
          icon: Icons.check_circle,
          iconColor: AppColors.safeGreen,
          value: safeCount.toString(),
          label: 'Safe',
          iconFilled: true,
        )),
        const SizedBox(width: 10),
        Expanded(child: _StatCard(
          icon: Icons.warning_rounded,
          iconColor: AppColors.flaggedRed,
          value: flaggedCount.toString(),
          label: 'Flagged',
          iconFilled: true,
        )),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;
  final bool iconFilled;

  const _StatCard({
    required this.icon,
    required this.iconColor,
    required this.value,
    required this.label,
    this.iconFilled = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 22, color: iconColor),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}
