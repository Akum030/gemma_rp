const fs = require('fs');
const path = require('path');

// ============================================================
// Cat_74 (Electric Motors & Components) Training Data Generator
// Generates 2000 training records with priority-based attributes
// ============================================================

// Read and parse CSV
const csvPath = path.join(__dirname, 'Cat_74_5k_data.csv');
const csvData = fs.readFileSync(csvPath, 'utf8').split('\n').slice(1).filter(l => l.trim());
const isqPairs = csvData.map(line => {
    const firstComma = line.indexOf(',');
    return { key: line.substring(0, firstComma).trim(), value: line.substring(firstComma + 1).trim().replace(/^"|"$/g, '') };
}).filter(p => p.key && p.value);

// Group values by normalized key category
const keyGroups = {};
isqPairs.forEach(p => { 
    if (!keyGroups[p.key]) keyGroups[p.key] = [];
    keyGroups[p.key].push(p.value);
});

// ============================================================
// KEY SYNONYM MAPPINGS with priorities
// key_priority 1 = most appropriate key name
// key_priority 2 = common alternative
// key_priority 3 = less common but valid alternative
// ============================================================

const KEY_SYNONYMS = {
    // --- BRAND cluster ---
    "brand": [
        { key: "brand", priority: 1 },
        { key: "company", priority: 2 },
        { key: "manufacturer", priority: 3 },
        { key: "make", priority: 4 }
    ],
    // --- POWER cluster ---
    "power": [
        { key: "power", priority: 1 },
        { key: "wattage", priority: 2 },
        { key: "motor_power", priority: 3 },
        { key: "power_rating", priority: 4 }
    ],
    // --- VOLTAGE cluster ---
    "voltage": [
        { key: "voltage", priority: 1 },
        { key: "operating_voltage", priority: 2 },
        { key: "supply_voltage", priority: 3 },
        { key: "rated_voltage", priority: 4 }
    ],
    // --- SPEED cluster ---
    "speed": [
        { key: "speed", priority: 1 },
        { key: "rpm", priority: 2 },
        { key: "motor_speed", priority: 3 },
        { key: "rated_speed", priority: 4 }
    ],
    // --- PHASE cluster ---
    "phase": [
        { key: "phase", priority: 1 },
        { key: "phase_type", priority: 2 },
        { key: "number_of_phase", priority: 3 },
        { key: "input_phase", priority: 4 }
    ],
    // --- MATERIAL cluster ---
    "material": [
        { key: "material", priority: 1 },
        { key: "body_material", priority: 2 },
        { key: "material_type", priority: 3 },
        { key: "casing_material", priority: 4 }
    ],
    // --- USAGE cluster ---
    "usage": [
        { key: "usage_application", priority: 1 },
        { key: "application", priority: 2 },
        { key: "usage", priority: 3 },
        { key: "suitable_for", priority: 4 }
    ],
    // --- TYPE cluster ---
    "type": [
        { key: "type", priority: 1 },
        { key: "motor_type", priority: 2 },
        { key: "product_type", priority: 3 },
        { key: "device_type", priority: 4 }
    ],
    // --- CURRENT cluster ---
    "current": [
        { key: "current", priority: 1 },
        { key: "current_rating", priority: 2 },
        { key: "rated_current", priority: 3 },
        { key: "input_current", priority: 4 }
    ],
    // --- MOUNTING cluster ---
    "mounting": [
        { key: "mounting_type", priority: 1 },
        { key: "mounting", priority: 2 },
        { key: "mounting_style", priority: 3 },
        { key: "mounting_method", priority: 4 }
    ],
    // --- IP RATING cluster ---
    "ip_rating": [
        { key: "ip_rating", priority: 1 },
        { key: "protection_class", priority: 2 },
        { key: "degree_of_protection", priority: 3 }
    ],
    // --- CAPACITY cluster ---
    "capacity": [
        { key: "capacity", priority: 1 },
        { key: "load_capacity", priority: 2 },
        { key: "weight_capacity", priority: 3 },
        { key: "lifting_capacity", priority: 4 }
    ],
    // --- TORQUE cluster ---
    "torque": [
        { key: "torque", priority: 1 },
        { key: "output_torque", priority: 2 },
        { key: "rated_torque", priority: 3 },
        { key: "maximum_torque", priority: 4 }
    ],
    // --- HORSEPOWER cluster ---
    "horsepower": [
        { key: "horsepower", priority: 1 },
        { key: "horse_power", priority: 2 },
        { key: "hp", priority: 3 },
        { key: "motor_horsepower", priority: 4 }
    ],
    // --- COLOR cluster ---
    "color": [
        { key: "color", priority: 1 },
        { key: "colour", priority: 2 },
        { key: "body_color", priority: 3 }
    ],
    // --- MODEL cluster ---
    "model": [
        { key: "model_number", priority: 1 },
        { key: "model_name", priority: 2 },
        { key: "model", priority: 3 },
        { key: "model_no", priority: 4 }
    ],
    // --- SIZE cluster ---
    "size": [
        { key: "size", priority: 1 },
        { key: "dimension", priority: 2 },
        { key: "frame_size", priority: 3 },
        { key: "size_dimension", priority: 4 }
    ],
    // --- FREQUENCY cluster ---
    "frequency": [
        { key: "frequency", priority: 1 },
        { key: "frequency_hertz", priority: 2 },
        { key: "operating_frequency", priority: 3 }
    ],
    // --- WEIGHT cluster ---
    "weight": [
        { key: "weight", priority: 1 },
        { key: "item_weight", priority: 2 },
        { key: "net_weight", priority: 3 }
    ],
    // --- INSULATION cluster ---
    "insulation": [
        { key: "insulation_class", priority: 1 },
        { key: "insulation_type", priority: 2 },
        { key: "winding_insulation", priority: 3 }
    ],
    // --- STARTER cluster ---
    "starter": [
        { key: "starter_type", priority: 1 },
        { key: "starting_method", priority: 2 },
        { key: "starter", priority: 3 }
    ],
    // --- POLES cluster ---
    "poles": [
        { key: "number_of_poles", priority: 1 },
        { key: "no_of_poles", priority: 2 },
        { key: "poles", priority: 3 },
        { key: "pole", priority: 4 }
    ],
    // --- ENCLOSURE cluster ---
    "enclosure": [
        { key: "enclosure", priority: 1 },
        { key: "body_enclosure", priority: 2 },
        { key: "housing_protection", priority: 3 }
    ],
    // --- DIAMETER cluster ---
    "diameter": [
        { key: "diameter", priority: 1 },
        { key: "shaft_diameter", priority: 2 },
        { key: "inner_diameter", priority: 3 }
    ],
    // --- STROKE LENGTH cluster ---
    "stroke_length": [
        { key: "stroke_length", priority: 1 },
        { key: "stroke", priority: 2 },
        { key: "travel_length", priority: 3 }
    ],
    // --- AUTOMATION cluster ---
    "automation": [
        { key: "automation_grade", priority: 1 },
        { key: "operation_mode", priority: 2 },
        { key: "working_mode", priority: 3 }
    ],
    // --- WARRANTY cluster ---
    "warranty": [
        { key: "warranty", priority: 1 },
        { key: "warranty_period", priority: 2 },
        { key: "guarantee", priority: 3 }
    ],
    // --- CONDITION cluster ---
    "condition": [
        { key: "condition", priority: 1 },
        { key: "product_condition", priority: 2 }
    ],
    // --- PRESSURE cluster ---
    "pressure": [
        { key: "pressure", priority: 1 },
        { key: "working_pressure", priority: 2 },
        { key: "max_pressure", priority: 3 },
        { key: "input_pressure", priority: 4 }
    ],
    // --- FLOW RATE cluster ---
    "flow_rate": [
        { key: "flow_rate", priority: 1 },
        { key: "max_flow_rate", priority: 2 },
        { key: "air_flow", priority: 3 }
    ],
    // --- TEMPERATURE cluster ---
    "temperature": [
        { key: "ambient_temperature", priority: 1 },
        { key: "operating_temperature", priority: 2 },
        { key: "temperature_range", priority: 3 },
        { key: "max_temperature", priority: 4 }
    ],
    // --- ENCODER cluster ---
    "encoder": [
        { key: "encoder_type", priority: 1 },
        { key: "encoder", priority: 2 },
        { key: "feedback_type", priority: 3 }
    ],
    // --- POWER SOURCE cluster ---
    "power_source": [
        { key: "power_source", priority: 1 },
        { key: "power_supply", priority: 2 },
        { key: "power_type", priority: 3 }
    ],
    // --- EFFICIENCY cluster ---
    "efficiency": [
        { key: "efficiency", priority: 1 },
        { key: "energy_efficiency_grade", priority: 2 },
        { key: "star_rating", priority: 3 }
    ]
};

