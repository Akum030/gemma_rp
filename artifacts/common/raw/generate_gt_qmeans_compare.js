/**
 * Ground Truth + QMeans + Gemma V4 Comparison Pipeline (Node.js)
 * ================================================================
 * 
 * Step 1 (Generate GT + fetch QMeans, while Gemma runs on server):
 *   node generate_gt_qmeans_compare.js prepare
 * 
 * Step 2 (Full comparison after getting Gemma CSV):
 *   node generate_gt_qmeans_compare.js compare gemma_v4_1000_results.csv
 */

const fs = require('fs');
const http = require('http');
const path = require('path');

const QUERIES_FILE = path.join(__dirname, 'compare', '76cat_queries');
const OUTPUT_DIR = path.join(__dirname, 'compare');
const GT_CACHE = path.join(OUTPUT_DIR, 'gt_results.json');
const QM_CACHE = path.join(OUTPUT_DIR, 'qmeans_results.json');
const COMPARISON_CSV = path.join(OUTPUT_DIR, 'final_gt_qmeans_gemma_comparison.csv');

// ============================================================================
// PART 1: GROUND TRUTH GENERATOR
// ============================================================================

const BRANDS = {
  'crompton greaves': 'Crompton Greaves', 'godrej lawkim': 'Godrej Lawkim',
  'allen bradley': 'Allen Bradley', 'bharat bijlee': 'Bharat Bijlee',
  'gold power': 'Gold Power', 'apex cool': 'Apex Cool', 'am gold': 'AM Gold',
  'skn kelson': 'SKN Kelson', 'ti motion': 'Ti Motion', 'sew-eurodrive': 'SEW-Eurodrive',
  'sew eurodrive': 'SEW-Eurodrive', 'l & t': 'L&T', 'l&t': 'L&T',
  'siemens': 'Siemens', 'abb': 'ABB', 'crompton': 'Crompton',
  'havells': 'Havells', 'kirloskar': 'Kirloskar', 'lubi': 'Lubi',
  'panasonic': 'Panasonic', 'bosch': 'Bosch', 'makita': 'Makita',
  'schneider': 'Schneider', 'mitsubishi': 'Mitsubishi', 'kollmorgen': 'Kollmorgen',
  'honeywell': 'Honeywell', 'danfoss': 'Danfoss', 'eaton': 'Eaton',
  'parker': 'Parker', 'rotork': 'Rotork', 'belimo': 'Belimo',
  'oriental': 'Oriental', 'godrej': 'Godrej', 'lawkim': 'Lawkim',
  'sunflag': 'Sunflag', 'kenstar': 'Kenstar', 'leadshine': 'Leadshine',
  'tata': 'Tata', 'voltas': 'Voltas', 'baldor': 'Baldor',
  'rexroth': 'Rexroth', 'hydromatik': 'Hydromatik', 'brueninghaus': 'Brueninghaus',
  'remi': 'Remi', 'rhino': 'Rhino', 'pbl': 'PBL', 'impel': 'Impel',
  'transtech': 'Transtech', 'weishaupt': 'Weishaupt', 'ecoflam': 'Ecoflam',
  'hanning': 'Hanning', 'festo': 'Festo', 'spal': 'Spal',
  'venex': 'Venex', 'suguna': 'Suguna', 'paragon': 'Paragon',
  'petrosa': 'Petrosa', 'happymodel': 'Happymodel', 'yako': 'Yako',
  'spg': 'SPG', 'powerspeed': 'PowerSpeed', 'vtv': 'VTV',
  'dys': 'DYS', 'jencoder': 'Jencoder', 'jayashree': 'Jayashree',
  'rexnord': 'Rexnord', 'rotomotive': 'Rotomotive', 'autonic': 'Autonic',
  'hindustan': 'Hindustan', 'bch': 'BCH', 'bhavani': 'Bhavani',
  'rawat': 'Rawat', 'delton': 'Delton', 'arun': 'Arun', 'jyoti': 'Jyoti',
  'alqer': 'Alqer', 'elldo': 'ELLDO', 'vishal': 'Vishal', 'amdo': 'Amdo',
  'kapcon': 'Kapcon', 'peco': 'Peco', 'boparai': 'Boparai',
  'symphony': 'Symphony', 'laxmi': 'Laxmi', 'intermot': 'Intermot',
  'foredom': 'Foredom',
};

