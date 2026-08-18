import 'dart:convert';
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/services/api_service.dart';
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
      final user = FirebaseAuth.instance.currentUser;
      UserProfile profile = const UserProfile();

      // Try local first
      final row = await _dao.getProfile();
      if (row != null) {
        profile = UserProfile.fromRow(row);
      }

      // If auth, sync from cloud
      if (user != null) {
        try {
          final apiService = ApiService();
          final data = await apiService.getUserProfile();
          if (data != null) {
            profile = UserProfile(
              displayName: data['displayName'] ?? profile.displayName,
              allergies: Set<String>.from((data['allergies'] as List?) ?? []),
              conditions: Set<String>.from((data['conditions'] as List?) ?? []),
              goals: Set<String>.from((data['goals'] as List?) ?? []),
            );
            // Update local with cloud data
            await _dao.saveProfile(UserProfileTableCompanion.insert(
              displayName: Value(profile.displayName),
              allergiesJson: Value(jsonEncode(profile.allergies.toList())),
              conditionsJson: Value(jsonEncode(profile.conditions.toList())),
              goalsJson: Value(jsonEncode(profile.goals.toList())),
              isSynced: const Value(true),
            ));
          } else if (row != null && !row.isSynced) {
            // Push local to cloud
            final success = await apiService.patchUserProfile({
              'allergies': profile.allergies.toList(),
              'conditions': profile.conditions.toList(),
              'goals': profile.goals.toList(),
            });
            if (success) {
               await _dao.saveProfile(UserProfileTableCompanion.insert(
                 displayName: Value(profile.displayName),
                 allergiesJson: Value(jsonEncode(profile.allergies.toList())),
                 conditionsJson: Value(jsonEncode(profile.conditions.toList())),
                 goalsJson: Value(jsonEncode(profile.goals.toList())),
                 isSynced: const Value(true),
               ));
            }
          }
        } catch (e) {
          print('Cloud sync failed, falling back to local: $e');
          // We intentionally catch this so the profile screen doesn't break.
          // The local 'profile' variable loaded above will be used instead.
        }
      }

      state = AsyncValue.data(profile);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> save(UserProfile profile) async {
    // Update state optimistically *before* the DB write so the UI
    // immediately reflects the new values regardless of DB timing.
    // This also ensures the screen stays in the data() branch even if
    // the DB write fails — the in-memory state is correct; the only
    // loss is on-disk persistence (which we log below).
    state = AsyncValue.data(profile);

    try {
      // Save locally
      await _dao.saveProfile(UserProfileTableCompanion.insert(
        displayName: Value(profile.displayName),
        allergiesJson: Value(jsonEncode(profile.allergies.toList())),
        conditionsJson: Value(jsonEncode(profile.conditions.toList())),
        goalsJson: Value(jsonEncode(profile.goals.toList())),
        isSynced: const Value(false),
      ));
    } catch (e) {
      // DB write failed (schema mismatch, constraint violation, etc.).
      // State is already updated optimistically above, so the UI stays
      // consistent. Log and continue — the profile is correct in memory.
      debugPrint('UserProfileNotifier.save() DB write failed: $e');
      return;
    }

    // Sync to cloud if authenticated
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      try {
        final apiService = ApiService();
        final success = await apiService.patchUserProfile({
          'allergies': profile.allergies.toList(),
          'conditions': profile.conditions.toList(),
          'goals': profile.goals.toList(),
        });

        if (success) {
          await _dao.saveProfile(UserProfileTableCompanion.insert(
            displayName: Value(profile.displayName),
            allergiesJson: Value(jsonEncode(profile.allergies.toList())),
            conditionsJson: Value(jsonEncode(profile.conditions.toList())),
            goalsJson: Value(jsonEncode(profile.goals.toList())),
            isSynced: const Value(true),
          ));
        }
      } catch (e) {
        // Cloud sync is best-effort — a network failure or missing backend
        // in CI must not surface as an unhandled exception in the screen.
        debugPrint('UserProfileNotifier cloud sync failed (non-fatal): $e');
      }
    }
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
