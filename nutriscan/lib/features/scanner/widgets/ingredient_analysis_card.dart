import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';

class IngredientAnalysisCard extends StatefulWidget {
  final List<IngredientItem> ingredients;

  const IngredientAnalysisCard({super.key, required this.ingredients});

  @override
  State<IngredientAnalysisCard> createState() => _IngredientAnalysisCardState();
}

class _IngredientAnalysisCardState extends State<IngredientAnalysisCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final flaggedCount = widget.ingredients.where((i) => i.isFlagged).length;
    final displayList =
        _expanded ? widget.ingredients : widget.ingredients.take(5).toList();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Ingredients',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (flaggedCount > 0)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF0EF),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: AppColors.flaggedRed.withOpacity(0.3), width: 1),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: AppColors.flaggedRed, size: 13),
                      const SizedBox(width: 4),
                      Text(
                        '$flaggedCount flagged',
                        style: const TextStyle(
                          color: AppColors.flaggedRed,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),

          // Card
          Container(
            decoration: BoxDecoration(
              color: AppColors.cardBg,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 14,
                  offset: const Offset(0, 5),
                ),
              ],
              border: Border.all(color: AppColors.divider, width: 0.8),
            ),
            child: Column(
              children: [
                ...displayList.asMap().entries.map((entry) {
                  final i = entry.key;
                  final item = entry.value;
                  final isLast = i == displayList.length - 1;

                  return Column(
                    children: [
                      _IngredientRow(item: item),
                      if (!isLast)
                        Divider(
                          height: 1,
                          thickness: 0.6,
                          color: AppColors.divider,
                          indent: 16,
                          endIndent: 16,
                        ),
                    ],
                  );
                }),

                // Show more / less toggle
                if (widget.ingredients.length > 5)
                  InkWell(
                    onTap: () => setState(() => _expanded = !_expanded),
                    borderRadius: const BorderRadius.vertical(
                        bottom: Radius.circular(20)),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      decoration: BoxDecoration(
                        color: AppColors.lightGreen.withOpacity(0.35),
                        borderRadius: const BorderRadius.vertical(
                            bottom: Radius.circular(20)),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _expanded
                                ? 'Show less'
                                : 'Show ${widget.ingredients.length - 5} more',
                            style: const TextStyle(
                              color: AppColors.mediumGreen,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(width: 4),
                          AnimatedRotation(
                            turns: _expanded ? 0.5 : 0,
                            duration: const Duration(milliseconds: 250),
                            child: const Icon(
                              Icons.keyboard_arrow_down_rounded,
                              color: AppColors.mediumGreen,
                              size: 18,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _IngredientRow extends StatelessWidget {
  final IngredientItem item;

  const _IngredientRow({required this.item});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Warning or OK icon
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: item.isFlagged
                ? const Icon(Icons.warning_amber_rounded,
                    color: AppColors.flaggedRed, size: 16)
                : Container(
                    width: 8,
                    height: 8,
                    margin: const EdgeInsets.only(top: 4, left: 4),
                    decoration: const BoxDecoration(
                      color: AppColors.safeGreen,
                      shape: BoxShape.circle,
                    ),
                  ),
          ),
          const SizedBox(width: 10),

          // Text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: TextStyle(
                    color: item.isFlagged
                        ? AppColors.textPrimary
                        : AppColors.textSecondary,
                    fontSize: 13.5,
                    fontWeight: item.isFlagged
                        ? FontWeight.w600
                        : FontWeight.w400,
                    height: 1.4,
                  ),
                ),
                if (item.isFlagged && item.flagReason != null) ...[
                  const SizedBox(height: 3),
                  Text(
                    item.flagReason!,
                    style: const TextStyle(
                      color: AppColors.flaggedRed,
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