// ============================================================
// ATTRIBUTE VALUE POOLS (sampled from real CSV data)
// ============================================================

const VALUE_POOLS = {
    brand: [],
    power: [],
    voltage: [],
    speed: [],
    phase: [],
    material: [],
    usage: [],
    type: [],
    current: [],
    mounting: [],
    ip_rating: [],
    capacity: [],
    torque: [],
    horsepower: [],
    color: [],
    model: [],
    size: [],
    frequency: [],
    weight: [],
    poles: [],
    automation: [],
    temperature: [],
    power_source: [],
    starter: [],
    enclosure: [],
    diameter: [],
    stroke_length: [],
    pressure: [],
    condition: [],
    insulation: [],
    encoder: [],
    efficiency: [],
    warranty: []
};

// Map original CSV keys to our clusters
const KEY_TO_CLUSTER = {
    'Brand': 'brand', 'Brand.': 'brand', 'Brand/Make': 'brand', 'Brand/Model': 'brand',
    'Motor Brand': 'brand', 'Manufacturer Brand': 'brand', 'Compressor Brand': 'brand',
    'Power': 'power', 'Rated Power': 'power', 'Power Rating': 'power', 'Motor Power': 'power',
    'Power (Watts or HP)': 'power', 'Power (Watts or H.P.)': 'power', 'Power HP': 'power',
    'Power in HP': 'power', 'Power/Voltage': 'power', 'Product Power': 'power',
    'Power Consumption': 'power', 'Power Capacity': 'power', 'Output Power': 'power',
    'Machine Power': 'power', 'Spindle Power': 'power', 'Power Output': 'power',
    'Wattage': 'power', 'Watt': 'power', 'Power range': 'power', 'Power(HP)': 'power',
    'Kw/Hp': 'power',
    'Voltage': 'voltage', 'Motor Voltage': 'voltage', 'Operating Voltage': 'voltage',
    'Input Voltage': 'voltage', 'Rated Voltage': 'voltage', 'Rated Operational Voltage': 'voltage',
    'Voltage (Volt)': 'voltage', 'Voltage V': 'voltage', 'Voltage Type': 'voltage',
    'Power/Voltage (V)': 'voltage', 'Coil Voltage': 'voltage', 'Output Voltage': 'voltage',
    'Power Supply Voltage': 'voltage', 'Battery Voltage': 'voltage', 'Brake Voltage (V)': 'voltage',
    'Speed': 'speed', 'Speed (RPM)': 'speed', 'Speed(RPM)': 'speed', 'Rated Speed': 'speed',
    'Motor Speed': 'speed', 'Speed (Rpm)': 'speed', 'Motor RPM': 'speed',
    'Maximum Speed': 'speed', 'Max. Speed': 'speed', 'No Load Speed': 'speed',
    'Operating Speed': 'speed', 'Maximum Spindle Speed': 'speed', 'Speed At Rated Load': 'speed',
    'Phase': 'phase', 'Phase Type': 'phase', 'Phase Configuration': 'phase',
    'No Of Phase': 'phase', 'Number Of Phase': 'phase', 'Number of Phase': 'phase',
    'Input Phase': 'phase', 'Motor Phase': 'phase',
    'Material': 'material', 'Material Type': 'material', 'Body Material': 'material',
    'Casing Material': 'material', 'Item Material': 'material', 'Material Used': 'material',
    'Material/Body': 'material', 'Bristle Material': 'material', 'Material Grade': 'material',
    'Material of construction': 'material', 'Material of Construction(Contact)': 'material',
    'Frame Material': 'material', 'Chassis Material': 'material', 'Blade Material': 'material',
    'Winding Material': 'material', 'Coil Material': 'material', 'Tower Material': 'material',
    'Cooler Body Material': 'material',
    'Usage/Application': 'usage', 'Application': 'usage', 'Usage': 'usage',
    'Usage/Applications': 'usage', 'Product Usage/Application': 'usage',
    'Suitable For': 'usage', 'Kind Of Application': 'usage', 'Place of Application': 'usage',
    'Type': 'type', 'Motor Type': 'type', 'Type Of Motor': 'type', 'Product Type': 'type',
    'Device Type': 'type', 'model type': 'type', 'Servo Motor Type': 'type',
    'Current': 'current', 'Current Rating': 'current', 'Rated Current': 'current',
    'Current Rating (Amps)': 'current', 'Input Current': 'current', 'Output Current': 'current',
    'Current Type': 'current',
    'Mounting Type': 'mounting', 'Mounting': 'mounting', 'Mounting Style': 'mounting',
    'Mounting Method': 'mounting', 'Mounting Options': 'mounting',
    'IP Rating': 'ip_rating', 'Protection Class': 'ip_rating', 'Degree of Protection': 'ip_rating',
    'Housing Protection': 'ip_rating',
    'Capacity': 'capacity', 'Load Capacity': 'capacity', 'Weight Capacity': 'capacity',
    'Weightlifting Capacity': 'capacity', 'Gate Weight Capacity': 'capacity',
    'Running Capacity': 'capacity', 'Capacity Range': 'capacity', 'Capacity(Ton)': 'capacity',
    'Output Capacity': 'capacity', 'Rated Output Capacity': 'capacity', 'AC Ton Capacity': 'capacity',
    'Motor Capacity': 'capacity', 'Storage Capacity': 'capacity', 'Production Capacity': 'capacity',
    'Tank Capacity': 'capacity',
    'Torque': 'torque', 'Output Torque': 'torque', 'Running Torque': 'torque',
    'Stall Torque': 'torque', 'Maximum Torque': 'torque', 'Torque (KGCM)': 'torque',
    'Horsepower': 'horsepower', 'Horse Power': 'horsepower', 'Motor Horse Power': 'horsepower',
    'Motor Horsepower': 'horsepower', 'Engine Horsepower': 'horsepower',
    'Color': 'color', 'Colour': 'color',
    'Model Name/Number': 'model', 'Model Number': 'model', 'Model': 'model',
    'Model No': 'model', 'Model No.': 'model', 'Model Name': 'model', 'Model Series': 'model',
    'Size': 'size', 'Size/Dimension': 'size', 'Frame Size': 'size', 'Frame size': 'size',
    'Frame sizes': 'size', 'Dimensions': 'size', 'Dimension': 'size',
    'Frequency': 'frequency', 'Frequency (Hertz)': 'frequency', 'Frequency Hertz': 'frequency',
    'Frequency(hertz)': 'frequency', 'Operating Frequency': 'frequency',
    'Weight': 'weight', 'Item Weight': 'weight',
    'Number of Poles': 'poles', 'No of Poles': 'poles', 'No. of Poles': 'poles',
    'No. of Poles.': 'poles', 'No.Of Poles': 'poles', 'Pole': 'poles', 'Poles': 'poles',
    'Automation Grade': 'automation', 'Operation Mode': 'automation', 'Working Mode': 'automation',
    'Ambient Temperature': 'temperature', 'Temperature': 'temperature',
    'Temperature Range': 'temperature', 'Operating Temperature': 'temperature',
    'Max Temperature': 'temperature', 'Maximum Operating Temperature': 'temperature',
    'Power Source': 'power_source', 'Power Supply': 'power_source', 'Power Type': 'power_source',
    'Power Of Source': 'power_source',
    'Starter Type': 'starter', 'Starting Method': 'starter',
    'Enclosure': 'enclosure', 'Body Enclosure': 'enclosure',
    'Diameter': 'diameter', 'Shaft Diameter': 'diameter', 'Hollow Shaft Diameter': 'diameter',
    'Inner Diameter': 'diameter', 'Gearbox Diameter': 'diameter', 'Motor Diameter': 'diameter',
    'Stroke Length': 'stroke_length',
    'Pressure': 'pressure', 'Working Pressure': 'pressure', 'Maximum Pressure': 'pressure',
    'Max. Pressure': 'pressure', 'Input Pressure': 'pressure',
    'Condition': 'condition',
    'Insulation Class': 'insulation', 'Insulation Type': 'insulation',
    'Winding Insulation': 'insulation', 'Winding protection': 'insulation',
    'Encoder Type': 'encoder',
    'Efficiency': 'efficiency', 'Energy Efficiency Grade': 'efficiency',
    'Star Rating': 'efficiency', 'Full load efficiency': 'efficiency',
    'Warranty': 'warranty', 'Warranty Period': 'warranty', 'Guarantee': 'warranty',
    'Waraanty': 'warranty', 'warrenty': 'warranty'
};