function cleanQuery(q) {
  try { q = decodeURIComponent(q); } catch (e) {}
  return q.replace(/\+/g, ' ').replace(/\s+/g, ' ').trim();
}

function extractGroundTruth(rawQuery) {
  const query = cleanQuery(rawQuery);
  const q = query.toLowerCase();
  const attrs = {};

  // --- BRAND ---
  const brandKeys = Object.keys(BRANDS).sort((a, b) => b.length - a.length);
  for (const bk of brandKeys) {
    // Create regex with word boundaries where possible
    const escaped = bk.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`(?:^|\\s|,)${escaped}(?:\\s|,|$|'s)`, 'i');
    if (pattern.test(q) || (bk.length >= 4 && q.includes(bk))) {
      attrs.brand = BRANDS[bk];
      break;
    }
  }

  // --- POWER (HP) ---
  const hpMatch = q.match(/(\d+\.?\d*)\s*(?:hp|horse\s*power)/i);
  if (hpMatch) attrs.power = hpMatch[1] + ' HP';

  // --- POWER (KW) ---
  const kwMatch = q.match(/(\d+\.?\d*)\s*(?:kw|kilowatt)/i);
  if (kwMatch) {
    if (!attrs.power) attrs.power = kwMatch[1] + ' KW';
    else attrs.power_kw = kwMatch[1] + ' KW';
  }

  // --- POWER (Watt) - but not kw ---
  if (!attrs.power && !kwMatch) {
    const wMatch = q.match(/(\d+\.?\d*)\s*(?:watt|watts|w)\b/i);
    if (wMatch) {
      const val = wMatch[1];
      // Avoid matching voltage patterns like "230v" → "230 w" false positive
      if (!q.match(new RegExp(val + '\\s*v', 'i'))) {
        attrs.power = val + ' W';
      }
    }
  }

  // --- PHASE ---
  if (/(?:single|1)\s*(?:-?\s*)?phase/i.test(q)) attrs.phase = 'single phase';
  else if (/(?:three|3)\s*(?:-?\s*)?phase/i.test(q)) attrs.phase = 'three phase';
  else if (/(?:two|2)\s*(?:-?\s*)?phase/i.test(q)) attrs.phase = 'two phase';

  // --- VOLTAGE ---
  const vMatch = q.match(/(\d+\.?\d*)\s*(?:v|volt|volts)\b/i);
  if (vMatch) attrs.voltage = vMatch[1] + 'V';

  // --- SPEED (RPM) ---
  const rpmMatch = q.match(/(\d+)\s*rpm/i);
  if (rpmMatch) attrs.speed = rpmMatch[1] + ' RPM';

  // --- MOTOR TYPE ---
  const motorTypes = [
    [/squirrel\s*cage/i, 'squirrel cage motor'],
    [/slip\s*ring/i, 'slip ring motor'],
    [/worm\s*gear/i, 'worm geared motor'],
    [/helical\s*gear/i, 'helical geared motor'],
    [/planetary\s*gear/i, 'planetary geared motor'],
    [/brushless\s*dc|bldc/i, 'BLDC motor'],
    [/brushless/i, 'brushless motor'],
    [/induction/i, 'induction motor'],
    [/servo\s*motor|servo\b/i, 'servo motor'],
    [/stepper/i, 'stepper motor'],
    [/gear(?:ed)?\s*motor/i, 'geared motor'],
    [/synchronous/i, 'synchronous motor'],
    [/pmdc/i, 'PMDC motor'],
    [/hydraulic\s*piston/i, 'hydraulic piston motor'],
    [/hydraulic\s*motor|hydraulic/i, 'hydraulic motor'],
    [/vibrat(?:ory|ion)\s*motor/i, 'vibratory motor'],
    [/shaded\s*pole/i, 'shaded pole motor'],
    [/dc\s*motor|\bdc\b.*motor/i, 'DC motor'],
    [/ac\s*motor|\bac\b.*motor/i, 'AC motor'],
  ];

  for (const [pattern, value] of motorTypes) {
    if (pattern.test(q)) {
      attrs.motor_type = value;
      break;
    }
  }

  // --- PRODUCT TYPE (non-motor) ---
  if (!attrs.motor_type) {
    const productTypes = [
      [/dol\s*starter|direct\s*on\s*line\s*starter/i, 'DOL starter'],
      [/soft\s*start/i, 'soft starter'],
      [/star\s*delta\s*starter/i, 'star delta starter'],
      [/motor\s*starter|starter/i, 'motor starter'],
      [/linear\s*actuator/i, 'linear actuator'],
      [/rotary\s*actuator/i, 'rotary actuator'],
      [/pneumatic\s*actuator/i, 'pneumatic actuator'],
      [/actuator/i, 'actuator'],
      [/rotary\s*encoder/i, 'rotary encoder'],
      [/shaft\s*encoder|encoder/i, 'encoder'],
      [/carbon\s*brush/i, 'carbon brush'],
      [/armature/i, 'armature'],
      [/valve\s*positioner|positioner/i, 'valve positioner'],
      [/slip\s*ring/i, 'slip ring'],
    ];
    for (const [pattern, value] of productTypes) {
      if (pattern.test(q)) {
        attrs.product_type = value;
        break;
      }
    }
  }

  // --- USAGE / APPLICATION ---
  const usages = [
    [/vacuum\s*cleaner/i, 'vacuum cleaner'], [/air\s*cooler/i, 'air cooler'],
    [/air\s*conditioner/i, 'air conditioner'], [/mixer\s*grinder/i, 'mixer grinder'],
    [/table\s*fan/i, 'table fan'], [/wall\s*fan/i, 'wall fan'],
    [/tower\s*fan/i, 'tower fan'], [/exhaust\s*fan/i, 'exhaust fan'],
    [/ceiling\s*fan/i, 'ceiling fan'], [/desert\s*(?:type)?\s*cooler/i, 'desert cooler'],
    [/rolling\s*shutter/i, 'rolling shutter'], [/sliding\s*gate/i, 'sliding gate'],
    [/swing\s*gate/i, 'swing gate'], [/sliding\s*door/i, 'sliding door'],
    [/kitchen\s*(?:hood|chimney)/i, 'kitchen chimney'],
    [/concrete\s*vibrator/i, 'concrete vibrator'],
    [/sewing\s*machine/i, 'sewing machine'], [/centrifuge/i, 'centrifuge'],
    [/submersible/i, 'submersible pump'], [/incubator/i, 'incubator'],
    [/polisher/i, 'polisher'], [/mig\s*(?:welding)?/i, 'MIG welding'],
    [/cooler/i, 'cooler'], [/chimney/i, 'chimney'], [/blower/i, 'blower'],
    [/exhaust/i, 'exhaust'], [/fan\b/i, 'fan'], [/pump/i, 'pump'],
    [/crane/i, 'crane'], [/lift\b/i, 'lift'], [/gate\b/i, 'gate'],
    [/door\b/i, 'door'], [/shutter/i, 'shutter'], [/drone/i, 'drone'],
    [/spindle/i, 'spindle'], [/burner/i, 'burner'],
  ];
  for (const [pattern, value] of usages) {
    if (pattern.test(q)) {
      attrs.usage = value;
      break;
    }
  }

  // --- MOUNTING ---
  if (/foot\s*cum\s*flange/i.test(q)) attrs.mounting = 'foot cum flange';
  else if (/foot\s*mount/i.test(q)) attrs.mounting = 'foot mounted';
  else if (/flange\s*mount/i.test(q)) attrs.mounting = 'flange mounted';
  else if (/face\s*mount/i.test(q)) attrs.mounting = 'face mounted';
  else if (/\bvertical\b/i.test(q) && /motor|shaft/i.test(q)) attrs.mounting = 'vertical';

  // --- ENCLOSURE ---
  if (/\btefc\b/i.test(q)) attrs.enclosure = 'TEFC';
  else if (/\bip55\b/i.test(q)) attrs.enclosure = 'IP55';
  else if (/\bip54\b/i.test(q)) attrs.enclosure = 'IP54';
  else if (/flame\s*proof|flameproof|fireproof/i.test(q)) attrs.enclosure = 'flameproof';

  // --- EFFICIENCY ---
  const effMatch = q.match(/\b(ie[234])\b/i);
  if (effMatch) attrs.efficiency = effMatch[1].toUpperCase();

  // --- POLES ---
  const poleMatch = q.match(/(\d+)\s*pole/i);
  if (poleMatch) attrs.poles = poleMatch[1] + ' pole';

  // --- SHAFT TYPE ---
  if (/dual\s*shaft|double\s*shaft/i.test(q)) attrs.shaft_type = 'dual shaft';
  else if (/hollow\s*shaft/i.test(q)) attrs.shaft_type = 'hollow shaft';
  else if (/side\s*shaft/i.test(q)) attrs.shaft_type = 'side shaft';

  // --- MODEL NUMBER (Siemens patterns) ---
  const siemensModel = q.match(/\b(1fk2[\w-]+|1fl[26][\w-]+|1le[\w-]+|3tw[\w-]+|6dr[\w-]+)\b/i);
  if (siemensModel) attrs.model_number = siemensModel[1].toUpperCase();

  // --- NEMA / FRAME SIZE ---
  const nemaMatch = q.match(/nema\s*(\d+)/i);
  if (nemaMatch) attrs.frame_size = 'NEMA ' + nemaMatch[1];

  // --- STEP ANGLE ---
  const angleMatch = q.match(/(\d+\.?\d*)\s*degree/i);
  if (angleMatch) attrs.step_angle = angleMatch[1] + ' degree';

  // --- MATERIAL ---
  if (/\balumini?um\b/i.test(q)) attrs.material = 'aluminium';
  else if (/cast\s*iron/i.test(q)) attrs.material = 'cast iron';
  else if (/\bcopper\b/i.test(q)) attrs.material = 'copper';
  else if (/mild\s*steel/i.test(q)) attrs.material = 'mild steel';

  // --- KV rating ---
  const kvMatch = q.match(/(\d+)\s*kv\b/i);
  if (kvMatch && !kwMatch) attrs.kv_rating = kvMatch[1] + ' KV';

  // --- CURRENT (Amps) ---
  const ampMatch = q.match(/(\d+\.?\d*)\s*(?:amp|amps|a)\b/i);
  if (ampMatch) attrs.current = ampMatch[1] + ' A';

  // If nothing found, try generic product detection
  if (Object.keys(attrs).length === 0) {
    if (/motor|motar|moter/i.test(q)) attrs.product_type = 'motor';
    else if (/starter/i.test(q)) attrs.product_type = 'starter';
    else if (/actuator/i.test(q)) attrs.product_type = 'actuator';
    else if (/encoder/i.test(q)) attrs.product_type = 'encoder';
    else if (/brush/i.test(q)) attrs.product_type = 'carbon brush';
  }

  return attrs;
}


