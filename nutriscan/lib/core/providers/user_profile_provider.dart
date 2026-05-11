import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../database/app_database.dart';
import '../database/tables.dart';
import '../database/user_profile_dao.dart';
import 'scan_history_provider.dart';

// ── DAO provider ─────────────────────────────────────────────────────────────

final userProfileDaoProvider = Provider<UserProfileDao>((ref) {
  return ref.watch(databaseProvider).userProfileDao;
});

// ── Typed profile model ───────────────────────────────────────────────────────

class UserProfile {
  final String displayName;
  final Set<String> allergies;
  final Set<String> conditions;
  final Set<String> goals;

  const UserProfile({
    this.displayName = '',
    this.allergies = const {},
    this.conditions = const {},
    this.goals = const {},
  });

  UserProfile copyWith({
    String? displayName,
    Set<String>? allergies,
    Set<String>? conditions,
    Set<String>? goals,
  }) {
    return UserProfile(
      displayName: displayName ?? this.displayName,
      allergies: allergies ?? this.allergies,
      conditions: conditions ?? this.conditions,
      goals: goals ?? this.goals,
    );
  }

  factory UserProfile.fromRow(UserProfileTableData row) {
    return UserProfile(
      displayName: row.displayName,
      allergies: Set<String>.from(jsonDecode(row.allergiesJson) as List),
      conditions: Set<String>.from(jsonDecode(row.conditionsJson) as List),
      goals: Set<String>.from(jsonDecode(row.goalsJson) as List),
    );
  }
}

// ── StateNotifier ─────────────────────────────────────────────────────────────

class UserProfileNotifier extends StateNotifier<AsyncValue<UserProfile>> {
  final UserProfileDao _dao;

  UserProfileNotifier(this._dao) : super(const AsyncValue.loading()) {
    _load();
  }

  Future<void> _load() async {
    try {
      final row = await _dao.getProfile();
      state = AsyncValue.data(
        row != null ? UserProfile.fromRow(row) : const UserProfile(),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> save(UserProfile profile) async {
    await _dao.saveProfile(UserProfileTableCompanion.insert(
      displayName: Value(profile.displayName),
      allergiesJson: Value(jsonEncode(profile.allergies.toList())),
      conditionsJson: Value(jsonEncode(profile.conditions.toList())),
      goalsJson: Value(jsonEncode(profile.goals.toList())),
    ));
    state = AsyncValue.data(profile);
  }

  void toggleAllergy(String item) {
    final current = state.value ?? const UserProfile();
    final updated = Set<String>.from(current.allergies);
    updated.contains(item) ? updated.remove(item) : updated.add(item);
    state = AsyncValue.data(current.copyWith(allergies: updated));
  }

  void toggleCondition(String item) {
    final current = state.value ?? const UserProfile();
    final updated = Set<String>.from(current.conditions);
    updated.contains(item) ? updated.remove(item) : updated.add(item);
    state = AsyncValue.data(current.copyWith(conditions: updated));
  }

  void toggleGoal(String item) {
    final current = state.value ?? const UserProfile();
    final updated = Set<String>.from(current.goals);
    updated.contains(item) ? updated.remove(item) : updated.add(item);
    state = AsyncValue.data(current.copyWith(goals: updated));
  }

  void setName(String name) {
    final current = state.value ?? const UserProfile();
    state = AsyncValue.data(current.copyWith(displayName: name));
  }
}

final userProfileProvider =
    StateNotifierProvider<UserProfileNotifier, AsyncValue<UserProfile>>((ref) {
  return UserProfileNotifier(ref.watch(userProfileDaoProvider));
});
