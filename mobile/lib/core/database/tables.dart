import 'package:drift/drift.dart';

/// One row per product scan.
class ScanHistoryTable extends Table {
  TextColumn get id => text()();
  TextColumn get productName => text()();
  TextColumn get brand => text()();
  IntColumn get healthScore => integer()();
  IntColumn get novaGroup => integer()(); // 1–4
  TextColumn get nutrientsJson => text()(); // JSON encoded
  TextColumn get ingredientsJson => text()(); // JSON encoded
  TextColumn get alternativesJson => text()(); // JSON encoded
  DateTimeColumn get scannedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Single-row table — user's health profile.
class UserProfileTable extends Table {
  // Always row id = 1 (singleton)
  IntColumn get id => integer().withDefault(const Constant(1))();
  TextColumn get displayName => text().withDefault(const Constant(''))();
  TextColumn get allergiesJson => text().withDefault(const Constant('[]'))();
  TextColumn get conditionsJson => text().withDefault(const Constant('[]'))();
  TextColumn get goalsJson => text().withDefault(const Constant('[]'))();

  @override
  Set<Column> get primaryKey => {id};
}
