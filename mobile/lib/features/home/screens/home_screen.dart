import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers/auth_provider.dart';
import '../widgets/hero_scan_card.dart';
import '../widgets/stats_row.dart';
import '../widgets/personalize_banner.dart';
import '../widgets/recent_scans_section.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.value?.user;

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
                  Column(
                    children: [
                      if (user?.photoURL != null)
                        CircleAvatar(
                          radius: 22,
                          backgroundImage: NetworkImage(user!.photoURL!),
                        )
                      else
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: AppColors.lightGreen,
                            borderRadius: BorderRadius.circular(22),
                          ),
                          child: const Icon(Icons.person_outline, color: AppColors.mediumGreen, size: 22),
                        ),
                      const SizedBox(height: 4),
                      Text(
                        user?.displayName?.split(' ').first ?? 'Guest',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.mediumGreen,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Hero scan card
              HeroScanCard(key: const ValueKey('home_scan_card'), onTap: () => context.push('/scanner')),
              const SizedBox(height: 16),

              // Stats
              const StatsRow(),
              const SizedBox(height: 16),

              // Personalize banner
              PersonalizeBanner(key: const ValueKey('home_personalize_banner'), onTap: () => context.go('/profile')),
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
