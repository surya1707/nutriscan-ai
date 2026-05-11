import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/history/screens/history_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/scanner/screens/scanner_screen.dart';
import '../../features/scanner/screens/results_screen.dart';
import '../../features/scanner/models/scan_result_model.dart';
import '../../shared/widgets/main_shell.dart';

final router = GoRouter(
  initialLocation: '/',
  routes: [
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
