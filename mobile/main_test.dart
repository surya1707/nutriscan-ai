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

  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  final db = AppDatabase();

  runApp(
    ProviderScope(
      overrides: [
        databaseProvider.overrideWithValue(db),
      ],
      child: const _NutriScanTestApp(),
    ),
  );
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
