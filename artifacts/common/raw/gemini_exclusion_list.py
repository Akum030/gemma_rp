import pandas as pd
import requests
import time
import json
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
INPUT_CSV = "exclusion_test_queries.csv"
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.0-flash-lite"
DELAY_MS = 100
OUTPUT_CSV = "gemini_dataset_exclusion_list.csv"
BATCH_SIZE = 100

# ============================================================================
# PASTE YOUR COMPRESSED ATTRIBUTES HERE
# Copy ALL lines from compressed_attributes_isq.txt and paste below
# ============================================================================
ATTRIBUTE_DATASET = """
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
240 v:voltage:specification
400 v:voltage:specification
220 v:voltage:specification
230 volts:voltage:specification
220v:voltage:specification
440v:voltage:specification
220-400 vac:voltage:specification
360 v:voltage:specification
340 v:voltage:specification
230vac:voltage:specification
1000:voltage:specification
230v:voltage:specification
paint coated:surface finishing:specification
color coated:surface finishing:specification
painted:surface finishing:specification
powder coated:surface finishing:specification
good:surface finishing:specification
ms:surface finishing:specification
polished:surface finishing:specification
superior quality paint finish:surface finishing:specification
galvanised:surface finishing:specification
powder coated paint:surface finishing:specification
coated:surface finishing:specification
power coated / painted / chrome plated:surface finishing:specification
automatic:automation grade:specification
semi-automatic:automation grade:specification
fully:automation grade:specification
fully automatic:automation grade:specification
semiautomatic:automation grade:specification
manual:automation grade:specification
semi automatic:automation grade:specification
as per client requirement.:automation grade:specification
yes:automation grade:specification
a:automation grade:specification
semi automated:automation grade:specification
manual/automation:automation grade:specification
a grade:automation grade:specification
fully automatic touch screen:automation grade:specification
gold refining plant:automation grade:specification
three phase:phase:specification
3 phase:phase:specification
silver refining plant:phase:specification
single phase:phase:specification
1 phase:phase:specification
single:phase:specification
3:phase:specification
hand operated:phase:specification
single/three:phase:specification
shegal face 1.5kelo wat:phase:specification
1:phase:specification
three:phase:specification
single phase a.c:phase:specification
single or triple:phase:specification
single 220:phase:specification
stainless steel:body material:specification
mild steel:body material:specification
titanium,pp:body material:specification
titanium, glass, pph:body material:specification
ms:body material:specification
ss:body material:specification
iron:body material:specification
pp, upvc, titanium:body material:specification
p.p:body material:specification
poly proplyene:body material:specification
pp:body material:specification
pph:body material:specification
pu:body material:specification
steel:body material:specification
ms / ss:body material:specification
new only:i deal in:specification
new and second hand:i deal in:specification
second hand only:i deal in:specification
new:i deal in:specification
new one only:i deal in:specification
only new:i deal in:specification
30 inch:size:specification
45mm*45mm:size:specification
12 mm:size:specification
65/132:size:specification
2250x540x1160mm. (lxwxh):size:specification
5 x 5 x 5 to 22 x 8 12 ( l x w x h ):size:specification
x.x.x:size:specification
see pdf:size:specification
18 inch:size:specification
as per customer requirement:size:specification
19*50:size:specification
55 mm, height 750mm(approx:size:specification
65 mm:size:specification
dia 500:size:specification
as per design:size:specification
made in india:country of origin:specification
india:country of origin:specification
silver refining plant:heating range:specification
80c:heating range:specification
900:heating range:specification
35:heating range:specification
standard:heating range:specification
100:heating range:specification
fully automatic:heating range:specification
100c:heating range:specification
good:heating range:specification
50:heating range:specification
up to 1100 degree c:heating range:specification
auto heating:heating range:specification
110 degreec:heating range:specification
50 to 250 degree c:heating range:specification
50 to 250 deg c:heating range:specification
58 rpm:screw speed:specification
600 rpm:screw speed:specification
45 rpm:screw speed:specification
see pdf:screw speed:specification
50 rpm:screw speed:specification
5-5 rpm:screw speed:specification
1200 rpm:screw speed:specification
110 rpm:screw speed:specification
0-80 rpm:screw speed:specification
0-90 rpm:screw speed:specification
5-52 rpm:screw speed:specification
90 rpm:screw speed:specification
5.52 rpm:screw speed:specification
80rpm:screw speed:specification
4-45 rpm:screw speed:specification
plastic:material to be extruded:specification
aluminium:material to be extruded:specification
alumunium:material to be extruded:specification
noodle:material to be extruded:specification
puff:material to be extruded:specification
metal:material to be extruded:specification
pp tape:material to be extruded:specification
yarn:material to be extruded:specification
aluminum profiles:material to be extruded:specification
welding electrodes:material to be extruded:specification
aluminm melting furnace , 90 feet handling system with rotcutter & finish cutter and puller & streacher and handling table with all conveior belt and roller sleeve and agin oven and die oven and pollution system and dross recovery machine:material to be extruded:specification
any:material to be extruded:specification
pbat:material to be extruded:specification
copper and aluminium:material to be extruded:specification
pp abs hips hm:material to be extruded:specification
edr:brand:specification
gurukrupa enterprises:brand:specification
hulk lokpal:brand:specification
rajco:brand:specification
k-jhil:brand:specification
gold star:brand:specification
he:brand:specification
ek danta refiners:brand:specification
aec:brand:specification
microgold:brand:specification
prasad enterprise:brand:specification
kabra:brand:specification
jt:brand:specification
m tech jewel equipment:brand:specification
ddri:brand:specification
industrial:usage/application:specification
pharmaceutical industry, food and beverages and cosmetics industries:usage/application:specification
cosmetics:usage/application:specification
garbage bags,medical bags:usage/application:specification
wire & cable:usage/application:specification
chemical laboratory:usage/application:specification
mulch film:usage/application:specification
for the determination of bitumen percentage in bituminous mixtures:usage/application:specification
herbal extraction:usage/application:specification
herbal extractor plant:usage/application:specification
hospital and hotal:usage/application:specification
fire fighting:usage/application:specification
laundry:usage/application:specification
pharma lab:usage/application:specification
aluminium extrusion:usage/application:specification
0.5 kva:power:specification
2 hp:power:specification
220:power:specification
2/3kw:power:specification
ac:power:specification
1200w:power:specification
220 v:power:specification
electric:power:specification
220v:power:specification
electronic:power:specification
2 kw:power:specification
35-40 amp:power:specification
up to 40 kw:power:specification
5 kw:power:specification
230 v ac:power:specification
99%:purity:specification
99.9% pure:purity:specification
99.99:purity:specification
99.95-99.99:purity:specification
999:purity:specification
9999:purity:specification
999+:purity:specification
999.5 / 99.99:purity:specification
99.9%-99.99%:purity:specification
99.99%:purity:specification
99.90%:purity:specification
99.99 percent:purity:specification
good:purity:specification
best:purity:specification
50:purity:specification
650 kg:weight:specification
1000t:weight:specification
700:weight:specification
2-8 ton:weight:specification
800kg:weight:specification
3 ton:weight:specification
25-30kg:weight:specification
1500 kgs:weight:specification
400-kg:weight:specification
250 kg:weight:specification
12 kg:weight:specification
approx 10kg:weight:specification
216 kg:weight:specification
as per requirement:weight:specification
25 kg:weight:specification
aba 35*45:model name/number:specification
as 48:model name/number:specification
aza 0944 centrifuge extractor (hand operated):model name/number:specification
aza 0946 centrifuge extractor (motorised):model name/number:specification
mp/ex-tape-110:model name/number:specification
sjps135:model name/number:specification
oeplmono01:model name/number:specification
10:model name/number:specification
solid phase extraction positive pressure:model name/number:specification
see pdf:model name/number:specification
mepup:model name/number:specification
twin screw food extruder:model name/number:specification
stpz:model name/number:specification
twin screw:model name/number:specification
gem blomo:model name/number:specification
50hz:frequency:specification
5:frequency:specification
50 hz:frequency:specification
50/60 hz:frequency:specification
zzz:frequency:specification
40hz:frequency:specification
50 - 60 hz:frequency:specification
50 hz.:frequency:specification
20 hz:frequency:specification
50/60:frequency:specification
50/60hz:frequency:specification
50-60 hz:frequency:specification
220-230 voltage:frequency:specification
semi automatic:frequency:specification
good:frequency:specification
50 mt:production capacity:specification
250 mt.per month:production capacity:specification
500mtr/min:production capacity:specification
100 kg/hr:production capacity:specification
50 kg/hr:production capacity:specification
200 kg/hr:production capacity:specification
500 kg/hr:production capacity:specification
1000 kg/hr:production capacity:specification
90 kg to 450 kg per hour:production capacity:specification
140 kg/hr:production capacity:specification
more than 1000 kg/hr:production capacity:specification
90 kg/hr:production capacity:specification
300 kg/hr:production capacity:specification
60 kg/hour:production capacity:specification
450 kg/hr:production capacity:specification
electric:power source:specification
electrical:power source:specification
client scope:power source:specification
220b:power source:specification
220 v:power source:specification
on request:power source:specification
electricity:power source:specification
ac:power source:specification
electric operated:power source:specification
single phase:power source:specification
3 phase 50 hz:power source:specification
yes:power source:specification
1 kw:power source:specification
electric, gas, diesel:power source:specification
solvent extraction plant:power source:specification
75mm:diameter:specification
60 mm:diameter:specification
2-2.5 mm:diameter:specification
52mm to 90mm:diameter:specification
51/105:diameter:specification
10 x 10 x 10:diameter:specification
75 mm (screw diameter):diameter:specification
20 to 50mm:diameter:specification
55/120:diameter:specification
fully automatic:diameter:specification
depends on material:diameter:specification
65/132:diameter:specification
as per requirement:diameter:specification
as per size:diameter:specification
20 mm - 400 mm pipe size:diameter:specification
60 micron:film thickness:specification
10-50 micron:film thickness:specification
150 micron:film thickness:specification
100 micron:film thickness:specification
20-200 micron:film thickness:specification
20 - 150 ( micron ):film thickness:specification
100 ( micron ):film thickness:specification
25-250 micron:film thickness:specification
0.05 mm:film thickness:specification
0.12 mm:film thickness:specification
30 to 75 mic:film thickness:specification
10 micron:film thickness:specification
0.03 - 0.22mm:film thickness:specification
10 - 100 micron:film thickness:specification
20 - 100 ( micron ):film thickness:specification
low:height:specification
as per size:height:specification
5feet:height:specification
10 feet:height:specification
40kg/75kg/100kg/137kg:height:specification
6 feet:height:specification
6:height:specification
9 ft.:height:specification
12 feet:height:specification
10feet:height:specification
1500 m:height:specification
2000 m:height:specification
310 m:height:specification
5 - 9 feet:height:specification
1255 m:height:specification
1 kw:lead:specification
fully automatic:lead:specification
1kw:lead:specification
glass:lead:specification
less than 10 mg/nm3:lead:specification
yes:installation services:specification
no:installation services:specification
free:installation services:specification
optional:installation services:specification
see pdf:installation services:specification
as per requirement:installation services:specification
depends on material:installation services:specification
installed by company:installation services:specification
extra:installation services:specification
we provide:installation services:specification
shakti scope:installation services:specification
no installation charges:installation services:specification
very easy to be installed:installation services:specification
provided:installation services:specification
free of cost - no extra cost for installation:installation services:specification
5 hp:motor power:specification
10 kw:motor power:specification
1 hp:motor power:specification
1400 rpm:motor power:specification
5kw:motor power:specification
1/2 hp:motor power:specification
as per requirement:motor power:specification
220w:motor power:specification
touch screen , fully automatic:motor power:specification
10w:motor power:specification
7.5 w:motor power:specification
na:motor power:specification
2kw:motor power:specification
2hp:motor power:specification
2 hp:motor power:specification
abc:dimension:specification
xxx:dimension:specification
1500mm*3000mm*6000mm*:dimension:specification
silver refining plant:dimension:specification
25 x 25:dimension:specification
10 x 10:dimension:specification
900:dimension:specification
12 x 12:dimension:specification
3ft*3ft*7ft:dimension:specification
customised:dimension:specification
10 x 10 x 10:dimension:specification
2x2.5x6feet (lxwxh):dimension:specification
automatic gold refining machine:dimension:specification
40x32x72:dimension:specification
5f by 5f:dimension:specification
any kind of metal extrusion:type:specification
semi-automatic:type:specification
yarn extruder:type:specification
fully automatic:type:specification
new:type:specification
horizontal:type:specification
die roll:type:specification
pipe extruder:type:specification
3 layer blown film machine:type:specification
cable extruder:type:specification
automatic:type:specification
processing plant:type:specification
clay extruder:type:specification
profile extruder:type:specification
continuous extrusion machine:type:specification
304/316l stainless steel:material:specification
frp:material:specification
ss:material:specification
cast iron:material:specification
silver refining plant:material:specification
ss 316l:material:specification
stainless steel:material:specification
pp or pvdf:material:specification
mild steel:material:specification
abs:material:specification
galvanized iron:material:specification
c.s./s.s.:material:specification
hdpe:material:specification
metal:material:specification
aluminium:material:specification
185 degree celsius:temperature:specification
100c:temperature:specification
200 degs:temperature:specification
200:temperature:specification
140-200degree:temperature:specification
0-300 degree celsius:temperature:specification
300 degree c:temperature:specification
upto 400 deg/cel:temperature:specification
65 degree celcius:temperature:specification
ambient:temperature:specification
3000r/min:temperature:specification
standard:temperature:specification
rt to 105 degreec:temperature:specification
130 deg c:temperature:specification
high:temperature:specification
copper:wire material:specification
stainless steel:wire material:specification
lead:wire material:specification
aluminium:wire material:specification
copper,aluminium:wire material:specification
pvc:wire material:specification
mild steel:wire material:specification
425 tons:capacity:specification
100 tpd - 1000 tpd:capacity:specification
500 ton:capacity:specification
25 kg:capacity:specification
5 kg:capacity:specification
100kg:capacity:specification
10 tpd:capacity:specification
100g 2kg:capacity:specification
100 tpd:capacity:specification
50 tpd:capacity:specification
250 kl to 10000 kl:capacity:specification
100 kg/hr:capacity:specification
50 kg:capacity:specification
2000 tpd:capacity:specification
500 tpd:capacity:specification
electricity:driven type:specification
hand and electric:driven type:specification
electric:driven type:specification
gear box:driven type:specification
automatic:driven type:specification
good:driven type:specification
servo:driven type:specification
twin screw extruder:driven type:specification
ac motor; 4kw:driven type:specification
hand operated:driven type:specification
dc motor; 3.7kw:driven type:specification
dual settings allow users to set dierent pressures for extraction and column drying:driven type:specification
on request:driven type:specification
motor:driven type:specification
ac vfd:driven type:specification
55 kw:power consumption:specification
electric:power consumption:specification
25 kw:power consumption:specification
60hp:power consumption:specification
50kw.:power consumption:specification
146-194 kw:power consumption:specification
7.5 kw:power consumption:specification
upto 22kw:power consumption:specification
18 kw:power consumption:specification
5 hp:power consumption:specification
125x90 mm:power consumption:specification
80 kw:power consumption:specification
146 - 194 ( kw ):power consumption:specification
5 kw:power consumption:specification
10kw:power consumption:specification
70mm:wire thickness:specification
3mm:wire thickness:specification
nil:wire thickness:specification
depends:wire thickness:specification
see pdf:wire thickness:specification
typically adjustable; varies by material type:wire thickness:specification
according to machine capability:wire thickness:specification
2.5 kg:wire thickness:specification
24 months:warranty:specification
1 year:warranty:specification
12 months:warranty:specification
1 year with services:warranty:specification
12months:warranty:specification
one year:warranty:specification
6 months:warranty:specification
see pdf:warranty:specification
1 year warranty:warranty:specification
one year warranty:warranty:specification
no warranty:warranty:specification
2 year:warranty:specification
1 +1 year extended warranty:warranty:specification
1+1 years extended warranty:warranty:specification
1 year manufacturing defect:warranty:specification
21.7 mm:screw diameter:specification
45mm:screw diameter:specification
35 mm:screw diameter:specification
40mm:screw diameter:specification
52:screw diameter:specification
55mm:screw diameter:specification
45 ( mm ):screw diameter:specification
45 mm and 45 mm:screw diameter:specification
55/120:screw diameter:specification
52mm dia:screw diameter:specification
30 x 15 x 18 to 60 x 40 x 20 ( l x w x h ):screw diameter:specification
depends on material:screw diameter:specification
65/132:screw diameter:specification
146 - 194 ( kw ):screw diameter:specification
50 mm:screw diameter:specification
5:bowl capacity:specification
1.5 liter:bowl capacity:specification
1000 gms:bowl capacity:specification
1500ml:bowl capacity:specification
250 gm:bowl capacity:specification
1.5 kg:bowl capacity:specification
1.5ltrs:bowl capacity:specification
1.5kg:bowl capacity:specification
1000ml:bowl capacity:specification
2.5 kg:bowl capacity:specification
2-3 ltr:bowl capacity:specification
2liter:bowl capacity:specification
1500g:bowl capacity:specification
1500:bowl capacity:specification
1500 grams:bowl capacity:specification
self:product type:specification
manual:product type:specification
testing tool:product type:specification
standard:product type:specification
hand:product type:specification
gold refining plant:product type:specification
electrical operated:product type:specification
electrically:product type:specification
machine:product type:specification
bitumen extractor:product type:specification
hand oprate:product type:specification
high speed mixer:product type:specification
polished:product type:specification
hand operated and easy operated:product type:specification
manual gold refinery:product type:specification
ld:plastic processed:specification
pvc:plastic processed:specification
pvc, resion:plastic processed:specification
plastic prosesh:plastic processed:specification
pvc pipe:plastic processed:specification
extruder:plastic processed:specification
an:plastic processed:specification
pvc pipe , cpvc pipe:plastic processed:specification
twin screw:plastic processed:specification
hdpe:plastic processed:specification
pvc hdpe pipe manufacturers:plastic processed:specification
nylon delrin:plastic processed:specification
engineering plastic:plastic processed:specification
powder coating:plastic processed:specification
pvc resin:plastic processed:specification
3 mm:panel thickness:specification
3mm:panel thickness:specification
mannered:packaging type:specification
silver refining plant:packaging type:specification
wooden:packaging type:specification
export quality:packaging type:specification
box based on product:packaging type:specification
based on size:packaging type:specification
wooden packing:packaging type:specification
box:packaging type:specification
cardboard:packaging type:specification
standard wooden packing:packaging type:specification
wooden export quality packing:packaging type:specification
wooden box:packaging type:specification
pp:packaging type:specification
roll:packaging type:specification
export type:packaging type:specification
230v:voltage supply:specification
230 v, 50hz:voltage supply:specification
110 to 240v:voltage supply:specification
240 v:voltage supply:specification
220v:voltage supply:specification
220 v:voltage supply:specification
230 v ac:voltage supply:specification
230 v:voltage supply:specification
a.c:voltage supply:specification
415 v:voltage supply:specification
220:voltage supply:specification
ac 220v:voltage supply:specification
420v:voltage supply:specification
20 v:voltage supply:specification
220-230 v:voltage supply:specification
semi-automatic:automatic grade:specification
automatic and semi automatic:automatic grade:specification
automatic:automatic grade:specification
manual:automatic grade:specification
semi automatic:automatic grade:specification
costomized:automatic grade:specification
custom:automatic grade:specification
fully automatic:automatic grade:specification
250 kva:automatic grade:specification
fully-automatic:automatic grade:specification
yes:automatic grade:specification
manul:automatic grade:specification
automatic for conical twin screw extruder:automatic grade:specification
high automation:automatic grade:specification
automatic,semi-automatic:automatic grade:specification
semi-automatic:operation type:specification
automatic:operation type:specification
semi automatic:operation type:specification
hydraulic:operation type:specification
new:condition:specification
used:condition:specification
0-40:machine power:specification
25 hp:machine power:specification
0-40 kw:machine power:specification
20 hp:machine power:specification
48 - 75 ( kw ):machine power:specification
1-5 kw:machine power:specification
40 kw:machine power:specification
40-80:machine power:specification
80-100:machine power:specification
146 - 194 ( kw ):machine power:specification
80-600:machine power:specification
50 kw:machine power:specification
30 kw:machine power:specification
depends on material:machine power:specification
10 kw:machine power:specification
white:color:specification
blue:color:specification
transparent,silver,etc:color:specification
green blue:color:specification
ss:color:specification
silver:color:specification
gray:color:specification
any:color:specification
blue and white (base):color:specification
white (body):color:specification
blue / white:color:specification
sky blue:color:specification
bst:color:specification
silver,white:color:specification
blue and yellow:color:specification
abc:depth:specification
10:depth:specification
fully automatic:depth:specification
as per size:depth:specification
20:depth:specification
xxx:depth:specification
22mm:depth:specification
60 cm:depth:specification
200 mm:depth:specification
nitric and hcl:gases:specification
nitric:gases:specification
free:gases:specification
fully automatic:gases:specification
no gases:gases:specification
no gas:gases:specification
fumes and dust:gases:specification
not detectable:gases:specification
3:number of phases:specification
single and three:number of phases:specification
100mm:die size:specification
65/100 mm:die size:specification
8 inch:die size:specification
600 to 1000mm:die size:specification
90 mm:die size:specification
automatic:die size:specification
65 mm:die size:specification
on request:die size:specification
20 to 110mm:die size:specification
customizable:die size:specification
50:die size:specification
250 mm:die size:specification
100 mm:die size:specification
see pdf:die size:specification
1/2,5/8:die size:specification
solvent extraction plant:design type:specification
standard:design type:specification
pilot:design type:specification
on request:design type:specification
customised:design type:specification
indigeous:design type:specification
customized:design type:specification
cvbbcv:design type:specification
kumar:design type:specification
semi automatic:design type:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums. we can supply any capaci:design type:specification
semi autometic:design type:specification
turn key project:design type:specification
415 v:design type:specification
as per design:design type:specification
standard:oil tank capacity:specification
100 to 500 litre:oil tank capacity:specification
customized:oil tank capacity:specification
as per req:oil tank capacity:specification
350l:oil tank capacity:specification
as per reqiurement:oil tank capacity:specification
70 l:oil tank capacity:specification
500 liter:oil tank capacity:specification
standard:thickness:specification
100 ( micron ):thickness:specification
12mm:thickness:specification
customized:thickness:specification
micron:thickness:specification
20 - 100 ( micron ):thickness:specification
20 - 150 ( micron ):thickness:specification
on request:thickness:specification
10 mm:thickness:specification
2.1:thickness:specification
10-18 mm:thickness:specification
100 micron:thickness:specification
20-150 mm:thickness:specification
3 mm:thickness:specification
from 0.2 mm to 0.8 mm:thickness:specification
no:hand operated:specification
yes:hand operated:specification
50hp:voltage (v):specification
240:voltage (v):specification
380 volt:voltage (v):specification
220 v:voltage (v):specification
440 v / 380 v:voltage (v):specification
415 - 420:voltage (v):specification
380:voltage (v):specification
415 v:voltage (v):specification
220:voltage (v):specification
240 v:voltage (v):specification
240 watt:voltage (v):specification
115v:voltage (v):specification
240v:voltage (v):specification
415:voltage (v):specification
415 ac:voltage (v):specification
na:line speed:specification
1750 rpm:line speed:specification
400 rpm:line speed:specification
100:line speed:specification
max 1200 m/min:line speed:specification
yes:line speed:specification
semi automatic:line speed:specification
fully automatic:line speed:specification
7 hours:line speed:specification
150 meter per 1 minute:line speed:specification
2:line speed:specification
3mpm up to 100mpm:line speed:specification
40m/min:line speed:specification
50:line speed:specification
80 rpm:line speed:specification
abc:flange width:specification
fully automatic:flange width:specification
as per size:flange width:specification
depand on size:flange width:specification
350 mm:flange width:specification
spe:features:specification
super salients:features:specification
high speed:features:specification
latest:features:specification
rust proof:features:specification
educational trainer research type:features:specification
longer functional life & easy to maintain:features:specification
corrosion resistance:features:specification
pesticide insecticide:features:specification
corrosion proof:features:specification
plc hmi base:features:specification
cost effective:features:specification
time rendered:features:specification
��� automatic pulp ejection ��� non-drip spout ��� reverse function:features:specification
quick setup:features:specification
automatic:machine type:specification
mother baby extruder:machine type:specification
3 layer aba for ldpe & hdpe:machine type:specification
die casting equipment:machine type:specification
twin screw extruder:machine type:specification
tube extrusion machine:machine type:specification
horizontal basket extruder:machine type:specification
continuous extrusion machine:machine type:specification
pipe extrusion machine:machine type:specification
blown film extrusion machine:machine type:specification
extruder for xlpe, epr:machine type:specification
fully automatic:machine type:specification
extraction plant:machine type:specification
solvent extraction:machine type:specification
extraction equipment:machine type:specification
industrial & commerical:working area:specification
4000 sqmtr:working area:specification
25 m2:working area:specification
the exclusive 7" controlpad(tm) facilitates the set-up and interaction with the extractor.:working area:specification
5 acres of land and more:working area:specification
50 hz:frequency (hz):specification
50 - 60 hz:frequency (hz):specification
50:frequency (hz):specification
50 - 60hz:frequency (hz):specification
60 hz:frequency (hz):specification
50-60:frequency (hz):specification
50z:frequency (hz):specification
50-60 hz:frequency (hz):specification
60:frequency (hz):specification
50hz:frequency (hz):specification
140-160 (kg/hour):output:specification
100-200 kg/hr:output:specification
50-100 kg/hr:output:specification
150-170 kg/hour:output:specification
20 - 80:output:specification
220-240 (kg/hour):output:specification
0-50 kg/hr:output:specification
300-350 kg/hr:output:specification
1300-1500 kg/hour:output:specification
300-350 kg/hour:output:specification
50 -350kg per.hour:output:specification
40 ( kw ):output:specification
upto 60 m / min.:output:specification
100 kg/hour:output:specification
depends on material:output:specification
75 bar:pressure:specification
customized:pressure:specification
10-20 bar:pressure:specification
10 bar:pressure:specification
8:pressure:specification
0- 100psi:pressure:specification
784:pressure:specification
no:pressure:specification
1 bar:pressure:specification
4-5 kg:pressure:specification
30 - 50 bar:pressure:specification
20-100psi:pressure:specification
50~5000ul:pressure:specification
standard:pressure:specification
8 to 12 bar:pressure:specification
0-50:output(kg/hr):specification
300-350:output(kg/hr):specification
200-300:output(kg/hr):specification
50-100:output(kg/hr):specification
100-200:output(kg/hr):specification
100-200 kg/hr:output(kg/hr):specification
depends on size of cable:output(kg/hr):specification
18:1:screw l/d:specification
18.1:screw l/d:specification
52:screw l/d:specification
see pdf:screw l/d:specification
132:1:screw l/d:specification
30:1:screw l/d:specification
40:screw l/d:specification
32-40:screw l/d:specification
all type of ss & ms:material grade:specification
ss 304:material grade:specification
ss316:material grade:specification
ss304, ss316:material grade:specification
ss309:material grade:specification
304, 304l, 316, 316l:material grade:specification
ss304:material grade:specification
fe500:material grade:specification
all:material grade:specification
304:material grade:specification
316:material grade:specification
industrial grade:material grade:specification
ss 304, ss 316:material grade:specification
food grade:material grade:specification
sb 265 gr.2:material grade:specification
rf521:model number:specification
d-gld:model number:specification
j-923i:model number:specification
nf4arm-2k4arm:model number:specification
stb-83:model number:specification
sil 10 / 25 / 50 / 100:model number:specification
52/2:model number:specification
lg engineers:model number:specification
aba-4545 s:model number:specification
ppm-35et:model number:specification
sfc-isr-02:model number:specification
si 90:model number:specification
zv72:model number:specification
om-3050-60-1500:model number:specification
28x28:model number:specification
cable insulation extrusion line:application:specification
laboratory use:application:specification
mixing:application:specification
electric cable instulation:application:specification
industry:application:specification
gasket manufacturing:application:specification
gas handling:application:specification
food process industry:application:specification
solvent extraction plant ,cattle feed plant:application:specification
industrial:application:specification
industrial/commercial:application:specification
all types:application:specification
pp, hips, hdpe, ldpe:application:specification
tube well casting, industrial waste & chemical drain domestic plumbing:application:specification
general purpose film, liner bag, shrink film, stretch film, mulch film, courier bag:application:specification
100 kg:capacity(kg):specification
30 kg:capacity(kg):specification
5 kg:capacity(kg):specification
10 kg:capacity(kg):specification
10:capacity(kg):specification
20 kg:capacity(kg):specification
200:capacity(kg):specification
1 kg:capacity(kg):specification
50 kg:capacity(kg):specification
40 kg:capacity(kg):specification
70 kg:capacity(kg):specification
20:capacity(kg):specification
30:capacity(kg):specification
90 kg:capacity(kg):specification
50:capacity(kg):specification
based on size:packaging size:specification
no:packaging size:specification
50 kg:packaging size:specification
custom:packaging size:specification
as specified:packaging size:specification
na:packaging size:specification
as per requirement:packaging size:specification
25 kg:packaging size:specification
depending on size of extruder:packaging size:specification
1 tpd:packaging size:specification
as per product:packaging size:specification
6ft x 14ft x 6ft:packaging size:specification
1kg, 5kg, 25kg:packaging size:specification
customized:packaging size:specification
box:packaging size:specification
20 ton:max force or load:specification
500 to 5500 ton:max force or load:specification
>150 ton:max force or load:specification
230 bar:max force or load:specification
conical:screw design:specification
twin screw:screw design:specification
design for special application:screw design:specification
corotating twin screw extruder:screw design:specification
segmented:screw design:specification
universal:screw design:specification
swaraj make:screw design:specification
parallel:screw design:specification
co rotating:screw design:specification
bimetallic:screw design:specification
pvc pipe and profole:screw design:specification
twin:screw design:specification
own:screw design:specification
conical twin screw:screw design:specification
parallel twin screw:screw design:specification
bitumen extractor:type of testing machines:specification
bitumen:type of testing machines:specification
electric:type of testing machines:specification
civil laboratory:type of testing machines:specification
bitumen centrifuge extractor:type of testing machines:specification
electrically operated:type of testing machines:specification
soil testing:type of testing machines:specification
hand operated:type of testing machines:specification
butiment testing machine:type of testing machines:specification
motorised:type of testing machines:specification
material testing equipment:type of testing machines:specification
manual:type of testing machines:specification
na:type of testing machines:specification
civil:type of testing machines:specification
bitumen testing:type of testing machines:specification
96:no of position:specification
48:no of position:specification
144:no of position:specification
96 position:no of position:specification
48, 96, 144:no of position:specification
12, 24:no of position:specification
12 & 24:no of position:specification
yes:no of position:specification
12:no of position:specification
12-24 port:no of position:specification
12 , 24 , 144:no of position:specification
48,96,144:no of position:specification
6:no of position:specification
144 individually regulated:no of position:specification
48/96/144:no of position:specification
bimetallic:screw type:specification
co rotating:screw type:specification
all:screw type:specification
conical:screw type:specification
counter rotating:screw type:specification
commercial:industry type:specification
laboratory:industry type:specification
hospital:industry type:specification
chemical:industry type:specification
scientific glass:industry type:specification
pharma:industry type:specification
bio fertilizer:industry type:specification
all:industry type:specification
lab equipment:industry type:specification
industrial:industry type:specification
chemical industry:industry type:specification
hospital and lab:industry type:specification
for college:industry type:specification
100 lph:plant capacity:specification
300 mt/month:plant capacity:specification
100 ton/day:plant capacity:specification
single phase:electricity connection:specification
three phase:electricity connection:specification
semi automatic:operation mode:specification
semi-automatic:operation mode:specification
automatic:operation mode:specification
manual:operation mode:specification
fuel injector cleaning machine:operation mode:specification
hand operated:operation mode:specification
fully automatic:operation mode:specification
automatic and semiautomatic:operation mode:specification
painted:surface finish:specification
polished:surface finish:specification
chrome plated:surface finish:specification
transparent:surface finish:specification
galvanized:surface finish:specification
aluminnium:surface finish:specification
paint coated:surface finish:specification
color coated:surface finish:specification
oil painted:surface finish:specification
coated:surface finish:specification
powder coated:surface finish:specification
3000 mm:length:specification
30m:length:specification
42d:length:specification
3800 mm:length:specification
1-20 ft:length:specification
13000mm:length:specification
1800mm:length:specification
3000 mm to 10000 mm:length:specification
1250 mm:length:specification
8inch:length:specification
2300 mm:length:specification
3840 mm:length:specification
electric:power type:specification
electric and air operated:power type:specification
230 v:voltage supply (v):specification
220:voltage supply (v):specification
240 v:voltage supply (v):specification
230 v ac:voltage supply (v):specification
220v:voltage supply (v):specification
230v:voltage supply (v):specification
230:voltage supply (v):specification
230 volt:voltage supply (v):specification
75 kg/hr:average productivity:specification
70 - 110 kg/hour:average productivity:specification
300kg per hours:average productivity:specification
200-800kgs/hour:average productivity:specification
depends on material:average productivity:specification
150 kg:average productivity:specification
50 kg per hours:average productivity:specification
na:average productivity:specification
2400/day:average productivity:specification
10 mt per day:average productivity:specification
24kg/hr:average productivity:specification
1 ton per hours:average productivity:specification
100 bundles per day:average productivity:specification
40 kg per hrs:average productivity:specification
100 - 500 kg per/hr.:average productivity:specification
415 v:voltage (volt):specification
220 v:voltage (volt):specification
440:voltage (volt):specification
220:voltage (volt):specification
220- 240:voltage (volt):specification
415-420:voltage (volt):specification
420 v:voltage (volt):specification
440v:voltage (volt):specification
380:voltage (volt):specification
415v:voltage (volt):specification
220 - 440:voltage (volt):specification
3 phase:voltage (volt):specification
220-380 v ac:voltage (volt):specification
110-380v:voltage (volt):specification
220 v-380 v:voltage (volt):specification
30 nm:screw torque:specification
60 nm:screw torque:specification
6000 ft/lbs:screw torque:specification
132 to 400 knm:screw torque:specification
6 n-m:screw torque:specification
240 nm:screw torque:specification
50 hz:screw torque:specification
8135 nm:screw torque:specification
6435 nm:screw torque:specification
see pdf:screw torque:specification
64 n/mm2:screw torque:specification
900:screw torque:specification
5-50 rpm:screw torque:specification
conical twin screw imported bimetallic type:screw torque:specification
75 nm:screw torque:specification
240:power (v):specification
380 v:power (v):specification
your scoop:power (v):specification
200:average productivity (kg/hour):specification
24 hours 500-600 kg. production:average productivity (kg/hour):specification
120 to 350 kg/hr:average productivity (kg/hour):specification
100 coils per days:average productivity (kg/hour):specification
25 kg/h:average productivity (kg/hour):specification
400:average productivity (kg/hour):specification
220-230 kg/hr:average productivity (kg/hour):specification
1500:weight (kg):specification
up to 45:weight (kg):specification
700:weight (kg):specification
150kg:weight (kg):specification
3500:weight (kg):specification
3000:weight (kg):specification
1100:weight (kg):specification
2000:weight (kg):specification
1750:weight (kg):specification
20 to 315 mm:diameter (millimeter):specification
120:diameter (millimeter):specification
100:purity (%):specification
999+:purity (%):specification
99.99:purity (%):specification
95%:purity (%):specification
999:purity (%):specification
95 %:purity (%):specification
99.90%:purity (%):specification
999.5/- 9999:purity (%):specification
5kw:power (kw):specification
2.25 kw:power (kw):specification
4.5:power (kw):specification
4.5 kw:power (kw):specification
single phase:power (kw):specification
120 kw:power (kw):specification
3:power (kw):specification
11:power (kw):specification
10:power (kw):specification
4:power (kw):specification
5.5:power (kw):specification
220:power (kw):specification
4.5kw:power (kw):specification
0.5 kw:power (kw):specification
cnc:control type:specification
non-cnc:control type:specification
plc:control type:specification
boiler:steam supply:specification
by steam boiler:steam supply:specification
yes:steam supply:specification
pipe with prv:steam supply:specification
as per req:steam supply:specification
as per capacity:steam supply:specification
20 kg/hr,5.0 bar min pressure:steam supply:specification
clear:finishing:specification
polycarbonate casing to prevent contamination, the machine has all pneumatic cylinders of festo make:finishing:specification
color coated:finishing:specification
good quality pu paint:finishing:specification
mirror polishing, matt polishing, acid passivation, perox cleaning:finishing:specification
hard chrome, nitrated or bimetallic:finishing:specification
customized:finishing:specification
mirror polish:finishing:specification
polished:finishing:specification
polycarbonate casing to prevent contamination,the machine has all pneumatic cylinders of festo make:finishing:specification
mirror polishing, matt polishing:finishing:specification
matte polish & mirror:finishing:specification
paint coated:finishing:specification
powder coated:finishing:specification
premium quality paint:finishing:specification
paint coated:surface treatment:specification
polished:surface treatment:specification
painted:surface treatment:specification
see pdf:surface treatment:specification
required:surface treatment:specification
bimetallic:surface treatment:specification
yes:surface treatment:specification
powder coated:surface treatment:specification
supreme color coated:surface treatment:specification
color coated:surface treatment:specification
nitride treatment:surface treatment:specification
available:surface treatment:specification
galvanised:surface treatment:specification
bimetallic,nitrided,hard-facing,chrome-plated,etc:surface treatment:specification
powder coating:surface treatment:specification
stainless steel:machine body material:specification
ss 316 / ss 304 / ms:machine body material:specification
800x800x1650mm (lxwxh):size/dimension:specification
as per order:size/dimension:specification
48:size/dimension:specification
4,"to9"inch(diameter):size/dimension:specification
depends on material:min finish wire diameter:specification
1-2 mm:min finish wire diameter:specification
0-1 mm:min finish wire diameter:specification
2-3 mm:min finish wire diameter:specification
0.8 (as per customer requirement):min finish wire diameter:specification
4 core:min finish wire diameter:specification
1 mm to up to requirement:min finish wire diameter:specification
1440 rpm:speed:specification
3500 rpm:speed:specification
2400 rpm:speed:specification
1500 rpm:speed:specification
1140rpm:speed:specification
motorized:speed:specification
3000 rpm:speed:specification
2300rpm:speed:specification
hand:speed:specification
3500 r.p.m:speed:specification
2400 - 3600 rpm:speed:specification
2400-3600 rpm:speed:specification
manual:speed:specification
80 mpm:speed:specification
as per astm d2172:speed:specification
304:steel grade:specification
ss:steel grade:specification
ss 304 ms:steel grade:specification
titanium:steel grade:specification
ss 316:steel grade:specification
1500 rpm:speed (rpm):specification
1500-3000:speed (rpm):specification
2000-5000:speed (rpm):specification
1440:speed (rpm):specification
2400-3600 rpm:speed (rpm):specification
3500 rpm:speed (rpm):specification
5500r.p.m/11000 rpm:speed (rpm):specification
as per plant:sheet thickness:specification
2 mm:sheet thickness:specification
15mm:sheet thickness:specification
10mm , 15mm:sheet thickness:specification
8mm:sheet thickness:specification
2mm:sheet thickness:specification
3mm:sheet thickness:specification
12mm / 8mm:sheet thickness:specification
8to 15mm:sheet thickness:specification
12mm:sheet thickness:specification
5 to 10 mm:sheet thickness:specification
20-80 mm:sheet thickness:specification
3mm to 25mm:sheet thickness:specification
8 mm:sheet thickness:specification
0.8-3mm:sheet thickness:specification
300 - 600 to 1600 - 2500 ( mm ):lay flat width:specification
750 - 1200 ( mm ):lay flat width:specification
on request:lay flat width:specification
2100 mm:lay flat width:specification
12 feet:lay flat width:specification
18 feet / 24 feet / 36 feet:lay flat width:specification
1100 mm:lay flat width:specification
35ft:lay flat width:specification
300 - 600 to 1600 - 2500:lay flat width:specification
650-1250:lay flat width:specification
600-1050 mm:lay flat width:specification
65 mm:lay flat width:specification
700 mm:lay flat width:specification
up to 650mm width:lay flat width:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width:specification
no maintenance:maintenance:specification
no maintenane:maintenance:specification
yes:maintenance:specification
normal lubrication and cleaning as per maintenance chart:maintenance:specification
no:maintenance:specification
n maintenance:maintenance:specification
nomal lubrication as well as cleaning as per maintenance chart:maintenance:specification
after one year:maintenance:specification
75-150 kg/hr:capacity (kilogram/hour):specification
45 to 50 kg:capacity (kilogram/hour):specification
100 kg/h:capacity (kilogram/hour):specification
120 to 350 kg/hr:capacity (kilogram/hour):specification
90 kg/h:capacity (kilogram/hour):specification
up to 3,000 kilograms per hour:capacity (kilogram/hour):specification
500kg:capacity (kilogram/hour):specification
450:capacity (kilogram/hour):specification
100-300 kg/hour:capacity (kilogram/hour):specification
32, 40, 45, 55 mm:screw diameter (mm):specification
45 mm:screw diameter (mm):specification
35 & 40:screw diameter (mm):specification
4 kw:power consumption (kw):specification
110 kw:power consumption (kw):specification
shft:brand/make:specification
asepta:brand/make:specification
tecson:brand/make:specification
goyum:brand/make:specification
amerging technologies:brand/make:specification
rufouz hitek:brand/make:specification
athena:brand/make:specification
velp:brand/make:specification
ud:brand/make:specification
saini:brand/make:specification
lakshmi:brand/make:specification
aditya:brand/make:specification
prasad lab:brand/make:specification
100:range:specification
20 to 50mm:range:specification
20 to 110mm:range:specification
500 kg to 5 tonne:range:specification
see pdf:range:specification
customized:range:specification
5 racks and 108 samples a batch:range:specification
up to 25 kg:range:specification
1-2:range:specification
20 mm to 400 mm pipe size:range:specification
5 - 50 m3/hr:range:specification
wide:range:specification
100%:air flow:specification
40 l/s:air flow:specification
semi automatic:font roll diameter:specification
abc:font roll diameter:specification
xxx:font roll diameter:specification
400:font roll diameter:specification
10 x 10:font roll diameter:specification
automatic:font roll diameter:specification
as per the size:font roll diameter:specification
touch screen , fully automatic:font roll diameter:specification
semi and fully automatic:font roll diameter:specification
fully automatic:font roll diameter:specification
as per requirment:font roll diameter:specification
none:font roll diameter:specification
2.5 mm:font roll diameter:specification
at par size:font roll diameter:specification
3 feet:font roll diameter:specification
china:design:specification
parallel twin screw:design:specification
customized:design:specification
conical twin screw:design:specification
radhekrishna standard:design:specification
on request:design:specification
conical:design:specification
modern:design:specification
standard:design:specification
conical twin:design:specification
twin screw segmented:design:specification
ss:design:specification
conical twin extruder:design:specification
stainless steel:design:specification
automatic:design:specification
customized:compass:specification
as per design:compass:specification
na:compass:specification
415 v 50 hz 4 wire:wire diameter:specification
1 sqmm:wire diameter:specification
depends on material:wire diameter:specification
500mm dia:wire diameter:specification
n.a:wire diameter:specification
customiz:wire diameter:specification
2 mm to 10 mm:wire diameter:specification
depends:wire diameter:specification
2 mm:wire diameter:specification
pipe 16 and 20 mm:wire diameter:specification
8mm:wire diameter:specification
na:wire diameter:specification
10mm:wire diameter:specification
nilk:wire diameter:specification
1 mm:wire diameter:specification
scs 2e:model:specification
sga:model:specification
diamond gear box model:model:specification
wshe 50:model:specification
sset 52/18v:model:specification
scs 6 r:model:specification
20d:model:specification
vmosa 3040-1000,vmosa 3045-55-1250,vmosa 3050-60-1500,vmosa 3050-60-1700:model:specification
twinex 78:model:specification
th-044:model:specification
nc11:model:specification
mts-915:model:specification
mech o tech llp:model:specification
skxd-jy01:model:specification
line-m-ext-ps:model:specification
nil:shelf life:specification
24 months:shelf life:specification
12 months:shelf life:specification
8" to 60":drum size:specification
650mm:drum size:specification
50mm:drum size:specification
250mm:drum size:specification
26/36/48:drum size:specification
1500 ml:drum size:specification
customized:drum size:specification
50 nb to 200 nb:drum size:specification
standard:drum size:specification
1250x1250:drum size:specification
18 inch:drum size:specification
2 litre:drum size:specification
500:drum size:specification
round:shape:specification
rectangular:shape:specification
round head:shape:specification
taper:shape:specification
rectangle:shape:specification
ractangle:shape:specification
u type:shape:specification
lcmsms:shape:specification
hexagonal:shape:specification
cylindrical:shape:specification
cylinderical:shape:specification
60 kw:machine power (kw):specification
40 kw:machine power (kw):specification
20 kw:machine power (kw):specification
100 kw:machine power (kw):specification
80 kw:machine power (kw):specification
0-40:machine power (kw):specification
41 - 80 kw:machine power (kw):specification
upto 40 kw:machine power (kw):specification
40-80:machine power (kw):specification
12kw:machine power (kw):specification
6 kw:machine power (kw):specification
7kw:machine power (kw):specification
80-100:machine power (kw):specification
100-120:machine power (kw):specification
1 to 10 kw:machine power (kw):specification
ss 304:material of construction(contact):specification
ss 316:material of construction(contact):specification
bio-degradable corn starch:raw material:specification
cassava:raw material:specification
polypropylene:raw material:specification
pet:raw material:specification
ldpe / lldpe:raw material:specification
pp:raw material:specification
pvc/wpc for conical twin screw extruder:raw material:specification
hdpe:raw material:specification
rice bran:raw material:specification
soybean oilseeds:raw material:specification
rapeseed oilcake:raw material:specification
nylon:raw material:specification
as per requirement:raw material:specification
mustard seed oilcake:raw material:specification
castor seeds:raw material:specification
10:no of unit to be tested:specification
96:no of unit to be tested:specification
1:no of unit to be tested:specification
yes:no of unit to be tested:specification
10-16 samples per run:no of unit to be tested:specification
48/96:no of unit to be tested:specification
25 kgs:no of unit to be tested:specification
extract rapidly 15-60 minutes , 32 samples can be extracted at the same time:no of unit to be tested:specification
1000:no of unit to be tested:specification
36 samples:no of unit to be tested:specification
depends:no of unit to be tested:specification
2:no of unit to be tested:specification
one:no of unit to be tested:specification
manual:technology:specification
advanced horizontal extractor, desolventizer-toaster, distillation and solvent recovery s:technology:specification
advanced horizontal solvent extractor and desolventizer-toaster, evaporation systems, and:technology:specification
horizontal extractor, desolventizer-toaster, distillation systems, and meal conditioning:technology:specification
advanced horizontal extractor, desolventizer-toaster, distillation, and recuperation systems:technology:specification
horizontal extractor, desolventizer-toaster, distillation units, and recuperation system:technology:specification
advanced solvent extraction, desolventizer-toaster, distillation systems and solvent recovery sectio:technology:specification
magnetic bead:technology:specification
pan india:service location:specification
vasai:service location:specification
mumbai:service location:specification
on site:service location:specification
local area:service location:specification
all over india:service location:specification
mumbai and dubai:service location:specification
india:service location:specification
rajkot:service location:specification
all india:service location:specification
mumbai and delhi:service location:specification
twin:screw number:specification
on request:screw number:specification
220:screw number:specification
55/120:screw number:specification
twin screw:screw number:specification
na:screw number:specification
65/132:screw number:specification
as per required:screw number:specification
51/105, 55/120, 65/132:screw number:specification
2:screw number:specification
55/120, 65/132, 51/105:screw number:specification
yes:screw number:specification
51/105, 55/120, 65/132, 80/156:screw number:specification
55/120, 65/132, 80/156:screw number:specification
singal:screw number:specification
silver:metal:specification
gold:metal:specification
pvc:plastic type:specification
polyethylene:plastic type:specification
pp:plastic type:specification
water/chemicals/gold and sliver manufacturing:storage material:specification
chemicals/oils:storage material:specification
chemical, acid, water:storage material:specification
cement,chemicals,fly ash:storage material:specification
220:electrical unit consumption:specification
vacuum:electrical unit consumption:specification
25 to 200kwh:electrical unit consumption:specification
as per req:electrical unit consumption:specification
300:electrical unit consumption:specification
10-150 kw:electrical unit consumption:specification
upto 100 kw:electrical unit consumption:specification
single switch raises and lowers the sample racks and creates an airtight seal:electrical unit consumption:specification
depends upon uses:electrical unit consumption:specification
15&16:electrical unit consumption:specification
na:electrical unit consumption:specification
naaa:electrical unit consumption:specification
no:electrical unit consumption:specification
230 v ac / 6 amp:electrical unit consumption:specification
depends on application:max. vacuum:specification
no:max. vacuum:specification
standard:max. vacuum:specification
650 mm:max. vacuum:specification
na:max. vacuum:specification
atmospheric:max. vacuum:specification
760:max. vacuum:specification
700 mm of hg:max. vacuum:specification
as per req:max. vacuum:specification
20":max. vacuum:specification
-700mm hg:max. vacuum:specification
naaaa:max. vacuum:specification
strong:resistance:specification
na:resistance:specification
nil:resistance:specification
ac:motor:specification
4 hp:motor:specification
2 h p:motor:specification
ac motor:motor:specification
3hp:motor:specification
3 hp:motor:specification
as per req:motor:specification
yes:motor:specification
dc:motor:specification
3 h.p:motor:specification
30:motor:specification
3 hp 3 pharse:motor:specification
2 hp:motor:specification
12 kw:motor:specification
3 hp 3-phase motor:motor:specification
2 tones and above(approx):weight of machinery:specification
500 kg approx:weight of machinery:specification
350 tonnes:weight of machinery:specification
as per req:weight of machinery:specification
2-3 tones:weight of machinery:specification
15 hp and 15 hp:main motor:specification
30kw:main motor:specification
10 hp:main motor:specification
7.5 / 15 / 7.5 hp:main motor:specification
20 hp:main motor:specification
to turn raw plastic pellets or granules into the processed forms:main motor:specification
abb:main motor:specification
15hp & 20hp:main motor:specification
55:main motor:specification
abb - switzerland or equivalent:main motor:specification
12.5 (hp):main motor:specification
15 hp:main motor:specification
siemens - japan or equivalent:main motor:specification
22kw:main motor:specification
abb - or equivalent:main motor:specification
900 mm:roller size:specification
26" nip roll:roller size:specification
42" nip roll:roller size:specification
800 mm:roller size:specification
52" nip roll:roller size:specification
600mm:roller size:specification
1300 mm:roller size:specification
42":roller size:specification
gold jewellry:dust:specification
jewellry:dust:specification
free:dust:specification
fully automatic:dust:specification
as per requirement:dust:specification
silver jewellry:dust:specification
yes:dust:specification
no dust:dust:specification
silver dust:dust:specification
500-600 mg/nm3:dust:specification
less than 50 mg/nm3:dust:specification
0-10 bar,10-15 bar,15-20 bar,20-30 bar,30-40 bar:max design pressure:specification
7 bar:max design pressure:specification
10 kgs:max design pressure:specification
horizontal:orientation:specification
vertical:orientation:specification
three:layer:specification
three layer:layer:specification
two layer:layer:specification
singal layer:layer:specification
3:layer:specification
singal:layer:specification
multilayer:layer:specification
singallayer:layer:specification
twol layer:layer:specification
monolayer:layer:specification
2 layer:layer:specification
2 layer aba:layer:specification
3 layer:layer:specification
single layer, two layer and three layers:layer:specification
standard:packing type:specification
wooden:packing type:specification
box:packing type:specification
300 - 600 to 1600 - 2500 ( mm ):lay flat width range:specification
100mm-1500mm:lay flat width range:specification
62inches:lay flat width range:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width range:specification
1200 mm:lay flat width range:specification
600 - 1250 to 11400 - 2100 ( mm ):lay flat width range:specification
300 - 600 to 1600 - 2500:lay flat width range:specification
550 - 1600 mm:lay flat width range:specification
1350 to 3000 mm:lay flat width range:specification
depends on material:surface finish coating:specification
color coated:surface finish coating:specification
on request:main drive ac:specification
ac:main drive ac:specification
750 kw:main drive ac:specification
25 hp:main drive ac:specification
20hp:main drive ac:specification
yes:main drive ac:specification
delta or crompton ac drive:main drive ac:specification
ac 20 hp:main drive ac:specification
11 kw - 40 kw:main drive ac:specification
545mm:basket diameter:specification
300 x 300 mm:basket diameter:specification
28 inches:basket diameter:specification
powder coated:finish type:specification
depends on material:finish type:specification
rolls:finish type:specification
6 mm:max inlet wire diameter (mm):specification
>12 mm:max inlet wire diameter (mm):specification
0-3 mm:max inlet wire diameter (mm):specification
6-9 mm:max inlet wire diameter (mm):specification
0-3 mm, 3-6 mm, 6-9 mm, 9-12 mm:max inlet wire diameter (mm):specification
0-3 mm, 3-6 mm, 6-9 mm:max inlet wire diameter (mm):specification
9-12 mm:max inlet wire diameter (mm):specification
3-6 mm:max inlet wire diameter (mm):specification
13:1:l/d ratio:specification
na:l/d ratio:specification
1:26:l/d ratio:specification
26/1:l/d ratio:specification
20:10:l/d ratio:specification
h:l/d ratio:specification
22:1:l/d ratio:specification
26:1:l/d ratio:specification
20:1:l/d ratio:specification
18:1:l/d ratio:specification
6:1 - 16:1:l/d ratio:specification
32 : 1:l/d ratio:specification
25:1:l/d ratio:specification
5:1:l/d ratio:specification
24:1:l/d ratio:specification
20 hp:main motor power:specification
10 hp:main motor power:specification
15 hp:main motor power:specification
30-75kw:main motor power:specification
75kw:main motor power:specification
18.28 kw,22.25 kw,37.25 kw,45kw:main motor power:specification
digital:display type:specification
no display:display type:specification
timer:display type:specification
led:display type:specification
analogue:display type:specification
analog:display type:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):overall dimension:specification
600 x 220 x 420 cm:overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x x h ):overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h):overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12 ) l x w x h ):overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12:overall dimension:specification
22 x 8 x 12 ( l x w x h )mmm:overall dimension:specification
255 x 180 x 300 cm:overall dimension:specification
450 x 300 x 430 cm:overall dimension:specification
255 x 280 x 300 cm:overall dimension:specification
5.7 x 1.8 x 3.7	cm:overall dimension:specification
na:diesel consumption:specification
none:diesel consumption:specification
steam:diesel consumption:specification
depend on the project:diesel consumption:specification
hexane:diesel consumption:specification
2.50%:diesel consumption:specification
bvncbn:diesel consumption:specification
as per req:diesel consumption:specification
1.5 liters per hour:diesel consumption:specification
no:diesel consumption:specification
none:micelle concentration:specification
as per req:micelle concentration:specification
depend on capacity of plant:micelle concentration:specification
up to 75%:micelle concentration:specification
na:altimeter:specification
as per design:altimeter:specification
200m/min:speed range:specification
1 to 40 rpm:speed range:specification
1 to 50 rpm:speed range:specification
foodgrade:processing type:specification
exturding machine:processing type:specification
30 kw:power consumption (kilowatt):specification
100 hp:power consumption (kilowatt):specification
60 hp:power consumption (kilowatt):specification
automatic:technique:specification
hot rolled:technique:specification
all:technique:specification
european technology with proven design.:technique:specification
extrusion:technique:specification
gtaw:technique:specification
solvent & aqueous based:technique:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):dimensions:specification
fuel injector cleaning machine:dimensions:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ):dimensions:specification
370x550x550 mm:dimensions:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ):dimensions:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ) [ feet ]:dimensions:specification
30 x 25 x 24 feet:dimensions:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ) [ feet ]:dimensions:specification
600*600*700mm:dimensions:specification
h 24" * w 14" * l 24":dimensions:specification
20 x 5 x 9 to 28 x 8 x 14 ( l x w x h ):dimensions:specification
1300 x 1850 x 960 mm (l x d x h):dimensions:specification
2.1x0.88x1.2 m:dimensions:specification
4.5x4x5 meters:dimensions:specification
20" x 30":dimensions:specification
370 w:wattage:specification
1 hp:wattage:specification
2:die:specification
single die:die:specification
spiral:die:specification
one no 75 mm lip size:die:specification
2 nos:die:specification
50mm (hm/hdpe) 100 (ld/ldpe):die:specification
10 kg:capacity.:specification
800kg - 2ton/day:capacity.:specification
80-100:capacity(pieces per hour):specification
100-120:capacity(pieces per hour):specification
40-60:capacity(pieces per hour):specification
20-40:capacity(pieces per hour):specification
60-80:capacity(pieces per hour):specification
3 ton:machine weight:specification
0.8 tonnes:machine weight:specification
12 ton:machine weight:specification
6 ton:machine weight:specification
1 ton:machine weight:specification
650 kg:machine weight:specification
600 kg (approx):machine weight:specification
12500 kg. (approx.):machine weight:specification
depends on material:diameter millimeter:specification
16 & 20 mm inline & online drip pipe machine:diameter millimeter:specification
450 mm:diameter millimeter:specification
20 mm - 25 mm - 32 mm:diameter millimeter:specification
100 ( micron ):coating thickness:specification
0.008 - 0.03 mm:coating thickness:specification
1.2 - 5mm:thickness (millimeter):specification
30 mm diameter to 120 mm diameter.:thickness (millimeter):specification
45 ( mm ):screw size:specification
on request:screw size:specification
32mm:screw size:specification
extruder a-45 mm (inner & outer layer) extruder b-55 mm (middle layer):screw size:specification
35 mm:screw size:specification
extruder a 35 mm (inner and outer layer) extruder b 45 mm (middle layer):screw size:specification
65 mm:screw size:specification
315 x 740 x 1200 mm:screw size:specification
260 x 640 x 950 mm:screw size:specification
2 inch:screw size:specification
3 inch:screw size:specification
260 x 540 x 700 mm:screw size:specification
415 x 790 x 1330 mm:screw size:specification
63mm:screw size:specification
5 minutes:processing time:specification
3-5 hours:processing time:specification
40 to 60 min:processing time:specification
3 hrs:processing time:specification
indstrial solvent cooker:product:specification
twin screw gear boxes:product:specification
65 mm:barrel bore:specification
45 mm:barrel bore:specification
52mm dia:screw length:specification
see pdf:screw length:specification
100inch:screw length:specification
820 mm:screw length:specification
50 mm:screw length:specification
0.75 kw:air blower:specification
3.5 kw:air blower:specification
3hp:air blower:specification
ac 415v:drive motor:specification
ac drive:drive motor:specification
15 kw:drive motor:specification
1440 rpm:drive motor:specification
6 kw:drive motor:specification
three phase electric motor:drive motor:specification
full:drive motor:specification
fully automatic:burner:specification
m tech jewel equipment:burner:specification
no burner:burner:specification
electric:burner:specification
yes:burner:specification
lpg:burner:specification
diesel fired:burner:specification
qunying:brand name:specification
micro:brand name:specification
a.r.m.k:brand name:specification
minimax:brand name:specification
depends on motor kw:motor kw:specification
depends on motor size:motor kw:specification
asphalt testing:uses:specification
electric bitumen extractors are used for determination of bitumen percentage in hot mixed paving mix:uses:specification
noodle extrude:uses:specification
can be used in gold industry:uses:specification
used to make baby dana:uses:specification
industrial:uses:specification
or mass output used widely in agro chemical, pesticide & chemical industries.:uses:specification
mechotechllp:form:specification
liquid:form:specification
powder:form:specification
custom:form:specification
sheet:form:specification
granules:form:specification
khus extract:form:specification
other:flow rate:specification
500 m^3/hr:flow rate:specification
0.01-7ml/min:flow rate:specification
1,3 up to 3m3 /h:flow rate:specification
hlb, c18:spe cartridge size:specification
cool:spe cartridge size:specification
1ml (standard):spe cartridge size:specification
1 ml, 0.6 ml:spe cartridge size:specification
c 18:spe cartridge size:specification
1 ml, 3 ml, 6 ml:spe cartridge size:specification
1cc, 3cc and, 6cc columns:spe cartridge size:specification
1ml, 3ml:spe cartridge size:specification
1 ml:spe cartridge size:specification
1ml,3ml,6ml:spe cartridge size:specification
1 ml, 3ml, 6ml:spe cartridge size:specification
1 ml,3ml:spe cartridge size:specification
1ml:spe cartridge size:specification
48:spe cartridge size:specification
1, 3 & 6 ml:spe cartridge size:specification
vaccum manifold & accessories:standard with equipment:specification
yes:standard with equipment:specification
includes waste reservoir with assembly to allow for waste:standard with equipment:specification
pump , trap and silicon tube:standard with equipment:specification
1 ml:standard with equipment:specification
no:standard with equipment:specification
cartridges, manifolds, vacuum pump, glass chamber & ptfe cap.:standard with equipment:specification
1ml:standard with equipment:specification
pp dana making machine:type of machine:specification
granules making machine:type of machine:specification
bag making machine:type of machine:specification
biodegradable bag making machine:type of machine:specification
zip lock extruder:type of machine:specification
plastic bag making machine:type of machine:specification
powder coating machine:type of machine:specification
10 inch:size/diameter:specification
2 inch:size/diameter:specification
3 inch:size/diameter:specification
1/2 inch,1 inch,4 inch,>4 inch:size/diameter:specification
customized:tank volume:specification
5000 l:tank volume:specification
standard:wall thickness:specification
10 mm:wall thickness:specification
10mm:wall thickness:specification
3 mm:wall thickness:specification
depending upon the capacity.:wall thickness:specification
good:quality:specification
excellent:quality:specification
high:quality:specification
standard:quality:specification
commercial and isi:quality:specification
as per client requirements:service duration:specification
any:service duration:specification
1 week:service duration:specification
based on project:service duration:specification
35 days:service duration:specification
30 days:service duration:specification
7 days:service duration:specification
3 days:service duration:specification
2 to 5 days:service duration:specification
4 days:service duration:specification
9-12 mm:max inlet wire diameter:specification
12 mm:max inlet wire diameter:specification
3-6 mm:max inlet wire diameter:specification
45:line speed (meter/minute):specification
7.5 to 10 mpm:line speed (meter/minute):specification
color coated:finish:specification
polished:finish:specification
d:finish:specification
coated:finish:specification
powder coated:finish:specification
paint coated:finish:specification
polish:finish:specification
146 - 194 ( kw ):connected load:specification
146 - 194:connected load:specification
48 - 75 ( kw ):connected load:specification
about 100 kw:connected load:specification
43 hp:connected load:specification
25.5 kw:connected load:specification
28 kw:connected load:specification
42.5 kw:connected load:specification
24 kw:connected load:specification
45 kw:connected load:specification
115 hp:connected load:specification
43hp:connected load:specification
24 hp:connected load:specification
75hp:connected load:specification
60hp:connected load:specification
gas:fuel type:specification
electricity:fuel type:specification
a:grade:specification
ss202:grade:specification
food grade:grade:specification
d2:grade:specification
automatic:grade:specification
automatic, semi-automatic:grade:specification
semi automatic:grade:specification
manual / semi automatic:grade:specification
semi-automatic:grade:specification
ss304:grade:specification
ss316:grade:specification
manual:grade:specification
automatic,semi-automatic,manual:grade:specification
lab:grade:specification
grade 1:grade:specification
40:machine power (kilowatt):specification
220 kw:machine power (kilowatt):specification
lead:melting material:specification
copper:melting material:specification
20:capacity(kg/hr):specification
100:capacity(kg/hr):specification
550 kg/hr:capacity(kg/hr):specification
plc:control system:specification
plc, hmi touchscreen for real time monitoring:control system:specification
plc with hmi touchscreen for full process automation:control system:specification
plc with hmi touchscreen interface:control system:specification
plc with hmi:control system:specification
plc, hmi touchscreen with automation features:control system:specification
plc control:control system:specification
industrial spare parts packaging:usage/ application:specification
lidding film, vaccum bags, edible oil, medical, uht milk, dairy products.:usage/ application:specification
na:dual pressure regulators:specification
two different pressure settings for extraction and column washing/drying:dual pressure regulators:specification
290kg:net weight:specification
450 kg:net weight:specification
2000 kg:net weight:specification
3000 kg:net weight:specification
1800 kg:net weight:specification
100:production capacity(kg/hr):specification
500:production capacity(kg/hr):specification
1500:capacity (kg):specification
120-150/hr:capacity (kg):specification
250 kg/hr:capacity (kg):specification
110-1500 kg/hr:capacity (kg):specification
8-12 kg/h:capacity (kg):specification
48 kg:capacity (kg):specification
25 kg:capacity (kg):specification
250:capacity (kg):specification
tailor-made:working capacity:specification
10 ltr per batch:working capacity:specification
108 samples:working capacity:specification
customized:working capacity:specification
extraction and purification nucleic acid:working capacity:specification
25 kg per hr:working capacity:specification
55.93 kw:total connected load:specification
18.43 kw:total connected load:specification
74 kw:total connected load:specification
74kw:total connected load:specification
16 kw:total connected load:specification
62.1 kw:total connected load:specification
14.5 kw:total connected load:specification
95:total connected load:specification
45-127kw:total connected load:specification
for industrial:usage:specification
extruder machine:usage:specification
gold refining:usage:specification
industrial:usage:specification
silver refining:usage:specification
for washing:usage:specification
jewellery industry:usage:specification
refining plant:usage:specification
packaging films such as agricultural seed,liquid, electrostatic protection film and many others.:usage:specification
plastic film:usage:specification
for making window glass seal profile:usage:specification
for epe cutting:usage:specification
tube extrusion:usage:specification
gold industries:usage:specification
gold jewellery industries:usage:specification
yes:manufacturer:specification
mechotech llp:manufacturer:specification
mechotech for plant:manufacturer:specification
b k machines:manufacturer:specification
techno biobase:manufacturer:specification
sadguru enterprise:manufacturer:specification
v r enterprises:manufacturer:specification
sladjana sales corporation:manufacturer:specification
dry type:feed type:specification
wet type:feed type:specification
food grade:grade standard:specification
ss 304:grade standard:specification
industrial:grade standard:specification
analytical grade:grade standard:specification
12 bolt:no. of screws:specification
6 bolt:no. of screws:specification
4 bolt:no. of screws:specification
plastic waste bags lums making machine:snacks type:specification
namkeen:snacks type:specification
wire insulation:snacks type:specification
paint coated:finishing type:specification
color coated:finishing type:specification
polished:finishing type:specification
automatic:automation type:specification
semi-automatic:automation type:specification
semi automatic:automation type:specification
1000 kg:machine capacity:specification
100grm to.2 kg:machine capacity:specification
4000 kg:machine capacity:specification
10 to 25 kg:machine capacity:specification
mild steel:machine material:specification
ms:machine material:specification
900 mm:drum diameter:specification
510 mm:drum diameter:specification
1070 mm:drum diameter:specification
non dried:is it dried:specification
dried:is it dried:specification
stainless steel:coating:specification
ms powder coating:coating:specification
erc extractor:suitable for:specification
10*10 sq. ft.:suitable for:specification
home:suitable for:specification
silicone and synthetic rubber:suitable for:specification
2-4 sq. ft. area:suitable for:specification
yes:certification:specification
iso 9001: 2008:certification:specification
ce:certification:specification
ce/sgs:certification:specification
iso:certification:specification
xxx1:capacity / size:specification
1000 mt:capacity / size:specification
60 kw:rated power (kw):specification
24 kw:rated power (kw):specification
0-100 a:output current:specification
5a:output current:specification
ss316:contact parts:specification
ss 304:contact parts:specification
50 to 800 degree celsius:heating range (deg. celsius):specification
70:heating range (deg. celsius):specification
50 to 250 degree celsius:heating range (deg. celsius):specification
75 mm:drain size:specification
50 mm:drain size:specification
3 mm:min finish wire diameter (mm):specification
1-2 mm:min finish wire diameter (mm):specification
2-3 mm:min finish wire diameter (mm):specification
0-1 mm, 1-2 mm, 2-3 mm:min finish wire diameter (mm):specification
0-1 mm:min finish wire diameter (mm):specification
3-4 mm:min finish wire diameter (mm):specification
0.05%:accuracy:specification
yes:accuracy:specification
fresh:style:specification
horizontal:style:specification
arch:style:specification
rectangular:style:specification
1 kg, 2 kg, 5 kg, 10 kg, 20 kg:available capacity:specification
10 kg ,20 kg ,50 kg,100 kg:available capacity:specification
1 kg,2 kg,5 kg,10 kg,20 kg:available capacity:specification
10 kg,20 kg,50 kg,100 kg:available capacity:specification
plastic:material compatibility:specification
metal:material compatibility:specification
pp:material compatibility:specification
oil soluble:solubility:specification
garlic soluble:solubility:specification
40 hrc:hardness:specification
50hrc:hardness:specification
50-60 hrc:hardness:specification
50 hrc:hardness:specification
45-60 hrc:hardness:specification
60 hrc:hardness:specification
yes:herbal:specification
extraction plant:herbal:specification
complete civil work with installation:installation type:specification
free stand:installation type:specification
220v:operating voltage:specification
230 v:operating voltage:specification
handbag:type of bag:specification
carry bag:type of bag:specification
shopping bag:type of bag:specification
laptop bag:type of bag:specification
grain bag:type of bag:specification
jumbo bag:type of bag:specification
stand alone:type of instruments:specification
plasma:type of instruments:specification
organic:is it organic:specification
non organic:is it organic:specification
pipes:output shape:specification
sheets:output shape:specification
65 degree:max temperature:specification
70:max temperature:specification
80 degree c:max temperature:specification
60 degree c:max temperature:specification
40 nm:nominal torque:specification
30 nm:nominal torque:specification
13.2 mm:barrel diameter:specification
20 mm:barrel diameter:specification
water:medium used:specification
oil:medium used:specification
mts:standard:specification
astm:standard:specification
etp,dhp,dap,dlp:standard:specification
advance:feature:specification
auto acid filling:feature:specification
cost effective:feature:specification
heavy duty:feature:specification
rustproof:feature:specification
printed:feature:specification
odourless:feature:specification
corrugated:feature:specification
portable:feature:specification
low to high throughput:feature:specification
gold dust can be refined:feature:specification
screen changer/air knife/hopper loader with dosing unit/silo with blower in option:feature:specification
wear-resisting:feature:specification
high efficiency:feature:specification
lldpe:tank material:specification
plastic:tank material:specification
2:weight (ton):specification
5.5:weight (ton):specification
12 tone:weight (ton):specification
50 ml:pack size:specification
500 ml:pack size:specification
175 ml:pack size:specification
150 ml:pack size:specification
800-1500mm:pack size:specification
110 ml:pack size:specification
10ml-1 ltr:pack size:specification
250 ml:pack size:specification
baheda extract:name of extract:specification
guduchi extract:name of extract:specification
aritha extract:name of extract:specification
vacha extract:name of extract:specification
brahmi extract:name of extract:specification
jatamansi extract:name of extract:specification
gokshur extract:name of extract:specification
cabbage extract:name of extract:specification
avocado extract:name of extract:specification
harde extract:name of extract:specification
lotus extract:name of extract:specification
mehandi extract:name of extract:specification
peach extract:name of extract:specification
lodhra extract:name of extract:specification
lavang(clove) extract:name of extract:specification
monolayer:no. of layer:specification
two layer:no. of layer:specification
2:no. of layer:specification
3 layer:no. of layer:specification
5:no. of layer:specification
online:payment mode:specification
online and offline:payment mode:specification
online/offline:payment mode:specification
online /offline:payment mode:specification
offline and online:payment mode:specification
0.25 hp:electric motor:specification
1/2 hp:electric motor:specification
53 rpm:screen speed:specification
45 rpm:screen speed:specification
twin:number of extruder:specification
2 nos.:number of extruder:specification
1 nos.:number of extruder:specification
300 mm:film width:specification
250 mm:film width:specification
40 to 250 mm:film width:specification
650-1000,750-1250,750-1500,900-1700 mm:film width:specification
150-600 mm:film width:specification
500-800 mm:film width:specification
2500mm:film width:specification
3000mm:film width:specification
1500 mm:film width:specification
1200 mm:film width:specification
1000 mm:film width:specification
800 mm:film width:specification
400 mm:film width:specification
600 mm:film width:specification
700 mm:film width:specification
3 x 4 inch pcs:cooling blower:specification
2 (hp):cooling blower:specification
3" x 2pcs:cooling blower:specification
1/2" x 1 pc:cooling blower:specification
2 1/2" x 1 pc:cooling blower:specification
2" x 2pcs:cooling blower:specification
10 zone:temp. controller:specification
4 zone:temp. controller:specification
5 zone:temp. controller:specification
local area:location:specification
banglore:location:specification
indiamart:location:specification
india:location:specification
maharashtra:location:specification
indore (m.p.):location:specification
pan india:location:specification
worldwide:location:specification
local:location:specification
all:location:specification
10.85 kw:total heating load:specification
23.1 kw:total heating load:specification
33.1 kw:total heating load:specification
7.1 kw:total heating load:specification
27.1 kw:total heating load:specification
20 kg/hour:max extrusion output:specification
25 kg/hour:max extrusion output:specification
135 kg/hr:max extrusion output:specification
90 kg/hour:max extrusion output:specification
100 l:capacity(litre):specification
200 l:capacity(litre):specification
air blower:blower type:specification
inflatable blower:blower type:specification
centrifugal blower:blower type:specification
100 psi:inlet pressure:specification
75 psi:inlet pressure:specification
1 kw:power (w):specification
2000 w:power (w):specification
1-10 kw:power (w):specification
10 kw:power (w):specification
0-500 rpm:rotate speed range:specification
500 rpm:rotate speed range:specification
0-500rpm:rotate speed range:specification
600 min-1 pp (pellet) + talk (30% - 50%, fine powder):screw speed range pp:specification
500 min -1 pp (pellet) + talk (30% - 50%, fine powder):screw speed range pp:specification
250 - 800 (kg/h):throughput range abs:specification
650 - 2000 (kg/h) abs (powder):throughput range abs:specification
400 - 1100 abs (powder):throughput range abs:specification
300 - 500 (kg/h):throughput range pellet:specification
450 - 800 pa5 (pellet) + gf (30%):throughput range pellet:specification
750 - 1400 (kg/h) pa5 (pellet) + gf (30%):throughput range pellet:specification
300 - 550 (kg/h):throughput range pc hight molecular weight:specification
500 - 800 pc (powder, hight molecular weight):throughput range pc hight molecular weight:specification
800 - 1600 (kg/h) pc (powder, hight molecular weight):throughput range pc hight molecular weight:specification
900 - 1600 (kg/h) pp (pellet) + gf (30%):throughput range pp pellet:specification
350 - 550 (kg/h):throughput range pp pellet:specification
550 - 900 pp (pellet) + gf (30%):throughput range pp pellet:specification
700 - 1100 (kg/h) modified ppo (pellet + powder):throughput range modified ppo:specification
250 - 400 (kg/h):throughput range modified ppo:specification
450 - 600 modified ppo (pellet + powder):throughput range modified ppo:specification
fruit:part used:specification
flower bud:part used:specification
rhizome:part used:specification
root:part used:specification
leaves:part used:specification
flower:part used:specification
leaf:part used:specification
bark:part used:specification
stem:part used:specification
peel:part used:specification
nelumbo nucifera:botanical name:specification
morinda citrifolia:botanical name:specification
raphanus sativus:botanical name:specification
thymus vulgaris:botanical name:specification
brassica oleracea var. capitata:botanical name:specification
bacopa monneiri:botanical name:specification
pranus persica:botanical name:specification
nardostachyas jatamansi:botanical name:specification
symplocos racemosa:botanical name:specification
acorus calamus:botanical name:specification
tribulus terrestris:botanical name:specification
persea americana:botanical name:specification
terminalia belerica:botanical name:specification
terminalia chebula:botanical name:specification
lawsonia inermis:botanical name:specification
40 kg/h:throughput:specification
1~10:throughput:specification
1 to 12 samples:throughput:specification
100 kg/h:throughput:specification
1(kg/h):throughput:specification
10 kg/h:throughput:specification
8 hour:process time:specification
6 hour:process time:specification
gold:refining material:specification
gold and silver & diamond jewellery:refining material:specification
silver:refining material:specification
gold and silver,diamond,jewellery,dust .e.t.c:refining material:specification
3 kw to 300 kw:power rating:specification
230 v, 50 hz / 60 hz:power rating:specification
only new:deals in:specification
new only:deals in:specification
new:deals in:specification
30:1 l/d:screw ratio:specification
28:1 l/d:screw ratio:specification
27 l/d:screw ratio:specification
301 l/d:screw ratio:specification
8:1:screw ratio:specification
27 mm:screw ratio:specification
30:1 l/c:screw ratio:specification
28.1 l/d:screw ratio:specification
271 l /d:screw ratio:specification
30 : 1:screw ratio:specification
90 mm:paper code o.d.:specification
95 mm:paper code o.d.:specification
auto mini series:series:specification
pp series:series:specification
hhpep series:series:specification
mini series:series:specification
aba series:series:specification
tc 55:series:specification
tc 86:series:specification
tp 75:series:specification
tp 115:series:specification
20 hp:driving a.c. motor + inverter:specification
20 hp x 2 pcs hp:driving a.c. motor + inverter:specification
65+85 mm:die diameter:specification
50 mm:die diameter:specification
100 mm:die diameter:specification
upto 2000mm:die diameter:specification
90&120(changeable) mm:die diameter:specification
70 mm:paper core i.d.:specification
75 mm:paper core i.d.:specification
8 nos.:heating zone:specification
2 nos.:heating zone:specification
3 zone:heating zone:specification
7:heating zone:specification
3 nos.:heating zone:specification
3 nos:heating zone:specification
5 nos.:heating zone:specification
2 no.:heating zone:specification
34kw:total consuming load:specification
34 kw:total consuming load:specification
7 nos.:heat zone:specification
3 nos:heat zone:specification
45 mm:screw die:specification
35mm:screw die:specification
35 mm:screw die:specification
40 mm:screw die:specification
55 mm:screw die:specification
50 mm:screw die:specification
25mm:screw die:specification
45 + 55 mm:screw die:specification
35 + 45 cm:screw die:specification
25 kw:connecting load:specification
60 kw:connecting load:specification
7 kw:connecting load:specification
30 kw:connecting load:specification
40 kw:connecting load:specification
8 kw:connecting load:specification
2.2:peak output (kg/unit):specification
3:peak output (kg/unit):specification
5.2:peak output (kg/unit):specification
65 kg / hr:peak output (kg/unit):specification
4.5:peak output (kg/unit):specification
1.1:peak output (kg/unit):specification
2.6 kw:peak output (kg/unit):specification
2.8:peak output (kg/unit):specification
5.5:peak output (kg/unit):specification
1.7:peak output (kg/unit):specification
2 nos:winders:specification
2:winders:specification
250-300 kg/hr:max output:specification
1 - 10 kg/h:max output:specification
90 kg/hr:max output:specification
25 kg/hour:max output:specification
all types:max output:specification
60-90 kg/h:max output:specification
150 kg/h:max output:specification
50 kg/hour:max output:specification
120 kg:max output:specification
225kg/hr:max output:specification
30-35kg/hr:max output:specification
55-60kg/hr:max output:specification
125kg/hr:max output:specification
120kg/hr:max output:specification
160kg/hr:max output:specification
0.9 kw:drive power:specification
55 kw:drive power:specification
22 kw:drive power:specification
helical:gear box:specification
helical 160 cd:gear box:specification
bonfiglioli - italy or equivalent:gear box:specification
elecon - or equivalent:gear box:specification
bonfiglioli - or equivalent:gear box:specification
hbk 140:gear box:specification
800 mm:niproll size:specification
1100 mm:niproll size:specification
1000 mm:niproll size:specification
300 mm:niproll size:specification
600 mm:niproll size:specification
500 mm:niproll size:specification
8 inch:niproll size:specification
box:pack type:specification
wooden box:pack type:specification
loose:pack type:specification
twin screw:type of extruder:specification
twin screw extruder:type of extruder:specification
2 layer, 3 layer tank optional:layer of tank:specification
na:layer of tank:specification
automatic:automation:specification
manual / fully automated control systems with scada/plc integration:automation:specification
manual / fully automated systems with scada/plc integration:automation:specification
manual / fully automated with scada/plc controls:automation:specification
manual / fully automated with scada/plc systems:automation:specification
semi automatic:automation:specification
fully automatic:automation:specification
30:1:ld ratio:specification
20 ratio 1:ld ratio:specification
261:ld ratio:specification
hm,hdpe virgin raw material:material used:specification
pp (polypropylene):material used:specification
ms:material used:specification
pp:material used:specification
lldpe,hdpe:material used:specification
anticorrosive pph (polypropylene):material used:specification
-10 degree c to 40 degree c (14 degree f to 104 degree f):working temperature:specification
100 to 260 degree c:working temperature:specification
-10 degreec to 40 degreec ( 14 degreef to 104 degreef ):working temperature:specification
-10 degreec to 40 degreec (14 degreef to 104 degreef ):working temperature:specification
lcd 8x45 character:display:specification
digital:display:specification
no display:display:specification
7" color touch screen:display:specification
up to 200 degreec:temperature control:specification
normal 300 deg:temperature control:specification
normal 300 degree:temperature control:specification
electric heat and water cooler:temperature control:specification
digital pid:temperature control:specification
blue / white:colour:specification
white:colour:specification
silver:colour:specification
sky blue or apple green or other color:colour:specification
blue/ ivory:colour:specification
silver and red:colour:specification
natural:colour:specification
bronze:colour:specification
customized:colour:specification
grey:colour:specification
780-850:rotor speed (r/min):specification
1100:rotor speed (r/min):specification
automatic,semi auto:auto grade:specification
automatic,semi automatic:auto grade:specification
20-40 hr:production:specification
30-50 hr:production:specification
50 kg:production:specification
0.4 kg - 5-6 kg:production:specification
150-250 hr:production:specification
100-150 hr:production:specification
250-350 hr:production:specification
110-180 hr:production:specification
40-50 (kg/hr.):production:specification
50-80 hr:production:specification
75 inch:screw diameters:specification
65 inch:screw diameters:specification
120 inch:screw diameters:specification
90 inch:screw diameters:specification
140 inch:screw diameters:specification
100 inch:screw diameters:specification
50 inch:screw diameters:specification
11 kw:heating power:specification
9 kw:heating power:specification
8.5 x 2 kw:heating power:specification
800:heating power:specification
6 kw:heating power:specification
2 kw:heating power:specification
7.5 kw:heating power:specification
8 kw:heating power:specification
42 kw:whole power required:specification
40 kw:whole power required:specification
30 kw:whole power required:specification
20 kw:whole power required:specification
280 v:input voltage:specification
240 v:input voltage:specification
180 v:input voltage:specification
0.8w:input voltage:specification
120 v:input voltage:specification
230 v:input voltage:specification
440 v:input voltage:specification
1 hp:blower:specification
7.5 hp:blower:specification
3 hp high capacity:blower:specification
1/2 h.p.:blower:specification
50 to 75%:solvent recovery:specification
80%:solvent recovery:specification
60-70%:solvent recovery:specification
30 to 100 ml:solvent volume:specification
from 30 to 100 ml:solvent volume:specification
700 mm:width:specification
600mm:width:specification
2.5 mm:width:specification
8.6 mtr:width:specification
68 cm:width:specification
1000 mm to 2500 mm:width:specification
1400 mm:width:specification
1220 mm:width:specification
1443 mm:width:specification
800 mm:width:specification
1500 mm:width:specification
1575 mm:width:specification
80 - 400 mm:width:specification
50gm:min batch quantity:specification
500g:min batch quantity:specification
co-rotating twin screw extruder:title:specification
electrically operated bitumen extractor:title:specification
20 mm:pipe range single die:specification
110 mm:pipe range single die:specification
19 mm:pipe range twin die:specification
63 mm:pipe range twin die:specification
400 v:power supply:specification
(uniphase) 220 v 50-60 hz:power supply:specification
440 volts,50 hz,a.c.,three phase with neutral (can also be designed as per specific requirement):power supply:specification
230 v, 50 hz, single phase, a.c:power supply:specification
ac 220/110v 50/60 hzs:power supply:specification
230 v a.c:power supply:specification
230 v a.c. single phase:power supply:specification
230v,50 hz (1 phase) or 440v,50 hz (3 phase):power supply:specification
single phase 220 watt:power supply:specification
440 volts, 50 hz, a.c., three phase with neutral (can also be designed as per specific requirement):power supply:specification
230v:power supply:specification
220v 50hz:power supply:specification
electric:power supply:specification
240 v:power supply:specification
440 volts,50 hz,a.c.,three phase with neutral ( can also be designed as per specific requirement:power supply:specification
steel:material of construction:specification
mild steel as well as high-grade stainless steel for durability and corrosi:material of construction:specification
mild steel as well as high-grade stainless steel for corrosion resistance a:material of construction:specification
mild steel and stainless steel corrosion-resistant materials as per require:material of construction:specification
stainless steel,mild steel:material of construction:specification
mild steel as well as high-quality stainless steel for durability and corrosion resistance as per th:material of construction:specification
mild steel as well as high-quality stainless steel and corrosion-resistant:material of construction:specification
ss 304:material of construction:specification
stainless steel:material of construction:specification
consulation services:deal in:specification
core rotating twin screw extruder lab scale:deal in:specification
new only:deal in:specification
all kinds extarction solutions:deal in:specification
ll / ldpe / hm / hdpe:polymer:specification
ll / ldpe:polymer:specification
550mm - 1600mm:lay flat range:specification
500mm - 1350mm:lay flat range:specification
closed circuit works by vacuum:transfer of acid:specification
closed circuit works by vacuum 200l:transfer of acid:specification
40 h.p:power required:specification
45 h.p:power required:specification
51 h.p:power required:specification
20 h.p:power required:specification
32 h.p:power required:specification
88-132 vac/176-264 vac, 50/60hz:power required:specification
within 1 week:duration:specification
4-8 hours:duration:specification
1-2 months:duration:specification
950mm adjustable:center height:specification
1000mm adjustable:center height:specification
1410 x 790 x 1580:overall dimensions (lxbxh) (mm):specification
1730 x 905 x 1820:overall dimensions (lxbxh) (mm):specification
single screw:screw:specification
ld27:screw:specification
2 x 90 mm:screw:specification
made of nitriding steel (en41b musco):screw:specification
2 x 68 mm:screw:specification
2 x 52 mm:screw:specification
2 x 92 mm:screw:specification
2 x 65:screw:specification
2 x 65 mm:screw:specification
2 x 52:screw:specification
mini-45:model no:specification
ml 32:model no:specification
rmb a65 b75:model no:specification
edf/ind-cba-15:model no:specification
granulex-100ds:model no:specification
spt - 01 - 10:model no:specification
nnt-se-ca:model no:specification
edf/ind-cba-17:model no:specification
edf/ind-cba-16:model no:specification
tr/tp/75:model no:specification
rmb a45 b45:model no:specification
jjez0106e:model no:specification
appl/dl-90 ac:model no:specification
appl/dl-75 ac:model no:specification
rmb a40 b45:model no:specification
120 kg/hr:peak output:specification
8kgs:peak output:specification
45 kg/hr:peak output:specification
65kg/hr:peak output:specification
45kg/hr:peak output:specification
55 kg/hr:peak output:specification
65 kg/hr:peak output:specification
90 kg/hr:peak output:specification
12 kgs:peak output:specification
65 kg./hr.:peak output:specification
80 kg/hr:peak output:specification
28 kg/hr:peak output:specification
8.7 kw:heater capacity:specification
4 kw:heater capacity:specification
22.1 kw:heater capacity:specification
7/4 kw:heater capacity:specification
24:center distance:specification
20.5 - 78 mm:center distance:specification
10.5 mm to 48 mm:center distance:specification
44 , 55 , 75.35 mm:center distance:specification
25 micron:thickness of film:specification
100 micron:thickness of film:specification
30 micron:thickness of film:specification
20 micron:thickness of film:specification
28 micron:thickness of film:specification
40 micron:thickness of film:specification
80 micron:thickness of film:specification
1000 - 2500 kg/hr:output (kg/hr):specification
250 - 300:output (kg/hr):specification
25 kw:heating load:specification
17 kw:heating load:specification
16 kw:heating load:specification
10.5 kw:heating load:specification
12 kw:heating load:specification
11.5 kw:heating load:specification
2hp + 40hp:heating load:specification
15 kw:heating load:specification
5.5 kw + 6.5 kw:heating load:specification
5.5 kw:heating load:specification
23 kw:heating load:specification
20 kw:heating load:specification
6 kw:heating load:specification
10 (kw):heating load:specification
100-200 mm:max bag length:specification
1-100 mm:max bag length:specification
200-300 mm:max bag length:specification
300-400 mm:max bag length:specification
400-500 mm:max bag length:specification
10mm:shell thickness:specification
10 mm:shell thickness:specification
0.75 hp:driving motor power:specification
7.5 hp:driving motor power:specification
15 hp:driving motor power:specification
0.33 kw:winder motor:specification
1.08 kw:winder motor:specification
2.0 x 2.0 x 2.8 meter:space requirement ( lxwxh):specification
3.1 x 2.7 x 4.9 meter:space requirement ( lxwxh):specification
titanium:reactor material:specification
metal:reactor material:specification
2 station winder:winder:specification
single station:winder:specification
d station:winder:specification
one no of single station surface type winder:winder:specification
two station:winder:specification
30 ul-1000 ul:process volume:specification
30 ul 1000 ul:process volume:specification
#ERROR!:recovery rate:specification
over 100 %:recovery rate:specification
over 98 %:recovery rate:specification
cv<=3%:stability:specification
cv<5%:stability:specification
uv sterilization:pollution control:specification
uv light:pollution control:specification
40 kg/hr:maximum output:specification
220 kg/hr:maximum output:specification
25 to 30 kg./hr:maximum output:specification
130 kg/hr:maximum output:specification
25-30kg/hr:maximum output:specification
200 kg/hr:maximum output:specification
180-200 kg/hr:maximum output:specification
120,220,240 kg/hr:maximum output:specification
220-240 kg/hr:maximum output:specification
150kg/hr:maximum output:specification
240 kg/hr:maximum output:specification
3 layeer die:die type:specification
spiral:die type:specification
spiral 2l:die type:specification
40 inch:lay flat width and diameter:specification
600 - 1250 to 11400 - 2100 ( mm ):lay flat width and diameter:specification
600 mm:lay flat width and diameter:specification
300 - 600 to 1600 - 2500:lay flat width and diameter:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width and diameter:specification
twin screw:extruder type:specification
twin screw extruder:extruder type:specification
schneider - france or equivalent:switch gears:specification
schneider - or equivalent:switch gears:specification
1440:rpm:specification
1000:rpm:specification
50:rpm:specification
1kw monophase compressor:cooling unit:specification
1 kw monophase compressor:cooling unit:specification
condenser:cooling unit:specification
1 kw:cooling unit:specification
sle-cct-19:product code:specification
llu:product code:specification
sant engineering industries:power(w):specification
45:power(w):specification
37 kw:power(w):specification
55 kw:power(w):specification
depends on size of machine:power(w):specification
mono yarn extrusion plant:service type:specification
installation service:service type:specification
gold refining service:service type:specification
gold and silver refining service:service type:specification
extraction plant installation:service type:specification
extraction plant amc:service type:specification
recovery and refining:service type:specification
solvent plant maintenance:service type:specification
gold refining services:service type:specification
solvent extraction plants repairing:service type:specification
mild steel:product material:specification
plastic:product material:specification
45mm:bag width:specification
35mm:bag width:specification
40mm:bag width:specification
315 mm:pipe diameter:specification
40mm:pipe diameter:specification
1/2 to 2.5 inch:pipe diameter:specification
20-110 mm:pipe diameter:specification
i = 2.5 - 5:transmission:specification
i = 20 , 25:transmission:specification
44-64:screw l/d ratio:specification
30:1 (customized):screw l/d ratio:specification
28/1:screw l/d ratio:specification
26:01:00:screw l/d ratio:specification
yes:icmr(govt) approved:specification
no:icmr(govt) approved:specification
7.5 hp:main drive:specification
20 hp:main drive:specification
10 hp:main drive:specification
25 hp:main drive:specification
3hp:main drive:specification
15 hp:main drive:specification
5 hp + 7.5 hp ac varriable frequency (crompton motor & abb make ac drive):main drive:specification
3 x 15 (ac) (kw):main drive:specification
3 x 22 (ac) (kw):main drive:specification
15+25 hp:main drive:specification
3 x 30 (ac) (kw):main drive:specification
7.5/15 hp:main drive:specification
17.5 hp:main drive:specification
20 hp a.c. kirloskar / abb make a.c.:main drive:specification
18.5kw:main drive:specification
chemical process:process:specification
chemical:process:specification
neutralizing section, bleaching plant, deodorizing section:process:specification
liquid extraction:process:specification
aqua cold process:process:specification
550-1250 mm:layflat width:specification
1000mm:layflat width:specification
500-800mm:layflat width:specification
900-1600 mm:layflat width:specification
max.4000mm:layflat width:specification
for food processing:general use:specification
industrial:general use:specification
used for gold refining:usage/applications:specification
dispersion of pigments and additives into thermosetting resins for powder coatings:usage/applications:specification
to produce long continuous products such as tubing and tire treads:usage/applications:specification
double scrubber:no of scrubber:specification
single scrubber:no of scrubber:specification
28x2x8mm:dimension(l*w*h):specification
22x2x4mm:dimension(l*w*h):specification
24x2x4mm:dimension(l*w*h):specification
100 litre:storage capacity:specification
3000 litre:storage capacity:specification
25 litre:storage capacity:specification
500 litre:storage capacity:specification
1000 litre:storage capacity:specification
6000 litre:storage capacity:specification
500 l:storage capacity:specification
1000l:storage capacity:specification
500l:storage capacity:specification
0-50 ton:storage capacity:specification
no smell,no smoke:exhausted gas:specification
no smell,no smoke,ph7,no nitrogen oxide:exhausted gas:specification
no smell, no smoke:exhausted gas:specification
no smell,no gas:exhausted gas:specification
paint coated:surface:specification
galvanized:surface:specification
polished:surface:specification
100%:surface:specification
gi - 50:model name:specification
d 45:model name:specification
solvent extraction using hexane:extraction method:specification
as per requirement:extraction method:specification
solvent:extraction method:specification
steam distillation:extraction method:specification
solvent extraction:extraction method:specification
includes training, maintenance, and a reliable supply chain for spare parts:after-sales support:specification
comprehensive service, including training and spare parts supply:after-sales support:specification
comprehensive training, spare parts availability, and regular maintenance suppor:after-sales support:specification
comprehensive training, maintenance, and spare parts supply:after-sales support:specification
iso, ce and asme compliance for durability and reliability:design standards:specification
iso, ce and asme-certified designs for durability and reliability:design standards:specification
iso-certified , ce and adhering to asme regulations:design standards:specification
iso, asme, and ce certifications for quality and reliability:design standards:specification
ion exchange resin:treatment:specification
gas nitriding:treatment:specification
gas nitrating:treatment:specification
meets global standards for emissions and waste management:environmental compliance:specification
adheres to international safety and emission standards:environmental compliance:specification
designed to meet global standards for emissions and environmental safety:environmental compliance:specification
designed to meet global environmental and safety standards:environmental compliance:specification
adheres to international safety and environmental standards:environmental compliance:specification
seven seas enterprise:manufactured by:specification
asha engineering works:manufactured by:specification
lakshmi advance bio- tech:manufactured by:specification
(kg/9h),3kg:refining capacity:specification
1 kg. ( also available in 4 kg capacity and custom made on required specification):refining capacity:specification
ex-j type:extractor type:specification
centrifuge hydro:extractor type:specification
20 - 150 ( micron ):range of thickness of wall ceiling panels:specification
20 - 150 ( micron ) [ as per customer ]:range of thickness of wall ceiling panels:specification
10 - 100 ( micron ):range of thickness of wall ceiling panels:specification
automatic pc compatible auto sequencing regular six place solvent extraction system:description:specification
we will assit you in buying most appropriate co-rotating twin screw extruder machine by providing co:description:specification
1hp 440 voltage rpm 1440:vacuum pump:specification
oil free vacuum pump 45 lpm:vacuum pump:specification
gold:material processed:specification
pet:material processed:specification
all types:material processed:specification
compostable:material processed:specification
ldpe:material processed:specification
pharma power:material processed:specification
food:material processed:specification
pvc:material processed:specification
lldpe:material processed:specification
hdpe:material processed:specification
xlpe:material processed:specification
fr/hr:material processed:specification
gold & silver:material processed:specification
biodegradable:material processed:specification
pestiside for former:material processed:specification
aqua regia:processing method:specification
electrolytic:processing method:specification
gravity separation:processing method:specification
600 mm:width of lay flat:specification
500 mm:width of lay flat:specification
760 mm:width of lay flat:specification
460 mm:width of lay flat:specification
800 mm:nip roll size:specification
1625 mm:nip roll size:specification
555 mm (22 inch):nip roll size:specification
550 mm:nip roll size:specification
555 mm:nip roll size:specification
1250 mm:nip roll size:specification
508 mm:nip roll size:specification
500 mm:nip roll size:specification
660 mm:nip roll size:specification
810 mm:nip roll size:specification
40 mm:screw barrel size:specification
55 mm:screw barrel size:specification
16":maximum size:specification
24":maximum size:specification
80 mm:take up speed:specification
90 m/min:take up speed:specification
20-90 m/min:take up speed:specification
60 m/min:take up speed:specification
75 m/min:take up speed:specification
2.25kw:power load:specification
5 hp:power load:specification
38crmoaia/42crmoaia/w302:base material:specification
42crmo4,38crmoala,41craimo7,16mncr5,31crmov9,34craini7,etc:base material:specification
offline:service mode:specification
onsite:service mode:specification
monolayer:film layer structure:specification
3 layer:film layer structure:specification
3 layer (a/b/c):film layer structure:specification
fluoropolymer extruder:machine types:specification
monolayer extruder:machine types:specification
liquid extraction in packed bed:product name:specification
solid-liquid extraction (bonnoto type):product name:specification
. spray extraction column:product name:specification
solvent oil extraction plant:product name:specification
pvc pipe:material type:specification
stainless steel:material type:specification
5100:model no.:specification
ve-bfex-01:model no.:specification
d80ppvcext:model no.:specification
d45vext:model no.:specification
dnz:model no.:specification
sm-481:model no.:specification
silver:metal type:specification
gold:metal type:specification
refining:process type:specification
electrolytic:process type:specification
chemical:process type:specification
aqua regia:process type:specification
solvent extraction:process type:specification
volumes under 300l:flowrate:specification
1,8 to 3 m cube per hour:flowrate:specification
1500000:1 ton:specification
2500000:1 ton:specification
37 kw:driving motor:specification
2hpx4p:driving motor:specification
35 degreec (ambient) to 300 degreec:temperature control range:specification
35 c (ambient) to 300 c:temperature control range:specification
150 litres cold water(+1degree c) capacity:convection cooler:specification
20 l cold water:convection cooler:specification
150l cold water (+1degree c) capacity:convection cooler:specification
water pipe type (it has 4 column) it works under vacuum:filtration system:specification
auto filtration with vacuum pump:filtration system:specification
pump:filtration system:specification
300 capacity cube meter:vacuum system:specification
yes:vacuum system:specification
optional:vacuum system:specification
no:vacuum system:specification
52 mm:screw dia:specification
55mm:screw dia:specification
21.7:screw dia:specification
41 mm:screw dia:specification
81 mm:screw dia:specification
92mm parallel:screw dia:specification
62mm conical:screw dia:specification
35 x 45mm:screw dia:specification
2 x 40 & 45mm:screw dia:specification
45mm:screw dia:specification
90 mm:screw dia:specification
35 mm:screw dia:specification
nil:motor rating:specification
45 kw:motor rating:specification
60 kw:motor rating:specification
55 kw:motor rating:specification
65 kw:motor rating:specification
nil:air pressure:specification
0.5~0.8mpa:air pressure:specification
0.5- 0.8mpa:air pressure:specification
35kw:installed capacity:specification
45kw:installed capacity:specification
34.75 kva:installed capacity:specification
1000 mm:film size:specification
800 mm:film size:specification
1800 mm:film size:specification
700 mm:film size:specification
2500000:1:specification
5000000:1:specification
2000000:1:specification
2000:1:specification
less than 40 db:noise level:specification
up to 80 dba:noise level:specification
less than 60 db:noise level:specification
all types:l d ratio:specification
18-1 l/d:l d ratio:specification
371:l d ratio:specification
25:l d ratio:specification
5 lit:reagent:specification
300 ml:reagent:specification
depending on quantity:reagent:specification
up to 8 liter:reagent:specification
yes:control panel:specification
pcb:control panel:specification
seperate:control panel:specification
fully automatic:control panel:specification
on patended siebec cartridge:filtration:specification
hepa filter:filtration:specification
cyclone separator:filtration:specification
ulpa filter:filtration:specification
27 kw:contacting load:specification
36 kw:contacting load:specification
30 kw:contacting load:specification
15 kw:contacting load:specification
three layer:layer type:specification
mono layer:layer type:specification
two layer:layer type:specification
gold:material capability:specification
gold and silver:material capability:specification
gold only:material capability:specification
three layer:film layer:specification
multilayer - aba three layer:film layer:specification
single:film layer:specification
600 mm:door opening:specification
350 mm:door opening:specification
800 mm:door opening:specification
5 year:flow sysytem:specification
5 yers:flow sysytem:specification
750000:flow sysytem:specification
209 l:drum volume:specification
60 l:drum volume:specification
352 l:drum volume:specification
350 mm:drum depth:specification
410 mm:drum depth:specification
320 mm:drum depth:specification
800 rpm:drum speed:specification
750 rpm:drum speed:specification
980 rpm:drum speed:specification
500 mm:nip roll:specification
850 mm:nip roll:specification
55 inch:nip roll:specification
26":nip roll:specification
from 2,400 to 3,600 rpm:speed control:specification
2,400 to 3,600 rpm:speed control:specification
electronic speed control:speed control:specification
0-3600 rpm:speed control:specification
to mix, compound, and process various materials, particularly plastics and food components:use:specification
industrial:use:specification
gold refining plant:use:specification
gold and silver refining plant:use:specification
checking of bitumen percentage:use:specification
ss316:moc:specification
polypropylene chamber 12 / 24 port:moc:specification
mild steel:moc:specification
90 mm:mother extruder screw dia.:specification
125 mm:mother extruder screw dia.:specification
100 mm:mother extruder screw dia.:specification
55 mm:babby extruder screw dia.:specification
75 mm:babby extruder screw dia.:specification
65 mm:babby extruder screw dia.:specification
xxx:question:specification
40x48:question:specification
1w:question:specification
1kw:question:specification
masala chana:type of namkeen:specification
extruded snacks:type of namkeen:specification
snacks:type of namkeen:specification
22:1:l/d:specification
30:1:l/d:specification
18:1:l/d:specification
ie2, ie3:motor type:specification
single phase:motor type:specification
ac or dc:motor type:specification
ac:motor type:specification
frequency control:motor speed:specification
1440 rpm:motor speed:specification
60 to 160 rpm:motor speed:specification
160 rpm:motor speed:specification
1400 rpm:motor speed:specification
hexane is commonly used,while other solvents like ethanol or isopropanol may also be used:solvent type:specification
aqueous:solvent type:specification
bulk solvent:solvent type:specification
250 to 300 kw:total power:specification
130 kw:total power:specification
35 hp:total power:specification
35 kw:total power:specification
20 (kw):total power:specification
300kw:power (kilowatt):specification
155 kw:power (kilowatt):specification
2.1:power (kilowatt):specification
1 kg:material loading capacity:specification
5kg/13min:material loading capacity:specification
7 kg per min:material loading capacity:specification
100 t:material loading capacity (t):specification
500 kg:material loading capacity (t):specification
1 ton:material loading capacity (t):specification
suitable for extracting juice from a variety of fruits and vegetables in commercial settings:applications:specification
construction,automotive,aerospace,electronics etc.:applications:specification
raw oil production oil processing:applications:specification
nucleic acid extraction:applications:specification
melts the raw plastic material (such as ldpe, lldpe, or hdpe).:extruder:specification
30mm + 35mm groove feed:extruder:specification
90 mm 14 l/d water cooled:extruder:specification
roex 120.24 / roex 150.24:extruder:specification
277:voltage::specification
220v:voltage::specification
ac 220v 50hz:voltage::specification
380 v:voltage::specification
compact countertop heating courses with insulated firebrick walls to maintain high temperatures:type of furnace:specification
fix:type of furnace:specification
tilt:type of furnace:specification
20 1:screw l d ratio:specification
24 1:screw l d ratio:specification
28 1:screw l d ratio:specification
33 1:screw l d ratio:specification
30 1:screw l d ratio:specification
26 1:screw l d ratio:specification
dia 6" x 33" long:chamber size:specification
3.1/2" x 20" inch:chamber size:specification
3.6 x 3.6 x 2.0 mts:chamber size:specification
135 kg/hr:max. output pvc:specification
180 kg/hr:max. output pvc:specification
520 kg/hr:max. output pvc:specification
110 kg/hr:max. output pvc:specification
herbal products:application type:specification
industrial:application type:specification
jewelry making:application type:specification
laboratory:application type:specification
edible oil processing:application type:specification
aqua regia:refining method:specification
chemical:refining method:specification
electrolytic:refining method:specification
200 - 850 mm:working width:specification
800mm:working width:specification
1300mm:working width:specification
up to 280 kg/hr:output capacity:specification
180kg/hr:output capacity:specification
2 tons/day:output capacity:specification
55 (kw-ac):extruder drive:specification
75 (kw-ac):extruder drive:specification
15 ac kw:extruder drive:specification
45 (kw ac):extruder drive:specification
90 (kw-ac):extruder drive:specification
75 ac (kw):extruder drive:specification
560 kw ac:extruder drive:specification
55 kw-ac:extruder drive:specification
15 (kw-ac):extruder drive:specification
36 kw-ac:extruder drive:specification
45 kw-ac:extruder drive:specification
11 kw ac:extruder drive:specification
30 ac kw:extruder drive:specification
200 (kw-ac):extruder drive:specification
11:extruder drive:specification
25 d:effective screw length:specification
18 d:effective screw length:specification
28 d:effective screw length:specification
22 d:effective screw length:specification
7-10 barrel heating zones with precision control:heating zones:specification
8-10 precision controlled heating zones:heating zones:specification
10-12 zones for precise barrel temperature control:heating zones:specification
up to 750 mpm:output speed:specification
up to 130 kg / hour:output speed:specification
600-800rpm:output speed:specification
600-900 mm:sheet width:specification
500 to 1500mm:sheet width:specification
800-1600mm:sheet width:specification
460 x 700 (phi x l mm):roll size:specification
500 x 1070 (phi x l mm):roll size:specification
500 x 1150 (phi x l mm):roll size:specification
45 m/min:roll speed:specification
40 m/min:roll speed:specification
36 m/min:roll speed:specification
181:l and d ratio:specification
261:l and d ratio:specification
281:l and d ratio:specification
301:l and d ratio:specification
28:l and d ratio:specification
251:l and d ratio:specification
401:l and d ratio:specification
20-150 micron:thickness range:specification
25-200 micron:thickness range:specification
40-150 micron:thickness range:specification
20-200 micron:thickness range:specification
30 to 300 gsm:thickness range:specification
10 to 50 mic:thickness range:specification
20 to 80 mic:thickness range:specification
20 to 150 mic:thickness range:specification
ksa- semi automatic:winder type surface:specification
ksw - semi automatic:winder type surface:specification
kvp - semi automatic:winder type surface:specification
ksa - semi automatic:winder type surface:specification
750 kg/hr:max output upvc profile:specification
450 kg/hr:max output upvc profile:specification
300 kg/hr:max output upvc profile:specification
1100 mm:nip roller size:specification
1450 mm:nip roller size:specification
1800 mm:nip roller size:specification
1400 mm:nip roller size:specification
120 kg/hrs max:out put:specification
180-200 kgs/hr:out put:specification
300-330 kgs/hr:out put:specification
300-650 kg/hr:out put:specification
herb:part type:specification
leaf:part type:specification
root:part type:specification
650 - modified ppo (pellet + powder):screw speed range modified ppo:specification
700 min-1 modified ppo (pellet + powder):screw speed range modified ppo:specification
600 min -1 modified ppo (pellet + powder):screw speed range modified ppo:specification
1800x780:drum size (dxa):specification
1550x650:drum size (dxa):specification
1000x400:drum size (dxa):specification
730x320:drum size (dxa):specification
1070x400:drum size (dxa):specification
1450:capacity (lb):specification
1100:capacity (lb):specification
240:capacity (lb):specification
160:capacity (lb):specification
100-170 kg/hr:output rpvc filled:specification
450-700:output rpvc filled:specification
150-250 kg/hr:output rpvc filled:specification
120 to 180 litre:suitable for mixer capacity:specification
370 to 440 litre:suitable for mixer capacity:specification
50 to 90 litre:suitable for mixer capacity:specification
240 to 305 litre:suitable for mixer capacity:specification
110 kw:extruder motor:specification
150 kw:extruder motor:specification
45 kw:extruder motor:specification
180 kw:extruder motor:specification
450-550 kg/hr:output spvc unfilled:specification
85-130 kg/hr:output spvc unfilled:specification
140-190 kg/hr:output spvc unfilled:specification
600 kg/hr:max output upvc pipe:specification
850 kg/hr:max output upvc pipe:specification
1200 kg/hr:max output upvc pipe:specification
16-450 mm:pipe range:specification
16-110 mm:pipe range:specification
20-110 mm:pipe range:specification
16-250mm:pipe range:specification
aluminium extrusion:plant type:specification
industrial scale:plant type:specification
continuous type:plant type:specification
250 - 600 (kg/h):throughput range pc powder low molecular weight:specification
600 - 1450 (kg/h) pc (powder, low molecular weight):throughput range pc powder low molecular weight:specification
350 - 800 pc (powder, low molecular weight):throughput range pc powder low molecular weight:specification
150 - 600 (kg/h):throughput range a pet flake:specification
400 - 1450 (kg/h)a-pet (flake, non-dry):throughput range a pet flake:specification
250 - 800 a-pet (flake, non-dry):throughput range a pet flake:specification
200 - 750 (kg/h):throughput range pp talk:specification
500 - 1800 (kg/h) pp (pellet) + talk (30%, 5 - 10um):throughput range pp talk:specification
300 - 1000 pp (pellet) + talk (30%, 5 - 10um):throughput range pp talk:specification
100 - 350 (kg/h):throughput range pp:specification
230 - 850 (kg/h) pp (pellet) + talk (30% - 50%, fine powder):throughput range pp:specification
150 - 500 pp (pellet) + talk (30% - 50%, fine powder):throughput range pp:specification
600 min -1 pp (pellet) + gf (30%):screw speed range pp pellet:specification
700 min-1 pp (pellet) + gf (30%):screw speed range pp pellet:specification
650 pp (pellet) + gf (30%):screw speed range pp pellet:specification
600 min-1 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
500 min -1 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
650 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
1250-1450rpm:input speed:specification
1000 , 1500 rpm:input speed:specification
1500 rpm:input speed:specification
80 kg/hr:extruding output:specification
25 kg/hr:extruding output:specification
35 kg/hr:extruding output:specification
single station:surface winder:specification
single/two station:surface winder:specification
120 hp:surface winder:specification
650 pa5 (pellet) + gf (30%):screw speed range pellet:specification
700 min-1 pa5 (pellet) + gf (30%):screw speed range pellet:specification
600 min -1 pa5 (pellet) + gf (30%):screw speed range pellet:specification
140 kn:continuous load:specification
190 kn:continuous load:specification
318 kn:continuous load:specification
223 kn:short term load:specification
420 kn:short term load:specification
320 kn:short term load:specification
470 kn:short term load:specification
190-250 kg/hr:output spvc filled:specification
130-170 kg/hr:output spvc filled:specification
530-700 kg/hr:output spvc filled:specification
90-100 kg/hr:max. output:specification
180-200 kg/hr:max. output:specification
130-140 kg/hr:max. output:specification
13nm/cm3:specific torque:specification
11.3 nm/cm3:specific torque:specification
7.2 nm/cm:specific torque:specification
14.6nm/cm3:specific torque:specification
8.7 nm/cm3:specific torque:specification
5.46nm/cm3:specific torque:specification

"""
# ============================================================================
# END OF ATTRIBUTE DATA SECTION - DO NOT EDIT BELOW THIS LINE
# ============================================================================

