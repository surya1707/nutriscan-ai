import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/providers/scan_history_provider.dart';

class StatsRow extends ConsumerWidget {
  const StatsRow({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(scanStatsProvider);

    return statsAsync.when(
      loading: () => const _StatsRowSkeleton(),
      error: (_, __) => const _StatsRowSkeleton(),
      data: (stats) => Row(
        children: [
          Expanded(child: _StatCard(
            icon: Icons.layers_outlined,
            iconColor: AppColors.textSecondary,
            value: stats.total.toString(),
            label: 'Total\nscans',
          )),
          const SizedBox(width: 10),
          Expanded(child: _StatCard(
            icon: Icons.check_circle,
            iconColor: AppColors.safeGreen,
            value: stats.safe.toString(),
            label: 'Safe',
            iconFilled: true,
          )),
          const SizedBox(width: 10),
          Expanded(child: _StatCard(
            icon: Icons.warning_rounded,
            iconColor: AppColors.flaggedRed,
            value: stats.flagged.toString(),
            label: 'Flagged',
            iconFilled: true,
          )),
        ],
      ),
    );
  }
}

class _StatsRowSkeleton extends StatelessWidget {
  const _StatsRowSkeleton();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(3, (i) => Expanded(
        child: Container(
          margin: EdgeInsets.only(left: i == 0 ? 0 : 10),
          height: 88,
          decoration: BoxDecoration(
            color: AppColors.divider,
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      )),
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
