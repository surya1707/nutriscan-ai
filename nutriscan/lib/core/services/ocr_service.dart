import 'dart:io';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import '../../features/scanner/models/scan_result_model.dart';
import 'open_food_facts_service.dart';

/// Runs ML Kit OCR on [imageFile] and extracts a [ScanResult] from the
/// recognised ingredient text.
Future<ScanResult?> extractFromLabelImage(File imageFile) async {
  final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
  try {
    final inputImage = InputImage.fromFile(imageFile);
    final recognised = await recognizer.processImage(inputImage);
    final text = recognised.text;
    if (text.trim().isEmpty) return null;
    return _buildResultFromOcrText(text);
  } finally {
    recognizer.close();
  }
}

/// Builds a [ScanResult] directly from raw OCR text.
ScanResult _buildResultFromOcrText(String text) {
  // Find the ingredient section (look for keyword)
  final lower = text.toLowerCase();
  String ingredientText = text;

  final markers = ['ingredients:', 'ingredients :', 'contains:'];
  for (final marker in markers) {
    final idx = lower.indexOf(marker);
    if (idx != -1) {
      ingredientText = text.substring(idx + marker.length);
      break;
    }
  }

  // Trim at known section endings
  final endings = ['nutrition facts', 'serving size', 'allergen', 'best before', 'manufactured'];
  for (final ending in endings) {
    final idx = ingredientText.toLowerCase().indexOf(ending);
    if (idx != -1) {
      ingredientText = ingredientText.substring(0, idx);
    }
  }

  ingredientText = ingredientText.trim();

  // Parse using the same shared parser from OFF service
  final ingredients = _parseIngredients(ingredientText);

  // Estimate NOVA group from ingredient list heuristics
  final nova = _estimateNova(ingredients);

  // Build score with empty nutriments (OCR can't get exact numbers)
  final score = _estimateScoreFromIngredients(ingredients, nova);

  return ScanResult(
    productName: _extractProductName(text),
    brand: _extractBrand(text),
    healthScore: score,
    novaGroup: nova,
    nutrients: const [
      NutrientInfo(name: 'Calories', value: '—', unit: 'kcal', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Sugar', value: '—', unit: 'g', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Fat', value: '—', unit: 'g', level: NutritionLevel.moderate),
      NutrientInfo(name: 'Sodium', value: '—', unit: 'mg', level: NutritionLevel.moderate),
    ],
    ingredients: ingredients,
    alternatives: const [],
  );
}

String _extractProductName(String text) {
  // The product name is usually the first non-empty line in large text
  final lines = text.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
  if (lines.isEmpty) return 'Scanned Product';
  // Prefer lines that look like a name (not all-caps ingredient lists)
  for (final line in lines.take(5)) {
    if (line.length > 3 && line.length < 60 && !line.contains(',')) {
      return line;
    }
  }
  return lines.first;
}

String _extractBrand(String text) {
  // Look for common brand indicators
  final brandRegex = RegExp(r'(?:brand|by|made by|manufactured by)[:\s]+([A-Za-z\s]+)', caseSensitive: false);
  final match = brandRegex.firstMatch(text);
  return match?.group(1)?.trim() ?? 'Scanned Label';
}

List<IngredientItem> _parseIngredients(String raw) {
  if (raw.trim().isEmpty) return [];

  final cleaned = raw
      .replaceAll(RegExp(r'<[^>]+>'), '')
      .replaceAll(RegExp(r'\([^)]*%[^)]*\)'), '')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  final parts = cleaned
      .split(RegExp(r'[,;]'))
      .map((s) => s.trim())
      .where((s) => s.isNotEmpty && s.length > 1)
      .toList();

  const flaggedAdditives = _flaggedAdditives;

  return parts.map((ingredient) {
    final lower = ingredient.toLowerCase();
    String? flagReason;
    for (final entry in flaggedAdditives.entries) {
      if (lower.contains(entry.key)) {
        flagReason = entry.value;
        break;
      }
    }
    return IngredientItem(
      name: ingredient,
      isFlagged: flagReason != null,
      flagReason: flagReason,
    );
  }).toList();
}

/// Heuristic NOVA estimate based on presence of ultra-processed markers.
NovaGroup _estimateNova(List<IngredientItem> ingredients) {
  final allNames = ingredients.map((i) => i.name.toLowerCase()).join(' ');

  const ultraProcessedMarkers = [
    'syrup', 'artificial flavor', 'colour', 'color', 'modified starch',
    'emulsifier', 'preservative', 'sweetener', 'hydrolysed', 'interesterified'
  ];

  int markerCount = 0;
  for (final m in ultraProcessedMarkers) {
    if (allNames.contains(m)) markerCount++;
  }

  if (markerCount >= 3 || ingredients.where((i) => i.isFlagged).length >= 2) {
    return NovaGroup.group4;
  }
  if (markerCount >= 1) return NovaGroup.group3;
  if (ingredients.length > 5) return NovaGroup.group2;
  return NovaGroup.group1;
}

int _estimateScoreFromIngredients(List<IngredientItem> ingredients, NovaGroup nova) {
  double score = 85;
  switch (nova) {
    case NovaGroup.group1: break;
    case NovaGroup.group2: score -= 5; break;
    case NovaGroup.group3: score -= 15; break;
    case NovaGroup.group4: score -= 30; break;
  }
  final flagged = ingredients.where((i) => i.isFlagged).length;
  score -= (flagged * 8).clamp(0, 25).toDouble();
  return score.round().clamp(0, 100);
}

/// Re-export the flagged additives map for the OCR parser.
const Map<String, String> _flaggedAdditives = {
  'high-fructose corn syrup': 'Linked to metabolic disorders',
  'hfcs': 'High-fructose corn syrup — metabolic risk',
  'partially hydrogenated': 'Contains trans fats — cardiovascular risk',
  'hydrogenated vegetable oil': 'Trans fat source',
  'sodium benzoate': 'Artificial preservative — avoid in excess',
  'potassium bromate': 'Banned in many countries — potential carcinogen',
  'aspartame': 'Artificial sweetener — controversial safety profile',
  'acesulfame': 'Artificial sweetener',
  'saccharin': 'Artificial sweetener',
  'red 40': 'Synthetic dye — linked to hyperactivity',
  'yellow 5': 'Synthetic dye',
  'yellow 6': 'Synthetic dye',
  'blue 1': 'Synthetic dye',
  'carrageenan': 'May cause gut inflammation',
  'monosodium glutamate': 'Flavor enhancer — sensitivity concerns',
  'msg': 'Monosodium glutamate — sensitivity concerns',
  'bha': 'Butylated hydroxyanisole — potential endocrine disruptor',
  'bht': 'Butylated hydroxytoluene — potential endocrine disruptor',
  'sodium nitrate': 'Processed meat preservative — carcinogenic risk',
  'sodium nitrite': 'Processed meat preservative — carcinogenic risk',
  'artificial flavor': 'Synthetic flavoring',
  'artificial flavour': 'Synthetic flavoring',
  'artificial color': 'Synthetic coloring agent',
  'artificial colour': 'Synthetic coloring agent',
};
