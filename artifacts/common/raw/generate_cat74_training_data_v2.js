const fs = require('fs');
const path = require('path');

// ============================================================
// Cat_74 (Electric Motors & Components) Training Data Generator v2
// Generates 2000 high-quality training records with priority-based attributes
// ============================================================

// Read and parse CSV
const csvPath = path.join(__dirname, 'Cat_74_5k_data.csv');
const csvData = fs.readFileSync(csvPath, 'utf8').split('\n').slice(1).filter(l => l.trim());
const isqPairs = csvData.map(line => {
    const firstComma = line.indexOf(',');
    if (firstComma === -1) return null;
    return { key: line.substring(0, firstComma).trim(), value: line.substring(firstComma + 1).trim().replace(/^"|"$/g, '').trim() };
}).filter(p => p && p.key && p.value && p.value.length > 0 && p.value.length < 50);

// ============================================================
// KEY SYNONYM MAPPINGS
// ============================================================
const KEY_SYNONYMS = {
    brand: [
        { key: "brand", priority: 1 },
        { key: "company", priority: 2 },
        { key: "manufacturer", priority: 3 },
        { key: "make", priority: 4 }
    ],
    power: [
        { key: "power", priority: 1 },
        { key: "wattage", priority: 2 },
        { key: "motor_power", priority: 3 },
        { key: "power_rating", priority: 4 }
    ],
    voltage: [
        { key: "voltage", priority: 1 },
        { key: "operating_voltage", priority: 2 },
        { key: "supply_voltage", priority: 3 },
        { key: "rated_voltage", priority: 4 }
    ],
    speed: [
        { key: "speed", priority: 1 },
        { key: "rpm", priority: 2 },
        { key: "motor_speed", priority: 3 },
        { key: "rated_speed", priority: 4 }
    ],
    phase: [
        { key: "phase", priority: 1 },
        { key: "phase_type", priority: 2 },
        { key: "number_of_phase", priority: 3 },
        { key: "input_phase", priority: 4 }
    ],
    material: [
        { key: "material", priority: 1 },
        { key: "body_material", priority: 2 },
        { key: "material_type", priority: 3 },
        { key: "casing_material", priority: 4 }
    ],
    usage: [
        { key: "usage_application", priority: 1 },
        { key: "application", priority: 2 },
        { key: "usage", priority: 3 },
        { key: "suitable_for", priority: 4 }
    ],
    type: [
        { key: "type", priority: 1 },
        { key: "motor_type", priority: 2 },
        { key: "product_type", priority: 3 },
        { key: "device_type", priority: 4 }
    ],
    current: [
        { key: "current", priority: 1 },
        { key: "current_rating", priority: 2 },
        { key: "rated_current", priority: 3 },
        { key: "input_current", priority: 4 }
    ],
    mounting: [
        { key: "mounting_type", priority: 1 },
        { key: "mounting", priority: 2 },
        { key: "mounting_style", priority: 3 },
        { key: "mounting_method", priority: 4 }
    ],
    ip_rating: [
        { key: "ip_rating", priority: 1 },
        { key: "protection_class", priority: 2 },
        { key: "degree_of_protection", priority: 3 }
    ],
    capacity: [
        { key: "capacity", priority: 1 },
        { key: "load_capacity", priority: 2 },
        { key: "weight_capacity", priority: 3 },
        { key: "lifting_capacity", priority: 4 }
    ],
    torque: [
        { key: "torque", priority: 1 },
        { key: "output_torque", priority: 2 },
        { key: "rated_torque", priority: 3 },
        { key: "maximum_torque", priority: 4 }
    ],
    horsepower: [
        { key: "horsepower", priority: 1 },
        { key: "horse_power", priority: 2 },
        { key: "hp", priority: 3 },
        { key: "motor_horsepower", priority: 4 }
    ],
    color: [
        { key: "color", priority: 1 },
        { key: "colour", priority: 2 },
        { key: "body_color", priority: 3 }
    ],
    model: [
        { key: "model_number", priority: 1 },
        { key: "model_name", priority: 2 },
        { key: "model", priority: 3 },
        { key: "model_no", priority: 4 }
    ],
    size: [
        { key: "size", priority: 1 },
        { key: "dimension", priority: 2 },
        { key: "frame_size", priority: 3 }
    ],
    frequency: [
        { key: "frequency", priority: 1 },
        { key: "frequency_hertz", priority: 2 },
        { key: "operating_frequency", priority: 3 }
    ],
    weight: [
        { key: "weight", priority: 1 },
        { key: "item_weight", priority: 2 },
        { key: "net_weight", priority: 3 }
    ],
    insulation: [
        { key: "insulation_class", priority: 1 },
        { key: "insulation_type", priority: 2 },
        { key: "winding_insulation", priority: 3 }
    ],
    starter: [
        { key: "starter_type", priority: 1 },
        { key: "starting_method", priority: 2 },
        { key: "starter", priority: 3 }
    ],
    poles: [
        { key: "number_of_poles", priority: 1 },
        { key: "no_of_poles", priority: 2 },
        { key: "poles", priority: 3 }
    ],
    enclosure: [
        { key: "enclosure", priority: 1 },
        { key: "body_enclosure", priority: 2 },
        { key: "housing_protection", priority: 3 }
    ],
    diameter: [
        { key: "diameter", priority: 1 },
        { key: "shaft_diameter", priority: 2 },
        { key: "inner_diameter", priority: 3 }
    ],
    automation: [
        { key: "automation_grade", priority: 1 },
        { key: "operation_mode", priority: 2 },
        { key: "working_mode", priority: 3 }
    ],
    temperature: [
        { key: "ambient_temperature", priority: 1 },
        { key: "operating_temperature", priority: 2 },
        { key: "temperature_range", priority: 3 }
    ],
    power_source: [
        { key: "power_source", priority: 1 },
        { key: "power_supply", priority: 2 },
        { key: "power_type", priority: 3 }
    ],
    pressure: [
        { key: "pressure", priority: 1 },
        { key: "working_pressure", priority: 2 },
        { key: "max_pressure", priority: 3 }
    ],
    efficiency: [
        { key: "efficiency", priority: 1 },
        { key: "energy_efficiency_grade", priority: 2 },
        { key: "star_rating", priority: 3 }
    ],
    warranty: [
        { key: "warranty", priority: 1 },
        { key: "warranty_period", priority: 2 },
        { key: "guarantee", priority: 3 }
    ]
};

