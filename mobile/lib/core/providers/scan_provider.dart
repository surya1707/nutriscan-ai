import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/scanner/models/scan_result_model.dart';
import '../services/open_food_facts_service.dart';
import '../services/safety_score_service.dart';
import '../config/app_config.dart';
import '../../data/providers/api_provider.dart';
import 'user_profile_provider.dart';

// ── Scanner scan state ────────────────────────────────────────────────────────

enum ScanStatus { idle, scanning, loading, found, notFound, error }

class ScanState {
  final ScanStatus status;
  final ScanResult? result;
  final String? errorMessage;
  final String? lastBarcode;

  const ScanState({
    this.status = ScanStatus.idle,
    this.result,
    this.errorMessage,
    this.lastBarcode,
  });

  ScanState copyWith({
    ScanStatus? status,
    ScanResult? result,
    String? errorMessage,
    String? lastBarcode,
  }) {
    return ScanState(
      status: status ?? this.status,
      result: result ?? this.result,
      errorMessage: errorMessage ?? this.errorMessage,
      lastBarcode: lastBarcode ?? this.lastBarcode,
    );
  }
}

// ── Notifier ──────────────────────────────────────────────────────────────────

class ScanNotifier extends StateNotifier<ScanState> {
  final Ref _ref;

  ScanNotifier(this._ref) : super(const ScanState());

  bool _processing = false;

  /// Personalises a raw scan result using the current user profile.
  ScanResult _personalise(ScanResult raw) {
    final profileAsync = _ref.read(userProfileProvider);
    final profile = profileAsync.value;
    
    if (profile == null) return raw;

    // Apply personalised flags to ingredients
    final personalisedIngredients = SafetyScoreService.getPersonalisedIngredients(
      ingredients: raw.ingredients,
      profile: profile,
    );

    // Compute personalised safety score
    final breakdown = SafetyScoreService.computePersonalisedScore(
      ingredients: personalisedIngredients,
      nova: raw.novaGroup,
      profile: profile,
      nutrients: raw.nutrients,
    );

    return raw.copyWith(
      ingredients: personalisedIngredients,
      healthScore: breakdown.finalScore,
      breakdown: breakdown,
    );
  }

  /// Called by mobile_scanner when a barcode is detected.
  Future<void> onBarcodeDetected(String barcode) async {
    if (_processing || barcode == state.lastBarcode) return;
    _processing = true;

    state = ScanState(
      status: ScanStatus.loading,
      lastBarcode: barcode,
    );

    ScanResult? result;

    // Check Cloud Analysis
    if (AppConfig.enableCloudAnalysis) {
      final connectivity = await Connectivity().checkConnectivity();
      if (connectivity != ConnectivityResult.none) {
        final api = _ref.read(apiServiceProvider);
        result = await api.lookupBarcode(barcode, null); // Add real user_id if available
        if (result != null) {
          result = result.copyWith(source: AnalysisSource.cloud);
        }
      }
    }

    // Fallback to Local
    if (result == null) {
      result = await fetchProductByBarcode(barcode);
    }

    if (result != null) {
      final personalised = _personalise(result);
      state = ScanState(
        status: ScanStatus.found,
        result: personalised,
        lastBarcode: barcode,
      );
    } else {
      state = ScanState(
        status: ScanStatus.notFound,
        lastBarcode: barcode,
      );
    }

    _processing = false;
  }

  /// Called when OCR text has been extracted from the label image.
  Future<void> onOcrResult(ScanResult localResult) async {
    ScanResult? finalResult;

    // Check Cloud Analysis for ingredients
    if (AppConfig.enableCloudAnalysis) {
      final connectivity = await Connectivity().checkConnectivity();
      if (connectivity != ConnectivityResult.none) {
        final api = _ref.read(apiServiceProvider);
        final ingredientNames = localResult.ingredients.map((i) => i.name).toList();
        finalResult = await api.analyseIngredients(ingredientNames, null);
        if (finalResult != null) {
          finalResult = finalResult.copyWith(
            productName: localResult.productName,
            source: AnalysisSource.cloud,
          );
        }
      }
    }

    // Fallback to local result
    finalResult ??= localResult;

    final personalised = _personalise(finalResult);
    state = ScanState(
      status: ScanStatus.found,
      result: personalised,
    );
  }

  /// Reset so the scanner can detect another product.
  void reset() {
    _processing = false;
    state = const ScanState(status: ScanStatus.idle);
  }

  void setError(String message) {
    _processing = false;
    state = ScanState(status: ScanStatus.error, errorMessage: message);
  }
}

final scanProvider =
    StateNotifierProvider.autoDispose<ScanNotifier, ScanState>((ref) {
  return ScanNotifier(ref);
});
