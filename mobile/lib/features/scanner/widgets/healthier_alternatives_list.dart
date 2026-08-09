import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';

class HealthierAlternativesList extends StatelessWidget {
  final List<AlternativeProduct> alternatives;

  const HealthierAlternativesList({super.key, required this.alternatives});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Healthier Alternatives',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                'See all',
                style: TextStyle(
                  color: AppColors.mediumGreen,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        SizedBox(
          height: 148,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            itemCount: alternatives.length,
            separatorBuilder: (_, __) => const SizedBox(width: 12),
            itemBuilder: (context, index) {
              return _AlternativeCard(product: alternatives[index]);
            },
          ),
        ),
      ],
    );
  }
}

class _AlternativeCard extends StatelessWidget {
  final AlternativeProduct product;

  const _AlternativeCard({required this.product});

  Color _scoreColor(int score) {
    if (score >= 70) return AppColors.safeGreen;
    if (score >= 45) return AppColors.cautionAmber;
    return AppColors.flaggedRed;
  }

  @override
  Widget build(BuildContext context) {
    final scoreColor = _scoreColor(product.score);

    return Container(
      width: 130,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(20),
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
          // Emoji icon
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppColors.lightGreen.withOpacity(0.55),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                product.emoji,
                style: const TextStyle(fontSize: 22),
              ),
            ),
          ),

          // Name + brand
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                product.name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                product.brand,
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.w400,
                ),
              ),
            ],
          ),

          // Score bar
          Row(
            children: [
              Text(
                '${product.score}',
                style: TextStyle(
                  color: scoreColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: product.score / 100,
                    minHeight: 5,
                    backgroundColor: AppColors.divider,
                    valueColor: AlwaysStoppedAnimation(scoreColor),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
