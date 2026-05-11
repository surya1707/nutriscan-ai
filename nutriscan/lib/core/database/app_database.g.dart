// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $ScanHistoryTableTable extends ScanHistoryTable
    with TableInfo<$ScanHistoryTableTable, ScanHistoryTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ScanHistoryTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _productNameMeta =
      const VerificationMeta('productName');
  @override
  late final GeneratedColumn<String> productName = GeneratedColumn<String>(
      'product_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _brandMeta = const VerificationMeta('brand');
  @override
  late final GeneratedColumn<String> brand = GeneratedColumn<String>(
      'brand', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _healthScoreMeta =
      const VerificationMeta('healthScore');
  @override
  late final GeneratedColumn<int> healthScore = GeneratedColumn<int>(
      'health_score', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _novaGroupMeta =
      const VerificationMeta('novaGroup');
  @override
  late final GeneratedColumn<int> novaGroup = GeneratedColumn<int>(
      'nova_group', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _nutrientsJsonMeta =
      const VerificationMeta('nutrientsJson');
  @override
  late final GeneratedColumn<String> nutrientsJson = GeneratedColumn<String>(
      'nutrients_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _ingredientsJsonMeta =
      const VerificationMeta('ingredientsJson');
  @override
  late final GeneratedColumn<String> ingredientsJson = GeneratedColumn<String>(
      'ingredients_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _alternativesJsonMeta =
      const VerificationMeta('alternativesJson');
  @override
  late final GeneratedColumn<String> alternativesJson = GeneratedColumn<String>(
      'alternatives_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _scannedAtMeta =
      const VerificationMeta('scannedAt');
  @override
  late final GeneratedColumn<DateTime> scannedAt = GeneratedColumn<DateTime>(
      'scanned_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        productName,
        brand,
        healthScore,
        novaGroup,
        nutrientsJson,
        ingredientsJson,
        alternativesJson,
        scannedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'scan_history_table';
  @override
  VerificationContext validateIntegrity(
      Insertable<ScanHistoryTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('product_name')) {
      context.handle(
          _productNameMeta,
          productName.isAcceptableOrUnknown(
              data['product_name']!, _productNameMeta));
    } else if (isInserting) {
      context.missing(_productNameMeta);
    }
    if (data.containsKey('brand')) {
      context.handle(
          _brandMeta, brand.isAcceptableOrUnknown(data['brand']!, _brandMeta));
    } else if (isInserting) {
      context.missing(_brandMeta);
    }
    if (data.containsKey('health_score')) {
      context.handle(
          _healthScoreMeta,
          healthScore.isAcceptableOrUnknown(
              data['health_score']!, _healthScoreMeta));
    } else if (isInserting) {
      context.missing(_healthScoreMeta);
    }
    if (data.containsKey('nova_group')) {
      context.handle(_novaGroupMeta,
          novaGroup.isAcceptableOrUnknown(data['nova_group']!, _novaGroupMeta));
    } else if (isInserting) {
      context.missing(_novaGroupMeta);
    }
    if (data.containsKey('nutrients_json')) {
      context.handle(
          _nutrientsJsonMeta,
          nutrientsJson.isAcceptableOrUnknown(
              data['nutrients_json']!, _nutrientsJsonMeta));
    } else if (isInserting) {
      context.missing(_nutrientsJsonMeta);
    }
    if (data.containsKey('ingredients_json')) {
      context.handle(
          _ingredientsJsonMeta,
          ingredientsJson.isAcceptableOrUnknown(
              data['ingredients_json']!, _ingredientsJsonMeta));
    } else if (isInserting) {
      context.missing(_ingredientsJsonMeta);
    }
    if (data.containsKey('alternatives_json')) {
      context.handle(
          _alternativesJsonMeta,
          alternativesJson.isAcceptableOrUnknown(
              data['alternatives_json']!, _alternativesJsonMeta));
    } else if (isInserting) {
      context.missing(_alternativesJsonMeta);
    }
    if (data.containsKey('scanned_at')) {
      context.handle(_scannedAtMeta,
          scannedAt.isAcceptableOrUnknown(data['scanned_at']!, _scannedAtMeta));
    } else if (isInserting) {
      context.missing(_scannedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ScanHistoryTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ScanHistoryTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      productName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_name'])!,
      brand: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}brand'])!,
      healthScore: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}health_score'])!,
      novaGroup: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}nova_group'])!,
      nutrientsJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}nutrients_json'])!,
      ingredientsJson: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}ingredients_json'])!,
      alternativesJson: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}alternatives_json'])!,
      scannedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}scanned_at'])!,
    );
  }

  @override
  $ScanHistoryTableTable createAlias(String alias) {
    return $ScanHistoryTableTable(attachedDatabase, alias);
  }
}