// Map CSV keys to clusters
const KEY_TO_CLUSTER = {
    'Brand': 'brand', 'Brand.': 'brand', 'Brand/Make': 'brand', 'Brand/Model': 'brand',
    'Motor Brand': 'brand', 'Manufacturer Brand': 'brand', 'Compressor Brand': 'brand',
    'Truck Brand': 'brand',
    'Power': 'power', 'Rated Power': 'power', 'Power Rating': 'power', 'Motor Power': 'power',
    'Power (Watts or HP)': 'power', 'Power (Watts or H.P.)': 'power', 'Power HP': 'power',
    'Power in HP': 'power', 'Product Power': 'power', 'Output Power': 'power',
    'Machine Power': 'power', 'Spindle Power': 'power', 'Power Output': 'power',
    'Wattage': 'power', 'Watt': 'power', 'Power range': 'power', 'Power(HP)': 'power',
    'Kw/Hp': 'power', 'Power Capacity': 'power',
    'Voltage': 'voltage', 'Motor Voltage': 'voltage', 'Operating Voltage': 'voltage',
    'Input Voltage': 'voltage', 'Rated Voltage': 'voltage', 'Rated Operational Voltage': 'voltage',
    'Voltage (Volt)': 'voltage', 'Voltage V': 'voltage', 'Coil Voltage': 'voltage',
    'Output Voltage': 'voltage', 'Power Supply Voltage': 'voltage', 'Battery Voltage': 'voltage',
    'Speed': 'speed', 'Speed (RPM)': 'speed', 'Speed(RPM)': 'speed', 'Rated Speed': 'speed',
    'Motor Speed': 'speed', 'Speed (Rpm)': 'speed', 'Motor RPM': 'speed',
    'Maximum Speed': 'speed', 'No Load Speed': 'speed', 'Operating Speed': 'speed',
    'Phase': 'phase', 'Phase Type': 'phase', 'Phase Configuration': 'phase',
    'No Of Phase': 'phase', 'Number Of Phase': 'phase', 'Number of Phase': 'phase',
    'Input Phase': 'phase',
    'Material': 'material', 'Material Type': 'material', 'Body Material': 'material',
    'Casing Material': 'material', 'Item Material': 'material', 'Frame Material': 'material',
    'Chassis Material': 'material', 'Blade Material': 'material', 'Winding Material': 'material',
    'Usage/Application': 'usage', 'Application': 'usage', 'Usage': 'usage',
    'Usage/Applications': 'usage', 'Product Usage/Application': 'usage', 'Suitable For': 'usage',
    'Type': 'type', 'Motor Type': 'type', 'Type Of Motor': 'type', 'Product Type': 'type',
    'Device Type': 'type', 'Servo Motor Type': 'type',
    'Current': 'current', 'Current Rating': 'current', 'Rated Current': 'current',
    'Current Rating (Amps)': 'current', 'Input Current': 'current',
    'Mounting Type': 'mounting', 'Mounting': 'mounting', 'Mounting Style': 'mounting',
    'Mounting Method': 'mounting', 'Mounting Options': 'mounting',
    'IP Rating': 'ip_rating', 'Protection Class': 'ip_rating', 'Degree of Protection': 'ip_rating',
    'Capacity': 'capacity', 'Load Capacity': 'capacity', 'Weight Capacity': 'capacity',
    'Weightlifting Capacity': 'capacity', 'Gate Weight Capacity': 'capacity',
    'Running Capacity': 'capacity', 'Motor Capacity': 'capacity',
    'Production Capacity': 'capacity', 'Tank Capacity': 'capacity',
    'Torque': 'torque', 'Output Torque': 'torque', 'Running Torque': 'torque',
    'Stall Torque': 'torque', 'Maximum Torque': 'torque', 'Torque (KGCM)': 'torque',
    'Horsepower': 'horsepower', 'Horse Power': 'horsepower', 'Motor Horse Power': 'horsepower',
    'Motor Horsepower': 'horsepower',
    'Color': 'color', 'Colour': 'color',
    'Model Name/Number': 'model', 'Model Number': 'model', 'Model': 'model',
    'Model No': 'model', 'Model No.': 'model', 'Model Name': 'model',
    'Size': 'size', 'Size/Dimension': 'size', 'Frame Size': 'size', 'Frame size': 'size',
    'Dimensions': 'size', 'Dimension': 'size',
    'Frequency': 'frequency', 'Frequency (Hertz)': 'frequency', 'Frequency Hertz': 'frequency',
    'Frequency(hertz)': 'frequency',
    'Weight': 'weight', 'Item Weight': 'weight',
    'Number of Poles': 'poles', 'No of Poles': 'poles', 'No. of Poles': 'poles',
    'No.Of Poles': 'poles', 'Pole': 'poles', 'Poles': 'poles',
    'Automation Grade': 'automation', 'Operation Mode': 'automation',
    'Ambient Temperature': 'temperature', 'Temperature': 'temperature',
    'Temperature Range': 'temperature', 'Operating Temperature': 'temperature',
    'Max Temperature': 'temperature',
    'Power Source': 'power_source', 'Power Supply': 'power_source',
    'Starter Type': 'starter', 'Starting Method': 'starter',
    'Enclosure': 'enclosure', 'Body Enclosure': 'enclosure',
    'Diameter': 'diameter', 'Shaft Diameter': 'diameter', 'Inner Diameter': 'diameter',
    'Motor Diameter': 'diameter',
    'Pressure': 'pressure', 'Working Pressure': 'pressure', 'Maximum Pressure': 'pressure',
    'Input Pressure': 'pressure',
    'Efficiency': 'efficiency', 'Energy Efficiency Grade': 'efficiency',
    'Star Rating': 'efficiency',
    'Insulation Class': 'insulation', 'Insulation Type': 'insulation',
    'Warranty': 'warranty', 'Warranty Period': 'warranty', 'Guarantee': 'warranty'
};

