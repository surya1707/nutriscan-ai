import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/providers/user_profile_provider.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  late TextEditingController _nameController;
  bool _controllerInit = false;
  bool _saving = false;

  final _allergies = [
    'Peanuts', 'Tree Nuts', 'Dairy', 'Eggs', 'Soy',
    'Wheat / Gluten', 'Fish', 'Shellfish', 'Sesame', 'Mustard', 'Sulfites', 'Corn',
  ];
  final _conditions = [
    'Diabetes', 'Hypertension', 'High Cholesterol', 'Celiac Disease',
    'IBS', 'Kidney Disease', 'PCOS', 'Heart Disease',
  ];
  final _goals = [
    'Vegan', 'Vegetarian', 'Keto', 'Low Sodium', 'Low Sugar',
    'High Protein', 'Whole Foods', 'Halal', 'Kosher', 'Gluten-Free',
  ];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _save(UserProfile profile) async {
    setState(() => _saving = true);
    final updated = profile.copyWith(displayName: _nameController.text.trim());
    await ref.read(userProfileProvider.notifier).save(updated);
    setState(() => _saving = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Profile saved ✓'),
          backgroundColor: AppColors.safeGreen,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final profileAsync = ref.watch(userProfileProvider);

    return profileAsync.when(
      loading: () => const Scaffold(
        backgroundColor: AppColors.cream,
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (e, _) => Scaffold(
        backgroundColor: AppColors.cream,
        body: Center(child: Text('Error: $e')),
      ),
      data: (profile) {
        // Sync controller text once after first load
        if (!_controllerInit) {
          _nameController.text = profile.displayName;
          _controllerInit = true;
        }

        return Scaffold(
          backgroundColor: AppColors.cream,
          body: SafeArea(
            child: Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 24),
                        Text(
                          'HEALTH PROFILE',
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: AppColors.mediumGreen,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text('Make scans personal',
                            style: Theme.of(context).textTheme.headlineMedium),
                        const SizedBox(height: 8),
                        Text(
                          'We analyze every label against your profile.\nStored locally on your device.',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Display name
                        _SectionLabel(label: 'Display name'),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _nameController,
                          style: const TextStyle(
                              fontSize: 15, color: AppColors.textPrimary),
                          decoration:
                              const InputDecoration(hintText: 'e.g. Alex'),
                        ),
                        const SizedBox(height: 24),

                        // Allergies
                        _SectionLabel(label: 'Allergies'),
                        const SizedBox(height: 10),
                        _ChipGroup(
                          items: _allergies,
                          selected: profile.allergies,
                          onToggle: (v) =>
                              ref.read(userProfileProvider.notifier).toggleAllergy(v),
                        ),
                        const SizedBox(height: 24),

                        // Chronic conditions
                        _SectionLabel(label: 'Chronic conditions'),
                        const SizedBox(height: 10),
                        _ChipGroup(
                          items: _conditions,
                          selected: profile.conditions,
                          onToggle: (v) =>
                              ref.read(userProfileProvider.notifier).toggleCondition(v),
                        ),
                        const SizedBox(height: 24),

                        // Dietary goals
                        _SectionLabel(label: 'Dietary goals'),
                        const SizedBox(height: 10),
                        _ChipGroup(
                          items: _goals,
                          selected: profile.goals,
                          onToggle: (v) =>
                              ref.read(userProfileProvider.notifier).toggleGoal(v),
                        ),
                        const SizedBox(height: 32),
                      ],
                    ),
                  ),
                ),

                // Save button
                Padding(
                  padding: EdgeInsets.only(
                    left: 20,
                    right: 20,
                    bottom: MediaQuery.of(context).padding.bottom + 16,
                    top: 12,
                  ),
                  child: GestureDetector(
                    onTap: _saving ? null : () => _save(profile),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        color: _saving
                            ? AppColors.mediumGreen
                            : AppColors.darkGreen,
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (_saving)
                            const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          else
                            const Icon(Icons.save_outlined,
                                color: Colors.white, size: 20),
                          const SizedBox(width: 10),
                          Text(
                            _saving ? 'Saving…' : 'Save profile',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w500,
        color: AppColors.mediumGreen,
      ),
    );
  }
}

class _ChipGroup extends StatelessWidget {
  final List<String> items;
  final Set<String> selected;
  final ValueChanged<String> onToggle;

  const _ChipGroup({
    required this.items,
    required this.selected,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: items.map((item) {
        final isSelected = selected.contains(item);
        return GestureDetector(
          onTap: () => onToggle(item),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.darkGreen : Colors.white,
              borderRadius: BorderRadius.circular(30),
              border: Border.all(
                color: isSelected ? AppColors.darkGreen : AppColors.chipBorder,
                width: 1,
              ),
            ),
            child: Text(
              item,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w400,
                color: isSelected ? Colors.white : AppColors.chipText,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
