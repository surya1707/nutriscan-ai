class AppConfig {
  /// Base URL for the FastAPI backend.
  /// Use --dart-define=API_URL=https://your-api.com to override.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://192.168.29.217:8000', // Updated to match your new Wi-Fi IP
  );

  /// Toggle for cloud-based analysis. 
  /// If false, the app always uses the local heuristics.
  static const bool enableCloudAnalysis = bool.fromEnvironment(
    'ENABLE_CLOUD',
    defaultValue: true,
  );

  static bool get isProduction => const bool.fromEnvironment('dart.vm.product');
}
