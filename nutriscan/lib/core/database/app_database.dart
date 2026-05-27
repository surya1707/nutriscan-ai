import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'tables.dart';
import 'scan_history_dao.dart';
import 'user_profile_dao.dart';

import 'connection.dart' as impl;

part 'app_database.g.dart';

@DriftDatabase(
  tables: [ScanHistoryTable, UserProfileTable],
  daos: [ScanHistoryDao, UserProfileDao],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(impl.openConnection());

  @override
  int get schemaVersion => 1;
}
