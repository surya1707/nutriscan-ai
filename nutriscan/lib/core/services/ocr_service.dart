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
  final lower = text.toLowerCase();
  String ingredientText = text;

  // Improved marker detection
  final markers = ['ingredients:', 'ingredients :', 'contains:', 'composition:', 'ingrediënten:'];
  for (final marker in markers) {
    final idx = lower.indexOf(marker);
    if (idx != -1) {
      ingredientText = text.substring(idx + marker.length);
      break;
    }
  }

  // Trim at known section endings
  final endings = ['nutrition facts', 'serving size', 'allergen', 'best before', 'manufactured', 'distrib'];
  for (final ending in endings) {
    final idx = ingredientText.toLowerCase().indexOf(ending);
    if (idx != -1) {
      ingredientText = ingredientText.substring(0, idx);
    }
  }

  ingredientText = ingredientText.trim();
  final ingredients = _parseIngredients(ingredientText);
  final nova = _estimateNova(ingredients);
  final score = _estimateScoreFromIngredients(ingredients, nova);

  return ScanResult(
    productName: _extractProductName(text),
    brand: _extractBrand(text),
    healthScore: score,
    novaGroup: nova,
    nutrients: const [
      NutrientInfo(name: 'Calories', value: '—', unit: 'kcal', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Sugar', value: '—', unit: 'g', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Fat', value: '—', unit: 'g', level: NutritionLevel.unknown),
      NutrientInfo(name: 'Sodium', value: '—', unit: 'mg', level: NutritionLevel.unknown),
    ],
    ingredients: ingredients,
    alternatives: const [],
  );
}

String _extractProductName(String text) {
  final lines = text.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
  if (lines.isEmpty) return 'Scanned Product';
  for (final line in lines.take(5)) {
    // If it's the ingredient line, skip it
    if (line.toLowerCase().contains('ingredients')) continue;
    if (line.length > 3 && line.length < 60 && !line.contains(',')) {
      return line;
    }
  }
  return lines.first;
}

String _extractBrand(String text) {
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

  return parts.map((ingredient) {
    final lower = ingredient.toLowerCase();
    String? flagReason;
    for (final entry in _flaggedAdditives.entries) {
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
    'emulsifier', 'preservative', 'sweetener', 'hydrolysed', 'interesterified',
    'hydrogenated', 'maltodextrin', 'dextrose', 'inverted sugar'
  ];

  int markerCount = 0;
  for (final m in ultraProcessedMarkers) {
    if (allNames.contains(m)) markerCount++;
  }

  // If sugar is present, it's likely at least NOVA 3
  final hasSugar = allNames.contains('sugar') || allNames.contains('syrup');
  final hasOil = allNames.contains('oil') || allNames.contains('fat') && !allNames.contains('roasted peanuts');

  if (markerCount >= 3 || ingredients.where((i) => i.isFlagged).length >= 2) {
    return NovaGroup.group4;
  }
  if (markerCount >= 1 || (hasSugar && hasOil)) return NovaGroup.group3;
  if (ingredients.length > 5 || hasSugar || hasOil) return NovaGroup.group2;
  return NovaGroup.group1;
}

int _estimateScoreFromIngredients(List<IngredientItem> ingredients, NovaGroup nova) {
  double score = 85; // Base score for unprocessed

  // More aggressive deductions for OCR estimations
  switch (nova) {
    case NovaGroup.group1: break;
    case NovaGroup.group2: score -= 10; break;
    case NovaGroup.group3: score -= 25; break;
    case NovaGroup.group4: score -= 45; break;
  }

  final flagged = ingredients.where((i) => i.isFlagged).length;
  score -= (flagged * 10).clamp(0, 30).toDouble();

  // Check if "Sugar" is a top ingredient
  if (ingredients.isNotEmpty) {
    final firstThree = ingredients.take(3).map((i) => i.name.toLowerCase()).join(' ');
    if (firstThree.contains('sugar') || firstThree.contains('syrup')) {
      score -= 15;
    }
  }

  return score.round().clamp(0, 100);
}

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
