import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../database/app_database.dart';
import '../database/tables.dart';
import '../database/scan_history_dao.dart';
import '../../features/scanner/models/scan_result_model.dart';

// ── Singleton DB instance ────────────────────────────────────────────────────

final databaseProvider = Provider<AppDatabase>((ref) {
  final db = AppDatabase();
  ref.onDispose(db.close);
  return db;
});

// ── Scan History ─────────────────────────────────────────────────────────────

final scanHistoryDaoProvider = Provider<ScanHistoryDao>((ref) {
  return ref.watch(databaseProvider).scanHistoryDao;
});

/// Live stream of all scan history rows.
final scanHistoryProvider =
    StreamProvider<List<ScanHistoryTableData>>((ref) {
  return ref.watch(scanHistoryDaoProvider).watchAll();
});

/// Live stats for the home screen stats row.
final scanStatsProvider = FutureProvider<ScanStats>((ref) async {
  // Re-compute whenever the stream emits.
  ref.watch(scanHistoryProvider);
  return ref.read(scanHistoryDaoProvider).getStats();
});

/// Most recent 5 scans for the home screen.
final recentScansProvider =
    FutureProvider<List<ScanHistoryTableData>>((ref) async {
  ref.watch(scanHistoryProvider);
  return ref.read(scanHistoryDaoProvider).getRecent(5);
});

// ── Save / Delete helpers ─────────────────────────────────────────────────────

/// Saves a [ScanResult] to the database.
Future<void> saveScanResult(WidgetRef ref, ScanResult result) async {
  final dao = ref.read(scanHistoryDaoProvider);
  await dao.upsertScan(ScanHistoryTableCompanion.insert(
    id: result.id,
    productName: result.productName,
    brand: result.brand,
    healthScore: result.healthScore,
    novaGroup: _novaGroupToInt(result.novaGroup),
    nutrientsJson: jsonEncode(
      result.nutrients.map((n) => {
        'name': n.name,
        'value': n.value,
        'unit': n.unit,
        'level': n.level.name,
      }).toList(),
    ),
    ingredientsJson: jsonEncode(
      result.ingredients.map((i) => {
        'name': i.name,
        'isFlagged': i.isFlagged,
        'flagReason': i.flagReason,
      }).toList(),
    ),
    alternativesJson: jsonEncode(
      result.alternatives.map((a) => {
        'name': a.name,
        'brand': a.brand,
        'score': a.score,
        'emoji': a.emoji,
      }).toList(),
    ),
    scannedAt: DateTime.now(),
  ));
}

Future<void> deleteScanById(WidgetRef ref, String id) async {
  await ref.read(scanHistoryDaoProvider).deleteScan(id);
}

// ── Deserialization helpers ───────────────────────────────────────────────────

ScanResult scanResultFromRow(ScanHistoryTableData row) {
  final nutrients = (jsonDecode(row.nutrientsJson) as List).map((e) {
    return NutrientInfo(
      name: e['name'] as String,
      value: e['value'] as String,
      unit: e['unit'] as String,
      level: NutritionLevel.values.byName(e['level'] as String),
    );
  }).toList();

  final ingredients = (jsonDecode(row.ingredientsJson) as List).map((e) {
    return IngredientItem(
      name: e['name'] as String,
      isFlagged: e['isFlagged'] as bool? ?? false,
      flagReason: e['flagReason'] as String?,
    );
  }).toList();

  final alternatives = (jsonDecode(row.alternativesJson) as List).map((e) {
    return AlternativeProduct(
      name: e['name'] as String,
      brand: e['brand'] as String,
      score: e['score'] as int,
      emoji: e['emoji'] as String,
    );
  }).toList();

  return ScanResult(
    id: row.id,
    productName: row.productName,
    brand: row.brand,
    healthScore: row.healthScore,
    novaGroup: _intToNovaGroup(row.novaGroup),
    nutrients: nutrients,
    ingredients: ingredients,
    alternatives: alternatives,
  );
}

int _novaGroupToInt(NovaGroup g) {
  switch (g) {
    case NovaGroup.group1: return 1;
    case NovaGroup.group2: return 2;
    case NovaGroup.group3: return 3;
    case NovaGroup.group4: return 4;
  }
}

NovaGroup _intToNovaGroup(int n) {
  switch (n) {
    case 1: return NovaGroup.group1;
    case 2: return NovaGroup.group2;
    case 3: return NovaGroup.group3;
    default: return NovaGroup.group4;
  }
}