// Populate value pools from CSV data
isqPairs.forEach(p => {
    const cluster = KEY_TO_CLUSTER[p.key];
    if (cluster && VALUE_POOLS[cluster]) {
        VALUE_POOLS[cluster].push(p.value);
    }
});

// Deduplicate and clean value pools
Object.keys(VALUE_POOLS).forEach(k => {
    VALUE_POOLS[k] = [...new Set(VALUE_POOLS[k])].filter(v => v && v.length < 60 && v.length > 0);
});

// ============================================================
// QUERY TEMPLATES - Diverse natural-language patterns
// ============================================================

const QUERY_TEMPLATES = [
    // Simple: 2 attributes
    (attrs) => `${attrs.join(' ')} motor`,
    (attrs) => `${attrs[0]} motor ${attrs.slice(1).join(' ')}`,
    (attrs) => `need ${attrs.join(' ')} electric motor`,
    (attrs) => `buy ${attrs.join(' ')} motor online`,
    (attrs) => `${attrs.join(' ')} motor price`,
    
    // Medium: 3-4 attributes
    (attrs) => `${attrs.join(' ')} motor for ${pickRandom(['industrial', 'commercial', 'home', 'agricultural'])} use`,
    (attrs) => `${attrs[0]} ${attrs[1]} motor with ${attrs.slice(2).join(' and ')}`,
    (attrs) => `looking for ${attrs.join(' ')} motor`,
    (attrs) => `${attrs[0]} make ${attrs.slice(1).join(' ')} motor`,
    (attrs) => `best ${attrs.join(' ')} motor available`,
    
    // Specification style
    (attrs) => `motor specifications: ${attrs.join(', ')}`,
    (attrs) => `${attrs[0]} motor, ${attrs.slice(1).join(', ')}`,
    (attrs) => `electric motor ${attrs.join(' ')} type`,
    (attrs) => `${attrs[0]} ${attrs[1]} ${attrs[2] || ''} motor ${attrs[3] || ''}`.trim(),
    
    // Enquiry style
    (attrs) => `i need a ${attrs.join(' ')} motor`,
    (attrs) => `require ${attrs.join(' ')} motor for my project`,
    (attrs) => `${attrs.join(' ')} induction motor`,
    (attrs) => `${attrs.join(' ')} dc motor`,
    (attrs) => `${attrs.join(' ')} servo motor`,
    (attrs) => `${attrs.join(' ')} stepper motor`,
    (attrs) => `${attrs.join(' ')} gear motor`,
    (attrs) => `${attrs.join(' ')} bldc motor`,
    
    // Product-specific
    (attrs) => `${attrs[0]} ${attrs.slice(1).join(' ')} motor pump`,
    (attrs) => `${attrs.join(' ')} motor for conveyor`,
    (attrs) => `${attrs.join(' ')} motor for crane`,
    (attrs) => `${attrs.join(' ')} motor for compressor`,
    (attrs) => `${attrs.join(' ')} motor for fan`,
    (attrs) => `${attrs.join(' ')} motor for blower`,
    
    // Detailed specifications
    (attrs) => `${attrs[0]} motor with ${attrs[1]} and ${attrs[2] || attrs[1]} rating`,
    (attrs) => `${attrs.join(', ')} - electric motor`,
    (attrs) => `motor - ${attrs.join(' / ')}`,
];

