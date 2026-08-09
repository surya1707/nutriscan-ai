import 'package:drift/drift.dart';
import 'app_database.dart';
import 'tables.dart';

part 'user_profile_dao.g.dart';

@DriftAccessor(tables: [UserProfileTable])
class UserProfileDao extends DatabaseAccessor<AppDatabase>
    with _$UserProfileDaoMixin {
  UserProfileDao(super.db);

  /// Watch the singleton profile row (id = 1).
  Stream<UserProfileTableData?> watchProfile() =>
      (select(userProfileTable)..where((t) => t.id.equals(1)))
          .watchSingleOrNull();

  /// Get the profile once (returns null if not set yet).
  Future<UserProfileTableData?> getProfile() =>
      (select(userProfileTable)..where((t) => t.id.equals(1)))
          .getSingleOrNull();

  /// Save / overwrite the profile.
  Future<void> saveProfile(UserProfileTableCompanion profile) =>
      into(userProfileTable).insertOnConflictUpdate(
        profile.copyWith(id: const Value(1)),
      );
}
