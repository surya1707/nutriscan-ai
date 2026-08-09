import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';

class MainShell extends StatelessWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  int _locationToIndex(String location) {
    if (location.startsWith('/history')) return 1;
    if (location.startsWith('/profile')) return 2;
    return 0;
  }

  void _onTap(BuildContext context, int index) {
    switch (index) {
      case 0: context.go('/'); break;
      case 1: context.go('/history'); break;
      case 2: context.go('/profile'); break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final index = _locationToIndex(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: AppColors.divider, width: 0.5)),
        ),
        child: BottomNavigationBar(
          currentIndex: index,
          onTap: (i) => _onTap(context, i),
          items: [
            BottomNavigationBarItem(
              icon: _NavIcon(icon: Icons.eco_outlined, active: index == 0),
              activeIcon: _NavIcon(icon: Icons.eco, active: true),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: _NavIcon(icon: Icons.history_outlined, active: index == 1),
              activeIcon: _NavIcon(icon: Icons.history, active: true),
              label: 'History',
            ),
            BottomNavigationBarItem(
              icon: _NavIcon(icon: Icons.person_outline, active: index == 2),
              activeIcon: _NavIcon(icon: Icons.person, active: true),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }
}

class _NavIcon extends StatelessWidget {
  final IconData icon;
  final bool active;
  const _NavIcon({required this.icon, required this.active});

  @override
  Widget build(BuildContext context) {
    return Icon(icon, size: 24, color: active ? AppColors.navActive : AppColors.navInactive);
  }
}