// ============================================================
// ATTRIBUTE PRIORITY RULES
// Priority is contextual - based on how specific the value is
// for narrowing down the product in a search query
// ============================================================

// Base priority ranges for each attribute type
// Lower number = higher priority (more important for search)
const ATTRIBUTE_PRIORITY_RULES = {
    // Technical specs - most critical for motor selection
    power: { basePriority: 1, weight: 10 },
    horsepower: { basePriority: 1, weight: 10 },
    voltage: { basePriority: 1, weight: 9 },
    speed: { basePriority: 1, weight: 9 },
    
    // Identity attributes
    brand: { basePriority: 2, weight: 8 },
    model: { basePriority: 2, weight: 7 },
    type: { basePriority: 2, weight: 8 },
    
    // Electrical specs
    phase: { basePriority: 2, weight: 7 },
    current: { basePriority: 2, weight: 7 },
    frequency: { basePriority: 3, weight: 6 },
    
    // Physical specs
    mounting: { basePriority: 3, weight: 6 },
    material: { basePriority: 3, weight: 5 },
    size: { basePriority: 3, weight: 5 },
    weight: { basePriority: 4, weight: 4 },
    color: { basePriority: 4, weight: 3 },
    diameter: { basePriority: 3, weight: 5 },
    
    // Performance specs
    capacity: { basePriority: 2, weight: 7 },
    torque: { basePriority: 2, weight: 8 },
    ip_rating: { basePriority: 3, weight: 6 },
    efficiency: { basePriority: 3, weight: 5 },
    
    // Operational
    usage: { basePriority: 3, weight: 5 },
    automation: { basePriority: 3, weight: 5 },
    starter: { basePriority: 3, weight: 5 },
    poles: { basePriority: 3, weight: 6 },
    enclosure: { basePriority: 4, weight: 4 },
    
    // Environment
    temperature: { basePriority: 4, weight: 4 },
    pressure: { basePriority: 3, weight: 5 },
    
    // Other
    power_source: { basePriority: 3, weight: 5 },
    encoder: { basePriority: 3, weight: 5 },
    stroke_length: { basePriority: 3, weight: 5 },
    condition: { basePriority: 4, weight: 3 },
    insulation: { basePriority: 4, weight: 4 },
    warranty: { basePriority: 5, weight: 2 },
};

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function pickRandomN(arr, n) {
    const shuffled = [...arr].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, Math.min(n, shuffled.length));
}

