import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nutriscan_ai/features/auth/screens/auth_screen.dart';
import 'package:nutriscan_ai/features/auth/providers/auth_provider.dart';

class MockAuthNotifier extends AsyncNotifier<AuthState> with Mock implements AuthNotifier {
  @override
  Future<AuthState> build() async {
    return const AuthState(status: AuthStatus.unauthenticated);
  }
}

void main() {
  testWidgets('AuthScreen renders correctly and handles guest sign in', (WidgetTester tester) async {
    final mockAuthNotifier = MockAuthNotifier();
    
    when(() => mockAuthNotifier.continueAsGuest()).thenAnswer((_) async {});

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(() => mockAuthNotifier),
        ],
        child: const MaterialApp(
          home: AuthScreen(),
        ),
      ),
    );

    // Verify UI elements are present
    expect(find.text('NutriScan AI'), findsOneWidget);
    expect(find.text('Continue with Google'), findsOneWidget);
    expect(find.text('Continue with Email'), findsOneWidget);
    expect(find.text('Continue as Guest'), findsOneWidget);

    // Tap the guest sign in button
    await tester.tap(find.text('Continue as Guest'));
    await tester.pumpAndSettle();

    // Verify the method was called on our mock
    verify(() => mockAuthNotifier.continueAsGuest()).called(1);
  });
}