// Populate value pools
const VALUE_POOLS = {};
Object.keys(KEY_SYNONYMS).forEach(k => VALUE_POOLS[k] = []);

isqPairs.forEach(p => {
    const cluster = KEY_TO_CLUSTER[p.key];
    if (cluster && VALUE_POOLS[cluster]) {
        VALUE_POOLS[cluster].push(p.value);
    }
});

// Deduplicate and clean
Object.keys(VALUE_POOLS).forEach(k => {
    VALUE_POOLS[k] = [...new Set(VALUE_POOLS[k])];
});

// Filter out noisy/invalid values
const GLOBAL_NOISE = new Set([
    'NA', 'N/A', 'na', 'n/a', 'None', 'none', 'Any', 'any', '-', '--',
    'As per requirement', 'As Per Customer Requirement', 'As  Per Customer Requirement',
    'As per customer requirement', 'customize', 'Customized', 'customized',
    'Customisable', 'Customizable', 'good', 'W', 'STD', 'STANDARD',
    'dfghh', 'DEPENS ON MODEL', 'according to variant', 'High', 'low to high',
    'HYDRAULIC', 'Electric', 'Electrical', 'UPTO 2000KW', '900', '180', '200',
    '60', '160', '43', '24000', 'Yes', 'yes', 'No', 'no', 'all',
    'Vary for each variety of side remote motor chosen.',
    'Glass Grinding Edging Machine Motor', 'NATURAL', 'NONE',
    'As Required', 'as required', 'Motor', 'motor',
    'Regular', 'regular', 'Standard', 'standard', 'Normal', 'normal'
]);