def parse_attribute_dataset(raw_data):
    """Parse the attribute dataset into a structured format"""
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    
    # Remove placeholder text
    lines = [line for line in lines if not line.startswith('PASTE_') and not line.startswith('EACH_')]
    
    # Group by attribute name
    attr_dict = {}
    for line in lines:
        parts = line.split(':')
        if len(parts) == 3:
            value, name, attr_type = parts
            if name not in attr_dict:
                attr_dict[name] = []
            if value not in attr_dict[name]:
                attr_dict[name].append(value)
    
    return attr_dict

def create_dataset_prompt(query, attr_dict):
    """Create prompt with attribute dataset"""
    
    # Build attribute reference (compressed format)
    attr_reference = "Available Attributes for Industrial Extraction Plants and Extruder Machines:\n\n"
    for attr_name, values in attr_dict.items():
        value_list = ' | '.join(values[:20])
        if len(values) > 20:
            value_list += f" ... (+{len(values)-20} more)"
        attr_reference += f"- {attr_name}: {value_list}\n"
    
    prompt = f"""{attr_reference}

Extract product attributes from the query using ONLY the attributes listed above.

RULES:
1. Use ISQ format: attribute_value:attribute_name:attribute_type
2. attribute_type is always "specification"
3. Only extract attributes that match the available list
4. Return as a Python list

Examples:

Query: "440V three phase automatic extruder"
Output: ['440 v:voltage:specification', 'three phase:phase:specification', 'automatic:automation grade:specification']

Query: "stainless steel paint coated extraction plant"
Output: ['stainless steel:body material:specification', 'paint coated:surface finishing:specification']

Now extract attributes:

Query: "{query}"
Output: """
    
    return prompt