function shuffleArray(arr) {
    return [...arr].sort(() => Math.random() - 0.5);
}

// Determine attribute_priority dynamically based on query context
// More specific / numeric values get higher priority
function computeAttributePriority(selectedAttrs) {
    // Sort by weight (importance) descending
    const sorted = [...selectedAttrs].sort((a, b) => {
        const wA = ATTRIBUTE_PRIORITY_RULES[a.cluster]?.weight || 5;
        const wB = ATTRIBUTE_PRIORITY_RULES[b.cluster]?.weight || 5;
        // Add bonus for numeric/specific values
        const specificA = /\d/.test(a.value) ? 2 : 0;
        const specificB = /\d/.test(b.value) ? 2 : 0;
        return (wB + specificB) - (wA + specificA);
    });
    
    // Assign priorities 1, 2, 3... based on sorted position
    let currentPriority = 1;
    sorted.forEach((attr, i) => {
        attr.attributePriority = currentPriority;
        currentPriority++;
    });
    
    return sorted;
}

// Format value for natural query inclusion
function formatValueForQuery(cluster, value) {
    const v = value.toLowerCase().trim();
    switch(cluster) {
        case 'brand': return v;
        case 'power': return v.toLowerCase();
        case 'voltage': return v.toLowerCase().replace(/\s+/g, '');
        case 'speed': return v.toLowerCase();
        case 'phase': return v.toLowerCase();
        case 'color': return v.toLowerCase();
        default: return v.toLowerCase();
    }
}