// Build lowercase set for case-insensitive matching
const NOISE_LOWER = new Set([...GLOBAL_NOISE].map(v => v.toLowerCase().trim()));

Object.keys(VALUE_POOLS).forEach(k => {
    VALUE_POOLS[k] = VALUE_POOLS[k].filter(v => {
        const vl = v.toLowerCase().trim();
        if (NOISE_LOWER.has(vl)) return false;
        if (vl.includes('as per') || vl.includes('as required') || vl.includes('customer requirement')) return false;
        if (vl.includes('depend') || vl.includes('varies') || vl.includes('variable')) return false;
        if (v.length > 40) return false;
        if (v.length < 1) return false;
        // Filter power_source-type values from power pool
        if (k === 'power' && ['Electric Motor', 'Battery', 'AC', 'DC', 'Electric', 'Electrical',
            'dc', '3 PH', 'HYDRAULIC', 'low to high', 'High', '415', 'Three Phase',
            '230VAC', '380 V-600 V', '12 V DC', 'Electrical', '0.8A', 'AC', 'DC'].includes(v)) return false;
        // Filter non-color values from color pool
        if (k === 'color' && ['STD', 'STANDARD', 'NA', 'NATURAL', 'NONE', 'COPPER'].includes(v.toUpperCase())) return false;
        if (k === 'color' && v.toLowerCase().includes('requirement')) return false;
        // Filter non-power-source from power_source pool  
        if (k === 'power_source' && /^\d/.test(v) && !v.toLowerCase().includes('dc') && !v.toLowerCase().includes('ac')) return false;
        return true;
    });
});

// ============================================================
// IMPORTANCE WEIGHTS for attribute priority
// ============================================================
const IMPORTANCE = {
    power: 10, horsepower: 10, voltage: 9, speed: 9,
    brand: 8, type: 8, model: 7, torque: 8,
    phase: 7, current: 7, capacity: 7,
    mounting: 6, ip_rating: 6, poles: 6, frequency: 6,
    material: 5, size: 5, usage: 5, diameter: 5,
    automation: 5, starter: 5, pressure: 5, power_source: 5,
    enclosure: 4, temperature: 4, insulation: 4, encoder: 4,
    weight: 4, color: 3, efficiency: 5,
    warranty: 2
};

