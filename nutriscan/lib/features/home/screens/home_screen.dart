import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../widgets/hero_scan_card.dart';
import '../widgets/stats_row.dart';
import '../widgets/personalize_banner.dart';
import '../widgets/recent_scans_section.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              // Top row: brand + avatar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'NUTRISCAN AI',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: AppColors.mediumGreen,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Eat with\nintelligence.',
                        style: Theme.of(context).textTheme.displayLarge,
                      ),
                    ],
                  ),
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppColors.lightGreen,
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: const Icon(Icons.person_outline, color: AppColors.mediumGreen, size: 22),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Hero scan card
              HeroScanCard(onTap: () => context.push('/scanner')),
              const SizedBox(height: 16),

              // Stats
              const StatsRow(totalScans: 0, safeCount: 0, flaggedCount: 0),
              const SizedBox(height: 16),

              // Personalize banner
              PersonalizeBanner(onTap: () => context.go('/profile')),
              const SizedBox(height: 24),

              // Recent scans
              Text('Recent scans', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              const RecentScansSection(),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
