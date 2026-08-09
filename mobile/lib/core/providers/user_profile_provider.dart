import 'dart:convert';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
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
          final doc = await FirebaseFirestore.instance.collection('users').doc(user.uid).get(const GetOptions(source: Source.serverAndCache)).timeout(const Duration(seconds: 5));
          if (doc.exists) {
            final data = doc.data()!;
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
            ));
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
    // Save locally
    await _dao.saveProfile(UserProfileTableCompanion.insert(
      displayName: Value(profile.displayName),
      allergiesJson: Value(jsonEncode(profile.allergies.toList())),
      conditionsJson: Value(jsonEncode(profile.conditions.toList())),
      goalsJson: Value(jsonEncode(profile.goals.toList())),
    ));

    // Sync to cloud if authenticated
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      try {
        await FirebaseFirestore.instance.collection('users').doc(user.uid).set({
          'displayName': profile.displayName,
          'allergies': profile.allergies.toList(),
          'conditions': profile.conditions.toList(),
          'goals': profile.goals.toList(),
        }, SetOptions(merge: true)).timeout(const Duration(seconds: 5));
      } catch (e) {
        print('Warning: Failed to sync profile to cloud: $e');
      }
    }

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
