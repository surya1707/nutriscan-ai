import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../models/scan_result_model.dart';
import '../widgets/hero_score_header.dart';
import '../widgets/nova_classification_badge.dart';
import '../widgets/nutrient_insight_grid.dart';
import '../widgets/ingredient_analysis_card.dart';
import '../widgets/healthier_alternatives_list.dart';
import '../widgets/action_buttons_footer.dart';

class ResultsScreen extends StatefulWidget {
  final ScanResult? result;

  const ResultsScreen({super.key, this.result});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  late ScanResult _result;

  @override
  void initState() {
    super.initState();
    _result = widget.result ?? mockScanResult;
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: AppColors.cream,
        body: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            // ── Pinned App Bar ────────────────────────────────────────
            SliverAppBar(
              expandedHeight: 0,
              pinned: true,
              backgroundColor: AppColors.darkGreen,
              foregroundColor: Colors.white,
              elevation: 0,
              leading: Padding(
                padding: const EdgeInsets.all(8.0),
                child: GestureDetector(
                  onTap: () =>
                      context.canPop() ? context.pop() : context.go('/'),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ),
              title: const Text(
                'Scan Results',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w600,
                ),
              ),
              actions: [
                Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: GestureDetector(
                    onTap: () {/* share */},
                    child: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.ios_share_rounded,
                          color: Colors.white, size: 18),
                    ),
                  ),
                ),
              ],
            ),

            // ── Hero Score ────────────────────────────────────────────
            SliverToBoxAdapter(
              child: HeroScoreHeader(
                score: _result.healthScore,
                productName: _result.productName,
                brand: _result.brand,
              ),
            ),

            // ── Body Content ──────────────────────────────────────────
            SliverToBoxAdapter(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),
                  NovaClassificationBadge(group: _result.novaGroup),
                  const SizedBox(height: 24),
                  NutrientInsightGrid(nutrients: _result.nutrients),
                  const SizedBox(height: 24),
                  IngredientAnalysisCard(ingredients: _result.ingredients),
                  const SizedBox(height: 28),
                  HealthierAlternativesList(alternatives: _result.alternatives),
                  const SizedBox(height: 28),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Divider(color: AppColors.divider, height: 1),
                  ),
                  const SizedBox(height: 12),
                  // Pass result so Save button can persist it
                  ActionButtonsFooter(result: _result),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
