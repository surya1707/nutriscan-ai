import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import '../../../core/theme/app_theme.dart';
import '../models/annotated_block.dart';

class AROverlayPainter extends CustomPainter {
  final List<AnnotatedBlock> blocks;
  final Size imageSize;
  final InputImageRotation rotation;

  AROverlayPainter(this.blocks, this.imageSize, this.rotation);

  @override
  void paint(Canvas canvas, Size size) {
    if (imageSize.isEmpty) return;

    final double scaleX = size.width / imageSize.width;
    final double scaleY = size.height / imageSize.height;

    for (final block in blocks) {
      Color baseColor;
      switch (block.status) {
        case IngredientStatus.safe:
          baseColor = AppColors.safeGreen;
          break;
        case IngredientStatus.caution:
          baseColor = AppColors.cautionAmber;
          break;
        case IngredientStatus.danger:
          baseColor = AppColors.flaggedRed;
          break;
        case IngredientStatus.unknown:
        default:
          continue;
      }

      final paintFill = Paint()
        ..color = baseColor.withOpacity(block.status == IngredientStatus.danger ? 0.3 : 0.2)
        ..style = PaintingStyle.fill;

      final paintBorder = Paint()
        ..color = baseColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0;

      final paintDot = Paint()
        ..color = baseColor
        ..style = PaintingStyle.fill;

      // Coordinate transformation based on rotation
      Rect rect;
      switch (rotation) {
        case InputImageRotation.rotation90deg:
          rect = Rect.fromLTRB(
            block.boundingBox.top * scaleX,
            block.boundingBox.left * scaleY,
            block.boundingBox.bottom * scaleX,
            block.boundingBox.right * scaleY,
          );
          break;
        case InputImageRotation.rotation270deg:
          rect = Rect.fromLTRB(
            (imageSize.height - block.boundingBox.bottom) * scaleX,
            block.boundingBox.left * scaleY,
            (imageSize.height - block.boundingBox.top) * scaleX,
            block.boundingBox.right * scaleY,
          );
          break;
        default:
          rect = Rect.fromLTRB(
            block.boundingBox.left * scaleX,
            block.boundingBox.top * scaleY,
            block.boundingBox.right * scaleX,
            block.boundingBox.bottom * scaleY,
          );
      }

      final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(8));
      
      canvas.drawRRect(rrect, paintFill);
      canvas.drawRRect(rrect, paintBorder);
      
      // Status dot at top-left
      canvas.drawCircle(Offset(rect.left + 4, rect.top + 4), 4.0, paintDot);
    }
  }

  @override
  bool shouldRepaint(covariant AROverlayPainter oldDelegate) {
    return oldDelegate.blocks != blocks || oldDelegate.imageSize != imageSize || oldDelegate.rotation != rotation;
  }
}