// ============================================================================
// PART 2: QMEANS API FETCHER
// ============================================================================

function fetchQMeans(query) {
  return new Promise((resolve) => {
    const encoded = encodeURIComponent(query);
    const url = `http://34.93.70.216:8009/attribute-search-qmeans?query=${encoded}`;

    const req = http.get(url, { timeout: 30000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const attrs = {};
          if (parsed.response_code === 200 && parsed.attributes) {
            for (const [token, info] of Object.entries(parsed.attributes)) {
              const name = info.attr_name || '';
              const value = info.attr_value || '';
              if (name && value) attrs[name] = value;
            }
          }
          resolve({ success: true, attributes: attrs, response_time: parsed.response_time || 0 });
        } catch (e) {
          resolve({ success: false, attributes: {}, error: e.message });
        }
      });
    });

    req.on('error', (e) => resolve({ success: false, attributes: {}, error: e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ success: false, attributes: {}, error: 'timeout' }); });
  });
}

async function fetchAllQMeans(queries) {
  const results = {};
  const total = queries.length;

  console.log(`\nFetching QMeans for ${total} queries...`);
  console.log('='.repeat(80));

  for (let i = 0; i < total; i++) {
    const query = queries[i];
    const result = await fetchQMeans(query);
    result.query = query;
    results[query] = result;

    if ((i + 1) % 50 === 0) {
      const successCount = Object.values(results).filter(r => r.success).length;
      console.log(`  [${i + 1}/${total}] QMeans processed (${successCount}/${i + 1} success)`);
      // Save checkpoint
      fs.writeFileSync(QM_CACHE, JSON.stringify(Object.values(results), null, 2), 'utf-8');
    }

    // Small delay
    await new Promise(r => setTimeout(r, 30));
  }

  fs.writeFileSync(QM_CACHE, JSON.stringify(Object.values(results), null, 2), 'utf-8');
  const successCount = Object.values(results).filter(r => r.success).length;
  console.log(`\nQMeans done: ${successCount}/${total} successful`);

  return results;
}


