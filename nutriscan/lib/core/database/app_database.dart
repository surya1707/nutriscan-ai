import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'tables.dart';
import 'scan_history_dao.dart';
import 'user_profile_dao.dart';

part 'app_database.g.dart';

@DriftDatabase(
  tables: [ScanHistoryTable, UserProfileTable],
  daos: [ScanHistoryDao, UserProfileDao],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'nutriscan.db'));
    return NativeDatabase.createInBackground(file);
  });
}
