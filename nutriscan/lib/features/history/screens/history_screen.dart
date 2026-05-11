import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/providers/scan_history_provider.dart';
import '../../../core/database/app_database.dart';
import '../../../core/database/tables.dart';
import '../../scanner/models/scan_result_model.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(scanHistoryProvider);

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              Text(
                'HISTORY',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: AppColors.textMuted,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              Text('Scan history',
                  style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 16),

              Expanded(
                child: historyAsync.when(
                  loading: () => const Center(
                    child: CircularProgressIndicator(),
                  ),
                  error: (e, _) => Center(child: Text('Error: $e')),
                  data: (rows) {
                    if (rows.isEmpty) return const _EmptyHistoryState();
                    return ListView.separated(
                      itemCount: rows.length,
                      separatorBuilder: (_, __) =>
                          Divider(color: AppColors.divider, height: 1),
                      itemBuilder: (context, i) => _ScanHistoryTile(
                        row: rows[i],
                        onTap: () {
                          final result = scanResultFromRow(rows[i]);
                          context.push('/results', extra: result);
                        },
                        onDelete: () =>
                            deleteScanById(ref, rows[i].id),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ScanHistoryTile extends StatelessWidget {
  final ScanHistoryTableData row;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _ScanHistoryTile({
    required this.row,
    required this.onTap,
    required this.onDelete,
  });

  Color _scoreColor(int score) {
    if (score >= 60) return AppColors.safeGreen;
    if (score >= 40) return AppColors.cautionAmber;
    return AppColors.flaggedRed;
  }

  @override
  Widget build(BuildContext context) {
    final scoreColor = _scoreColor(row.healthScore);
    final dateStr = DateFormat('d MMM, h:mm a').format(row.scannedAt.toLocal());

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(0),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(
          children: [
            // Score circle
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: scoreColor.withOpacity(0.12),
                shape: BoxShape.circle,
                border: Border.all(color: scoreColor.withOpacity(0.4), width: 1.5),
              ),
              child: Center(
                child: Text(
                  '${row.healthScore}',
                  style: TextStyle(
                    color: scoreColor,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),

            // Name + date
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    row.productName,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14.5,
                      fontWeight: FontWeight.w600,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${row.brand}  ·  $dateStr',
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),

            // Delete
            IconButton(
              icon: const Icon(Icons.delete_outline,
                  color: AppColors.textMuted, size: 20),
              onPressed: onDelete,
              splashRadius: 20,
            ),

            const Icon(Icons.chevron_right_rounded,
                color: AppColors.textMuted, size: 20),
          ],
        ),
      ),
    );
  }
}

class _EmptyHistoryState extends StatelessWidget {
  const _EmptyHistoryState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.lightGreen,
              borderRadius: BorderRadius.circular(32),
            ),
            child: const Icon(Icons.history,
                color: AppColors.mediumGreen, size: 30),
          ),
          const SizedBox(height: 18),
          const Text(
            'Nothing scanned yet',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Your scans will appear here for quick\nreview.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          GestureDetector(
            onTap: () => context.push('/scanner'),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 28, vertical: 15),
              decoration: BoxDecoration(
                color: AppColors.darkGreen,
                borderRadius: BorderRadius.circular(30),
              ),
              child: const Text(
                'Start scanning',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