// ============================================================================
// PART 3: GEMMA RESULTS READER
// ============================================================================

function readGemmaResults(csvPath) {
  const results = {};
  const content = fs.readFileSync(csvPath, 'utf-8');
  const lines = content.split('\n');
  
  if (lines.length < 2) return results;
  
  // Parse CSV header
  const header = parseCSVLine(lines[0]);
  const queryIdx = header.indexOf('query');
  const successIdx = header.indexOf('success');
  const uniqueIdx = header.indexOf('unique_value_count');
  const totalIdx = header.indexOf('total_key_count');
  const rawIdx = header.indexOf('raw_output');
  const jsonIdx = header.indexOf('attributes_json');

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    
    const cols = parseCSVLine(lines[i]);
    const query = (cols[queryIdx] || '').trim();
    if (!query) continue;

    let allAttrs = [];
    try {
      if (cols[jsonIdx]) {
        const parsed = JSON.parse(cols[jsonIdx]);
        allAttrs = parsed.attributes || [];
      }
    } catch (e) {}

    // Group by unique values
    const valueGroups = {};
    for (const attr of allAttrs) {
      const val = String(attr.value || '').trim();
      const key = String(attr.attribute_key || '').trim();
      const keyP = attr.key_priority || 0;
      const attrP = attr.attribute_priority || 0;
      const valLower = val.toLowerCase();

      if (!valueGroups[valLower]) {
        valueGroups[valLower] = { value: val, keys: [], attr_priority: attrP };
      }
      valueGroups[valLower].keys.push({ key, key_priority: keyP });
    }

    results[query] = {
      success: cols[successIdx] === 'True',
      raw_output: cols[rawIdx] || '',
      unique_value_count: parseInt(cols[uniqueIdx]) || 0,
      total_key_count: parseInt(cols[totalIdx]) || 0,
      all_attributes: allAttrs,
      value_groups: valueGroups
    };
  }

  return results;
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}


