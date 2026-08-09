import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../core/config/app_config.dart';
import '../../features/scanner/models/scan_result_model.dart';
import '../../core/services/safety_score_service.dart';

class ApiService {
  final Dio _dio;

  ApiService() : _dio = Dio(BaseOptions(
    baseUrl: AppConfig.apiBaseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final user = FirebaseAuth.instance.currentUser;
        if (user != null) {
          try {
            final token = await user.getIdToken();
            if (token != null) {
              options.headers['Authorization'] = 'Bearer $token';
            }
          } catch (e) {
            print('Error getting Firebase token: $e');
          }
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) async {
        if (e.response?.statusCode == 401 && e.requestOptions.extra['retried'] != true) {
          e.requestOptions.extra['retried'] = true;
          
          final user = FirebaseAuth.instance.currentUser;
          if (user != null) {
            try {
              // Force token refresh
              final newToken = await user.getIdToken(true);
              if (newToken != null) {
                // Update header
                e.requestOptions.headers['Authorization'] = 'Bearer $newToken';
                // Retry request
                final response = await _dio.fetch(e.requestOptions);
                return handler.resolve(response);
              }
            } catch (refreshError) {
              // If token refresh fails, reject with clear message
              return handler.reject(DioException(
                requestOptions: e.requestOptions,
                error: 'Authentication expired. Please sign in again.',
                type: DioExceptionType.badResponse,
              ));
            }
          }
        }
        // Surface the error clearly if not handled above or if it still fails after retry
        if (e.response?.statusCode == 401) {
           return handler.reject(DioException(
            requestOptions: e.requestOptions,
            error: 'Authentication failed.',
            type: DioExceptionType.badResponse,
          ));
        }
        return handler.next(e);
      },
    ));
  }

  /// Analyze ingredients using the backend engine
  Future<ScanResult?> analyseIngredients(List<String> ingredients, String? userId) async {
    try {
      final response = await _dio.post('/scan/analyse', data: {
        'ingredients': ingredients,
        'user_id': userId,
      });

      if (response.statusCode == 200) {
        final data = response.data;
        return _mapToScanResult(data);
      }
    } catch (e) {
      print('Cloud Analysis Error: $e');
    }
    return null;
  }

  /// Lookup product by barcode via backend
  Future<ScanResult?> lookupBarcode(String barcode, String? userId) async {
    try {
      final response = await _dio.post('/scan/barcode', data: {
        'barcode': barcode,
        'user_id': userId,
      });

      if (response.statusCode == 200) {
        final data = response.data;
        return _mapToScanResult(data, isBarcode: true);
      }
    } catch (e) {
      print('Cloud Barcode Error: $e');
    }
    return null;
  }

  ScanResult _mapToScanResult(Map<String, dynamic> data, {bool isBarcode = false}) {
    // Map backend response back to Flutter ScanResult model
    final List<dynamic> rawIngredients = data['ingredients'] ?? [];
    final List<IngredientItem> ingredients = rawIngredients.map((i) => IngredientItem(
      name: i['name'],
      isFlagged: i['status'] != 'safe',
      flagReason: i['reason'],
    )).toList();

    final breakdownData = data['breakdown'];
    final breakdown = SafetyScoreBreakdown(
      allergenDeduction: (breakdownData['allergenDeduction'] as num).toDouble(),
      novaDeduction: (breakdownData['novaDeduction'] as num).toDouble(),
      additiveDeduction: (breakdownData['additiveDeduction'] as num).toDouble(),
      conditionDeduction: (breakdownData['conditionDeduction'] as num).toDouble(),
      nutrientDeduction: (breakdownData['nutrientDeduction'] as num?)?.toDouble() ?? 0.0,
      finalScore: data['safety_score'],
    );

    final nutrientsData = data['nutrients'] ?? {};
    final nutrients = <NutrientInfo>[];
    if (isBarcode) {
      // Map basic nutrients if available from OFF data in backend
      nutrients.add(NutrientInfo(
        name: 'Calories', 
        value: nutrientsData['energy-kcal_100g']?.toString() ?? '—', 
        unit: 'kcal', 
        level: _getLevel(nutrientsData['energy-kcal_100g'], 'cal')
      ));
      nutrients.add(NutrientInfo(
        name: 'Sugar', 
        value: nutrientsData['sugars_100g']?.toString() ?? '—', 
        unit: 'g', 
        level: _getLevel(nutrientsData['sugars_100g'], 'sugar')
      ));
      nutrients.add(NutrientInfo(
        name: 'Fat', 
        value: nutrientsData['fat_100g']?.toString() ?? '—', 
        unit: 'g', 
        level: _getLevel(nutrientsData['fat_100g'], 'fat')
      ));
      nutrients.add(NutrientInfo(
        name: 'Sodium', 
        // Some OFF results provide sodium in g, some mg, we just use sodium_100g or salt_100g / 2.5
        value: (nutrientsData['sodium_100g'] != null ? (double.parse(nutrientsData['sodium_100g'].toString()) * 1000).toStringAsFixed(0) : '—'), 
        unit: 'mg', 
        level: _getLevel(nutrientsData['sodium_100g'] != null ? double.parse(nutrientsData['sodium_100g'].toString()) * 1000 : null, 'sodium')
      ));
    }

    return ScanResult(
      productName: data['product_name'] ?? (isBarcode ? 'Product' : 'Scanned Label'),
      brand: data['brand'] ?? 'Unknown',
      healthScore: data['safety_score'],
      novaGroup: _mapNova(data['nova_class']),
      nutrients: nutrients,
      ingredients: ingredients,
      alternatives: [], // Backend will provide this in future phases
      breakdown: breakdown,
    );
  }

  NutritionLevel _getLevel(dynamic value, String type) {
    if (value == null) return NutritionLevel.unknown;
    final v = double.tryParse(value.toString()) ?? 0;
    if (type == 'sugar') return v > 15 ? NutritionLevel.poor : (v > 5 ? NutritionLevel.moderate : NutritionLevel.good);
    if (type == 'fat') return v > 20 ? NutritionLevel.poor : (v > 3 ? NutritionLevel.moderate : NutritionLevel.good);
    if (type == 'sodium') return v > 500 ? NutritionLevel.poor : (v > 120 ? NutritionLevel.moderate : NutritionLevel.good);
    return NutritionLevel.moderate;
  }

  NovaGroup _mapNova(int? group) {
    switch (group) {
      case 1: return NovaGroup.group1;
      case 2: return NovaGroup.group2;
      case 3: return NovaGroup.group3;
      case 4: return NovaGroup.group4;
      default: return NovaGroup.group4;
    }
  }

  // ── User Profile Endpoints ───────────────────────────────────────────────────

  Future<Map<String, dynamic>?> getUserProfile() async {
    try {
      final response = await _dio.get('/users/me');
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print('Cloud Get Profile Error: $e');
    }
    return null;
  }

  Future<bool> patchUserProfile(Map<String, dynamic> data) async {
    try {
      final response = await _dio.patch('/users/me', data: data);
      return response.statusCode == 200;
    } catch (e) {
      print('Cloud Patch Profile Error: $e');
      return false;
    }
  }

  // ── Scan History Endpoints ───────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>?> getScanHistory({int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/history', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(response.data);
      }
    } catch (e) {
      print('Cloud Get History Error: $e');
    }
    return null;
  }

  Future<bool> deleteScanHistoryItem(String id) async {
    try {
      final response = await _dio.delete('/history/$id');
      return response.statusCode == 204 || response.statusCode == 200;
    } catch (e) {
      print('Cloud Delete History Error: $e');
      return false;
    }
  }

  Future<bool> postScanHistory(Map<String, dynamic> scanData) async {
    try {
      final response = await _dio.post('/history', data: scanData);
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print('Cloud Post History Error: $e');
      return false;
    }
  }
}
