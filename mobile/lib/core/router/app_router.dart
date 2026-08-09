import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/history/screens/history_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/scanner/screens/scanner_screen.dart';
import '../../features/scanner/screens/results_screen.dart';
import '../../features/scanner/models/scan_result_model.dart';
import '../../features/auth/screens/auth_screen.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../shared/widgets/main_shell.dart';

final routerProvider = Provider<GoRouter>((ref) {
  // Listen to auth state changes to trigger a router refresh
  ref.listen(authProvider, (previous, next) {
    if (previous?.value?.status != next.value?.status) {
      ref.read(goRouterInstanceProvider).refresh();
    }
  });

  return ref.read(goRouterInstanceProvider);
});

final goRouterInstanceProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      if (authState.isLoading) return null;
      
      final isAuthScreen = state.uri.path == '/auth';
      final status = authState.value?.status;

      if (status == AuthStatus.unauthenticated && !isAuthScreen) {
        return '/auth';
      }

      if ((status == AuthStatus.authenticated || status == AuthStatus.guest) && isAuthScreen) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(path: '/auth', builder: (c, s) => const AuthScreen()),
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/', builder: (c, s) => const HomeScreen()),
          GoRoute(path: '/history', builder: (c, s) => const HistoryScreen()),
          GoRoute(path: '/profile', builder: (c, s) => const ProfileScreen()),
        ],
      ),
      GoRoute(path: '/scanner', builder: (c, s) => const ScannerScreen()),
      GoRoute(
        path: '/results',
        builder: (c, s) {
          final result = s.extra as ScanResult?;
          return ResultsScreen(result: result);
        },
      ),
    ],
  );
});
