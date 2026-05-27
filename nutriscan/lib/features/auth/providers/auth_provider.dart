import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/providers/scan_history_provider.dart';
import '../../../core/providers/user_profile_provider.dart';

enum AuthStatus { loading, authenticated, guest, unauthenticated }

class AuthState {
  final AuthStatus status;
  final User? user;

  const AuthState({
    required this.status,
    this.user,
  });
}

class AuthNotifier extends AsyncNotifier<AuthState> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  @override
  Future<AuthState> build() async {
    final prefs = await SharedPreferences.getInstance();
    final isGuest = prefs.getBool('is_guest') ?? false;

    // Listen to auth state changes to keep token refreshed
    _auth.idTokenChanges().listen((user) async {
      if (user != null) {
        final token = await user.getIdToken();
        await prefs.setString('auth_token', token ?? '');
      } else {
        await prefs.remove('auth_token');
      }
    });

    final currentUser = _auth.currentUser;
    if (currentUser != null) {
      return AuthState(status: AuthStatus.authenticated, user: currentUser);
    } else if (isGuest) {
      return const AuthState(status: AuthStatus.guest);
    } else {
      return const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> signInWithGoogle() async {
    state = const AsyncValue.loading();
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        state = await AsyncValue.guard(() => build());
        return; // User canceled
      }

      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      final AuthCredential credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('is_guest', false);

      // Sync local scans to cloud
      await syncScansWithCloud(ref);
      
      // Reload profile from cloud
      ref.invalidate(userProfileProvider);

      state = AsyncValue.data(AuthState(
        status: AuthStatus.authenticated,
        user: userCredential.user,
      ));
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      // Revert to initial state
      state = await AsyncValue.guard(() => build());
    }
  }

  Future<void> signInWithEmail(String email) async {
    // Send passwordless sign-in link
    try {
      var acs = ActionCodeSettings(
        url: 'https://nutriscan.app/finishSignUp',
        handleCodeInApp: true,
        androidPackageName: 'com.example.nutriscan_ai',
        androidInstallApp: true,
        androidMinimumVersion: '12',
      );
      await _auth.sendSignInLinkToEmail(
        email: email,
        actionCodeSettings: acs,
      );
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('email_for_sign_in', email);
    } catch (e) {
      print('Email sign in error: $e');
      rethrow;
    }
  }

  Future<void> continueAsGuest() async {
    state = const AsyncValue.loading();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('is_guest', true);
    state = const AsyncValue.data(AuthState(status: AuthStatus.guest));
  }

  Future<void> signOut() async {
    state = const AsyncValue.loading();
    await _auth.signOut();
    await _googleSignIn.signOut();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('is_guest', false);
    state = const AsyncValue.data(AuthState(status: AuthStatus.unauthenticated));
  }
}

final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(() {
  return AuthNotifier();
});
