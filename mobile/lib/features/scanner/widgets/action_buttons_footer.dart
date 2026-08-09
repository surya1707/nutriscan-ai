import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/providers/scan_history_provider.dart';
import '../models/scan_result_model.dart';

class ActionButtonsFooter extends ConsumerStatefulWidget {
  final ScanResult result;
  const ActionButtonsFooter({super.key, required this.result});

  @override
  ConsumerState<ActionButtonsFooter> createState() =>
      _ActionButtonsFooterState();
}

class _ActionButtonsFooterState extends ConsumerState<ActionButtonsFooter>
    with SingleTickerProviderStateMixin {
  bool _saved = false;
  late AnimationController _checkController;
  late Animation<double> _checkScale;
  late Animation<double> _checkOpacity;

  @override
  void initState() {
    super.initState();
    _checkController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _checkScale = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _checkController, curve: Curves.elasticOut),
    );
    _checkOpacity = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _checkController, curve: const Interval(0, 0.4)),
    );
  }

  @override
  void dispose() {
    _checkController.dispose();
    super.dispose();
  }

  Future<void> _handleSave() async {
    if (_saved) return;
    // Persist to SQLite
    await saveScanResult(ref, widget.result);
    setState(() => _saved = true);
    _checkController.forward();

    // Reset after 2.5 s
    await Future.delayed(const Duration(milliseconds: 2500));
    if (mounted) {
      setState(() => _saved = false);
      _checkController.reset();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
          20, 12, 20, MediaQuery.of(context).padding.bottom + 20),
      child: Column(
        children: [
          // ── Save to History ──────────────────────────────────────────
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            width: double.infinity,
            height: 56,
            decoration: BoxDecoration(
              color: _saved ? AppColors.safeGreen : AppColors.darkGreen,
              borderRadius: BorderRadius.circular(18),
              boxShadow: [
                BoxShadow(
                  color: (_saved ? AppColors.safeGreen : AppColors.darkGreen)
                      .withOpacity(0.35),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: _handleSave,
                borderRadius: BorderRadius.circular(18),
                child: Center(
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 250),
                    child: _saved
                        ? AnimatedBuilder(
                            key: const ValueKey('saved'),
                            animation: _checkController,
                            builder: (_, __) => FadeTransition(
                              opacity: _checkOpacity,
                              child: ScaleTransition(
                                scale: _checkScale,
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.check_circle_rounded,
                                        color: Colors.white, size: 20),
                                    SizedBox(width: 8),
                                    Text(
                                      'Saved to History!',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 15,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          )
                        : const Row(
                            key: ValueKey('unsaved'),
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.bookmark_add_outlined,
                                  color: Colors.white, size: 20),
                              SizedBox(width: 8),
                              Text(
                                'Save to History',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
              ),
            ),
          ),

          const SizedBox(height: 12),

          // ── Scan New Product ─────────────────────────────────────────
          SizedBox(
            width: double.infinity,
            height: 56,
            child: OutlinedButton.icon(
              onPressed: () {
                if (context.canPop()) {
                  context.pop();
                } else {
                  context.go('/scanner');
                }
              },
              icon: const Icon(Icons.qr_code_scanner_rounded, size: 20),
              label: const Text(
                'Scan New Product',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.darkGreen,
                side: const BorderSide(color: AppColors.mediumGreen, width: 1.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
