import 'package:flutter/foundation.dart';

class AppConfig {
  /// Base URL for the FastAPI backend.
  /// Use --dart-define=API_URL=https://your-api.com to override.
  static String get apiBaseUrl {
    const url = String.fromEnvironment(
      'API_URL',
      defaultValue: 'http://localhost:8000',
    );
    if (kReleaseMode && url == 'http://localhost:8000') {
      debugPrint('WARNING: Running in release mode with localhost API_URL default.');
    }
    return url;
  }

  /// Toggle for cloud-based analysis. 
  /// If false, the app always uses the local heuristics.
  static const bool enableCloudAnalysis = bool.fromEnvironment(
    'ENABLE_CLOUD',
    defaultValue: true,
  );

  static bool get isProduction => const bool.fromEnvironment('dart.vm.product');
}
