import 'package:flutter/material.dart';

class AppColors {
  // Brand
  static const cream = Color(0xFFF5F2EC);
  static const darkGreen = Color(0xFF2D4A3E);
  static const mediumGreen = Color(0xFF4A7C6F);
  static const lightGreen = Color(0xFFD6E4DF);
  static const chipBorder = Color(0xFFCBCBCB);
  static const chipText = Color(0xFF2D2D2D);

  // Status
  static const safeGreen = Color(0xFF2D8653);
  static const flaggedRed = Color(0xFFD94F3D);
  static const cautionAmber = Color(0xFFE5A020);

  // Neutrals
  static const textPrimary = Color(0xFF1A1A1A);
  static const textSecondary = Color(0xFF6B6B6B);
  static const textMuted = Color(0xFF9E9E9E);
  static const cardBg = Color(0xFFFFFFFF);
  static const divider = Color(0xFFE8E4DC);
  static const scannerOverlay = Color(0x99000000);

  // Bottom nav
  static const navActive = Color(0xFF2D4A3E);
  static const navInactive = Color(0xFF9E9E9E);
}

class AppTheme {
  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: AppColors.cream,
      colorScheme: ColorScheme.light(
        primary: AppColors.darkGreen,
        secondary: AppColors.mediumGreen,
        surface: AppColors.cream,
        background: AppColors.cream,
      ),
      fontFamily: 'SF Pro Display',
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.cream,
        elevation: 0,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: AppColors.textPrimary),
        titleTextStyle: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 17,
          fontWeight: FontWeight.w600,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.cream,
        selectedItemColor: AppColors.navActive,
        unselectedItemColor: AppColors.navInactive,
        selectedLabelStyle: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
        unselectedLabelStyle: TextStyle(fontSize: 11),
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.cardBg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.divider, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.divider, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.mediumGreen, width: 1.5),
        ),
        hintStyle: TextStyle(color: AppColors.textMuted, fontSize: 15),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 32, fontWeight: FontWeight.w700, color: AppColors.textPrimary, height: 1.15,
        ),
        headlineMedium: TextStyle(
          fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.textPrimary,
        ),
        titleLarge: TextStyle(
          fontSize: 17, fontWeight: FontWeight.w600, color: AppColors.textPrimary,
        ),
        titleMedium: TextStyle(
          fontSize: 15, fontWeight: FontWeight.w500, color: AppColors.textPrimary,
        ),
        bodyLarge: TextStyle(
          fontSize: 15, fontWeight: FontWeight.w400, color: AppColors.textPrimary, height: 1.5,
        ),
        bodyMedium: TextStyle(
          fontSize: 13, fontWeight: FontWeight.w400, color: AppColors.textSecondary, height: 1.5,
        ),
        labelSmall: TextStyle(
          fontSize: 11, fontWeight: FontWeight.w500, color: AppColors.textMuted, letterSpacing: 0.8,
        ),
      ),
    );
  }
}