// ============================================================
// UTILITY
// ============================================================
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function pickRandomN(arr, n) { return [...arr].sort(() => Math.random() - 0.5).slice(0, Math.min(n, arr.length)); }
function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5); }

// ============================================================
// PRODUCT TYPES for Cat_74
// ============================================================
const MOTOR_TYPES = [
    'motor', 'electric motor', 'induction motor', 'dc motor', 'ac motor',
    'servo motor', 'stepper motor', 'gear motor', 'bldc motor', 'brushless motor',
    'submersible motor', 'geared motor', 'brake motor', 'vibration motor',
    'motor pump', 'fan motor', 'exhaust fan motor', 'motor drive',
    'motor starter', 'motor controller', 'actuator', 'linear actuator',
    'carbon brush', 'motor brush', 'motor spare', 'encoder',
    'variable frequency drive', 'vfd', 'soft starter',
    'motor', 'motor', 'motor', 'electric motor', 'motor' // weighted towards motor
];

// ============================================================
// NATURAL QUERY GENERATORS
// ============================================================

function buildQuery(attrMap) {
    // attrMap: { cluster: value, ... }
    const clusters = Object.keys(attrMap);
    const vals = Object.values(attrMap).map(v => v.toLowerCase());
    const productType = pickRandom(MOTOR_TYPES);
    const r = Math.random();

    // Check if brand is present
    const hasBrand = clusters.includes('brand');
    const brandVal = hasBrand ? attrMap.brand.toLowerCase() : null;

    // Check if power/hp is present
    const hasPower = clusters.includes('power') || clusters.includes('horsepower');
    const powerVal = hasPower ? (attrMap.power || attrMap.horsepower || '').toLowerCase() : null;

    // Check if voltage  
    const hasVoltage = clusters.includes('voltage');
    const voltageVal = hasVoltage ? attrMap.voltage.toLowerCase() : null;

    // Check phase
    const hasPhase = clusters.includes('phase');
    const phaseVal = hasPhase ? attrMap.phase.toLowerCase() : null;

    // Check speed
    const hasSpeed = clusters.includes('speed');
    const speedVal = hasSpeed ? attrMap.speed.toLowerCase() : null;

    // Build natural parts
    const otherAttrs = clusters.filter(c => !['brand', 'power', 'horsepower', 'voltage', 'phase', 'speed'].includes(c));
    const otherVals = otherAttrs.map(c => attrMap[c].toLowerCase());

    // TEMPLATE SELECTION based on attributes present
    const templates = [];

    // Brand-led queries
    if (hasBrand) {
        templates.push(() => {
            const specs = [];
            if (powerVal) specs.push(powerVal);
            if (voltageVal) specs.push(voltageVal);
            if (phaseVal) specs.push(phaseVal);
            if (speedVal) specs.push(speedVal);
            specs.push(...otherVals);
            return `${brandVal} ${specs.join(' ')} ${productType}`;
        });
        templates.push(() => {
            const specs = [];
            if (powerVal) specs.push(powerVal);
            if (voltageVal) specs.push(voltageVal);
            if (phaseVal) specs.push(phaseVal);
            if (speedVal) specs.push(speedVal);
            specs.push(...otherVals);
            return `${brandVal} make ${productType} ${specs.join(' ')}`;
        });
        templates.push(() => {
            const specs = [];
            if (powerVal) specs.push(powerVal);
            if (voltageVal) specs.push(voltageVal);
            if (phaseVal) specs.push(phaseVal);
            if (speedVal) specs.push(speedVal);
            specs.push(...otherVals);
            return `${brandVal} ${productType}, ${specs.join(', ')}`;
        });
    }

    // Power-led queries
    if (hasPower) {
        templates.push(() => {
            const specs = [];
            if (brandVal) specs.push(brandVal);
            if (voltageVal) specs.push(voltageVal);
            if (phaseVal) specs.push(phaseVal);
            if (speedVal) specs.push(speedVal);
            specs.push(...otherVals);
            return `${powerVal} ${specs.join(' ')} ${productType}`;
        });
    }

    // Spec-heavy queries
    templates.push(() => {
        const allSpecs = [];
        if (brandVal) allSpecs.push(brandVal);
        if (powerVal) allSpecs.push(powerVal);
        if (voltageVal) allSpecs.push(voltageVal);
        if (phaseVal) allSpecs.push(phaseVal);
        if (speedVal) allSpecs.push(speedVal);
        allSpecs.push(...otherVals);
        return `${shuffle(allSpecs).join(' ')} ${productType}`;
    });

    // Enquiry-style
    templates.push(() => {
        const allSpecs = [];
        if (brandVal) allSpecs.push(brandVal);
        if (powerVal) allSpecs.push(powerVal);
        if (voltageVal) allSpecs.push(voltageVal);
        if (phaseVal) allSpecs.push(phaseVal);
        if (speedVal) allSpecs.push(speedVal);
        allSpecs.push(...otherVals);
        return pickRandom([
            `need ${shuffle(allSpecs).join(' ')} ${productType}`,
            `looking for ${shuffle(allSpecs).join(' ')} ${productType}`,
            `buy ${shuffle(allSpecs).join(' ')} ${productType}`,
            `i want ${shuffle(allSpecs).join(' ')} ${productType}`,
            `require ${shuffle(allSpecs).join(' ')} ${productType}`,
        ]);
    });

    // Comma-separated spec
    templates.push(() => {
        const allSpecs = [];
        if (brandVal) allSpecs.push(brandVal);
        if (powerVal) allSpecs.push(powerVal);
        if (voltageVal) allSpecs.push(voltageVal);
        if (phaseVal) allSpecs.push(phaseVal);
        if (speedVal) allSpecs.push(speedVal);
        allSpecs.push(...otherVals);
        return `${productType} ${shuffle(allSpecs).join(', ')}`;
    });

    // "with" style
    templates.push(() => {
        const primary = [];
        const secondary = [];
        if (brandVal) primary.push(brandVal);
        if (powerVal) primary.push(powerVal);
        if (voltageVal) secondary.push(voltageVal);
        if (phaseVal) secondary.push(phaseVal);
        if (speedVal) secondary.push(speedVal);
        secondary.push(...otherVals);
        const p = primary.join(' ');
        const s = secondary.join(' ');
        if (p && s) return `${p} ${productType} with ${s}`;
        return `${p}${s} ${productType}`;
    });

    // Application-specific
    if (clusters.includes('usage')) {
        templates.push(() => {
            const specs = [];
            if (brandVal) specs.push(brandVal);
            if (powerVal) specs.push(powerVal);
            if (voltageVal) specs.push(voltageVal);
            if (phaseVal) specs.push(phaseVal);
            if (speedVal) specs.push(speedVal);
            const useVal = attrMap.usage.toLowerCase();
            const others = otherVals.filter(v => v !== useVal);
            specs.push(...others);
            return `${specs.join(' ')} ${productType} for ${useVal}`;
        });
    }

    // Pick and execute a template
    const fn = pickRandom(templates);
    let query = fn().replace(/\s+/g, ' ').trim();

    return query;
}