// ============================================================================
// PART 4: COMPARISON ENGINE
// ============================================================================

const KEY_SYNONYMS = {
  'brand': ['brand', 'company', 'manufacturer', 'make'],
  'power': ['power', 'wattage', 'motor power', 'power rating', 'horsepower', 'horse power', 'hp', 'power kw'],
  'voltage': ['voltage', 'operating voltage', 'supply voltage', 'rated voltage'],
  'phase': ['phase', 'phase type', 'number of phase'],
  'speed': ['speed', 'rpm', 'motor speed', 'rated speed'],
  'motor type': ['motor type', 'type', 'product type', 'machine type'],
  'mounting': ['mounting', 'mounting type', 'mount type'],
  'usage': ['usage', 'application', 'usage application'],
  'enclosure': ['enclosure', 'body enclosure', 'enclosure type'],
  'efficiency': ['efficiency', 'efficiency class', 'energy efficiency'],
  'model number': ['model number', 'model', 'part number', 'model no'],
  'material': ['material', 'body material', 'construction material'],
  'product type': ['product type', 'type', 'product', 'part type'],
  'shaft type': ['shaft type', 'shaft'],
  'poles': ['poles', 'no of poles', 'number of poles'],
  'frame size': ['frame size', 'frame', 'nema size'],
  'gear ratio': ['gear ratio', 'ratio', 'reduction ratio'],
  'kv rating': ['kv rating', 'kv'],
  'step angle': ['step angle', 'angle'],
  'current': ['current', 'rated current', 'ampere'],
  'weight': ['weight', 'product weight'],
};

function normalizeKey(key) {
  const k = key.toLowerCase().trim().replace(/[_\-\s]+/g, ' ');
  for (const [canonical, synonyms] of Object.entries(KEY_SYNONYMS)) {
    if (synonyms.includes(k)) return canonical;
  }
  return k;
}

function normalizeValue(value) {
  return String(value).toLowerCase().trim().replace(/\s+/g, ' ');
}

function checkKeyMatch(gtKey, comparKeys) {
  const gtNorm = normalizeKey(gtKey);
  for (const ck of comparKeys) {
    if (normalizeKey(ck) === gtNorm) return true;
  }
  return false;
}