class ScanHistoryTableData extends DataClass
    implements Insertable<ScanHistoryTableData> {
  final String id;
  final String productName;
  final String brand;
  final int healthScore;
  final int novaGroup;
  final String nutrientsJson;
  final String ingredientsJson;
  final String alternativesJson;
  final DateTime scannedAt;
  const ScanHistoryTableData(
      {required this.id,
      required this.productName,
      required this.brand,
      required this.healthScore,
      required this.novaGroup,
      required this.nutrientsJson,
      required this.ingredientsJson,
      required this.alternativesJson,
      required this.scannedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['product_name'] = Variable<String>(productName);
    map['brand'] = Variable<String>(brand);
    map['health_score'] = Variable<int>(healthScore);
    map['nova_group'] = Variable<int>(novaGroup);
    map['nutrients_json'] = Variable<String>(nutrientsJson);
    map['ingredients_json'] = Variable<String>(ingredientsJson);
    map['alternatives_json'] = Variable<String>(alternativesJson);
    map['scanned_at'] = Variable<DateTime>(scannedAt);
    return map;
  }

  ScanHistoryTableCompanion toCompanion(bool nullToAbsent) {
    return ScanHistoryTableCompanion(
      id: Value(id),
      productName: Value(productName),
      brand: Value(brand),
      healthScore: Value(healthScore),
      novaGroup: Value(novaGroup),
      nutrientsJson: Value(nutrientsJson),
      ingredientsJson: Value(ingredientsJson),
      alternativesJson: Value(alternativesJson),
      scannedAt: Value(scannedAt),
    );
  }

  factory ScanHistoryTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ScanHistoryTableData(
      id: serializer.fromJson<String>(json['id']),
      productName: serializer.fromJson<String>(json['productName']),
      brand: serializer.fromJson<String>(json['brand']),
      healthScore: serializer.fromJson<int>(json['healthScore']),
      novaGroup: serializer.fromJson<int>(json['novaGroup']),
      nutrientsJson: serializer.fromJson<String>(json['nutrientsJson']),
      ingredientsJson: serializer.fromJson<String>(json['ingredientsJson']),
      alternativesJson: serializer.fromJson<String>(json['alternativesJson']),
      scannedAt: serializer.fromJson<DateTime>(json['scannedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'productName': serializer.toJson<String>(productName),
      'brand': serializer.toJson<String>(brand),
      'healthScore': serializer.toJson<int>(healthScore),
      'novaGroup': serializer.toJson<int>(novaGroup),
      'nutrientsJson': serializer.toJson<String>(nutrientsJson),
      'ingredientsJson': serializer.toJson<String>(ingredientsJson),
      'alternativesJson': serializer.toJson<String>(alternativesJson),
      'scannedAt': serializer.toJson<DateTime>(scannedAt),
    };
  }

  ScanHistoryTableData copyWith(
          {String? id,
          String? productName,
          String? brand,
          int? healthScore,
          int? novaGroup,
          String? nutrientsJson,
          String? ingredientsJson,
          String? alternativesJson,
          DateTime? scannedAt}) =>
      ScanHistoryTableData(
        id: id ?? this.id,
        productName: productName ?? this.productName,
        brand: brand ?? this.brand,
        healthScore: healthScore ?? this.healthScore,
        novaGroup: novaGroup ?? this.novaGroup,
        nutrientsJson: nutrientsJson ?? this.nutrientsJson,
        ingredientsJson: ingredientsJson ?? this.ingredientsJson,
        alternativesJson: alternativesJson ?? this.alternativesJson,
        scannedAt: scannedAt ?? this.scannedAt,
      );
  ScanHistoryTableData copyWithCompanion(ScanHistoryTableCompanion data) {
    return ScanHistoryTableData(
      id: data.id.present ? data.id.value : this.id,
      productName:
          data.productName.present ? data.productName.value : this.productName,
      brand: data.brand.present ? data.brand.value : this.brand,
      healthScore:
          data.healthScore.present ? data.healthScore.value : this.healthScore,
      novaGroup: data.novaGroup.present ? data.novaGroup.value : this.novaGroup,
      nutrientsJson: data.nutrientsJson.present
          ? data.nutrientsJson.value
          : this.nutrientsJson,
      ingredientsJson: data.ingredientsJson.present
          ? data.ingredientsJson.value
          : this.ingredientsJson,
      alternativesJson: data.alternativesJson.present
          ? data.alternativesJson.value
          : this.alternativesJson,
      scannedAt: data.scannedAt.present ? data.scannedAt.value : this.scannedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ScanHistoryTableData(')
          ..write('id: $id, ')
          ..write('productName: $productName, ')
          ..write('brand: $brand, ')
          ..write('healthScore: $healthScore, ')
          ..write('novaGroup: $novaGroup, ')
          ..write('nutrientsJson: $nutrientsJson, ')
          ..write('ingredientsJson: $ingredientsJson, ')
          ..write('alternativesJson: $alternativesJson, ')
          ..write('scannedAt: $scannedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, productName, brand, healthScore,
      novaGroup, nutrientsJson, ingredientsJson, alternativesJson, scannedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ScanHistoryTableData &&
          other.id == this.id &&
          other.productName == this.productName &&
          other.brand == this.brand &&
          other.healthScore == this.healthScore &&
          other.novaGroup == this.novaGroup &&
          other.nutrientsJson == this.nutrientsJson &&
          other.ingredientsJson == this.ingredientsJson &&
          other.alternativesJson == this.alternativesJson &&
          other.scannedAt == this.scannedAt);
}

class ScanHistoryTableCompanion extends UpdateCompanion<ScanHistoryTableData> {
  final Value<String> id;
  final Value<String> productName;
  final Value<String> brand;
  final Value<int> healthScore;
  final Value<int> novaGroup;
  final Value<String> nutrientsJson;
  final Value<String> ingredientsJson;
  final Value<String> alternativesJson;
  final Value<DateTime> scannedAt;
  final Value<int> rowid;
  const ScanHistoryTableCompanion({
    this.id = const Value.absent(),
    this.productName = const Value.absent(),
    this.brand = const Value.absent(),
    this.healthScore = const Value.absent(),
    this.novaGroup = const Value.absent(),
    this.nutrientsJson = const Value.absent(),
    this.ingredientsJson = const Value.absent(),
    this.alternativesJson = const Value.absent(),
    this.scannedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ScanHistoryTableCompanion.insert({
    required String id,
    required String productName,
    required String brand,
    required int healthScore,
    required int novaGroup,
    required String nutrientsJson,
    required String ingredientsJson,
    required String alternativesJson,
    required DateTime scannedAt,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        productName = Value(productName),
        brand = Value(brand),
        healthScore = Value(healthScore),
        novaGroup = Value(novaGroup),
        nutrientsJson = Value(nutrientsJson),
        ingredientsJson = Value(ingredientsJson),
        alternativesJson = Value(alternativesJson),
        scannedAt = Value(scannedAt);
  static Insertable<ScanHistoryTableData> custom({
    Expression<String>? id,
    Expression<String>? productName,
    Expression<String>? brand,
    Expression<int>? healthScore,
    Expression<int>? novaGroup,
    Expression<String>? nutrientsJson,
    Expression<String>? ingredientsJson,
    Expression<String>? alternativesJson,
    Expression<DateTime>? scannedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (productName != null) 'product_name': productName,
      if (brand != null) 'brand': brand,
      if (healthScore != null) 'health_score': healthScore,
      if (novaGroup != null) 'nova_group': novaGroup,
      if (nutrientsJson != null) 'nutrients_json': nutrientsJson,
      if (ingredientsJson != null) 'ingredients_json': ingredientsJson,
      if (alternativesJson != null) 'alternatives_json': alternativesJson,
      if (scannedAt != null) 'scanned_at': scannedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ScanHistoryTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? productName,
      Value<String>? brand,
      Value<int>? healthScore,
      Value<int>? novaGroup,
      Value<String>? nutrientsJson,
      Value<String>? ingredientsJson,
      Value<String>? alternativesJson,
      Value<DateTime>? scannedAt,
      Value<int>? rowid}) {
    return ScanHistoryTableCompanion(
      id: id ?? this.id,
      productName: productName ?? this.productName,
      brand: brand ?? this.brand,
      healthScore: healthScore ?? this.healthScore,
      novaGroup: novaGroup ?? this.novaGroup,
      nutrientsJson: nutrientsJson ?? this.nutrientsJson,
      ingredientsJson: ingredientsJson ?? this.ingredientsJson,
      alternativesJson: alternativesJson ?? this.alternativesJson,
      scannedAt: scannedAt ?? this.scannedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (productName.present) {
      map['product_name'] = Variable<String>(productName.value);
    }
    if (brand.present) {
      map['brand'] = Variable<String>(brand.value);
    }
    if (healthScore.present) {
      map['health_score'] = Variable<int>(healthScore.value);
    }
    if (novaGroup.present) {
      map['nova_group'] = Variable<int>(novaGroup.value);
    }
    if (nutrientsJson.present) {
      map['nutrients_json'] = Variable<String>(nutrientsJson.value);
    }
    if (ingredientsJson.present) {
      map['ingredients_json'] = Variable<String>(ingredientsJson.value);
    }
    if (alternativesJson.present) {
      map['alternatives_json'] = Variable<String>(alternativesJson.value);
    }
    if (scannedAt.present) {
      map['scanned_at'] = Variable<DateTime>(scannedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ScanHistoryTableCompanion(')
          ..write('id: $id, ')
          ..write('productName: $productName, ')
          ..write('brand: $brand, ')
          ..write('healthScore: $healthScore, ')
          ..write('novaGroup: $novaGroup, ')
          ..write('nutrientsJson: $nutrientsJson, ')
          ..write('ingredientsJson: $ingredientsJson, ')
          ..write('alternativesJson: $alternativesJson, ')
          ..write('scannedAt: $scannedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $UserProfileTableTable extends UserProfileTable
    with TableInfo<$UserProfileTableTable, UserProfileTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $UserProfileTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(1));
  static const VerificationMeta _displayNameMeta =
      const VerificationMeta('displayName');
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
      'display_name', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  static const VerificationMeta _allergiesJsonMeta =
      const VerificationMeta('allergiesJson');
  @override
  late final GeneratedColumn<String> allergiesJson = GeneratedColumn<String>(
      'allergies_json', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('[]'));
  static const VerificationMeta _conditionsJsonMeta =
      const VerificationMeta('conditionsJson');
  @override
  late final GeneratedColumn<String> conditionsJson = GeneratedColumn<String>(
      'conditions_json', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('[]'));
  static const VerificationMeta _goalsJsonMeta =
      const VerificationMeta('goalsJson');
  @override
  late final GeneratedColumn<String> goalsJson = GeneratedColumn<String>(
      'goals_json', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('[]'));
  @override
  List<GeneratedColumn> get $columns =>
      [id, displayName, allergiesJson, conditionsJson, goalsJson];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'user_profile_table';
  @override
  VerificationContext validateIntegrity(
      Insertable<UserProfileTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('display_name')) {
      context.handle(
          _displayNameMeta,
          displayName.isAcceptableOrUnknown(
              data['display_name']!, _displayNameMeta));
    }
    if (data.containsKey('allergies_json')) {
      context.handle(
          _allergiesJsonMeta,
          allergiesJson.isAcceptableOrUnknown(
              data['allergies_json']!, _allergiesJsonMeta));
    }
    if (data.containsKey('conditions_json')) {
      context.handle(
          _conditionsJsonMeta,
          conditionsJson.isAcceptableOrUnknown(
              data['conditions_json']!, _conditionsJsonMeta));
    }
    if (data.containsKey('goals_json')) {
      context.handle(_goalsJsonMeta,
          goalsJson.isAcceptableOrUnknown(data['goals_json']!, _goalsJsonMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  UserProfileTableData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return UserProfileTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      displayName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}display_name'])!,
      allergiesJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}allergies_json'])!,
      conditionsJson: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}conditions_json'])!,
      goalsJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}goals_json'])!,
    );
  }

  @override
  $UserProfileTableTable createAlias(String alias) {
    return $UserProfileTableTable(attachedDatabase, alias);
  }
}

class UserProfileTableData extends DataClass
    implements Insertable<UserProfileTableData> {
  final int id;
  final String displayName;
  final String allergiesJson;
  final String conditionsJson;
  final String goalsJson;
  const UserProfileTableData(
      {required this.id,
      required this.displayName,
      required this.allergiesJson,
      required this.conditionsJson,
      required this.goalsJson});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['display_name'] = Variable<String>(displayName);
    map['allergies_json'] = Variable<String>(allergiesJson);
    map['conditions_json'] = Variable<String>(conditionsJson);
    map['goals_json'] = Variable<String>(goalsJson);
    return map;
  }

  UserProfileTableCompanion toCompanion(bool nullToAbsent) {
    return UserProfileTableCompanion(
      id: Value(id),
      displayName: Value(displayName),
      allergiesJson: Value(allergiesJson),
      conditionsJson: Value(conditionsJson),
      goalsJson: Value(goalsJson),
    );
  }

  factory UserProfileTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return UserProfileTableData(
      id: serializer.fromJson<int>(json['id']),
      displayName: serializer.fromJson<String>(json['displayName']),
      allergiesJson: serializer.fromJson<String>(json['allergiesJson']),
      conditionsJson: serializer.fromJson<String>(json['conditionsJson']),
      goalsJson: serializer.fromJson<String>(json['goalsJson']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'displayName': serializer.toJson<String>(displayName),
      'allergiesJson': serializer.toJson<String>(allergiesJson),
      'conditionsJson': serializer.toJson<String>(conditionsJson),
      'goalsJson': serializer.toJson<String>(goalsJson),
    };
  }

  UserProfileTableData copyWith(
          {int? id,
          String? displayName,
          String? allergiesJson,
          String? conditionsJson,
          String? goalsJson}) =>
      UserProfileTableData(
        id: id ?? this.id,
        displayName: displayName ?? this.displayName,
        allergiesJson: allergiesJson ?? this.allergiesJson,
        conditionsJson: conditionsJson ?? this.conditionsJson,
        goalsJson: goalsJson ?? this.goalsJson,
      );
  UserProfileTableData copyWithCompanion(UserProfileTableCompanion data) {
    return UserProfileTableData(
      id: data.id.present ? data.id.value : this.id,
      displayName:
          data.displayName.present ? data.displayName.value : this.displayName,
      allergiesJson: data.allergiesJson.present
          ? data.allergiesJson.value
          : this.allergiesJson,
      conditionsJson: data.conditionsJson.present
          ? data.conditionsJson.value
          : this.conditionsJson,
      goalsJson: data.goalsJson.present ? data.goalsJson.value : this.goalsJson,
    );
  }

  @override
  String toString() {
    return (StringBuffer('UserProfileTableData(')
          ..write('id: $id, ')
          ..write('displayName: $displayName, ')
          ..write('allergiesJson: $allergiesJson, ')
          ..write('conditionsJson: $conditionsJson, ')
          ..write('goalsJson: $goalsJson')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, displayName, allergiesJson, conditionsJson, goalsJson);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is UserProfileTableData &&
          other.id == this.id &&
          other.displayName == this.displayName &&
          other.allergiesJson == this.allergiesJson &&
          other.conditionsJson == this.conditionsJson &&
          other.goalsJson == this.goalsJson);
}

class UserProfileTableCompanion extends UpdateCompanion<UserProfileTableData> {
  final Value<int> id;
  final Value<String> displayName;
  final Value<String> allergiesJson;
  final Value<String> conditionsJson;
  final Value<String> goalsJson;
  const UserProfileTableCompanion({
    this.id = const Value.absent(),
    this.displayName = const Value.absent(),
    this.allergiesJson = const Value.absent(),
    this.conditionsJson = const Value.absent(),
    this.goalsJson = const Value.absent(),
  });
  UserProfileTableCompanion.insert({
    this.id = const Value.absent(),
    this.displayName = const Value.absent(),
    this.allergiesJson = const Value.absent(),
    this.conditionsJson = const Value.absent(),
    this.goalsJson = const Value.absent(),
  });
  static Insertable<UserProfileTableData> custom({
    Expression<int>? id,
    Expression<String>? displayName,
    Expression<String>? allergiesJson,
    Expression<String>? conditionsJson,
    Expression<String>? goalsJson,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (displayName != null) 'display_name': displayName,
      if (allergiesJson != null) 'allergies_json': allergiesJson,
      if (conditionsJson != null) 'conditions_json': conditionsJson,
      if (goalsJson != null) 'goals_json': goalsJson,
    });
  }

  UserProfileTableCompanion copyWith(
      {Value<int>? id,
      Value<String>? displayName,
      Value<String>? allergiesJson,
      Value<String>? conditionsJson,
      Value<String>? goalsJson}) {
    return UserProfileTableCompanion(
      id: id ?? this.id,
      displayName: displayName ?? this.displayName,
      allergiesJson: allergiesJson ?? this.allergiesJson,
      conditionsJson: conditionsJson ?? this.conditionsJson,
      goalsJson: goalsJson ?? this.goalsJson,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (displayName.present) {
      map['display_name'] = Variable<String>(displayName.value);
    }
    if (allergiesJson.present) {
      map['allergies_json'] = Variable<String>(allergiesJson.value);
    }
    if (conditionsJson.present) {
      map['conditions_json'] = Variable<String>(conditionsJson.value);
    }
    if (goalsJson.present) {
      map['goals_json'] = Variable<String>(goalsJson.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('UserProfileTableCompanion(')
          ..write('id: $id, ')
          ..write('displayName: $displayName, ')
          ..write('allergiesJson: $allergiesJson, ')
          ..write('conditionsJson: $conditionsJson, ')
          ..write('goalsJson: $goalsJson')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $ScanHistoryTableTable scanHistoryTable =
      $ScanHistoryTableTable(this);
  late final $UserProfileTableTable userProfileTable =
      $UserProfileTableTable(this);
  late final ScanHistoryDao scanHistoryDao =
      ScanHistoryDao(this as AppDatabase);
  late final UserProfileDao userProfileDao =
      UserProfileDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [scanHistoryTable, userProfileTable];
}

typedef $$ScanHistoryTableTableCreateCompanionBuilder
    = ScanHistoryTableCompanion Function({
  required String id,
  required String productName,
  required String brand,
  required int healthScore,
  required int novaGroup,
  required String nutrientsJson,
  required String ingredientsJson,
  required String alternativesJson,
  required DateTime scannedAt,
  Value<int> rowid,
});
typedef $$ScanHistoryTableTableUpdateCompanionBuilder
    = ScanHistoryTableCompanion Function({
  Value<String> id,
  Value<String> productName,
  Value<String> brand,
  Value<int> healthScore,
  Value<int> novaGroup,
  Value<String> nutrientsJson,
  Value<String> ingredientsJson,
  Value<String> alternativesJson,
  Value<DateTime> scannedAt,
  Value<int> rowid,
});

class $$ScanHistoryTableTableFilterComposer
    extends Composer<_$AppDatabase, $ScanHistoryTableTable> {
  $$ScanHistoryTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get brand => $composableBuilder(
      column: $table.brand, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get healthScore => $composableBuilder(
      column: $table.healthScore, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get novaGroup => $composableBuilder(
      column: $table.novaGroup, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get nutrientsJson => $composableBuilder(
      column: $table.nutrientsJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get ingredientsJson => $composableBuilder(
      column: $table.ingredientsJson,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get alternativesJson => $composableBuilder(
      column: $table.alternativesJson,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get scannedAt => $composableBuilder(
      column: $table.scannedAt, builder: (column) => ColumnFilters(column));
}

class $$ScanHistoryTableTableOrderingComposer
    extends Composer<_$AppDatabase, $ScanHistoryTableTable> {
  $$ScanHistoryTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get brand => $composableBuilder(
      column: $table.brand, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get healthScore => $composableBuilder(
      column: $table.healthScore, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get novaGroup => $composableBuilder(
      column: $table.novaGroup, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get nutrientsJson => $composableBuilder(
      column: $table.nutrientsJson,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get ingredientsJson => $composableBuilder(
      column: $table.ingredientsJson,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get alternativesJson => $composableBuilder(
      column: $table.alternativesJson,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get scannedAt => $composableBuilder(
      column: $table.scannedAt, builder: (column) => ColumnOrderings(column));
}

class $$ScanHistoryTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $ScanHistoryTableTable> {
  $$ScanHistoryTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get productName => $composableBuilder(
      column: $table.productName, builder: (column) => column);

  GeneratedColumn<String> get brand =>
      $composableBuilder(column: $table.brand, builder: (column) => column);

  GeneratedColumn<int> get healthScore => $composableBuilder(
      column: $table.healthScore, builder: (column) => column);

  GeneratedColumn<int> get novaGroup =>
      $composableBuilder(column: $table.novaGroup, builder: (column) => column);

  GeneratedColumn<String> get nutrientsJson => $composableBuilder(
      column: $table.nutrientsJson, builder: (column) => column);

  GeneratedColumn<String> get ingredientsJson => $composableBuilder(
      column: $table.ingredientsJson, builder: (column) => column);

  GeneratedColumn<String> get alternativesJson => $composableBuilder(
      column: $table.alternativesJson, builder: (column) => column);

  GeneratedColumn<DateTime> get scannedAt =>
      $composableBuilder(column: $table.scannedAt, builder: (column) => column);
}

class $$ScanHistoryTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ScanHistoryTableTable,
    ScanHistoryTableData,
    $$ScanHistoryTableTableFilterComposer,
    $$ScanHistoryTableTableOrderingComposer,
    $$ScanHistoryTableTableAnnotationComposer,
    $$ScanHistoryTableTableCreateCompanionBuilder,
    $$ScanHistoryTableTableUpdateCompanionBuilder,
    (
      ScanHistoryTableData,
      BaseReferences<_$AppDatabase, $ScanHistoryTableTable,
          ScanHistoryTableData>
    ),
    ScanHistoryTableData,
    PrefetchHooks Function()> {
  $$ScanHistoryTableTableTableManager(
      _$AppDatabase db, $ScanHistoryTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ScanHistoryTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ScanHistoryTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ScanHistoryTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> productName = const Value.absent(),
            Value<String> brand = const Value.absent(),
            Value<int> healthScore = const Value.absent(),
            Value<int> novaGroup = const Value.absent(),
            Value<String> nutrientsJson = const Value.absent(),
            Value<String> ingredientsJson = const Value.absent(),
            Value<String> alternativesJson = const Value.absent(),
            Value<DateTime> scannedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ScanHistoryTableCompanion(
            id: id,
            productName: productName,
            brand: brand,
            healthScore: healthScore,
            novaGroup: novaGroup,
            nutrientsJson: nutrientsJson,
            ingredientsJson: ingredientsJson,
            alternativesJson: alternativesJson,
            scannedAt: scannedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String productName,
            required String brand,
            required int healthScore,
            required int novaGroup,
            required String nutrientsJson,
            required String ingredientsJson,
            required String alternativesJson,
            required DateTime scannedAt,
            Value<int> rowid = const Value.absent(),
          }) =>
              ScanHistoryTableCompanion.insert(
            id: id,
            productName: productName,
            brand: brand,
            healthScore: healthScore,
            novaGroup: novaGroup,
            nutrientsJson: nutrientsJson,
            ingredientsJson: ingredientsJson,
            alternativesJson: alternativesJson,
            scannedAt: scannedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ScanHistoryTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $ScanHistoryTableTable,
    ScanHistoryTableData,
    $$ScanHistoryTableTableFilterComposer,
    $$ScanHistoryTableTableOrderingComposer,
    $$ScanHistoryTableTableAnnotationComposer,
    $$ScanHistoryTableTableCreateCompanionBuilder,
    $$ScanHistoryTableTableUpdateCompanionBuilder,
    (
      ScanHistoryTableData,
      BaseReferences<_$AppDatabase, $ScanHistoryTableTable,
          ScanHistoryTableData>
    ),
    ScanHistoryTableData,
    PrefetchHooks Function()>;
typedef $$UserProfileTableTableCreateCompanionBuilder
    = UserProfileTableCompanion Function({
  Value<int> id,
  Value<String> displayName,
  Value<String> allergiesJson,
  Value<String> conditionsJson,
  Value<String> goalsJson,
});
typedef $$UserProfileTableTableUpdateCompanionBuilder
    = UserProfileTableCompanion Function({
  Value<int> id,
  Value<String> displayName,
  Value<String> allergiesJson,
  Value<String> conditionsJson,
  Value<String> goalsJson,
});

class $$UserProfileTableTableFilterComposer
    extends Composer<_$AppDatabase, $UserProfileTableTable> {
  $$UserProfileTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get allergiesJson => $composableBuilder(
      column: $table.allergiesJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get conditionsJson => $composableBuilder(
      column: $table.conditionsJson,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get goalsJson => $composableBuilder(
      column: $table.goalsJson, builder: (column) => ColumnFilters(column));
}

class $$UserProfileTableTableOrderingComposer
    extends Composer<_$AppDatabase, $UserProfileTableTable> {
  $$UserProfileTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get allergiesJson => $composableBuilder(
      column: $table.allergiesJson,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get conditionsJson => $composableBuilder(
      column: $table.conditionsJson,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get goalsJson => $composableBuilder(
      column: $table.goalsJson, builder: (column) => ColumnOrderings(column));
}

class $$UserProfileTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $UserProfileTableTable> {
  $$UserProfileTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => column);

  GeneratedColumn<String> get allergiesJson => $composableBuilder(
      column: $table.allergiesJson, builder: (column) => column);

  GeneratedColumn<String> get conditionsJson => $composableBuilder(
      column: $table.conditionsJson, builder: (column) => column);

  GeneratedColumn<String> get goalsJson =>
      $composableBuilder(column: $table.goalsJson, builder: (column) => column);
}

class $$UserProfileTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $UserProfileTableTable,
    UserProfileTableData,
    $$UserProfileTableTableFilterComposer,
    $$UserProfileTableTableOrderingComposer,
    $$UserProfileTableTableAnnotationComposer,
    $$UserProfileTableTableCreateCompanionBuilder,
    $$UserProfileTableTableUpdateCompanionBuilder,
    (
      UserProfileTableData,
      BaseReferences<_$AppDatabase, $UserProfileTableTable,
          UserProfileTableData>
    ),
    UserProfileTableData,
    PrefetchHooks Function()> {
  $$UserProfileTableTableTableManager(
      _$AppDatabase db, $UserProfileTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$UserProfileTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$UserProfileTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$UserProfileTableTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> displayName = const Value.absent(),
            Value<String> allergiesJson = const Value.absent(),
            Value<String> conditionsJson = const Value.absent(),
            Value<String> goalsJson = const Value.absent(),
          }) =>
              UserProfileTableCompanion(
            id: id,
            displayName: displayName,
            allergiesJson: allergiesJson,
            conditionsJson: conditionsJson,
            goalsJson: goalsJson,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> displayName = const Value.absent(),
            Value<String> allergiesJson = const Value.absent(),
            Value<String> conditionsJson = const Value.absent(),
            Value<String> goalsJson = const Value.absent(),
          }) =>
              UserProfileTableCompanion.insert(
            id: id,
            displayName: displayName,
            allergiesJson: allergiesJson,
            conditionsJson: conditionsJson,
            goalsJson: goalsJson,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$UserProfileTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $UserProfileTableTable,
    UserProfileTableData,
    $$UserProfileTableTableFilterComposer,
    $$UserProfileTableTableOrderingComposer,
    $$UserProfileTableTableAnnotationComposer,
    $$UserProfileTableTableCreateCompanionBuilder,
    $$UserProfileTableTableUpdateCompanionBuilder,
    (
      UserProfileTableData,
      BaseReferences<_$AppDatabase, $UserProfileTableTable,
          UserProfileTableData>
    ),
    UserProfileTableData,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$ScanHistoryTableTableTableManager get scanHistoryTable =>
      $$ScanHistoryTableTableTableManager(_db, _db.scanHistoryTable);
  $$UserProfileTableTableTableManager get userProfileTable =>
      $$UserProfileTableTableTableManager(_db, _db.userProfileTable);
}