// ============================================================
// MAIN GENERATION LOGIC
// ============================================================

function generateTrainingRecord(recordIndex) {
    // Decide how many attributes this query will have (2-7)
    const numAttrs = 2 + Math.floor(Math.random() * 6); // 2 to 7
    
    // Select which attribute clusters to use
    const availableClusters = Object.keys(VALUE_POOLS).filter(k => VALUE_POOLS[k].length > 0);
    const selectedClusters = pickRandomN(availableClusters, numAttrs);
    
    // Pick random values from each selected cluster
    const selectedAttrs = selectedClusters.map(cluster => ({
        cluster,
        value: pickRandom(VALUE_POOLS[cluster]),
        synonyms: KEY_SYNONYMS[cluster] || [{ key: cluster, priority: 1 }]
    }));
    
    // Compute attribute priorities based on specificity & importance
    const prioritizedAttrs = computeAttributePriority(selectedAttrs);
    
    // Build query string from attribute values
    const queryParts = shuffleArray(prioritizedAttrs).map(a => formatValueForQuery(a.cluster, a.value));
    const template = pickRandom(QUERY_TEMPLATES);
    let query;
    try {
        query = template(queryParts);
    } catch(e) {
        query = queryParts.join(' ') + ' motor';
    }
    
    // Clean up query
    query = query.replace(/\s+/g, ' ').trim().toLowerCase();
    
    // Build attributes array with key synonyms and priorities
    const attributes = [];
    prioritizedAttrs.forEach(attr => {
        const synonyms = attr.synonyms;
        synonyms.forEach(syn => {
            attributes.push({
                attribute_key: syn.key,
                value: attr.value,
                key_priority: syn.priority,
                attribute_priority: attr.attributePriority
            });
        });
    });
    
    return {
        query,
        attributes
    };
}

