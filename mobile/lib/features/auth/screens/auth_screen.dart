import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/auth_provider.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  bool _showEmailInput = false;
  final _emailController = TextEditingController();
  bool _isLoading = false;

  void _handleGoogleSignIn() async {
    setState(() => _isLoading = true);
    await ref.read(authProvider.notifier).signInWithGoogle();
    setState(() => _isLoading = false);
  }

  void _handleEmailSignIn() async {
    if (_emailController.text.isEmpty || !_emailController.text.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a valid email')),
      );
      return;
    }
    setState(() => _isLoading = true);
    try {
      await ref.read(authProvider.notifier).signInWithEmail(_emailController.text);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sign-in link sent to your email!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    }
    setState(() => _isLoading = false);
  }

  void _handleGuestSignIn() async {
    setState(() => _isLoading = true);
    await ref.read(authProvider.notifier).continueAsGuest();
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(
                Icons.spa_rounded,
                size: 80,
                color: AppColors.darkGreen,
              ),
              const SizedBox(height: 24),
              const Text(
                'NutriScan AI',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: AppColors.darkGreen,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Sync your scans across devices',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 64),
              
              if (_isLoading)
                const Center(child: CircularProgressIndicator(color: AppColors.darkGreen))
              else ...[
                // Google Sign In Button
                ElevatedButton.icon(
                  key: const ValueKey('auth_google_btn'),
                  onPressed: _handleGoogleSignIn,
                  icon: const Icon(Icons.g_mobiledata, size: 32),
                  label: const Text('Continue with Google', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.darkGreen,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                
                // Email Sign In
                if (!_showEmailInput)
                  OutlinedButton.icon(
                    key: const ValueKey('auth_email_toggle_btn'),
                    onPressed: () => setState(() => _showEmailInput = true),
                    icon: const Icon(Icons.email_outlined),
                    label: const Text('Continue with Email', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.darkGreen,
                      side: const BorderSide(color: AppColors.darkGreen),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  )
                else ...[
                  TextField(
                    key: const ValueKey('auth_email_field'),
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    decoration: InputDecoration(
                      hintText: 'Enter your email',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide.none,
                      ),
                      suffixIcon: IconButton(
                        key: const ValueKey('auth_email_send_btn'),
                        icon: const Icon(Icons.send_rounded, color: AppColors.darkGreen),
                        onPressed: _handleEmailSignIn,
                      ),
                    ),
                  ),
                ],
                
                const SizedBox(height: 32),
                
                // Guest Sign In
                TextButton(
                  key: const ValueKey('auth_guest_btn'),
                  onPressed: _handleGuestSignIn,
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.textSecondary,
                  ),
                  child: const Text('Continue as Guest', style: TextStyle(decoration: TextDecoration.underline)),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