def call_gemini_api(query, attr_dict, max_retries=3):
    """Call Gemini API with dataset context"""
    for attempt in range(max_retries):
        try:
            prompt = create_dataset_prompt(query, attr_dict)
            
            payload = {
                "model": GEMINI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 300
            }
            
            headers = {
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                content = content.replace("'", '"')
                
                try:
                    if content.startswith('[') and content.endswith(']'):
                        isq_list = json.loads(content)
                    else:
                        isq_list = [item.strip() for item in content.replace('\n', ',').split(',') if item.strip()]
                except:
                    isq_list = [content] if content else []
                
                valid_isqs = [isq for isq in isq_list if isq.count(':') == 2]
                
                return {
                    'success': True,
                    'query': query,
                    'gemini_dataset_attr_count': len(valid_isqs),
                    'gemini_dataset_isq_list': str(valid_isqs),
                    'gemini_dataset_isq_pipe': ' | '.join(valid_isqs),
                    'gemini_dataset_raw_output': content
                }
            else:
                if attempt < max_retries - 1:
                    print(f" [Retry {attempt+1}]", end="")
                    time.sleep(2)
                    continue
                return {
                    'success': False,
                    'query': query,
                    'gemini_dataset_attr_count': 0,
                    'gemini_dataset_isq_list': '[]',
                    'gemini_dataset_isq_pipe': '',
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f" [Retry {attempt+1}]", end="")
                time.sleep(2)
                continue
            return {
                'success': False,
                'query': query,
                'gemini_dataset_attr_count': 0,
                'gemini_dataset_isq_list': '[]',
                'gemini_dataset_isq_pipe': '',
                'error': str(e)
            }

def main():
    # Parse attribute dataset
    print("Parsing attribute dataset...")
    attr_dict = parse_attribute_dataset(ATTRIBUTE_DATASET)
    total_attrs = sum(len(values) for values in attr_dict.values())
    print(f"Loaded {len(attr_dict)} unique attribute types")
    print(f"Total attribute values: {total_attrs}")
    print()
    
    # Read queries
    print(f"Reading queries from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    if 'query' not in df.columns:
        print("ERROR: 'query' column not found in CSV!")
        return
    
    queries = df['query'].dropna().tolist()
    total_queries = len(queries)
    
    print(f"Processing {total_queries} queries with Gemini (WITH DATASET)")
    print(f"Progress updates every {BATCH_SIZE} queries")
    print("=" * 80)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{total_queries}] {query[:60]}...", end=" ")
        
        result = call_gemini_api(str(query), attr_dict)
        
        if result['success']:
            success_count += 1
            print(f"OK ({result['gemini_dataset_attr_count']} attrs)")
        else:
            fail_count += 1
            print(f"ERROR")
        
        results.append(result)
        
        if i % BATCH_SIZE == 0:
            print()
            print("=" * 80)
            print(f"BATCH SUMMARY [{i}/{total_queries}]")
            print(f"  Completed: {i} queries")
            print(f"  Success: {success_count}")
            print(f"  Failed: {fail_count}")
            print(f"  Progress: {(i/total_queries)*100:.1f}%")
            print(f"  Estimated time remaining: {((total_queries-i)*0.15/60):.1f} minutes")
            print("=" * 80)
            print()
        
        time.sleep(DELAY_MS / 1000)
    
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 80)
    print("FINAL SUMMARY - GEMINI WITH DATASET")
    print("=" * 80)
    print(f"[DONE] Results saved to: {OUTPUT_CSV}")
    print(f"[DONE] Total queries: {total_queries}")
    print(f"[DONE] Successful: {success_count} ({(success_count/total_queries)*100:.1f}%)")
    print(f"[DONE] Failed: {fail_count} ({(fail_count/total_queries)*100:.1f}%)")
    
    total_attrs_extracted = sum(r.get('gemini_dataset_attr_count', 0) for r in results)
    avg_attrs = total_attrs_extracted / total_queries if total_queries > 0 else 0
    print(f"[DONE] Total attributes extracted: {total_attrs_extracted}")
    print(f"[DONE] Average attributes per query: {avg_attrs:.2f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
