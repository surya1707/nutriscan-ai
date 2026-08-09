import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/services/api_service.dart';
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

/// Saves a [ScanResult] to the database and cloud if authenticated.
Future<void> saveScanResult(WidgetRef ref, ScanResult result) async {
  final dao = ref.read(scanHistoryDaoProvider);
  
  final companion = ScanHistoryTableCompanion.insert(
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
    isSynced: const Value(false),
  );
  
  await dao.upsertScan(companion);

  // Sync to cloud
  final user = FirebaseAuth.instance.currentUser;
  if (user != null) {
    final apiService = ApiService();
    final success = await apiService.postScanHistory({
      'id': result.id,
      'product_name': result.productName,
      'brand': result.brand,
      'health_score': result.healthScore,
      'nova_group': _novaGroupToInt(result.novaGroup),
      'nutrients': jsonDecode(companion.nutrientsJson.value),
      'ingredients': jsonDecode(companion.ingredientsJson.value),
      'alternatives': jsonDecode(companion.alternativesJson.value),
      'scanned_at': companion.scannedAt.value.toIso8601String(),
    });
    
    if (success) {
      await dao.upsertScan(companion.copyWith(isSynced: const Value(true)));
    }
  }
}

Future<void> deleteScanById(WidgetRef ref, String id) async {
  await ref.read(scanHistoryDaoProvider).deleteScan(id);
  
  final user = FirebaseAuth.instance.currentUser;
  if (user != null) {
    final apiService = ApiService();
    await apiService.deleteScanHistoryItem(id);
  }
}

/// Merges local guest scans into cloud history, and pulls cloud scans down.
Future<void> syncScansWithCloud(Ref ref) async {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) return;

  final dao = ref.read(scanHistoryDaoProvider);
  final localScans = await dao.getAll();
  final apiService = ApiService();

  // Push unsynced local to cloud
  for (final scan in localScans) {
    if (!scan.isSynced) {
      final success = await apiService.postScanHistory({
        'id': scan.id,
        'product_name': scan.productName,
        'brand': scan.brand,
        'health_score': scan.healthScore,
        'nova_group': scan.novaGroup,
        'nutrients': jsonDecode(scan.nutrientsJson),
        'ingredients': jsonDecode(scan.ingredientsJson),
        'alternatives': jsonDecode(scan.alternativesJson),
        'scanned_at': scan.scannedAt.toIso8601String(),
      });
      if (success) {
        await dao.upsertScan(ScanHistoryTableCompanion.insert(
          id: scan.id,
          productName: scan.productName,
          brand: scan.brand,
          healthScore: scan.healthScore,
          novaGroup: scan.novaGroup,
          nutrientsJson: scan.nutrientsJson,
          ingredientsJson: scan.ingredientsJson,
          alternativesJson: scan.alternativesJson,
          scannedAt: scan.scannedAt,
          isSynced: const Value(true),
        ));
      }
    }
  }

  // Pull cloud to local
  final cloudScans = await apiService.getScanHistory(limit: 100);
  if (cloudScans != null) {
    for (final data in cloudScans) {
      await dao.upsertScan(ScanHistoryTableCompanion.insert(
        id: data['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(),
        productName: data['product_name'] ?? 'Unknown',
        brand: data['brand'] ?? '',
        healthScore: data['health_score'] ?? data['safety_score'] ?? 0,
        novaGroup: data['nova_group'] ?? data['nova_class'] ?? 4,
        nutrientsJson: jsonEncode(data['nutrients'] ?? []),
        ingredientsJson: jsonEncode(data['ingredients'] ?? []),
        alternativesJson: jsonEncode(data['alternatives'] ?? []),
        scannedAt: data['scanned_at'] != null ? DateTime.parse(data['scanned_at']) : DateTime.now(),
        isSynced: const Value(true),
      ));
    }
  }
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