function checkValueMatch(gtVal, comparVals) {
  const gtV = normalizeValue(gtVal);
  for (const cv of comparVals) {
    const cvN = normalizeValue(cv);
    if (gtV === cvN) return true;
    if (gtV.includes(cvN) || cvN.includes(gtV)) return true;
    // Numeric match
    const gtNums = new Set((gtV.match(/\d+\.?\d*/g) || []));
    const cvNums = new Set((cvN.match(/\d+\.?\d*/g) || []));
    if (gtNums.size > 0 && gtNums.size === cvNums.size) {
      let allMatch = true;
      for (const n of gtNums) { if (!cvNums.has(n)) allMatch = false; }
      if (allMatch) return true;
    }
  }
  return false;
}

function buildComparison(queries, gtResults, qmResults, gemResults) {
  const rows = [];

  for (const query of queries) {
    const gtAttrs = gtResults[query] || {};
    const qmData = qmResults[query] || {};
    const qmAttrs = qmData.attributes || {};
    const gemData = gemResults[query] || {};

    const gtCount = Object.keys(gtAttrs).length;
    const qmCount = Object.keys(qmAttrs).length;
    const gemUnique = gemData.unique_value_count || 0;
    const gemTotalKeys = gemData.total_key_count || 0;
    const gemAllAttrs = gemData.all_attributes || [];
    const gemValueGroups = gemData.value_groups || {};

    // Gemma primary attrs (key_priority=1 only)
    const gemPrimaryAttrs = {};
    const gemPriorityInfo = [];
    for (const vg of Object.values(gemValueGroups)) {
      const sortedKeys = vg.keys.sort((a, b) => (a.key_priority || 99) - (b.key_priority || 99));
      const primary = sortedKeys[0];
      if (primary) {
        gemPrimaryAttrs[primary.key] = vg.value;
        gemPriorityInfo.push(`${primary.key}=${vg.value}(P${vg.attr_priority || '?'})`);
      }
    }

    // All gemma keys + values for matching
    const allGemmaKeys = new Set(gemAllAttrs.map(a => String(a.attribute_key || '').trim()));
    const allGemmaValues = new Set(gemAllAttrs.map(a => normalizeValue(a.value || '')));

    // GT vs QMeans
    let gtVsQmKeyMatch = 0, gtVsQmValMatch = 0;
    const qmKeys = Object.keys(qmAttrs);
    const qmVals = Object.values(qmAttrs);
    for (const [gk, gv] of Object.entries(gtAttrs)) {
      if (checkKeyMatch(gk, qmKeys)) gtVsQmKeyMatch++;
      if (checkValueMatch(gv, qmVals)) gtVsQmValMatch++;
    }

    // GT vs Gemma
    let gtVsGemKeyMatch = 0, gtVsGemValMatch = 0;
    const gtVsGemDetails = [];
    for (const [gk, gv] of Object.entries(gtAttrs)) {
      const keyMatched = checkKeyMatch(gk, [...allGemmaKeys]);
      const valMatched = checkValueMatch(gv, [...allGemmaValues]);
      if (keyMatched) gtVsGemKeyMatch++;
      if (valMatched) gtVsGemValMatch++;

      // Find priority info for matched gemma attribute
      let matchPriority = '';
      for (const vg of Object.values(gemValueGroups)) {
        if (checkValueMatch(gv, [vg.value])) {
          for (const k of vg.keys) {
            if (checkKeyMatch(gk, [k.key])) {
              matchPriority = `kp=${k.key_priority},ap=${vg.attr_priority || '?'}`;
              break;
            }
          }
          break;
        }
      }

      gtVsGemDetails.push(`${gk}:${gv}->${keyMatched ? 'MATCH' : 'MISS'}${matchPriority ? '(' + matchPriority + ')' : ''}`);
    }

    // QMeans vs Gemma
    let qmVsGemKeyMatch = 0, qmVsGemValMatch = 0;
    for (const [qk, qv] of Object.entries(qmAttrs)) {
      if (checkKeyMatch(qk, [...allGemmaKeys])) qmVsGemKeyMatch++;
      if (checkValueMatch(qv, [...allGemmaValues])) qmVsGemValMatch++;
    }

    // Winner
    let winner = 'TIE';
    if (gtVsGemKeyMatch > gtVsQmKeyMatch) winner = 'GEMMA';
    else if (gtVsQmKeyMatch > gtVsGemKeyMatch) winner = 'QMEANS';

    rows.push({
      query,
      gt_attr_count: gtCount,
      qmeans_attr_count: qmCount,
      gemma_unique_values: gemUnique,
      gemma_total_keys: gemTotalKeys,
      gt_attrs: gtCount > 0 ? JSON.stringify(gtAttrs) : '',
      qmeans_attrs: qmCount > 0 ? JSON.stringify(qmAttrs) : '',
      gemma_primary_attrs: Object.keys(gemPrimaryAttrs).length > 0 ? JSON.stringify(gemPrimaryAttrs) : '',
      gt_vs_qmeans_key_match: gtVsQmKeyMatch,
      gt_vs_qmeans_value_match: gtVsQmValMatch,
      gt_vs_gemma_key_match: gtVsGemKeyMatch,
      gt_vs_gemma_value_match: gtVsGemValMatch,
      qmeans_vs_gemma_key_match: qmVsGemKeyMatch,
      qmeans_vs_gemma_value_match: qmVsGemValMatch,
      gt_vs_qmeans_key_pct: gtCount > 0 ? Math.round(gtVsQmKeyMatch / gtCount * 100) + '%' : 'N/A',
      gt_vs_gemma_key_pct: gtCount > 0 ? Math.round(gtVsGemKeyMatch / gtCount * 100) + '%' : 'N/A',
      gemma_priority_info: gemPriorityInfo.join(' | '),
      winner_key_match: winner,
      gt_vs_gemma_detail: gtVsGemDetails.join(' | '),
    });
  }

  return rows;
}

