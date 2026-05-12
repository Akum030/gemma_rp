# Ground Truth vs QMeans - Comparison Logic Explanation

## Query 1: "Cooler Motor"

### Ground Truth (Claude Opus) Output:
```json
{
  "attributes": [
    {"attribute_key": "motor_type", "value": "cooler motor", "key_priority": 1, "attribute_priority": 1},
    {"attribute_key": "product_type", "value": "cooler motor", "key_priority": 2, "attribute_priority": 1},
    {"attribute_key": "application", "value": "cooler", "key_priority": 1, "attribute_priority": 2},
    {"attribute_key": "use", "value": "cooler", "key_priority": 2, "attribute_priority": 2}
  ]
}
```

**Ground Truth Keys:** motor_type, product_type, application, use  
**Ground Truth Values:** "cooler motor", "cooler"  
**Total Keys:** 4  
**Unique Values:** 2

### QMeans Output:
```json
{
  "success": true,
  "attributes": {
    "usage": "cooler",
    "part type": "motor"
  }
}
```

**QMeans Keys:** usage, part type  
**QMeans Values:** "cooler", "motor"  
**Total Keys:** 2

### Comparison Logic:

#### Key Normalization:
- Converts to lowercase
- Replaces underscores (_) and hyphens (-) with spaces
- Strips whitespace

**Ground Truth Keys (normalized):**
- `motor_type` → `motor type`
- `product_type` → `product type`
- `application` → `application`
- `use` → `use`

**QMeans Keys (normalized):**
- `usage` → `usage`
- `part type` → `part type`

#### Key Matching:
- ❌ `motor type` (GT) ≠ `usage` (QM)
- ❌ `motor type` (GT) ≠ `part type` (QM)
- ❌ `product type` (GT) ≠ `usage` (QM)
- ❌ `product type` (GT) ≠ `part type` (QM)
- ❌ `application` (GT) ≠ `usage` (QM)
- ❌ `application` (GT) ≠ `part type` (QM)
- ❌ `use` (GT) ≠ `usage` (QM)
- ❌ `use` (GT) ≠ `part type` (QM)

**Result: 0 matched keys** (0.00% match rate)

#### Value Matching:
**Ground Truth Values (normalized):**
- `cooler motor` → `cooler motor`
- `cooler` → `cooler`

**QMeans Values (normalized):**
- `cooler` → `cooler`
- `motor` → `motor`

**Matched Values:** ✅ `cooler`

**Result: 1 matched value** (50% match rate - 1 out of 2 GT unique values)

### Why Columns Show This Way:

| Column | Value | Explanation |
|--------|-------|-------------|
| matched_key_count | 0 | No exact key matches after normalization |
| matched_value_count | 1 | "cooler" appears in both |
| gt_only_keys | 4 | product type, application, use, motor type |
| qmeans_only_keys | 2 | usage, part type |
| key_match_rate | 0.00% | 0 matched / 4 GT unique keys |
| value_match_rate | 50.00% | 1 matched / 2 GT unique values |
| matched_keys | (empty) | No keys matched |
| matched_values | cooler | Value that appeared in both |

### Semantic Analysis:
While the keys don't match **literally**, they are semantically related:
- GT's "use" / "application" ≈ QMeans' "usage" (similar meaning)
- GT's "motor_type" / "product_type" ≈ QMeans' "part type" (similar meaning)

The comparison tool uses **exact matching** after normalization, not semantic similarity.

---

## Query 2: "Actuators"

### Ground Truth (Claude Opus) Output:
```json
{
  "attributes": [
    {"attribute_key": "application", "value": "actuator", "key_priority": 1, "attribute_priority": 1},
    {"attribute_key": "use", "value": "actuator", "key_priority": 2, "attribute_priority": 1},
    {"attribute_key": "product_category", "value": "actuator", "key_priority": 1, "attribute_priority": 2},
    {"attribute_key": "category", "value": "actuator", "key_priority": 2, "attribute_priority": 2}
  ]
}
```

**Ground Truth Keys:** application, use, product_category, category  
**Ground Truth Values:** "actuator"  
**Total Keys:** 4  
**Unique Values:** 1

### QMeans Output:
```json
{
  "success": true,
  "attributes": {},  ← EMPTY!
  "response_time": 15.98
}
```

**QMeans Keys:** *(none)*  
**QMeans Values:** *(none)*  
**Total Keys:** 0

### Comparison Logic:

#### Key Matching:
Ground Truth has 4 keys, QMeans has 0 keys.

**Result: 0 matched keys** (0.00% match rate)

#### Value Matching:
Ground Truth has 1 unique value ("actuator"), QMeans has 0 values.

**Result: 0 matched values** (0.00% match rate)

### Why Columns Show This Way:

| Column | Value | Explanation |
|--------|-------|-------------|
| matched_key_count | 0 | QMeans returned no attributes |
| matched_value_count | 0 | QMeans returned no attributes |
| gt_only_keys | 4 | product category, category, application, use |
| qmeans_only_keys | 0 | QMeans didn't extract anything |
| key_match_rate | 0.00% | 0 matched / 4 GT unique keys |
| value_match_rate | 0.00% | 0 matched / 1 GT unique value |
| matched_keys | (empty) | Nothing to match |
| matched_values | (empty) | Nothing to match |

### Analysis:
**QMeans failed to extract any attributes** for this query, while Ground Truth correctly identified it as an "actuator" product category/application.

---

## Key Insights

### 1. **Different Key Naming Conventions**
- Ground Truth uses: motor_type, product_type, application, use, product_category
- QMeans uses: usage, part type, motor type, model name/number

These are semantically similar but **textually different**, causing low key match rates.

### 2. **QMeans Returns Fewer Attributes**
- Ground Truth averages **5.1 keys** per query (with synonyms)
- QMeans averages **1.9 keys** per query
- Ground Truth provides **synonym keys** (application + use, motor_type + product_type)
- QMeans provides **single keys only**

### 3. **Value Matching Works Better**
- Values like "cooler", "siemens", "3 phase" match despite different keys
- 52.4% of queries have at least one value match
- Values are more standardized across systems than keys

### 4. **QMeans Has Empty Responses**
- Some queries return `"attributes": {}` (like "Actuators")
- Ground Truth has higher success rate (98.2% vs QMeans)

---

## Recommendations

### Option 1: Semantic Key Mapping
Create a mapping table to convert keys:
```
GT Key              → QMeans Key
motor_type         → motor type
product_type       → part type
application        → usage
use                → usage
product_category   → part type
```

### Option 2: Focus on Value Comparison
Since values match better than keys, evaluate models based on:
- Correct value extraction (regardless of key name)
- Value completeness

### Option 3: Standardize Key Schema
Define a canonical schema that all systems should use:
```
Canonical Keys:
- brand
- motor_type
- power
- voltage
- phase
- application
```

Would you like me to create a version of the comparison with semantic key mapping applied?
