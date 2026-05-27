import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';
import '../../../core/services/safety_score_service.dart';

class SafetyScoreBreakdownCard extends StatefulWidget {
  final SafetyScoreBreakdown breakdown;

  const SafetyScoreBreakdownCard({super.key, required this.breakdown});

  @override
  State<SafetyScoreBreakdownCard> createState() =>
      _SafetyScoreBreakdownCardState();
}

class _SafetyScoreBreakdownCardState extends State<SafetyScoreBreakdownCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.divider, width: 0.8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            // Header (Tap to expand)
            InkWell(
              onTap: () => setState(() => _isExpanded = !_isExpanded),
              borderRadius: BorderRadius.circular(20),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.lightGreen.withOpacity(0.4),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.analytics_outlined,
                          color: AppColors.darkGreen, size: 20),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Personal Score Breakdown',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          Text(
                            'Tap to see how your profile affected the score',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      _isExpanded
                          ? Icons.keyboard_arrow_up_rounded
                          : Icons.keyboard_arrow_down_rounded,
                      color: AppColors.textMuted,
                    ),
                  ],
                ),
              ),
            ),

            if (_isExpanded) ...[
              const Divider(height: 1),
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _BreakdownRow(
                      label: 'Allergens',
                      deduction: widget.breakdown.allergenDeduction,
                      icon: Icons.warning_amber_rounded,
                      color: AppColors.flaggedRed,
                    ),
                    const SizedBox(height: 12),
                    _BreakdownRow(
                      label: 'NOVA Processing',
                      deduction: widget.breakdown.novaDeduction,
                      icon: Icons.factory_outlined,
                      color: AppColors.cautionAmber,
                    ),
                    const SizedBox(height: 12),
                    _BreakdownRow(
                      label: 'Additives / Additives',
                      deduction: widget.breakdown.additiveDeduction,
                      icon: Icons.science_outlined,
                      color: Colors.purple,
                    ),
                    const SizedBox(height: 12),
                    _BreakdownRow(
                      label: 'Personal Conditions',
                      deduction: widget.breakdown.conditionDeduction,
                      icon: Icons.health_and_safety_outlined,
                      color: Colors.blue,
                    ),
                    const SizedBox(height: 12),
                    _BreakdownRow(
                      label: 'High Sugar/Fat/Sodium',
                      deduction: widget.breakdown.nutrientDeduction,
                      icon: Icons.fastfood_outlined,
                      color: Colors.deepOrange,
                    ),
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Divider(),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Final Personalised Score',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                          ),
                        ),
                        Text(
                          '${widget.breakdown.finalScore}',
                          style: const TextStyle(
                            fontWeight: FontWeight.w900,
                            fontSize: 18,
                            color: AppColors.darkGreen,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _BreakdownRow extends StatelessWidget {
  final String label;
  final double deduction;
  final IconData icon;
  final Color color;

  const _BreakdownRow({
    required this.label,
    required this.deduction,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
          ),
        ),
        Text(
          deduction > 0 ? '-${deduction.toStringAsFixed(0)}' : '0',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: deduction > 0 ? AppColors.flaggedRed : AppColors.textMuted,
          ),
        ),
      ],
    );
  }
}