// ============================================================
// COMPUTE ATTRIBUTE PRIORITY (query-context-aware)
// ============================================================
function computePriorities(selected) {
    // Sort by importance + numeric specificity bonus
    const sorted = [...selected].sort((a, b) => {
        const wA = (IMPORTANCE[a.cluster] || 5) + (/\d/.test(a.value) ? 2 : 0);
        const wB = (IMPORTANCE[b.cluster] || 5) + (/\d/.test(b.value) ? 2 : 0);
        return wB - wA;
    });
    sorted.forEach((attr, i) => { attr.attributePriority = i + 1; });
    return sorted;
}

// ============================================================
// GENERATE ONE TRAINING RECORD
// ============================================================
function generateRecord() {
    const numAttrs = 2 + Math.floor(Math.random() * 5); // 2 to 6 attributes
    const available = Object.keys(VALUE_POOLS).filter(k => VALUE_POOLS[k].length > 2);

    // Don't pick both power AND horsepower (they overlap)
    let selected = pickRandomN(available, numAttrs + 2).slice(0, numAttrs);
    if (selected.includes('power') && selected.includes('horsepower')) {
        selected = selected.filter(c => c !== 'horsepower');
    }

    // Pick values
    const attrMap = {};
    const attrs = selected.map(cluster => {
        const value = pickRandom(VALUE_POOLS[cluster]);
        attrMap[cluster] = value;
        return { cluster, value, synonyms: KEY_SYNONYMS[cluster] || [{ key: cluster, priority: 1 }] };
    });

    // Compute priorities
    const prioritized = computePriorities(attrs);

    // Build query
    const query = buildQuery(attrMap);

    // Build output attributes with synonyms
    const attributes = [];
    prioritized.forEach(attr => {
        attr.synonyms.forEach(syn => {
            attributes.push({
                attribute_key: syn.key,
                value: attr.value,
                key_priority: syn.priority,
                attribute_priority: attr.attributePriority
            });
        });
    });

    return { query, attributes };
}

