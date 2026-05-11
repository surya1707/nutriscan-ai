import 'package:drift/drift.dart';
import 'app_database.dart';
import 'tables.dart';

part 'scan_history_dao.g.dart';

@DriftAccessor(tables: [ScanHistoryTable])
class ScanHistoryDao extends DatabaseAccessor<AppDatabase>
    with _$ScanHistoryDaoMixin {
  ScanHistoryDao(super.db);

  /// Stream of all scans, newest first.
  Stream<List<ScanHistoryTableData>> watchAll() =>
      (select(scanHistoryTable)
            ..orderBy([(t) => OrderingTerm.desc(t.scannedAt)]))
          .watch();

  /// Insert or replace a scan.
  Future<void> upsertScan(ScanHistoryTableCompanion entry) =>
      into(scanHistoryTable).insertOnConflictUpdate(entry);

  /// Delete a scan by id.
  Future<int> deleteScan(String id) =>
      (delete(scanHistoryTable)..where((t) => t.id.equals(id))).go();

  /// Most recent N scans (for home screen).
  Future<List<ScanHistoryTableData>> getRecent(int limit) =>
      (select(scanHistoryTable)
            ..orderBy([(t) => OrderingTerm.desc(t.scannedAt)])
            ..limit(limit))
          .get();

  /// Count all / safe / flagged.
  Future<ScanStats> getStats() async {
    final all = await select(scanHistoryTable).get();
    final safe = all.where((r) => r.healthScore >= 60).length;
    final flagged = all.where((r) => r.healthScore < 40).length;
    return ScanStats(total: all.length, safe: safe, flagged: flagged);
  }
}

class ScanStats {
  final int total;
  final int safe;
  final int flagged;
  const ScanStats({required this.total, required this.safe, required this.flagged});
}
