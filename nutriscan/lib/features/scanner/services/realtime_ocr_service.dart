import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import '../models/annotated_block.dart';

class RealtimeOcrService {
  final TextRecognizer _textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);
  
  Map<String, List<String>> _ingredientDict = {};
  bool _isProcessing = false;
  DateTime _lastRun = DateTime.fromMillisecondsSinceEpoch(0);
  int _frameCount = 0;

  final StreamController<List<AnnotatedBlock>> _outputController = StreamController.broadcast();
  Stream<List<AnnotatedBlock>> get arStream => _outputController.stream;

  Future<void> initialize() async {
    try {
      final jsonStr = await rootBundle.loadString('assets/data/ingredients.json');
      final Map<String, dynamic> parsed = jsonDecode(jsonStr);
      _ingredientDict = {
        'safe': List<String>.from(parsed['safe'] ?? []),
        'caution': List<String>.from(parsed['caution'] ?? []),
        'danger': List<String>.from(parsed['danger'] ?? []),
      };
    } catch (e) {
      debugPrint('Failed to load ingredients dict: $e');
    }
  }

  Future<void> processImage(InputImage image) async {
    _frameCount++;
    // Process every 10th frame roughly, and debounce 300ms
    if (_frameCount % 10 != 0) return;
    
    final now = DateTime.now();
    if (now.difference(_lastRun).inMilliseconds < 300) return;
    if (_isProcessing) return;

    _isProcessing = true;
    _lastRun = now;

    try {
      final RecognizedText recognizedText = await _textRecognizer.processImage(image);
      final List<AnnotatedBlock> blocks = [];

      for (TextBlock block in recognizedText.blocks) {
        final text = block.text.toLowerCase().replaceAll(RegExp(r'[^a-z0-9 ]'), '');
        IngredientStatus status = IngredientStatus.unknown;

        // Check against dictionary
        if (_ingredientDict['danger']!.any((i) => text.contains(i))) {
          status = IngredientStatus.danger;
        } else if (_ingredientDict['caution']!.any((i) => text.contains(i))) {
          status = IngredientStatus.caution;
        } else if (_ingredientDict['safe']!.any((i) => text.contains(i))) {
          status = IngredientStatus.safe;
        }

        if (status != IngredientStatus.unknown) {
          blocks.add(AnnotatedBlock(
            boundingBox: block.boundingBox,
            text: block.text,
            status: status,
          ));
        }
      }

      if (!_outputController.isClosed) {
        _outputController.add(blocks);
      }
    } catch (e) {
      debugPrint('Realtime OCR error: $e');
    } finally {
      _isProcessing = false;
    }
  }

  void dispose() {
    _textRecognizer.close();
    _outputController.close();
  }
}