// ============================================================
// GENERATE 2000 RECORDS
// ============================================================

console.log('Generating 2000 training records for Cat_74 (Electric Motors)...');
console.log(`Source data: ${isqPairs.length} ISQ key-value pairs`);
console.log(`Unique clusters: ${Object.keys(VALUE_POOLS).filter(k => VALUE_POOLS[k].length > 0).length}`);
console.log('');

// Stats for value pools
Object.keys(VALUE_POOLS).forEach(k => {
    if (VALUE_POOLS[k].length > 0) {
        console.log(`  ${k}: ${VALUE_POOLS[k].length} unique values`);
    }
});
console.log('');

const records = [];
const seenQueries = new Set();

let attempts = 0;
while (records.length < 2000 && attempts < 10000) {
    attempts++;
    const record = generateTrainingRecord(records.length);
    
    // Skip duplicate queries
    if (seenQueries.has(record.query)) continue;
    seenQueries.add(record.query);
    
    // Validate: must have at least 2 attributes with values
    if (record.attributes.length < 4) continue; // At least 2 attrs × 2 key synonyms
    
    records.push(record);
}

console.log(`Generated ${records.length} unique training records`);
console.log(`Total attempts: ${attempts}`);

// ============================================================
// OUTPUT: JSONL format (one JSON per line) for Gemma fine-tuning
// ============================================================

const outputPath = path.join(__dirname, 'cat74_training_data_2000.jsonl');
const jsonlLines = records.map(r => JSON.stringify(r));
fs.writeFileSync(outputPath, jsonlLines.join('\n'), 'utf8');
console.log(`\nSaved to: ${outputPath}`);

// Also save a pretty-printed sample (first 5 records) for review
const samplePath = path.join(__dirname, 'cat74_training_data_sample.json');
fs.writeFileSync(samplePath, JSON.stringify(records.slice(0, 5), null, 2), 'utf8');
console.log(`Sample (5 records) saved to: ${samplePath}`);

// Stats
const avgAttrs = records.reduce((sum, r) => sum + r.attributes.length, 0) / records.length;
const attrCounts = {};
records.forEach(r => {
    const uniqueValues = new Set(r.attributes.map(a => a.value));
    uniqueValues.forEach(v => {
        const cluster = r.attributes.find(a => a.value === v);
        // count unique attribute_priority values
    });
    r.attributes.forEach(a => {
        attrCounts[a.attribute_key] = (attrCounts[a.attribute_key] || 0) + 1;
    });
});

console.log(`\nStats:`);
console.log(`  Average attributes per record: ${avgAttrs.toFixed(1)}`);
console.log(`  Min attributes: ${Math.min(...records.map(r => r.attributes.length))}`);
console.log(`  Max attributes: ${Math.max(...records.map(r => r.attributes.length))}`);

// Top 15 most used attribute keys
const sortedKeys = Object.entries(attrCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);
console.log(`\nTop 15 attribute keys used:`);
sortedKeys.forEach(([key, count]) => console.log(`  ${key}: ${count}`));

console.log('\nDone! Training data ready for Gemma fine-tuning.');
