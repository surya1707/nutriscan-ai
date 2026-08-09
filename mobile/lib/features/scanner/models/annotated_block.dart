import 'dart:ui';
import '../../../core/theme/app_theme.dart';

enum IngredientStatus { safe, caution, danger, unknown }

class AnnotatedBlock {
  final Rect boundingBox;
  final String text;
  final IngredientStatus status;

  AnnotatedBlock({
    required this.boundingBox,
    required this.text,
    required this.status,
  });
}