// ============================================================
// GENERATE 2000 RECORDS
// ============================================================
console.log('=== Cat_74 Training Data Generator v2 ===');
console.log(`Source: ${isqPairs.length} ISQ pairs`);
Object.keys(VALUE_POOLS).forEach(k => {
    if (VALUE_POOLS[k].length > 0) console.log(`  ${k}: ${VALUE_POOLS[k].length} values`);
});

const records = [];
const seen = new Set();
let attempts = 0;

while (records.length < 2000 && attempts < 15000) {
    attempts++;
    const rec = generateRecord();
    if (seen.has(rec.query)) continue;
    if (rec.attributes.length < 4) continue; // at least 2 attrs with 2+ synonyms each
    seen.add(rec.query);
    records.push(rec);
}

console.log(`\nGenerated: ${records.length} records (${attempts} attempts)`);

// Save JSONL
const outPath = path.join(__dirname, 'cat74_training_data_2000.jsonl');
fs.writeFileSync(outPath, records.map(r => JSON.stringify(r)).join('\n'), 'utf8');
console.log(`Saved: ${outPath}`);

// Save pretty sample
const samplePath = path.join(__dirname, 'cat74_training_data_sample.json');
fs.writeFileSync(samplePath, JSON.stringify(records.slice(0, 10), null, 2), 'utf8');
console.log(`Sample: ${samplePath}`);

// Stats
const avgAttrs = (records.reduce((s, r) => s + r.attributes.length, 0) / records.length).toFixed(1);
console.log(`\nAvg attributes/record: ${avgAttrs}`);
console.log(`Attr range: ${Math.min(...records.map(r => r.attributes.length))} - ${Math.max(...records.map(r => r.attributes.length))}`);

// Count attribute_priority distribution
const priDist = {};
records.forEach(r => {
    const uniquePris = new Set(r.attributes.map(a => a.attribute_priority));
    uniquePris.forEach(p => { priDist[p] = (priDist[p] || 0) + 1; });
});
console.log('\nAttribute priority distribution (how many records have N priorities):');
Object.keys(priDist).sort((a,b)=>a-b).forEach(p => console.log(`  Priority ${p}: ${priDist[p]} records`));

// Sample queries
console.log('\n=== Sample Queries ===');
records.slice(0, 15).forEach((r, i) => {
    const uniqueVals = [...new Set(r.attributes.map(a => a.value))];
    console.log(`${i+1}. "${r.query}"`);
    console.log(`   Attrs: ${uniqueVals.length} values, ${r.attributes.length} total entries`);
});

console.log('\nDone!');
