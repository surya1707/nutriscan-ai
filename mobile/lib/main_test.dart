// TEST-ONLY ENTRYPOINT — not used by the production app.
//
// Built exclusively by the android-e2e CI workflow via:
//   flutter build apk --debug -t lib/main_test.dart
//
// enableFlutterDriverExtension() must run BEFORE the real app so the
// appium-flutter-driver Dart VM Service handshake succeeds. Everything
// after that point is the unmodified production widget tree from
// main.dart — lib/main.dart itself is never imported here in a way
// that changes its behaviour, and is not edited by this file.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_driver/driver_extension.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'core/database/app_database.dart';
import 'core/providers/scan_history_provider.dart';

void main() async {
  enableFlutterDriverExtension();

  // Cold-start timing diagnostics — grep CI logcat for NUTRISCAN_TIMING to
  // understand which phase owns the ~15 s Dart VM Observatory dead zone seen
  // after every adb relaunch+reconnect in the E2E suite.
  // Usage: adb logcat -d | grep NUTRISCAN_TIMING
  final _t0 = DateTime.now().millisecondsSinceEpoch;
  debugPrint('[NUTRISCAN_TIMING] main() start: 0 ms');

  WidgetsFlutterBinding.ensureInitialized();
  debugPrint('[NUTRISCAN_TIMING] WidgetsFlutterBinding done: ${DateTime.now().millisecondsSinceEpoch - _t0} ms');

  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  debugPrint('[NUTRISCAN_TIMING] Firebase.initializeApp done: ${DateTime.now().millisecondsSinceEpoch - _t0} ms');

  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  // AppDatabase() calls openConnection() which wraps NativeDatabase.createInBackground().
  // The background isolate ("Drift isolate worker for .../nutriscan.db") is spawned
  // here and may be contributing to Observatory unresponsiveness during the first ~15 s.
  final db = AppDatabase();
  debugPrint('[NUTRISCAN_TIMING] AppDatabase() constructed (Drift isolate spawned): ${DateTime.now().millisecondsSinceEpoch - _t0} ms');

  runApp(
    ProviderScope(
      overrides: [
        databaseProvider.overrideWithValue(db),
      ],
      child: const _NutriScanTestApp(),
    ),
  );
  debugPrint('[NUTRISCAN_TIMING] runApp() returned: ${DateTime.now().millisecondsSinceEpoch - _t0} ms');
}

// Identical widget tree to NutriScanApp in main.dart. Duplicated (rather
// than imported and reused) so that main.dart never has to import
// anything from this file — keeps the production entrypoint completely
// untouched, per the "never touch main.dart" rule.
class _NutriScanTestApp extends ConsumerWidget {
  const _NutriScanTestApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'NutriScan AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: router,
    );
  }
}