function writeCSV(rows, filepath) {
  if (rows.length === 0) return;
  const keys = Object.keys(rows[0]);
  const header = keys.map(k => `"${k}"`).join(',');
  const lines = [header];

  for (const row of rows) {
    const vals = keys.map(k => {
      let v = String(row[k] || '');
      v = v.replace(/"/g, '""');
      return `"${v}"`;
    });
    lines.push(vals.join(','));
  }

  fs.writeFileSync(filepath, lines.join('\n'), 'utf-8');
}


// ============================================================================
// MAIN
// ============================================================================

async function main() {
  const args = process.argv.slice(2);
  const step = args[0] || 'all';
  const gemmaCSV = args[1] || '';

  // Read queries
  const content = fs.readFileSync(QUERIES_FILE, 'utf-8');
  const lines = content.split('\n').map(l => l.trim()).filter(l => l && l.toLowerCase() !== 'query');
  console.log(`Loaded ${lines.length} queries\n`);

  // ---- STEP 1: Ground Truth ----
  let gtResults;
  if (fs.existsSync(GT_CACHE)) {
    console.log(`Loading cached GT from ${GT_CACHE}`);
    gtResults = JSON.parse(fs.readFileSync(GT_CACHE, 'utf-8'));
  } else {
    console.log('--- Generating Ground Truth ---');
    gtResults = {};
    for (const query of lines) {
      gtResults[query] = extractGroundTruth(query);
    }
    fs.writeFileSync(GT_CACHE, JSON.stringify(gtResults, null, 2), 'utf-8');

    const totalAttrs = Object.values(gtResults).reduce((s, v) => s + Object.keys(v).length, 0);
    const withAttrs = Object.values(gtResults).filter(v => Object.keys(v).length > 0).length;
    console.log(`GT done: ${withAttrs}/${lines.length} queries have attrs (${totalAttrs} total, avg ${(totalAttrs / lines.length).toFixed(1)}/query)`);
  }

  // ---- STEP 2: QMeans ----
  let qmResults;
  if (fs.existsSync(QM_CACHE)) {
    console.log(`Loading cached QMeans from ${QM_CACHE}`);
    const qmList = JSON.parse(fs.readFileSync(QM_CACHE, 'utf-8'));
    qmResults = {};
    for (const r of qmList) qmResults[r.query] = r;
  } else {
    qmResults = await fetchAllQMeans(lines);
  }

  if (step === 'prepare') {
    console.log('\n✅ GT and QMeans prepared!');
    console.log('Now run Gemma inference on server, then:');
    console.log('  node generate_gt_qmeans_compare.js compare gemma_v4_1000_results.csv');
    return;
  }

  // ---- STEP 3: Read Gemma ----
  let gemResults = {};
  if (gemmaCSV && fs.existsSync(gemmaCSV)) {
    console.log(`\nLoading Gemma V4 results from ${gemmaCSV}`);
    gemResults = readGemmaResults(gemmaCSV);
    console.log(`  Loaded ${Object.keys(gemResults).length} Gemma results`);
  } else if (step === 'compare') {
    console.log('\n⚠️  Gemma CSV not found. Running without Gemma results.');
  }

  // ---- STEP 4: Build comparison ----
  console.log('\n--- Building Comparison ---');
  const comparison = buildComparison(lines, gtResults, qmResults, gemResults);
  writeCSV(comparison, COMPARISON_CSV);
  console.log(`\n✅ Comparison saved to: ${COMPARISON_CSV}`);

  // ---- Summary ----
  console.log('\n' + '='.repeat(80));
  console.log('COMPARISON SUMMARY');
  console.log('='.repeat(80));

  const total = comparison.length;
  const gtHas = comparison.filter(r => r.gt_attr_count > 0).length;
  const qmHas = comparison.filter(r => r.qmeans_attr_count > 0).length;
  const gemHas = comparison.filter(r => r.gemma_unique_values > 0).length;

  console.log(`\nQueries with attributes detected:`);
  console.log(`  Ground Truth:  ${gtHas}/${total} (${(gtHas * 100 / total).toFixed(1)}%)`);
  console.log(`  QMeans:        ${qmHas}/${total} (${(qmHas * 100 / total).toFixed(1)}%)`);
  console.log(`  Gemma V4:      ${gemHas}/${total} (${(gemHas * 100 / total).toFixed(1)}%)`);

  const gtQmKeyM = comparison.reduce((s, r) => s + r.gt_vs_qmeans_key_match, 0);
  const gtTotal = comparison.reduce((s, r) => s + r.gt_attr_count, 0);
  const gtGemKeyM = comparison.reduce((s, r) => s + r.gt_vs_gemma_key_match, 0);
  const gtQmValM = comparison.reduce((s, r) => s + r.gt_vs_qmeans_value_match, 0);
  const gtGemValM = comparison.reduce((s, r) => s + r.gt_vs_gemma_value_match, 0);

  console.log(`\nKey Match Rates (vs Ground Truth):`);
  console.log(`  QMeans: ${gtQmKeyM}/${gtTotal} (${(gtQmKeyM * 100 / Math.max(1, gtTotal)).toFixed(1)}%)`);
  console.log(`  Gemma:  ${gtGemKeyM}/${gtTotal} (${(gtGemKeyM * 100 / Math.max(1, gtTotal)).toFixed(1)}%)`);

  console.log(`\nValue Match Rates (vs Ground Truth):`);
  console.log(`  QMeans: ${gtQmValM}/${gtTotal} (${(gtQmValM * 100 / Math.max(1, gtTotal)).toFixed(1)}%)`);
  console.log(`  Gemma:  ${gtGemValM}/${gtTotal} (${(gtGemValM * 100 / Math.max(1, gtTotal)).toFixed(1)}%)`);

  if (Object.keys(gemResults).length > 0) {
    const gemWins = comparison.filter(r => r.winner_key_match === 'GEMMA').length;
    const qmWins = comparison.filter(r => r.winner_key_match === 'QMEANS').length;
    const ties = comparison.filter(r => r.winner_key_match === 'TIE').length;

    console.log(`\nHead-to-Head (per query, GT key match):`);
    console.log(`  Gemma wins:  ${gemWins} (${(gemWins * 100 / total).toFixed(1)}%)`);
    console.log(`  QMeans wins: ${qmWins} (${(qmWins * 100 / total).toFixed(1)}%)`);
    console.log(`  Ties:        ${ties} (${(ties * 100 / total).toFixed(1)}%)`);
  }

  const avgGt = gtTotal / Math.max(1, total);
  const avgQm = comparison.reduce((s, r) => s + r.qmeans_attr_count, 0) / Math.max(1, total);
  const avgGem = comparison.reduce((s, r) => s + r.gemma_unique_values, 0) / Math.max(1, total);
  const avgGemKeys = comparison.reduce((s, r) => s + r.gemma_total_keys, 0) / Math.max(1, total);

  console.log(`\nAvg attributes per query:`);
  console.log(`  Ground Truth:     ${avgGt.toFixed(2)}`);
  console.log(`  QMeans:           ${avgQm.toFixed(2)}`);
  console.log(`  Gemma (unique):   ${avgGem.toFixed(2)}`);
  console.log(`  Gemma (all keys): ${avgGemKeys.toFixed(2)}`);

  console.log('\n' + '='.repeat(80));
}

main().catch(console.error);
