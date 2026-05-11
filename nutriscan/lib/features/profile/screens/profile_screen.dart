import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _nameController = TextEditingController();

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

  final Set<String> _selectedAllergies = {};
  final Set<String> _selectedConditions = {};
  final Set<String> _selectedGoals = {};

  void _toggle(Set<String> set, String val) {
    setState(() {
      if (set.contains(val)) {
        set.remove(val);
      } else {
        set.add(val);
      }
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                    Text(
                      'Make scans personal',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
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
                      style: const TextStyle(fontSize: 15, color: AppColors.textPrimary),
                      decoration: const InputDecoration(hintText: 'e.g. Alex'),
                    ),
                    const SizedBox(height: 24),

                    // Allergies
                    _SectionLabel(label: 'Allergies'),
                    const SizedBox(height: 10),
                    _ChipGroup(
                      items: _allergies,
                      selected: _selectedAllergies,
                      onToggle: (v) => _toggle(_selectedAllergies, v),
                    ),
                    const SizedBox(height: 24),

                    // Chronic conditions
                    _SectionLabel(label: 'Chronic conditions'),
                    const SizedBox(height: 10),
                    _ChipGroup(
                      items: _conditions,
                      selected: _selectedConditions,
                      onToggle: (v) => _toggle(_selectedConditions, v),
                    ),
                    const SizedBox(height: 24),

                    // Dietary goals
                    _SectionLabel(label: 'Dietary goals'),
                    const SizedBox(height: 10),
                    _ChipGroup(
                      items: _goals,
                      selected: _selectedGoals,
                      onToggle: (v) => _toggle(_selectedGoals, v),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),

            // Save button pinned at bottom
            Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                bottom: MediaQuery.of(context).padding.bottom + 16,
                top: 12,
              ),
              child: GestureDetector(
                onTap: () {
                  // Save profile logic
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Profile saved!')),
                  );
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    color: AppColors.darkGreen,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.save_outlined, color: Colors.white, size: 20),
                      SizedBox(width: 10),
                      Text(
                        'Save profile',
                        style: TextStyle(
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
