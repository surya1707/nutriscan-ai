import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/scanner/models/scan_result_model.dart';
import '../services/open_food_facts_service.dart';

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
  ScanNotifier() : super(const ScanState());

  bool _processing = false;

  /// Called by mobile_scanner when a barcode is detected.
  Future<void> onBarcodeDetected(String barcode) async {
    // Debounce: skip if same barcode or already processing
    if (_processing || barcode == state.lastBarcode) return;
    _processing = true;

    state = ScanState(
      status: ScanStatus.loading,
      lastBarcode: barcode,
    );

    final result = await fetchProductByBarcode(barcode);

    if (result != null) {
      state = ScanState(
        status: ScanStatus.found,
        result: result,
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
  void onOcrResult(ScanResult result) {
    state = ScanState(
      status: ScanStatus.found,
      result: result,
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
  return ScanNotifier();
});
