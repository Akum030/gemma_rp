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
INPUT_CSV = "../validation_queries.csv"  # Same queries as zero-shot test
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
GEMINI_MODEL = "anthropic/claude-sonnet-4.5"
DELAY_MS = 100
OUTPUT_CSV = "gemini_2.5_pro_with_dataset_full.csv"
BATCH_SIZE = 100

# ============================================================================
# PASTE YOUR 11K ATTRIBUTE DATA HERE (ISQ FORMAT)
# Format: attribute_value:attribute_name:attribute_type
# ============================================================================
ATTRIBUTE_DATASET = r"""
voltage:440 v:specification
surface finishing:paint coated:specification
automation grade:automatic:specification
phase:three phase:specification
voltage:380 v:specification
body material:stainless steel:specification
i deal in:new only:specification
automation grade:semi-automatic:specification
phase:3 phase:specification
voltage:415 v:specification
size:30 inch:specification
country of origin:made in india:specification
product:silver refining plant:specification
heating range:specification
product:silver refining plant:specification
440 v:voltage:specification
paint coated:surface finishing:specification
automatic:automation grade:specification
three phase:phase:specification
380 v:voltage:specification
stainless steel:body material:specification
new only:i deal in:specification
semi-automatic:automation grade:specification
3 phase:phase:specification
415 v:voltage:specification
30 inch:size:specification
made in india:country of origin:specification
silver refining plant:phase:specification
silver refining plant:heating range:specification
58 rpm:screw speed:specification
plastic:material to be extruded:specification
single phase:phase:specification
mild steel:body material:specification
edr:brand:specification
industrial:usage/application:specification
titanium,pp:body material:specification
0.5 kva:power:specification
99%:purity:specification
650 kg:weight:specification
240 v:voltage:specification
1 phase:phase:specification
gurukrupa enterprises:brand:specification
400 v:voltage:specification
aba 35*45:model name/number:specification
220 v:voltage:specification
50hz:frequency:specification
single:phase:specification
50 mt:production capacity:specification
electric:power source:specification
75mm:diameter:specification
electrical:power source:specification
60 micron:film thickness:specification
600 rpm:screw speed:specification
2 hp:power:specification
low:height:specification
1 kw:lead:specification
yes:installation services:specification
3:phase:specification
titanium, glass, pph:body material:specification
220:power:specification
5 hp:motor power:specification
abc:dimension:specification
fully:automation grade:specification
5:frequency:specification
2/3kw:power:specification
any kind of metal extrusion:type:specification
hand operated:phase:specification
304/316l stainless steel:material:specification
semi-automatic:type:specification
hulk lokpal:brand:specification
client scope:power source:specification
pharmaceutical industry, food and beverages and cosmetics industries:usage/application:specification
50 hz:frequency:specification
cosmetics:usage/application:specification
185 degree celsius:temperature:specification
ms:body material:specification
ac:power:specification
copper:wire material:specification
425 tons:capacity:specification
frp:material:specification
1200w:power:specification
electricity:driven type:specification
45 rpm:screw speed:specification
fully automatic:automation grade:specification
10 kw:motor power:specification
ss:body material:specification
55 kw:power consumption:specification
70mm:wire thickness:specification
24 months:warranty:specification
electric:power consumption:specification
ss:material:specification
single/three:phase:specification
220b:power source:specification
21.7 mm:screw diameter:specification
garbage bags,medical bags:usage/application:specification
iron:body material:specification
shegal face 1.5kelo wat:phase:specification
wire & cable:usage/application:specification
230 volts:voltage:specification
rajco:brand:specification
99.9% pure:purity:specification
5:bowl capacity:specification
self:product type:specification
chemical laboratory:usage/application:specification
k-jhil:brand:specification
mulch film:usage/application:specification
ld:plastic processed:specification
3 mm:panel thickness:specification
mannered:packaging type:specification
cast iron:material:specification
230v:voltage supply:specification
silver refining plant:material:specification
silver refining plant:packaging type:specification
1:phase:specification
semi-automatic:automatic grade:specification
220v:voltage:specification
220 v:power:specification
semi-automatic:operation type:specification
ss 316l:material:specification
80c:heating range:specification
gold star:brand:specification
wooden:packaging type:specification
he:brand:specification
100 tpd - 1000 tpd:capacity:specification
new:condition:specification
0-40:machine power:specification
ek danta refiners:brand:specification
white:color:specification
blue:color:specification
electric:power:specification
50/60 hz:frequency:specification
440v:voltage:specification
india:country of origin:specification
220v:power:specification
abc:depth:specification
nitric and hcl:gases:specification
220 v:power source:specification
100c:temperature:specification
3:number of phases:specification
1.5 liter:bowl capacity:specification
semiautomatic:automation grade:specification
100mm:die size:specification
solvent extraction plant:design type:specification
standard:oil tank capacity:specification
standard:thickness:specification
hand and electric:driven type:specification
for the determination of bitumen percentage in bituminous mixtures:usage/application:specification
no:hand operated:specification
aec:brand:specification
microgold:brand:specification
prasad enterprise:brand:specification
50hp:voltage (v):specification
na:line speed:specification
zzz:frequency:specification
abc:flange width:specification
electric:driven type:specification
stainless steel:material:specification
220-400 vac:voltage:specification
spe:features:specification
stainless steel:wire material:specification
pp or pvdf:material:specification
automatic and semi automatic:automatic grade:specification
single and three:number of phases:specification
herbal extraction:usage/application:specification
automatic:machine type:specification
250 mt.per month:production capacity:specification
mother baby extruder:machine type:specification
pp, upvc, titanium:body material:specification
xxx:dimension:specification
p.p:body material:specification
export quality:packaging type:specification
as 48:model name/number:specification
nitric:gases:specification
industrial & commerical:working area:specification
500mtr/min:production capacity:specification
electronic:power:specification
25 hp:machine power:specification
1 year:warranty:specification
500 ton:capacity:specification
50 hz:frequency (hz):specification
kabra:brand:specification
140-160 (kg/hour):output:specification
3 layer aba for ldpe & hdpe:machine type:specification
45mm*45mm:size:specification
75 bar:pressure:specification
jt:brand:specification
three:phase:specification
single phase a.c:phase:specification
230 v, 50hz:voltage supply:specification
manual:automation grade:specification
automatic:automatic grade:specification
1 hp:motor power:specification
transparent,silver,etc:color:specification
m tech jewel equipment:brand:specification
25 kg:capacity:specification
mild steel:material:specification
ddri:brand:specification
abs:material:specification
galvanized iron:material:specification
poly proplyene:body material:specification
2 kw:power:specification
0-50:output(kg/hr):specification
18:1:screw l/d:specification
herbal extractor plant:usage/application:specification
sgsi:brand:specification
no:installation services:specification
all type of ss & ms:material grade:specification
affluent extrusion:brand:specification
360 v:voltage:specification
1000 gms:bowl capacity:specification
35-40 amp:power:specification
rf521:model number:specification
900:heating range:specification
1400 rpm:motor power:specification
cable insulation extrusion line:application:specification
peak test:brand:specification
pp:body material:specification
1000t:weight:specification
aza 0944 centrifuge extractor (hand operated):model name/number:specification
aza 0946 centrifuge extractor (motorised):model name/number:specification
100 kg/hr:production capacity:specification
50 kg/hr:production capacity:specification
100 kg:capacity(kg):specification
5 kg:capacity:specification
30 kg:capacity(kg):specification
100kg:capacity:specification
10 tpd:capacity:specification
200 kg/hr:production capacity:specification
5 kg:capacity(kg):specification
100g 2kg:capacity:specification
10 kg:capacity(kg):specification
100 tpd:capacity:specification
500 kg/hr:production capacity:specification
50 tpd:capacity:specification
250 kl to 10000 kl:capacity:specification
100 kg/hr:capacity:specification
50 kg:capacity:specification
2000 tpd:capacity:specification
500 tpd:capacity:specification
10:capacity(kg):specification
1to 200 kg:capacity:specification
based on size:packaging size:specification
1000 kg/hr:production capacity:specification
1 to100 kg:capacity:specification
20 kg:capacity:specification
90 kg to 450 kg per hour:production capacity:specification
140 kg/hr:production capacity:specification
20 kg:capacity(kg):specification
more than 1000 kg/hr:production capacity:specification
die casting equipment:machine type:specification
20 ton:max force or load:specification
30 tpd:capacity:specification
80 kg/hr:capacity:specification
90 kg/hr:production capacity:specification
10tpd:capacity:specification
500l:capacity:specification
200:capacity(kg):specification
1 tpd:capacity:specification
5000 tpd:capacity:specification
10tpd and more:capacity:specification
1 kg:capacity(kg):specification
1:capacity:specification
50 kg:capacity(kg):specification
40 kg:capacity(kg):specification
100l-20 ton:capacity:specification
300 kg/hr:production capacity:specification
pvc:plastic processed:specification
twin screw extruder:machine type:specification
c.s./s.s.:material:specification
conical:screw design:specification
yarn extruder:type:specification
10-200:capacity:specification
twin screw:screw design:specification
box based on product:packaging type:specification
1500 g:capacity:specification
pvc, resion:plastic processed:specification
bitumen extractor:type of testing machines:specification
2800 rpm:capacity:specification
hdpe:material:specification
hcp:brand:specification
bitumen:type of testing machines:specification
5 ton melting furamce:capacity:specification
60 kg/hour:production capacity:specification
fully automatic:type:specification
design for special application:screw design:specification
2 kg:capacity:specification
bestco:brand:specification
teknik:brand:specification
hospital and hotal:usage/application:specification
tube extrusion machine:machine type:specification
1500 gm:capacity:specification
metal:material:specification
aluminium:material:specification
96:no of position:specification
30 kg:capacity:specification
1 to 200kg:capacity:specification
1000 tpd:capacity:specification
8 kg:capacity:specification
500 kg/hr:capacity:specification
1000 - 1100 kg per day:capacity:specification
40 tpd:capacity:specification
3 kg:capacity:specification
450 kg/hr:production capacity:specification
1 to 100 kg:capacity:specification
1 to 10 kg:capacity:specification
50-500 tons per day:capacity:specification
10 kg:capacity:specification
30 kg:weighing capacity:specification
50 kg/h:capacity:specification
12 mm:size:specification
110 kg/hr:production capacity:specification
100 kg:capacity:specification
1 to 2kg:capacity:specification
3kg:capacity:specification
2280 kg/hr:production capacity:specification
200:production capacity:specification
200 tpd:capacity:specification
high:capacity:specification
25 kg/hr:production capacity:specification
10 tph:capacity:specification
unl:capacity:specification
corotating twin screw extruder:screw design:specification
segmented:screw design:specification
hpmc:brand:specification
new:type:specification
2kg:capacity:specification
1500gm:capacity:specification
bimetallic:screw type:specification
1.5l:capacity:specification
heaven extrusions:brand:specification
ldpe:material:specification
malik's:brand:specification
jaybe:brand:specification
naveen:brand:specification
1500 gms:capacity:specification
famsun:brand:specification
eureka:brand:specification
universal:screw design:specification
swaraj:brand:specification
commercial:industry type:specification
swaraj make:screw design:specification
plastic prosesh:plastic processed:specification
pvc pipe:plastic processed:specification
200*200 mm:platform size:specification
1500g or 3000 g:capacity:specification
aluminium:material to be extruded:specification
alumunium:material to be extruded:specification
parallel:screw design:specification
pvc:material:specification
fire fighting:usage/application:specification
48:no of position:specification
laboratory use:application:specification
mp/ex-tape-110:model name/number:specification
10 kg:production capacity:specification
70 kg:capacity(kg):specification
10 kg/hr:capacity:specification
100 lph:plant capacity:specification
20:capacity(kg):specification
30:capacity(kg):specification
25 tph:capacity:specification
90 kg:capacity(kg):specification
80kg:capacity:specification
1tpd:capacity:specification
200 tdp:capacity:specification
20 ton to 300 ton:capacity:specification
100 l:capacity:specification
250 to 300 kg/hr:production capacity:specification
25 kg/batch to 50 tpd:capacity:specification
500 g:capacity:specification
single phase:electricity connection:specification
based on size:packaging type:specification
1500 grams:capacity:specification
laundry:usage/application:specification
turbo:brand:specification
horizontal:type:specification
100 kg - 500 kg:capacity:specification
horizontal basket extruder:machine type:specification
semi automatic:operation mode:specification
pharma lab:usage/application:specification
48 samples:capacity:specification
jsl 304 ss grade:material:specification
co rotating:screw design:specification
14 to 60 kg per batch:capacity:specification
50 mt:capacity:specification
bimetallic:screw design:specification
stainless steel body:material:specification
painted:surface finish:specification
25:capacity:specification
20 ltrs to 500 ltrs:capacity:specification
25 kw:power consumption:specification
electric:type of testing machines:specification
3000gms:capacity:specification
depends on press capacity:capacity:specification
60hp:power consumption:specification
144:no of position:specification
96 position:no of position:specification
250 kg/hr:capacity:specification
250 liter:capacity:specification
50:capacity(kg):specification
400 kg/hr:production capacity:specification
3000 mm:length:specification
up to 250 kg:capacity:specification
semi automatic:automation grade:specification
1.50 ton in a day:production capacity:specification
200 ltr:capacity:specification
15 kg:capacity:specification
350 kg/hr:production capacity:specification
3mt - 5mt:production capacity:specification
5 metric tonne:capacity:specification
pvc pipe and profole:screw design:specification
50kw.:power consumption:specification
40hz:frequency:specification
500kg/shift:production capacity:specification
continuous extrusion machine:machine type:specification
electric:power type:specification
60 mm:diameter:specification
65/132:size:specification
ms:material:specification
20kg:capacity:specification
civil laboratory:type of testing machines:specification
pipe extrusion machine:machine type:specification
blown film extrusion machine:machine type:specification
polypropylene:material:specification
340 v:voltage:specification
100-200 kg/hr:output:specification
upto 25 kg:capacity:specification
0-40 kw:machine power:specification
12 months:warranty:specification
230 v:voltage supply (v):specification
standard:design type:specification
230vac:voltage:specification
ss316,304ms:material:specification
1750 rpm:line speed:specification
1000:voltage:specification
single or triple:phase:specification
3tons:capacity:specification
50 - 60 hz:frequency (hz):specification
50-100 kg/hr:output:specification
75 kg/hr:average productivity:specification
800 kg per day:capacity:specification
8-12kg/h:production capacity:specification
free:installation services:specification
415 v:voltage (volt):specification
30 nm:screw torque:specification
pph:body material:specification
60 nm:screw torque:specification
semi-automatic:operation mode:specification
up to 40 kw:power:specification
as per need:capacity:specification
customized:pressure:specification
240:voltage (v):specification
240:power (v):specification
200:average productivity (kg/hour):specification
1500:weight (kg):specification
20 to 315 mm:diameter (millimeter):specification
eie:brand:specification
glass, titanium, pph:material:specification
wooden packing:packaging type:specification
99.99:purity:specification
700:weight:specification
250 l:capacity:specification
150-170 kg/hour:output:specification
mild steel (body material):material:specification
50 - 60 hz:frequency:specification
100:purity (%):specification
steel / cast iron:material:specification
10-20 bar:pressure:specification
5kw:power (kw):specification
99.95-99.99:purity:specification
400 mm:filter diameter (millimeter):specification
220 v:voltage (volt):specification
20 - 80:output:specification
cnc:control type:specification
4 ton:capacity:specification
440:voltage (volt):specification
customized:production capacity:specification
220-240 (kg/hour):output:specification
300-350:output(kg/hr):specification
automatic:operation mode:specification
10 ton:capacity:specification
0-50 kg/hr:output:specification
pu:body material:specification
230v:voltage:specification
steel:body material:specification
1kg:capacity:specification
steel:material:specification
2-8 ton:weight:specification
6000 ft/lbs:screw torque:specification
300-350 kg/hr:output:specification
green blue:color:specification
aluminium extrusion:usage/application:specification
200 v:voltage:specification
pvc & hdpe:material:specification
pilot:design type:specification
1500mm*3000mm*6000mm*:dimension:specification
boiler:steam supply:specification
elpie:brand:specification
5 kw:power:specification
ms / ss:body material:specification
ss:color:specification
2250x540x1160mm. (lxwxh):size:specification
50 hz.:frequency:specification
multiseed oil extraction:usage/application:specification
200 degs:temperature:specification
clear:finishing:specification
as per client requirement.:automation grade:specification
borosilicate glass:material:specification
sritech:brand:specification
paint coated:surface treatment:specification
400 rpm:line speed:specification
noodle:material to be extruded:specification
stainless steel:machine body material:specification
800x800x1650mm (lxwxh):size/dimension:specification
sjps135:model name/number:specification
380v:voltage:specification
230 v ac:power:specification
nath ji:brand:specification
electric dryer:dryer type:specification
110 to 240v:voltage supply:specification
220-380 v:voltage:specification
rupson:brand:specification
gear box:driven type:specification
yes:hand operated:specification
ss316, ss304:material:specification
royle extrusion systems pvt. ltd., pune:brand:specification
extruder for xlpe, epr:machine type:specification
ms frame, alloy steel barrel and screw:body material:specification
1500 gms.:capacity:specification
bitumen material testing:usage/application:specification
popular:brand:specification
0.75kw:power:specification
800kg:weight:specification
manual:operation mode:specification
on request:power source:specification
depends on material:average electricity consumption:specification
depends on material:min finish wire diameter:specification
on request:design type:specification
1440 rpm:speed:specification
65/100 mm:die size:specification
304:steel grade:specification
200 litre:capacity:specification
280 v:voltage:specification
5kw:motor power:specification
shubham extrusion:brand:specification
1-2:capacity:specification
silver refining plant:dimension:specification
440 volts:voltage:specification
fully automatic:machine type:specification
ashok industries:brand:specification
stainless steel and mild steel:material:specification
25 x 25:dimension:specification
10 x 10:dimension:specification
20 hz:frequency:specification
50/60:frequency:specification
extraction of herbal products:usage/application:specification
1500 rpm:speed (rpm):specification
50/60hz:frequency:specification
7.5 kw:power:specification
silver:color:specification
as per plant:sheet thickness:specification
999:purity:specification
9999:purity:specification
10 bar:pressure:specification
50-60 hz:frequency:specification
220 volt:voltage:specification
999+:purity (%):specification
100:line speed:specification
1 hp:power:specification
20 hp:machine power:specification
brass, copper:material:specification
max 1200 m/min:line speed:specification
350 watt:power:specification
45mm:screw diameter:specification
48 - 75 ( kw ):machine power:specification
100 ( micron ):thickness:specification
3 ton:weight:specification
oeplmono01:model name/number:specification
5 x 5 x 5 to 22 x 8 12 ( l x w x h ):size:specification
300 - 600 to 1600 - 2500 ( mm ):lay flat width:specification
extruder:plastic processed:specification
no maintenance:maintenance:specification
alloy steel:material:specification
gray:color:specification
110-440 v:voltage:specification
upto 5000 litres:capacity:specification
30 tonne:production capacity:specification
55 kw:power:specification
sliding:open style:specification
a.c supply:power:specification
25-30kg:weight:specification
75-150 kg/hr:capacity (kilogram/hour):specification
32, 40, 45, 55 mm:screw diameter (mm):specification
candour technology:brand / model:specification
ms anitcorrosive powder coated finish:material:specification
220-230 voltage:frequency:specification
12mm:thickness:specification
4000 sqmtr:working area:specification
chemical,pharma industries:usage/application:specification
bitumen testing:usage/application:specification
single 220:phase:specification
100kg/hr:capacity:specification
automatic:driven type:specification
used:condition:specification
1300-1500 kg/hour:output:specification
300-350 kg/hour:output:specification
yes:automation grade:specification
220 vac:voltage:specification
footwear:material:specification
10-50 micron:film thickness:specification
35 mm:screw diameter:specification
380 volt:voltage (v):specification
4 kw:power consumption (kw):specification
crown kumar:brand:specification
shft:brand/make:specification
4-10 kw:power:specification
1.5 liter:capacity:specification
1500-3000:speed (rpm):specification
220 v:voltage (v):specification
0.5 kw:power:specification
1-80 t/h:capacity:specification
15.0 ton per batch:capacity:specification
50.0 ton per batch:capacity:specification
1500gms:capacity:specification
900:dimension:specification
new:brand:specification
12 x 12:dimension:specification
titanium:body material:specification
semi automatic:frequency:specification
1/2 hp:motor power:specification
mechotechllp:brand:specification
999+:purity:specification
100:range:specification
pp/ titanium:body material:specification
300 kg:capacity:specification
x.x.x:size:specification
1440:air volume (m3/h):specification
100%:air flow:specification
customised:design type:specification
yes:line speed:specification
10:model name/number:specification
pph, borosilicate glass & titanium:body material:specification
triple:phase:specification
230:voltage:specification
semi automatic:font roll diameter:specification
semi automatic:line speed:specification
230:power:specification
metal +pp:body material:specification
puff:material to be extruded:specification
china:design:specification
3mm:wire thickness:specification
stainless steel-314:material:specification
pp, glass, titanium:body material:specification
1:power:specification
sunshine scientific:brand:specification
customized:voltage:specification
customized:compass:specification
good:driven type:specification
ss steels 314:body material:specification
415 v 50 hz 4 wire:wire diameter:specification
1500 kgs:weight:specification
1 year with services:warranty:specification
146-194 kw:power consumption:specification
electricity:power source:specification
415-440 v:voltage:specification
70 - 110 kg/hour:average productivity:specification
1-5 kw:machine power:specification
220-440 v:voltage:specification
qubics:brand:specification
7.5 kw:power consumption:specification
solid phase extraction positive pressure:model name/number:specification
rrp:brand:specification
labtest:brand:specification
50 -350kg per.hour:output:specification
ac:power source:specification
1500ml:bowl capacity:specification
new and second hand:i deal in:specification
lead:wire material:specification
2 place:capacity:specification
scs 2e:model:specification
nil:shelf life:specification
two:phase:specification
prism:brand:specification
35:heating range:specification
wire & cable manufacturing:usage/application:specification
cable extruder:usage/application:specification
250 gm:bowl capacity:specification
3500 rpm:speed:specification
good:frequency:specification
good:usage/application:specification
8" to 60":drum size:specification
metal:body material:specification
optional:installation services:specification
pharmaceutical machines:usage/application:specification
as per order:size/dimension:specification
round:shape:specification
400-kg:weight:specification
bsi-model 300-mm:brand:specification
3ft*3ft*7ft:dimension:specification
a:automation grade:specification
60 hz:frequency:specification
220 / 380 / 415:voltage:specification
alloy:material:specification
semi automated:automation grade:specification
999.5 / 99.99:purity:specification
polypropelyne:body material:specification
220:voltage:specification
customised:dimension:specification
single phase ,230v & ac supply:power:specification
1.0 kw:power:specification
250 kg:weight:specification
stainless steel 304:material:specification
as per requirement:motor power:specification
220w:motor power:specification
servo:driven type:specification
see pdf:model name/number:specification
see pdf:size:specification
any:color:specification
see pdf:screw speed:specification
see pdf:installation services:specification
polypropylene:body material:specification
0.5 hp:power:specification
120 v:voltage:specification
as per requirement:machine structure:specification
220 volt, 50-60 hz, single phase, ac supply:power:specification
ss304:body material:specification
borosilicate glass, borosilicate glass.:material:specification
12 kg:weight:specification
color coated:surface finishing:specification
shiv:brand:specification
cable extrusion:usage/application:specification
herenba:brand:specification
bitumen test:usage/application:specification
3mm:panel thickness:specification
extruech:brand:specification
singal:phase:specification
ms/ss:body material:specification
fully automatic:line speed:specification
10 x 10 x 10:dimension:specification
titanium, glass pp:body material:specification
touch screen , fully automatic:motor power:specification
480v:voltage:specification
chemical industries:usage/application:specification
electrical:power:specification
1.5 kg:bowl capacity:specification
2400 rpm:speed:specification
8:pressure:specification
200:temperature:specification
50:frequency:specification
2x2.5x6feet (lxwxh):dimension:specification
mild steel (body):material:specification
1hp:power:specification
7 hours:line speed:specification
xxx:frequency:specification
standard:phase:specification
standard:heating range:specification
10 to 100tph:production capacity:specification
240v:voltage:specification
60hz:frequency:specification
pp:filter medium material:specification
gold:type of metal:specification
mepup:model name/number:specification
20 tons/day:capacity:specification
die roll:type:specification
1500g:capacity:specification
1000:capacity:specification
to extrude dough:usage/application:specification
mahindra:brand:specification
1500kg:capacity:specification
60 kw:machine power (kw):specification
ss 304:material of construction(contact):specification
1500 or 3000 g capacity:capacity:specification
1.5 ltrs:capacity:specification
bitumen centrifuge extractor:type of testing machines:specification
100:production capacity:specification
12 sample and 24 sample:capacity:specification
extraction:usage/application:specification
40mm:screw diameter:specification
extraction plant:machine type:specification
solvent extraction:machine type:specification
extraction equipment:machine type:specification
appl:brand:specification
curcumin extraction:usage/application:specification
oleoresin extraction plant:machine type:specification
mustard oleoresin extraction:machine type:specification
extrusion:machine type:specification
senna leaves extraction plant:usage/application:specification
plain:pattern type:specification
jockey extruder:machine type:specification
1500 / 3000 grams:capacity:specification
natural color extraction plant:usage/application:specification
extraction:machine type:specification
solvent extraction:usage/application:specification
aza:brand:specification
18 inch:size:specification
bitumen:material:specification
starting from 50 tons/day:capacity:specification
140kg/hr:production capacity:specification
160 kg/hour:production capacity:specification
150 kg/hr:production capacity:specification
350 kg/hr:capacity:specification
110kg/hr:production capacity:specification
20 tpd:capacity:specification
capacuty 100kg:capacity:specification
50tpd:capacity:specification
700kg/hr:capacity:specification
1000 kg/hr:capacity:specification
680 kg/hr:capacity:specification
650 kg/hr:capacity:specification
950 kg/hr:capacity:specification
750 kg/hr:capacity:specification
780kg/hr:capacity:specification
200 kg/hr:capacity:specification
50kg/hr:capacity:specification
750kg/hr:capacity:specification
550kg/hr:capacity:specification
620kg/hr:capacity:specification
80kg/hr:capacity:specification
220kg/hr:capacity:specification
280kg/hr:capacity:specification
400kg/hr:capacity:specification
50 kg/hr:capacity:specification
60kg/hr:capacity:specification
15 to 150 kgs:capacity:specification
bio-degradable corn starch:raw material:specification
10:no of unit to be tested:specification
twin:screw design:specification
aluminum:material:specification
5tons:capacity:specification
300 tpd:capacity:specification
ss/ms:material:specification
manual:technology:specification
an:plastic processed:specification
pvc pipe , cpvc pipe:plastic processed:specification
pvc pipe plant:usage/application:specification
pan india:service location:specification
twin screw:plastic processed:specification
spices:usage/application:specification
metal:material to be extruded:specification
twin:screw number:specification
hdpe:plastic processed:specification
40 kw:machine power:specification
electrically operated:type of testing machines:specification
silver:metal:specification
500 to 5500 ton:max force or load:specification
own:screw design:specification
1500 or 3000gm:capacity:specification
twin screw food extruder:model name/number:specification
stpz:model name/number:specification
electric operated:power source:specification
pvc:plastic type:specification
savan:brand:specification
up to 550 kg/ hr:production capacity:specification
motor operated:machine type:specification
capsiacinoids oleoresin extraction:machine type:specification
silver:material:specification
pp tape:material to be extruded:specification
twin screw:model name/number:specification
upto 22kw:power consumption:specification
nutmeg oleoresin extraction:machine type:specification
jeet automation:brand:specification
scientico:brand:specification
blown film:body material:specification
150 to 200 kg/hr:production capacity:specification
10 litre:capacity:specification
1200 kg/hr:capacity:specification
6000 kl:capacity:specification
150 kg/hr:capacity:specification
300kg/hr:capacity:specification
650kg/hr:capacity:specification
600kg/hr:capacity:specification
250 kg/hr:production capacity:specification
contacts aria ss 304:material:specification
96:no of unit to be tested:specification
pvc hdpe pipe manufacturers:plastic processed:specification
pp:material:specification
nylon delrin:plastic processed:specification
conical twin screw:screw design:specification
dyeing:usage/application:specification
200 kg:capacity:specification
s.s 304:material:specification
1:no of unit to be tested:specification
engineering plastic:plastic processed:specification
semi-automatic:machine type:specification
250 kg:capacity:specification
15 kg to:capacity:specification
soil testing:type of testing machines:specification
hand operated:type of testing machines:specification
1000 mt press line:capacity:specification
aparna:brand:specification
18 kw:power consumption:specification
yarn:material to be extruded:specification
extruder machine:machine type:specification
sandal wood absolute:usage/application:specification
fennel seed oleoresin extraction:machine type:specification
230volt:power:specification
extruder machine:usage/application:specification
pigment extraction:machine type:specification
solvent extraction plant:machine type:specification
dye extraction:machine type:specification
flower extraction:machine type:specification
bayleaf oleoresin extraction:machine type:specification
parallel twin screw:design:specification
nonafoil:brand:specification
unitech:brand:specification
pvc pipe:machine type:specification
herbal:usage/application:specification
labh group:brand:specification
170kg/hr:production capacity:specification
0.05 kg to 100 kg per hour:production capacity:specification
capacity 1 ton:capacity:specification
800 kg/hr:capacity:specification
50 ton per batch:capacity:specification
1 ton starting capacity:capacity:specification
500kg/hr:capacity:specification
175kg/hr:capacity:specification
250kg/hr:capacity:specification
1500kg/shift:production capacity:specification
mech o tech llp:brand:specification
unique:brand:specification
as per requirement:production capacity:specification
second hand only:i deal in:specification
box:packaging type:specification
approx 10kg:weight:specification
aimtest:brand:specification
100-10,000 tpd:capacity:specification
2-2.5 mm:diameter:specification
60/40 tin/lead:composition (tin/lead):specification
3 kw:power:specification
blue and white (base):color:specification
1500 rpm:speed:specification
automatic gold refining machine:dimension:specification
216 kg:weight:specification
10w:motor power:specification
7.5 w:motor power:specification
na:motor power:specification
yug:brand:specification
apc:brand:specification
pp & teflon material:body material:specification
single phase:power:specification
water/chemicals/gold and sliver manufacturing:storage material:specification
240:voltage:specification
as per requirement:weight:specification
1000 m. ton press line:capacity:specification
indigeous:design type:specification
25 kg:weight:specification
1.5ltrs:bowl capacity:specification
220:electrical unit consumption:specification
30w:power:specification
alloy steel:body material:specification
240 v ac:voltage:specification
15 kw:power:specification
52:screw diameter:specification
18.1:screw l/d:specification
2 phase:phase:specification
liquid silicon rubber injection molding:application use:specification
as per customer requirement:size:specification
1 ph:power:specification
19*50:size:specification
99.9%-99.99%:purity:specification
single phase:power source:specification
5 hp:power consumption:specification
140-200degree:temperature:specification
electricity:power:specification
1140rpm:speed:specification
depends on application:max. vacuum:specification
aqua extraction:machine type:specification
white (body):color:specification
pp, titanium & glass:body material:specification
microtest equipment:brand:specification
laboratory:usage/application:specification
painted:surface finishing:specification
240 v:voltage supply:specification
customized:thickness:specification
as per local requirement:voltage:specification
55 mm, height 750mm(approx:size:specification
lab experiment:usage/application:specification
oleo resins:usage/application:specification
customized:design type:specification
twin screw extruder:driven type:specification
five star engineers:brand:specification
s.s with polypropylene:body material:specification
cardboard:packaging type:specification
m.s material:material:specification
65 mm:size:specification
150 meter per 1 minute:line speed:specification
1 sqmm:wire diameter:specification
ss 304:material:specification
strong:resistance:specification
dia 500:size:specification
tarpaulin:usage/application:specification
0.8 mm to 50 mm:wire diameter range:specification
280-360 v:voltage:specification
ac:motor:specification
0-300 degree celsius:temperature:specification
0- 100psi:pressure:specification
220 v ac:voltage:specification
40x32x72:dimension:specification
abc:font roll diameter:specification
2kw:motor power:specification
2 tones and above(approx):weight of machinery:specification
ton:weight:specification
230-320 v:voltage:specification
vpmr:brand:specification
300 degree c:temperature:specification
2hp:motor power:specification
4 hp:motor:specification
sai thermoformers:brand:specification
vbncvb:voltage:specification
cvbbcv:design type:specification
40-80:machine power:specification
2 hp:motor power:specification
5hp:power:specification
xxx:font roll diameter:specification
8 inch:die size:specification
15 hp and 15 hp:main motor:specification
900 mm:roller size:specification
vpmr,sladjana:brand:specification
pp,glass:body material:specification
gold jewellry:dust:specification
ss 316, ss 304:material:specification
415:voltage:specification
as per design:size:specification
as per design:compass:specification
2-5 kw:power:specification
motorized:speed:specification
extrusion:usage/application:specification
120v:voltage:specification
5.5kw:power:specification
650mm:drum size:specification
80-100:machine power:specification
415 volts ac:voltage:specification
300kg per hours:average productivity:specification
micron:thickness:specification
jeweltech industries:brand:specification
200-800kgs/hour:average productivity:specification
gem blomo:model name/number:specification
9 feet / 12 feet / 18 feet:size:specification
60 hp:power:specification
0-10 bar,10-15 bar,15-20 bar,20-30 bar,30-40 bar:max design pressure:specification
pharmac engineers:brand:specification
extraction of essential oils from flowers, gums etc.:usage/application:specification
customized:design:specification
used for recovery of solvent by indirect steam heating.:usage/application:specification
3000 rpm:speed:specification
powder coating:plastic processed:specification
150 meter/min:capacity:specification
basket extruder:brand:specification
own make:brand:specification
50 hp:motor power:specification
5:capacity:specification
1.5 ltr:capacity:specification
10ltr:capacity:specification
screw:compressor technology:specification
40 kw:machine power (kw):specification
butiment testing machine:type of testing machines:specification
3ltr:capacity:specification
motorised:type of testing machines:specification
stainless steeel:material:specification
15kg:capacity:specification
12 sample , 24 sample:capacity:specification
blue / white:color:specification
v fast:brand:specification
screw element for twin screw extruders:model name/number:specification
55mm:screw diameter:specification
lutein extraction plant:machine type:specification
gold:body material:specification
15 hp:motor power:specification
cable extruder machine:usage/application:specification
electric cable making machine:usage/application:specification
powder coated:surface finishing:specification
conical twin screw:design:specification
pvc resin:plastic processed:specification
80 kg:capacity(kg):specification
200kg/hr:capacity:specification
staring from 10 kgs:capacity:specification
1200 kg/h:production capacity:specification
300 ton per day:capacity:specification
580kg/hr:capacity:specification
680kg/hr:capacity:specification
130kg/hr:capacity:specification
420kg/hr:capacity:specification
850 kg/hr:capacity:specification
100kg/hr:production capacity:specification
ac motor; 4kw:driven type:specification
4 ton:weight:specification
12-15 kg aprox:weight:specification
sky blue:color:specification
2300rpm:speed:specification
milacron:brand:specification
sset:brand:specification
no:phase:specification
hand:speed:specification
yes:oem service:specification
220:voltage (volt):specification
1 gr. 5kg:capacity:specification
10 gram se 1kg:capacity:specification
unilab:brand:specification
125x90 mm:power consumption:specification
ss enterprises:brand:specification
horizontal:orientation:specification
40 ( kw ):output:specification
0.75 kw:power:specification
three:layer:specification
lucid fusion:brand:specification
aluminium:wire material:specification
1 kg to 50 kg:capacity:specification
lead:material:specification
utest:brand:specification
1.5 to 11 kw:power:specification
15.0 ton:capacity:specification
400:font roll diameter:specification
d-gld:model number:specification
200 kg:weight:specification
784:pressure:specification
sswpl:brand:specification
asepta:brand/make:specification
supertechno:brand:specification
100 to 500 tons per day:capacity:specification
2:line speed:specification
100:capacity:specification
99.99%:purity:specification
german:brand:specification
j-923i:model number:specification
standard:packing type:specification
3500 r.p.m:speed:specification
single phase a.c.:phase:specification
52mm to 90mm:diameter:specification
41b:material:specification
extracts essential oils and active ingredients from various materials like leaves, flowers, barks:usage/application:specification
20 - 100 ( micron ):thickness:specification
6 ton:weight:specification
750 - 1200 ( mm ):lay flat width:specification
220:voltage supply (v):specification
50:frequency (hz):specification
ss 316:material:specification
no:max. vacuum:specification
no:pressure:specification
ocean extrusions pvt ltd:brand:specification
customize:capacity:specification
80 kw:power consumption:specification
146 - 194 ( kw ):voltage:specification
3 phase 50 hz:power source:specification
kumar:design type:specification
krishna:brand:specification
2400 - 3600 rpm:speed:specification
shreeji:brand:specification
40 kg:weight:specification
this is used for a quantitative determination of bitumen in hot mix paving mixtures and pavement sam:usage/application:specification
upto 400 deg/cel:temperature:specification
borosilicate glass, mild steel, etc:material:specification
pipe extruder:type:specification
10000 kg/month:capacity:specification
100g -25kg:capacity:specification
5f by 5f:dimension:specification
ss:steel grade:specification
125 kg - 750 kg:weight:specification
2-5 hp:motor power:specification
varies with size:basket rotation:specification
genist:brand:specification
laxmi:brand:specification
2kg:capacity(kg):specification
40:capacity(kg):specification
100grm to 1kg:capacity:specification
1 tdp:capacity:specification
180 kg/hr:production capacity:specification
2:capacity(kg):specification
3kg/hour:capacity:specification
3kg to 5kg:production capacity:specification
2 ton/day:capacity:specification
1 kg.:capacity:specification
1 kg:capacity:specification
200gm-2 kg.:capacity:specification
g2m:brand:specification
laboratory:industry type:specification
3 layer blown film machine:type:specification
500:capacity:specification
ss304 / ss316 / ms:material:specification
150kg/hr:capacity:specification
800kg/hr:capacity:specification
resin:plastic processed:specification
monolayer extruder:machine type:specification
1.5ltr:capacity:specification
hospital:industry type:specification
70 kg:capacity:specification
three layer:layer:specification
580 kg/hr:production capacity:specification
two layer:layer:specification
900 kg/hr:production capacity:specification
600 kg/hr:production capacity:specification
plastic/paper/non woven/woven:usage/application:specification
jewellry:dust:specification
radhekrishna standard:design:specification
yes:machine type:specification
yes:power source:specification
ms / ss / ci:material:specification
cable types:material:specification
fep, fpa, etfe:material:specification
multiple:material:specification
manual/automation:automation grade:specification
glass, titanium, pph:body material:specification
pvc, xlpe, ldpe, hdpe:material:specification
30mm up to 150mm:size:specification
no:packaging size:specification
ms/ss:material:specification
50 x 50:dimension:specification
ss 316 / 316l / 304 / ms:material:specification
k-jhil scientific pvt. ltd:brand:specification
glass, ss, titanium:body material:specification
titanium, pph, glass:body material:specification
standard wooden packing:packaging type:specification
atmiya:brand:specification
a grade:automation grade:specification
micro technologies:brand:specification
titanium/ borosilicate/ polypropylene:body material:specification
440/220 v:voltage:specification
1-2 mm:min finish wire diameter:specification
320v:voltage:specification
steco:brand:specification
146 - 194 ( kw ):machine power:specification
20 - 150 ( micron ):thickness:specification
12 ton:weight:specification
oeplmulti02:model name/number:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ):size:specification
500 kg/hour:capacity:specification
liquid extraction of dairy products:usage/application:specification
no maintenane:maintenance:specification
ld,hm,biodegradable:material:specification
300 - 600 to 1600 - 2500 ( mm ):lay flat width range:specification
45 ( mm ):screw diameter:specification
singal layer:layer:specification
146 - 194 ( kw ):power consumption:specification
ylem parto:brand:specification
1to 100kg:capacity:specification
polycarbonate casing to prevent contamination, the machine has all pneumatic cylinders of festo make:finishing:specification
0.25 hp:power:specification
0.18kw:power:specification
upto 60 m / min.:output:specification
160 w:power:specification
99.90%:purity:specification
2 mm:sheet thickness:specification
1 kw:power source:specification
220/440 v:voltage:specification
100 kg/hour:output:specification
3:layer:specification
1.5kg:bowl capacity:specification
electric, gas, diesel:power source:specification
240 - 380 v:voltage:specification
depends on material:output:specification
on request:lay flat width:specification
on request:screw number:specification
depends on material:surface finish coating:specification
dr scientific:brand:specification
5 bar (g):outlet/discharge pressure:specification
3kg to 8kg:production capacity:specification
2kg to 3kg:production capacity:specification
polished:surface finish:specification
ldpe coated:coated type:specification
1- stage:machine type:specification
edutek:brand:specification
45kg/hr:capacity:specification
520kg/hr:capacity:specification
gold refining:usage/application:specification
120hr:capacity:specification
aluminum profiles:material to be extruded:specification
heavy duty:machine type:specification
chemical:industry type:specification
2l:capacity:specification
single screw mono layer:machine type:specification
50 kg:packaging size:specification
150 kg:capacity:specification
28kg/hr:production capacity:specification
ld/ pp/ hm/ biodegradable:material:specification
12 inch:size:specification
ocean international:brand:specification
extractions:usage/application:specification
480 kg/hr:production capacity:specification
430 kg/hr:production capacity:specification
120 kg/hr:production capacity:specification
855 kg/hr:production capacity:specification
700 kg/hr:production capacity:specification
325 kg/hr:production capacity:specification
powder coated:material:specification
755 kg/hr:production capacity:specification
35 kg/hr:production capacity:specification
550 kg/hr:production capacity:specification
780 kg/hr:production capacity:specification
520 kg/hr:production capacity:specification
222 bolt:voltage:specification
mel plast:brand:specification
8 to 15 kg/hr:capacity:specification
ss & ms:material:specification
440:voltage:specification
50-60hz:frequency:specification
240/440 v:voltage:specification
e n grade:material:specification
100 tpd - 500 tpd:capacity:specification
unity glass industry:brand:specification
on request:thickness:specification
on request:design:specification
on request:size:specification
on request:main drive ac:specification
wooden export quality packing:packaging type:specification
fully automatic touch screen:automation grade:specification
545mm:basket diameter:specification
laboratotory:usage/application:specification
hhpep-55sa:model name/number:specification
200-500kg/h:output:specification
manual:product type:specification
5 kw:power consumption:specification
titanium, pp, glass:body material:specification
220v:voltage supply:specification
200-800kgs/hour:output:specification
80-600:machine power:specification
ms structurals:body material:specification
3mpm up to 100mpm:line speed:specification
600 to 1000mm:die size:specification
film for liners, lamination film, film for shopping bags:usage/application:specification
150 micron:film thickness:specification
45 mm and 45 mm:screw diameter:specification
90 mm:die size:specification
280 - 380 v:voltage:specification
10kw:power consumption:specification
220v ac:voltage:specification
powder coated:finish type:specification
plastic:usage/application:specification
all india machinery:brand:specification
51/105:diameter:specification
100:heating range:specification
6 mm:max inlet wire diameter (mm):specification
gold refining plant:frequency:specification
gold refining plant:automation grade:specification
color coated:finishing:specification
40m/min:line speed:specification
cgt110:model name/number:specification
220-240v:voltage:specification
yes:customized:specification
220-240 v:voltage:specification
motorized electrically driven:power:specification
apollo machinery:brand:specification
12 hp:motor power:specification
13:1:l/d ratio:specification
60 hp:power consumption:specification
power mulch:model name/number:specification
20 hp:main motor power:specification
light:weight:specification
digital:display type:specification
hdpe pipe and fittings maintenance:usage/application:specification
50:line speed:specification
2 color:model name/number:specification
22 kw - 65 kw:voltage:specification
kumar:brand:specification
28 - 280 ( kg/hr ):output:specification
240w:power:specification
mixing:application:specification
440 v / 380 v:voltage (v):specification
vtech:brand:specification
hand/ 220v ac:power:specification
hand operated:driven type:specification
650kg:weight:specification
commercial:usage/application:specification
cable extruder:type:specification
200-300 kg/hr:output:specification
80mm:size:specification
130 kg/hr:production capacity:specification
50kg:capacity(kg):specification
2 kg:capacity(kg):specification
3kg:production capacity:specification
5kg to 8kg:production capacity:specification
320kg/hr:capacity:specification
ss316:material:specification
ss &ms:material:specification
plantation:machine type:specification
gold:metal:specification
1.5 lpm:capacity:specification
380kg/hr:production capacity:specification
235 kg/hr:production capacity:specification
955 kg/hr:production capacity:specification
565kg/hr:production capacity:specification
475 kg/hr:production capacity:specification
255 kg/hr:production capacity:specification
535 kg/hr:production capacity:specification
film extrusion:usage/application:specification
45 kg/hr:production capacity:specification
60 kg/hr:production capacity:specification
40 kg/hr:production capacity:specification
800 kg/hr:production capacity:specification
680 kg/hr:production capacity:specification
75 kg/hr:production capacity:specification
850 kg/hr:production capacity:specification
122kg/hr:capacity:specification
230kg/hr:production capacity:specification
30 kg/hr:production capacity:specification
70 kg/hr:production capacity:specification
35kg/hr:production capacity:specification
1 tpdd:capacity:specification
180kg/h:production capacity:specification
10:capacity:specification
as for recruitment:production capacity:specification
2kg/hour:capacity:specification
5 to 10 kg/hr:production capacity:specification
5kg to 10kg:production capacity:specification
scientific glass:industry type:specification
40 kg:capacity:specification
30kg/hr:capacity:specification
380kg/hr:capacity:specification
350kg/hr:capacity:specification
480kg/hr:capacity:specification
450kg/hr:capacity:specification
120kg/hr:capacity:specification
polymers:plastic processed:specification
masterbatch and recycle:plastic processed:specification
self:capacity:specification
material testing equipment:type of testing machines:specification
24 inch:size:specification
cnsl extraction:usage/application:specification
420kg/hr:production capacity:specification
175 kg/hr:production capacity:specification
675 kg/hr:production capacity:specification
98kg/hr:production capacity:specification
80 kg/hr:production capacity:specification
650 kg/hr:production capacity:specification
750 kg/hr:production capacity:specification
520 kg/hr:capacity:specification
280 kg/hr:production capacity:specification
55 kg/hr:production capacity:specification
144:capacity:specification
welding electrodes:material to be extruded:specification
275 kg/hr:production capacity:specification
355 kg/hr:production capacity:specification
32kg/hr:production capacity:specification
1200 kg/hr:production capacity:specification
125kg/ hr:capacity:specification
62kg/hr:production capacity:specification
12 sample:capacity:specification
700 tdp:capacity:specification
s.s:material:specification
80 rpm:line speed:specification
indulge:brand:specification
extraction machinery:machine type:specification
zybio:brand:specification
32 inch:blade size:specification
glass:material:specification
bst:brand:specification
glass:machine type:specification
10 x 10:font roll diameter:specification
10 x 10 x 10:diameter:specification
420 v:voltage:specification
single ph:power:specification
volumes under 300l:capacity:specification
single ph:motor power:specification
420 v:power:specification
fully automatic:frequency:specification
10:depth:specification
240v:motor power:specification
bst:color:specification
automatic:font roll diameter:specification
automatic:line speed:specification
automatic:die size:specification
6000 l:capacity:specification
automatic:type:specification
semi automatic:design type:specification
semi automatic:machine type:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):size:specification
solvent extraction plant:power source:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums. we can supply any capaci:machine type:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums. we can supply any capaci:design type:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums. we can supply any capaci:usage/application:specification
fs - 25 - lab:model name/number:specification
automatic:operation type:specification
na:diesel consumption:specification
mech o tech:brand:specification
extract:usage/application:specification
none:diesel consumption:specification
none:micelle concentration:specification
65 degree celcius:temperature:specification
500 kg approx:weight of machinery:specification
tecson:brand/make:specification
na:production capacity:specification
1.5 ton:weight:specification
monika enterprise:brand:specification
natural:material:specification
turn key project:machine type:specification
240-440 v:voltage:specification
915 x 350 mm:basket size:specification
2400-3600 rpm:speed:specification
testing tool:product type:specification
1:frequency:specification
230 v:voltage:specification
>150 ton:max force or load:specification
3phase:motor power:specification
5 - 50 kg/h:output:specification
4100 kg:weight:specification
dairy farm:usage/application:specification
for liquid extraction of dairy products:usage/application:specification
hdpe,ldpe,pe,pp:material:specification
2100 mm:lay flat width:specification
50hz to 60hz:frequency:specification
27 kg:weight:specification
single phase ac supply:phase:specification
1 bar:pressure:specification
good quality pu paint:finishing:specification
3 x 2x 5.5 feet:size:specification
na:altimeter:specification
dc motor; 3.7kw:driven type:specification
silver,white:color:specification
ambient:temperature:specification
na:compass:specification
manual:automatic grade:specification
boiling:usage/application:specification
precious metal:body material:specification
trimurti traders:brand:specification
fiber body:material:specification
more than 100 programs:capacity:specification
skylab:brand:specification
50 kw:machine power:specification
manual:speed:specification
280 - 440 v:voltage:specification
4 feet x 12 feet:size:specification
10 mm:thickness:specification
55 - 125 ( kg/hr ):output:specification
120 to 410 kg/hr:output:specification
220 - 440 v ac:voltage:specification
2-10 hp:power:specification
s.s with polypropylene:material:specification
110 kg/hr:capacity:specification
up to 6 kw:power:specification
10-20 hp,10-20 hp:power consumption:specification
10 ton /day:capacity:specification
450 kg:weight:specification
1500 g:bowl capacity (g):specification
15 h.p:power consumption:specification
mariya:model name/number:specification
65 mm:die size:specification
blue and yellow:color:specification
200m/min:speed range:specification
vertical:orientation:specification
good:surface finishing:specification
to find binder content only..:usage/application:specification
cattle animal cow goat poultry feed making:usage/application:specification
foodgrade:processing type:specification
super salients:features:specification
100kg:weight:specification
5000-10000 pieces/hour:capacity:specification
220-230 voltage:voltage:specification
230 volt:voltage:specification
plastic acid proof materials:material:specification
1kw se 2kw:power:specification
150kg:weight:specification
2800 kg:weight:specification
3,500 kg:weight:specification
high:motor power:specification
as per requirement:installation services:specification
60kw:motor power:specification
50 - 60hz:frequency (hz):specification
cts 63:model name/number:specification
600 kg:weight:specification
30 kw:machine power:specification
52:screw l/d:specification
graded steel:material:specification
30 kw:power consumption (kilowatt):specification
vpmr, sladjana:brand:specification
goyum:brand/make:specification
10 ton per 24 hours:capacity:specification
goyum:brand:specification
germany:frequency:specification
4 ton per 24 hours:capacity:specification
15 to 75 kw:power:specification
65mm:size:specification
220v to 420v:voltage:specification
nicotine (tobacco) extraction:usage/application:specification
blue / white / gray:color:specification
own:brand:specification
iron:material:specification
standard:product type:specification
steel and fiber:body material:specification
wooden box:packaging type:specification
steel and fiber:material:specification
24 hours 500-600 kg. production:average productivity (kg/hour):specification
120 kg:weight:specification
amerging technologies:brand/make:specification
75 mm (screw diameter):diameter:specification
hand:product type:specification
60 kgs:weight:specification
venus:brand:specification
50 kg scrap refining, 50 kg waste recycling/day:capacity:specification
0.25 kw/kg:power consumption:specification
99 set/sets per month industrial extractor for hot chamber die casting machine:capacity:specification
borosilicate glass & s.s pipe:body material:specification
k-jhil scientific glass:brand:specification
10, 20, & 50ltr:capacity:specification
15-200 kgs:capacity:specification
1.5 mtr x 0.6 mtr x 3 mtr:dimension:specification
12 inch:dimension:specification
220- 240:voltage (volt):specification
1kg to 500kg capacity:capacity:specification
fs-aba-2:model name/number:specification
48kg/hr:production capacity:specification
chemicals/oils:storage material:specification
noodle making:usage/application:specification
12 -24 sample:capacity:specification
80 ton/day:capacity:specification
220 kg/hr:production capacity:specification
70 rpm:line speed:specification
400 kg/hr:capacity:specification
en steel:material:specification
matest:brand:specification
coating extruder:machine type:specification
gold refining plant:product type:specification
processing plant:type:specification
220:screw number:specification
automatic:technique:specification
fully automatic:dimension:specification
as per the size:font roll diameter:specification
fully automatic:heating range:specification
as per the size:line speed:specification
150hp:power:specification
1:hp power:specification
20 to 50mm:range:specification
20 to 50mm:diameter:specification
500 l:capacity:specification
1000 l:capacity:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):dimensions:specification
ss 304:material grade:specification
semi autometic:design type:specification
semi autometic:machine type:specification
solvent extraction plant:brand:specification
solvent extraction plant:usage/application:specification
available:machine type:specification
available:usage/application:specification
available:brand:specification
370 w:power:specification
370 w:wattage:specification
2:die:specification
34:phase:specification
55/120:screw number:specification
manual:capacity:specification
conical:design:specification
55/120:screw diameter:specification
vacuum:voltage:specification
vacuum:electrical unit consumption:specification
55/120:diameter:specification
34:capacity:specification
10 kg:capacity.:specification
any:capacity:specification
all kinds:material:specification
as per customer requirement:capacity:specification
customized:machine type:specification
customized:dimension:specification
engineering plastic:material:specification
26*60*80:dimension:specification
0.002:frequency:specification
2kwt:power source:specification
15mm:sheet thickness:specification
10 hp:power:specification
50mm:drum size:specification
customized:color:specification
250mm:drum size:specification
iso:approval & licenses:specification
1 kw:power:specification
80-100:capacity(pieces per hour):specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):dimension:specification
5-5.30 p:voltage:specification
plastic:bag material:specification
100-120:capacity(pieces per hour):specification
146 - 194 ( kw ):power:specification
3 ton:machine weight:specification
titanium:material:specification
touch screen , fully automatic:automation grade:specification
touch screen , fully automatic:phase:specification
touch screen , fully automatic:power:specification
2500 kg:weight:specification
depends on material:machine power:specification
three phase:power source:specification
415v/440v:voltage:specification
depends on material:wire diameter:specification
on request:hopper:specification
depends on material:diameter millimeter:specification
380-415 v:voltage:specification
250 mt:production capacity:specification
48 - 75 ( kw ):voltage:specification
100 ( micron ):coating thickness:specification
semi- automatic:automation grade:specification
100 micron:film thickness:specification
28 - 280 ( kg/hr ):capacity:specification
sladjana sales corporation ( vpmr):brand:specification
1.7 to 4,825 kw:power:specification
220 v:voltage supply:specification
ms:surface finishing:specification
2-5 kg per hour:capacity:specification
standard:weight:specification
99.99 percent:purity:specification
touch screen , fully automatic:font roll diameter:specification
touch screen , fully automatic:line speed:specification
touch screen , fully automatic:frequency:specification
415 - 420:voltage (v):specification
1.2 - 5mm:thickness (millimeter):specification
1.2 to 5 mm:thickness (millimetre):specification
green and white:color:specification
80 mpm:speed:specification
45 ( mm ):screw size:specification
customized:power source:specification
polished:surface finishing:specification
132 to 400 knm:screw torque:specification
aluminium,mild steel:body material:specification
10 kw:machine power:specification
prabhu:brand:specification
ms steel:material:specification
4 hp:power:specification
60-90 hz:frequency:specification
0-25 mm:hole diameter:specification
5 minutes:processing time:specification
1000ml:bowl capacity:specification
gray and black:color:specification
as per astm d2172:speed:specification
50 l - 8000 l:capacity:specification
indstrial solvent cooker:product:specification
65 mm:barrel bore:specification
dual settings allow users to set dierent pressures for extraction and column drying:frequency:specification
fuel injector cleaning machine:brand:specification
fuel injector cleaning machine:engine type:specification
fuel injector cleaning machine:diameter range:specification
parallel twin screw:screw design:specification
semi and fully automatic:font roll diameter:specification
semi and fully automatic:frequency:specification
automactic:automation grade:specification
automactic:frequency:specification
semi and fully automatic:line speed:specification
2000 watts.:voltage:specification
semi and fully automatic:automation grade:specification
fuel injector cleaning machine:operation mode:specification
pp:packaging type:specification
dual settings allow users to set dierent pressures for extraction and column drying:driven type:specification
free:dust:specification
free:gases:specification
automatic:power source:specification
52mm dia:screw length:specification
fuel injector cleaning machine:dimensions:specification
100c:heating range:specification
2000 watts.:motor power:specification
turn key project:design type:specification
52mm dia:screw diameter:specification
automatic:frequency:specification
58 rpm:spindle speed:specification
2:ring number:specification
58 rpm:speed:specification
2:no. of feeds:specification
2:no. of speed:specification
500mm dia:wire diameter:specification
500 mm dia:size:specification
100:automation grade:specification
100:frequency:specification
100:motor power:specification
customer dependent:automation grade:specification
customer dependent:frequency:specification
sga:model:specification
sga:brand:specification
30 x 15 x 18 to 60 x 40 x 20 ( l x w x h ):screw diameter:specification
30 x 15 x 18 to 60 x 40 x 20 ( l x w x h ):size:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums. we can supply any capaci:voltage:specification
please refer to pdf:capacity:specification
please refer to pdf:material:specification
please refer to pdf:automation grade:specification
available:automation grade:specification
available:voltage:specification
available:frequency:specification
available:material:specification
available:power source:specification
415 v:design type:specification
30kw:power consumption:specification
30kw:main motor:specification
0.75 kw:take up power:specification
0.75 kw:air blower:specification
150hp:electrical motor:specification
ac 415v:power source:specification
ac 415v:drive motor:specification
manual:machine type:specification
1:material:specification
fully automatic:capacity:specification
fully automatic:depth:specification
fully automatic:dust:specification
fully automatic:power source:specification
automatic:dimension:specification
fully automatic:diameter:specification
fully automatic:flange width:specification
fully automatic:lead:specification
fully automatic:burner:specification
fully automatic:gases:specification
50kg/hr:output:specification
as per client requirement:capacity:specification
as per customer requirement:plastic processed:specification
standard:capacity:specification
standard:screw design:specification
customisable:dimension:specification
as per requirement:color:specification
standard:dimension:specification
qunying:brand name:specification
50 kg:production capacity:specification
10 hp:motor power:specification
2.5 kg:capacity:specification
manual:type of testing machines:specification
2.5 kg:bowl capacity:specification
fully automatic:font roll diameter:specification
10 hp:feed motor:specification
10 hp:main motor:specification
1kg:capacity(kg):specification
0.8 tonnes:machine weight:specification
12 feet:lay flat width:specification
240 -380 v:voltage:specification
0.12 - 1.2 kg/h:output:specification
900 kg:weight:specification
10 kw:power:specification
natural:size:specification
10 - 20 kg/hrs:output:specification
1050 kg:weight:specification
220 volts:power:specification
s d enterprises:brand:specification
1440:speed:specification
rotary extractor:usage/application:specification
lucky:brand:specification
5 hp:power:specification
zoomlion:brand:specification
n.a:wire diameter:specification
iec1255hm:model name/number:specification
2 h p:motor:specification
textile industry:usage/application:specification
all:wire type:specification
50 / 60 hz:frequency:specification
4hp:power:specification
p p:material:specification
3phase:phase:specification
adroit extrusion:brand:specification
30 kw:power:specification
3 phase:power:specification
150kh:capacity:specification
26/36/48:drum size:specification
mel/40/ex:model name/number:specification
shri balaji scientific works:brand:specification
1500 kg:weight:specification
gangaa:brand:specification
sisco india:brand:specification
bule:color:specification
on request:body material:specification
depends on material:screw diameter:specification
depends on material:line speed:specification
on request:weight:specification
depends on material:finish type:specification
on request:die size:specification
on request:driven type:specification
depends on material:installation services:specification
500 - 2000 g /hrs:output:specification
400 kg:weight:specification
innotech:brand:specification
customized:size:specification
motor:driven type:specification
4-5 kg:pressure:specification
1500rpm:speed:specification
750 rpm:speed:specification
120 - 200 kg/hr:output:specification
3 kwt:power:specification
18 feet / 24 feet / 36 feet:lay flat width:specification
ac:main drive ac:specification
blue white semance grey:color:specification
5 hp:machine power:specification
5:power consumption:specification
gm industries:brand:specification
le:brand:specification
creative autotech:brand:specification
230 v ac:voltage supply:specification
habricks:brand:specification
230 v:voltage supply:specification
depends on material:diameter:specification
depends on material:average productivity:specification
on request:screw size:specification
depends on motor kw:motor kw:specification
2.2 kw:power:specification
ac vfd:driven type:specification
stainless steel and cast iron:body material:specification
500 kgs:weight:specification
50:size:specification
twin screw:screw number:specification
48:capacity:specification
nickel recovery plant:material:specification
60 rpm:line speed:specification
high speed:features:specification
asphalt testing:uses:specification
plastic:material to be process:specification
aluminium:sheet material:specification
45 mm:barrel bore:specification
plastic:plastic processed:specification
helix:brand:specification
as per the size:motor power:specification
as per the size:dimension:specification
automatic refining machine:frequency:specification
fully automatic:motor power:specification
20 to 110mm:range:specification
semi automatic:automatic grade:specification
automatic refining machine:automation grade:specification
20 to 110mm:die size:specification
fully automatic:power:specification
fully automatic:body material:specification
20 to 110mm:size:specification
as per the size:power:specification
automatic:motor power:specification
48, 96, 144:no of position:specification
236 m/min:capacity:specification
3000 l:capacity:specification
25 l:capacity:specification
mechotechllp:form:specification
48,96,144:capacity:specification
y:body material:specification
as required:dimension:specification
good:purity:specification
costomized:automatic grade:specification
good:heating range:specification
custom:packaging size:specification
any:usage/application:specification
as specified:packaging size:specification
not applicable:phase:specification
cutomized:capacity:specification
standard:frequency:specification
mixing:usage/application:specification
as per requirement:space:specification
custom:capacity:specification
na:brand:specification
na:screw design:specification
na:screw number:specification
na:plastic processed:specification
as per requirement:capacity:specification
all:power:specification
all:voltage:specification
as per design:design type:specification
as per design:power source:specification
as per design:voltage:specification
customized:capacity:specification
customized:material:specification
other:color:specification
other:flow rate:specification
roll:packaging type:specification
mild steel:roller material:specification
stainless steel & mild steel both available:material:specification
automatic & semi automatic both:automation grade:specification
50 htz:frequency:specification
12, 24:no of position:specification
electrical:driven type:specification
12 & 24:no of position:specification
vaccum only:power source:specification
hlb, c18:spe cartridge size:specification
vaccum manifold & accessories:standard with equipment:specification
nsc/hyd/220/customisedcn:model name/number:specification
yes:no of position:specification
yes:frequency:specification
cool:spe cartridge size:specification
yes:standard with equipment:specification
mppl-tp/110gf:model name/number:specification
pp dana making machine:type of machine:specification
50 l:capacity:specification
1 kg per transaction:capacity:specification
100g to 2kg:production capacity:specification
1 to 100kg:capacity:specification
10 inch:size/diameter:specification
500 m^3/hr:flow rate:specification
35 kg per hr:capacity:specification
100 kg:production capacity:specification
upto 25 kg/hr:production capacity:specification
6kg:capacity:specification
solvent extraction machine:machine type:specification
solvent extraction machine:design type:specification
65/132:screw number:specification
65/132:diameter:specification
65/132:screw diameter:specification
customized:tank volume:specification
variables:capacity:specification
as per the requirement:frequency:specification
as per requirement:automation grade:specification
any:model name/number:specification
not required:power source:specification
based on requirement:capacity:specification
96:capacity:specification
as per requirements:capacity:specification
both:material:specification
nil:wire thickness:specification
as per size:depth:specification
as per requirement:diameter:specification
as per requirement:dust:specification
standard:wall thickness:specification
modern:design:specification
multi:color:specification
customizable:design type:specification
customize:size(mm):specification
customized:is it customized:specification
as per your requirement:capacity(kg):specification
tailor made:production capacity:specification
best:purity:specification
na:frequency:specification
customizable:die size:specification
good:quality:specification
as per client requirements:service duration:specification
optional:color:specification
na:type of testing machines:specification
customize:material:specification
as per size:diameter:specification
as per size:height:specification
customize:phase:specification
customize:voltage:specification
as per size:flange width:specification
as per requirment:font roll diameter:specification
as per requirment:line speed:specification
good:quality available:specification
as per requirment:dimension:specification
na:phase:specification
na:speed:specification
standard:design:specification
standard:size:specification
na:model name/number:specification
all:frequency:specification
all:material:specification
as per required:screw number:specification
na:size:specification
na:material:specification
na:packaging size:specification
na:usage/application:specification
na:l/d ratio:specification
as per required:phase:specification
as per required:voltage:specification
na:capacity:specification
na:voltage:specification
depends on capacity:motor power:specification
depends on capacity:voltage:specification
20:depth:specification
100 kg/hr:output:specification
manual:work type:specification
10:dimension:specification
50:power:specification
50:heating range:specification
50:purity:specification
40 kw:power consumption:specification
1100 mm:lay flat width:specification
12:no of position:specification
1ml (standard):spe cartridge size:specification
1 ml, 0.6 ml:spe cartridge size:specification
includes waste reservoir with assembly to allow for waste:standard with equipment:specification
corebitx 06:model name/number:specification
20 mm - 400 mm pipe size:diameter:specification
white and dark blue:color:specification
110 kg/hr to 700 kg/hr:capacity:specification
60 kw:power:specification
100-300:line speed:specification
iec001:model name/number:specification
dark blue:color:specification
100%:purity:specification
146 - 194 ( kw ):screw diameter:specification
for low quality cable extruder:usage/application:specification
60-1000 tpd:capacity:specification
copper,aluminium:wire material:specification
650 unit/ton:power consumption:specification
1 kl - 6 kl:capacity:specification
3 hours:line speed:specification
fully automatice:automation grade:specification
solid:brick type:specification
60x60x48:dimension:specification
export type:packaging type:specification
m tech jewel equipment:burner:specification
xxx:diameter:specification
silver jewellry:dust:specification
for wire extrusion:usage/application:specification
aasabi:brand:specification
2300 rpm:speed:specification
electrical operated:product type:specification
55-125 kg/hr:production capacity:specification
180-230 kg/hr:production capacity:specification
customiz:wire diameter:specification
12months:warranty:specification
2.1:thickness:specification
420v:voltage:specification
100kg/day:capacity:specification
vikas 35:model name/number:specification
750 kw:main drive ac:specification
v-tech:brand:specification
parth:brand:specification
300 gm to 150 kg:capacity:specification
300 gm to 5kg:capacity:specification
220 to 320 v:voltage:specification
9-12 mm:max inlet wire diameter:specification
100-500kg/h:production capacity:specification
up to 2500 tpd:capacity:specification
380:voltage (v):specification
edr-ewrm:brand:specification
100 kg per day:capacity:specification
elechem:brand:specification
laboratory equipment:usage/application:specification
clay extruder:type:specification
1000 - 5000 kg:capacity:specification
100 to 500 litre:oil tank capacity:specification
30 - 50 bar:pressure:specification
10-18 mm:thickness:specification
240v/440v:voltage:specification
2000-5000:speed (rpm):specification
eletric:power source:specification
240 v:voltage supply (v):specification
gpps:material:specification
415-420:voltage (volt):specification
45:line speed (meter/minute):specification
90%:purity:specification
400w:power:specification
65kg to 70kg/hr:production capacity:specification
20-200 micron:film thickness:specification
depend on the project:power source:specification
depend on the project:voltage:specification
depend on the project:design type:specification
120 hp:machine power:specification
100 hp:power:specification
jeweltech:brand:specification
indian:brand:specification
260 v:voltage:specification
230 v ac:voltage supply (v):specification
30-60kgs per hour:capacity:specification
500he:model name/number:specification
plastic carry bag:usage/application:specification
500 - 700kg/day in 8 hour:output:specification
sant engineering industries:brand:specification
1440rpm:speed:specification
smew:brand:specification
ll-110f:model name/number:specification
1 to 100kg.:capacity:specification
3600rpm:speed:specification
electrically:product type:specification
a.c:voltage supply:specification
custom:automatic grade:specification
polypropelyne homopolymer:body material:specification
240 v:power:specification
48 - 75 ( kw ):power consumption:specification
200kva:power consumption:specification
neptune plastic:brand:specification
reliable:brand:specification
100 - 750 kg. / hour:production capacity:specification
mixed type of design:design type:specification
infiniti extrusion techmac:brand:specification
220-415v:voltage:specification
35 kw:machine power:specification
1200 rpm:line speed:specification
12kl:capacity:specification
50 - 75 kgs:capacity:specification
smarcon:brand:specification
upto 1000 kg/day raw material:capacity:specification
35ft:lay flat width:specification
150 kg:average productivity:specification
100-120 pieces per hour:capacity:specification
40 - 130:output:specification
75 - 250 kg/hour:output:specification
60 kg per hour:capacity:specification
950 kg:weight:specification
6 n-m:screw torque:specification
superior quality paint finish:surface finishing:specification
25 ( kw ):machine power:specification
ek danta refiners,ek danta refiners:brand:specification
1 kg,1...200 kg:capacity:specification
415 v:voltage (v):specification
250kg:weight:specification
color coated:finish:specification
146 - 194 ( kw ):connected load:specification
12 ton:machine weight:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ):dimension:specification
220 - 380 v:voltage:specification
screw driven:driven type:specification
500 kg to 5 tonne:range:specification
30 kw:power consumption:specification
4 kw:power:specification
mehta tubes:brand:specification
oeplaba01:model name/number:specification
220b:power:specification
220:voltage (v):specification
40 ftx 50 ft x 15 h ft:size:specification
nf4arm-2k4arm:model number:specification
gas:fuel type:specification
automtic:automation grade:specification
arr:brand:specification
stainless steel (body):material:specification
3 hp:power:specification
100 micron:thickness:specification
75 kw:power consumption:specification
normal:dimension:specification
pvg:brand:specification
100-150kg/h:output:specification
one year:warranty:specification
as per requirement:packaging size:specification
normal:frequency:specification
varies:size:specification
customize:size:specification
customise:production capacity:specification
as per your need:capacity(kg):specification
as per need:purity:specification
as per requirement:purity:specification
as per customer:dimension:specification
excellent:quality:specification
all:body material:specification
costomized:material:specification
costomized:capacity:specification
standard:machine type:specification
20 kw:machine power (kw):specification
semi-automatic, fully automatic plc:automation grade:specification
vtre-012:model name/number:specification
12-24 port:no of position:specification
c 18:spe cartridge size:specification
pump , trap and silicon tube:standard with equipment:specification
1 ml, 3 ml, 6 ml:spe cartridge size:specification
1cc, 3cc and, 6cc columns:spe cartridge size:specification
a:grade:specification
12 , 24 , 144:no of position:specification
240 nm:screw torque:specification
dmh15:model name/number:specification
10kg to 20kg:capacity:specification
180 kg/hr:capacity:specification
120 kg/hr:capacity:specification
480 w:power:specification
2kg to 500kg:capacity:specification
1 to 50 kg:capacity:specification
20 ton/hr:capacity:specification
200 l:capacity:specification
up to 100 kg/hr:capacity:specification
20 - 150 ( micron ):film thickness:specification
polished:surface treatment:specification
hand:phase:specification
ldpe / lldpe:material:specification
50 mm:screw diameter:specification
20 w:power:specification
220 - 280 v:voltage:specification
blue, red etd:color:specification
1 - 5 kw:power:specification
yes:annual maintenance contract:specification
20-25 kw:power consumption:specification
250v:voltage:specification
20 - 40 ( kw ):voltage:specification
m1-ps-100-130:model name/number:specification
150 - 300 ( kg/hr ):production capacity:specification
55 - 65 - 55 ( mm ):screw diameter:specification
6 months:warranty:specification
steel fabricated:body material:specification
param enterprise:brand:specification
poly propolyn:body material:specification
sant engg inds:brand:specification
depends on size of machine:power consumption:specification
20-100psi:pressure:specification
machine:product type:specification
50~5000ul:pressure:specification
18kg:weight:specification
method nucleic acid extraction and purification instrument:usage/application:specification
11 kw to 75 kw:power:specification
10kw:power:specification
240 v:input voltage (v):specification
oeplmutli09:model name/number:specification
ss, alloys:material:specification
coperion:brand:specification
120 to 350 kg/hr:average productivity (kg/hour):specification
850-950 kg/hour:output:specification
80 kw:capacity:specification
100 gm to 1000gm:capacity:specification
labasia:brand:specification
1-5 liter:capacity (litre):specification
1-20:thickness (mm):specification
45 to 50 kg:capacity (kilogram/hour):specification
2 to 100 kg:capacity:specification
500-600 kg/h:capacity:specification
rufouz hitek:brand/make:specification
50kgph:capacity:specification
green agritech:brand:specification
didac:brand:specification
no:steam supply (kilogram):specification
240v:voltage(v):specification
240 v:voltage (v):specification
240 watt:voltage (v):specification
250kg/hr:production capacity:specification
1000 grams:capacity:specification
50 to 1000 tones/day:capacity:specification
sritech lipid:brand:specification
220 - 440 v:voltage:specification
380 v:power (v):specification
nmew:brand:specification
50-200 tons/day:capacity:specification
essential oil extraction:usage/application:specification
marktech:brand:specification
1250lph:capacity:specification
s.tech:brand:specification
410:voltage:specification
3000g:capacity:specification
115v:voltage (v):specification
2400 to 3600 rpm:speed:specification
pmi:brand:specification
white and black:color:specification
20-150 mm:thickness:specification
aba se3hr:model name/number:specification
ss / ms:material:specification
5-5000 kg / hr.:capacity:specification
50 hz:screw torque:specification
adroit:brand:specification
415 v:voltage supply:specification
caffeine extraction:usage/application:specification
40 tph:production capacity:specification
hand/ motor:driven type:specification
ssc:brand:specification
2-10 kw:power:specification
50 kg per hours:average productivity:specification
2 mm to 10 mm:wire diameter:specification
3 mm:thickness:specification
50:die size:specification
80 mpm:line speed:specification
300kg:weight:specification
sjps165e:model name/number:specification
ms, aluminium, ci casting:material:specification
speed regulator:driven type:specification
polypropylene and titanium:body material:specification
mirror polishing, matt polishing, acid passivation, perox cleaning:finishing:specification
3 ph. 415 v.:power:specification
ac motor:motor:specification
bitumen extractor:product type:specification
3000r/min:temperature:specification
1500 ml:drum size:specification
no display:display type:specification
110 v:voltage:specification
370w-550w:power:specification
80-100:line speed:specification
tripal:phase:specification
50w:power:specification
360-415 v:voltage:specification
3200rpm:speed:specification
this test is important because various pavement properties such as durability, compatibility, resist:usage/application:specification
half hp:motor power:specification
food garde:body material:specification
250 mm:die size:specification
500-550 kg/hour:output:specification
profile extruder:type:specification
40:machine power (kilowatt):specification
200-300:output(kg/hr):specification
bent:brand:specification
100 gm to 5kg:capacity:specification
99.99:purity (%):specification
10-125 kg/hr:production capacity:specification
lead:melting material:specification
25.0 ton per batch:capacity:specification
upto 1000 kgs per shift:capacity:specification
all:brand:specification
20:capacity(kg/hr):specification
1 to 200 kg:capacity:specification
2500 tpd:capacity:specification
100g to 1kg:capacity:specification
500 gm to 100kg:capacity:specification
jewellery hallmarking system:machine required:specification
600 kg/h:capacity:specification
51/105, 55/120, 65/132:screw number:specification
both ss & mild steel:material:specification
carton box:packaging type:specification
plc:control system:specification
vrundavan:brand:specification
cenmen:brand:specification
110 hz:frequency:specification
100 kw:machine power (kw):specification
as per customer requirment:capacity:specification
80 kw:machine power (kw):specification
arise technology:brand:specification
upvc pipe plant:plastic processed:specification
boro g:brand:specification
10-200 ltr.:capacity:specification
no:screw design:specification
20 ltr to 500 ltr.:capacity:specification
boro - g:brand:specification
2:screw number:specification
polished:finish:specification
shree amba:brand:specification
230 bar:max force or load:specification
laxmi industries:brand:specification
yes:plastic processed:specification
civil:type of testing machines:specification
compounding, mixing and processing of plastics:plastic processed:specification
bitumen testing:type of testing machines:specification
2 stage:machine type:specification
industrial spare parts packaging:usage/ application:specification
adtec:brand:specification
npm:brand:specification
55/120, 65/132, 51/105:screw number:specification
botics:brand:specification
job work:brand:specification
75 kgs/hr:capacity:specification
mechotech llp:brand:specification
tech-g kanpur:brand:specification
yes:screw number:specification
continuous extrusion machine:type:specification
gold & silver:usage/application:specification
16x22":size:specification
blown film plants:usage/application:specification
aluminm melting furnace , 90 feet handling system with rotcutter & finish cutter and puller & streacher and handling table with all conveior belt and roller sleeve and agin oven and die oven and pollution system and dross recovery machine:material to be extruded:specification
any:material to be extruded:specification
none:font roll diameter:specification
any:purity:specification
regular:frequency:specification
depends:wire diameter:specification
depends:line speed:specification
depends:wire thickness:specification
na:automation grade:specification
na:body material:specification
standard:pressure:specification
standard:temperature:specification
standard:driven type:specification
standard:max. vacuum:specification
na:dual pressure regulators:specification
standard:voltage:specification
standard:power:specification
ftl:model name/number:specification
100 mm:die size:specification
37kw:power:specification
new:i deal only:specification
48 individually regulated:frequency:specification
ptfe cable extruder:model name/number:specification
20 hp:motor power:specification
includes waste reservoir with assembly to allow for waste:phase:specification
1ml, 3ml:spe cartridge size:specification
1 ml:spe cartridge size:specification
290kg:net weight:specification
smwhydr1:model name/number:specification
corebitx 05:model name/number:specification
ex-tp / 75:model name/number:specification
aza 0947 filterless centifuge extractor:model name/number:specification
100:production capacity(kg/hr):specification
80:capacity(kg):specification
100:capacity(kg):specification
200 kg per charge:capacity:specification
granules making machine:type of machine:specification
400 kg per hour:capacity:specification
leveling:usage/application:specification
400-600kg/hr:capacity:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ):dimensions:specification
75 hz:frequency:specification
51/105, 55/120, 65/132, 80/156:screw number:specification
hindustan plastic & machine corporation (hpmc):brand:specification
20 ltrs. to 500 ltrs.:capacity:specification
steam operated:power source:specification
1.5kg:weight:specification
edr-grm-am:brand:specification
maniratna:brand:specification
sky color:color:specification
fast:speed:specification
120-150 kg/hr:production capacity:specification
1500:capacity (kg):specification
50mm to 250mm:diameter:specification
customized plant:capacity:specification
athena:brand/make:specification
2-3 ltr:bowl capacity:specification
shft:brand:specification
tailor-made:working capacity:specification
steelness steel:material:specification
2 mm:wire diameter:specification
p.p:material:specification
pbat:material to be extruded:specification
150-300 kg/h:production capacity:specification
surya lab expotech:brand:specification
polypropylene and ms booth:body material:specification
320 v:voltage:specification
500 gm to 3 kg:capacity:specification
alloy steel, heat treated barrel and screw for long life.:material:specification
45mm barrel dia:size:specification
7 kw:power:specification
460 v ac:voltage:specification
8135 nm:screw torque:specification
up to 45:weight (kg):specification
standard:material:specification
50hz / 60hz:frequency:specification
25 kw to 300kw:power:specification
220-230:power:specification
220:voltage supply:specification
whirler:brand:specification
95%:purity (%):specification
copper and aluminium:material to be extruded:specification
plasma:electrode material:specification
manual:voltage:specification
chemical:design type:specification
3000 l/hr:capacity:specification
25 m2:working area:specification
pp abs hips hm:material to be extruded:specification
90-100 kg:output:specification
420 v:voltage (volt):specification
tilting type - titanium model:type:specification
1 year:guarantee:specification
50 - 180 kg/hour:output:specification
ss, pvc, ms:body material:specification
singhal ya 3 phase:phase:specification
a to z:capacity:specification
there phase:phase:specification
single phase,three phase:phase:specification
330-350 (kg/hour):output:specification
6 kl:capacity:specification
100kg to 500kg/hr:capacity:specification
500 to 1000 l:capacity:specification
5 kg per day:capacity:specification
sladjana sales corporation:brand:specification
24vdc:voltage:specification
extruder:machine type:specification
150 tpd [1, 50,000 kgs per day]:capacity:specification
pvc/xlpe/ldpe/hdpe:material:specification
steam:diesel consumption:specification
230v:power source:specification
velp:brand/make:specification
nik:brand:specification
5-6 tone:weight:specification
50 to 60 hz:frequency:specification
8 to 12 bar:pressure:specification
8 to 10 bar:pressure:specification
240v:voltage (v):specification
120-150/hr:capacity (kg):specification
white & blue:color:specification
stb-83:model number:specification
1kg to 100kg:capacity:specification
30-200 tons/day:capacity:specification
410v:voltage:specification
yes:installation service:specification
5-5000 kg / hr.:production capacity:specification
white, blue:color:specification
30 mm diameter to 120 mm diameter.:thickness (millimeter):specification
200mt:production capacity:specification
55.93 kw:total connected load:specification
ss202:grade:specification
415:voltage (v):specification
200 kg per hour:capacity:specification
3000 l/h:capacity:specification
harrisons:brand:specification
380:voltage:specification
rt to 105 degreec:temperature:specification
pipe 16 and 20 mm:wire diameter:specification
as per requirement:size:specification
650 mm:max. vacuum:specification
400v:voltage:specification
ci:material:specification
three,single:phase:specification
mild steel,pp:material:specification
99.90/99.99:purity:specification
as per product:power:specification
100 kg per hour / 200 kh per hour:production capacity:specification
25kg:capacity:specification
999 to 99.99:purity:specification
415vac:voltage:specification
1500 ltrs. / hour:capacity:specification
wintech:brand:specification
semi automatic/ automatic:automation grade:specification
220 / 440 volts:voltage:specification
220-415:voltage:specification
bsi make:brand:specification
150:production capacity:specification
latest:features:specification
250 kg/hr:capacity (kg):specification
med source:brand:specification
compact and latest technology:design type:specification
efficient:design type:specification
40 mm:hose diameter:specification
10-200 ltrs:capacity:specification
3hp:motor:specification
pvc:wire material:specification
gsm 200:tarpaulin grade:specification
1kg to 200kg:capacity:specification
100 psi:pressure:specification
0.5 to 5.0 mm:size:specification
5 to 100 lit various:capacity:specification
for different cpacities:capacity:specification
100 kg/hour:production capacity:specification
220-240 v | 50 hz:voltage:specification
10,000 cmh:capacity:specification
130 deg c:temperature:specification
autometic:automation grade:specification
25 ton per day:capacity:specification
24 hours:frequency:specification
single phase or three phase:power source:specification
1 kg to 100 kg:production capacity:specification
global:brand:specification
single phase or three phase:phase:specification
220 v and also available in 440 v:voltage:specification
iflexo:brand:specification
industrial purpose:usage/application:specification
10 hp:main motor power:specification
for pre coating super quality wire:usage/application:specification
screw dia in mm 30 up 150:size:specification
kiran:brand:specification
carban steel:material:specification
en41b musco make:material:specification
bulk:quantity per pack:specification
for cable and wire:usage/application:specification
yes:corrosion resistant:specification
145x350 mm:size:specification
constrction:usage/application:specification
25x20x16 mm:size:specification
4 x 2 x 6 feet (l x b x h):dimension:specification
electric cable instulation:application:specification
depend on the project:diesel consumption:specification
400-600 mm:max sheet width:specification
300 watts:power:specification
24x36x48,20x18x84:dimension:specification
2.50 hours:line speed:specification
16x30x60:dimension:specification
8mm:wire diameter:specification
customized:drum size:specification
1 to 6 bar:pressure:specification
pharmaceuticals:usage/application:specification
painted:surface treatment:specification
as per client requirement:color:specification
hospital:usage/application:specification
high:temperature:specification
hard chrome, nitrated or bimetallic:finishing:specification
3 hp:motor power:specification
55mm 40 mm 35 mm 3 layeer machine:screw diameter:specification
for processing rubber, eva,epa, silicon rubber etc:usage/application:specification
20kg gold & dust refining:capacity:specification
100:capacity(kg/hr):specification
1-kg:capacity:specification
50kg:capacity:specification
5.kg:capacity:specification
30m:length:specification
1 kg/min:capacity:specification
100 kg/h:capacity (kilogram/hour):specification
600kg:capacity:specification
10kg + 10kg double dissolution tank and ppt:capacity:specification
as per client's requirement:production capacity:specification
kp industries:brand:specification
for laboratory:usage/application:specification
plastic compounding / recycling:plastic processed:specification
vishwakarma industries:brand:specification
55/120, 65/132, 80/156:screw number:specification
shreeji machinery:brand:specification
helix extrution:brand:specification
chetan industries:brand:specification
96 samples:capacity:specification
bcs:brand:specification
singal:screw number:specification
mahindra plastic industries:brand:specification
6000 to 12000:capacity:specification
natural:color:specification
medicinal:usage/application:specification
25 kg:packaging size:specification
gg industries:brand:specification
liquid:form:specification
bitumen extractor-with flameproof motor:type of testing machines:specification
six samples:capacity:specification
kankhal:brand:specification
adtech:brand:specification
ansar:brand:specification
52x18:screw number:specification
100kg/hour:capacity:specification
20 ltrs to 500 ltrs.:capacity:specification
no:plastic processed:specification
wood:material:specification
furniture:usage/application:specification
panchveer:brand:specification
d. k. machine tools:brand:specification
for industrial:usage:specification
9l:water tank capacity:specification
220 w:power:specification
g square:brand:specification
200:screw number:specification
maxgreen biomolecules llp:brand:specification
precision instruments:brand:specification
blue, white:color:specification
100 deg c:temperature:specification
lab:usage/application:specification
as per need:power source:specification
220 to 480 acv:voltage:specification
karni:brand:specification
customized:finishing:specification
blue and black:color:specification
10 ltrs:capacity:specification
10 ltr per batch:working capacity:specification
lab equipment:usage/application:specification
350v to 380v:voltage:specification
harini:brand:specification
2.25 kw:power (kw):specification
hand oprate:product type:specification
28 or 30 kg:weight:specification
mumbai:work location:specification
100 gm to 1 kg:capacity:specification
4 to 6 bar:pressure:specification
vertical:tank orientation:specification
na:weight:specification
electric energy (8 kwh):power source:specification
ss304:automation grade:specification
100-500 tpd:capacity:specification
standard:packaging type:specification
na:pressure:specification
na:temperature:specification
from 0.2 mm to 0.8 mm:thickness:specification
40 degree celsius:temperature:specification
300 v:voltage:specification
shiv shakti mechanical:brand:specification
up to 50kg:capacity:specification
lle:brand:specification
5 lit. to 25000 lit.:capacity:specification
1kg to 500kg:capacity:specification
extruder recycle:machine type:specification
100 kg. to 1000 kg:capacity:specification
company:type of service provider:specification
6435 nm:screw torque:specification
ms, borosil glass:body material:specification
customized:oil tank capacity:specification
industry:application:specification
up to 1100 degree c:heating range:specification
naugra:brand:specification
380acv-480acv:voltage:specification
as per req:dimension:specification
as per req:weight:specification
3 ph:phase:specification
any:start date / month:specification
230volts:voltage:specification
universal:brand:specification
hips:material:specification
sheet extruder:type:specification
3 phase:voltage:specification
automatch:driven type:specification
180-240 kg/hr:capacity:specification
crown extractor model iii 703:design type:specification
150 hp:machine power:specification
natural:type:specification
screw type extruder:type:specification
6-9 kw:power consumption:specification
for industrial use:usage/application:specification
1 stage:machine type:specification
filful:brand:specification
65/22:screw number:specification
dew:brand:specification
powder:form:specification
3,4,5 ltr.:capacity:specification
allumunium:material:specification
cassava:raw material:specification
three phase:electricity connection:specification
noodle extruder machine:machine type:specification
aluminium profile, section.:material to be extruded:specification
ideal for plastic product, dyeing processes, and general textile dewatering needs.:usage/application:specification
2:phase:specification
yes:manufacturer:specification
ss316 and ss304:material:specification
7.5 w:power:specification
3 hp:motor:specification
bhanu scientific glass co.:brand:specification
5feet:height:specification
jeweltech jewel equipments:brand:specification
15 days:packaging type:specification
no smell no smoke:frequency:specification
poly propylene (pp) & titanium:body material:specification
mild steel & pp:material:specification
nsc:brand:specification
mild steel,stainless steel:material:specification
industrial yellow:color:specification
3 x 4 x 6 feet:dimension:specification
1hp:motor power:specification
3x2x5 feet:dimension:specification
automatiic:automation grade:specification
3 hp:power consumption:specification
dry type:feed type:specification
a c motor:driven type:specification
100 to 500 kg/hr:capacity:specification
ss304:material:specification
ms and polypropylene:body material:specification
3 phase:motor power:specification
5 kw:motor power:specification
100 kg/h:capacity:specification
1.5liter:capacity:specification
65/132, 55/120, 51/105:screw number:specification
used in the textile processing industry:usage/application:specification
5 kwh:power consumption:specification
xtrutech:brand:specification
pharma:industry type:specification
650mm approx:diameter:specification
apex engineers:brand:specification
mild steel with stainless steel:material:specification
food grade:grade standard:specification
spe-48,spe-96,spe-144:model name/number:specification
conical type:screw design:specification
rectangular:shape:specification
220:frequency:specification
yes:screw design:specification
bitumen test:type of testing machines:specification
all of the above:material:specification
jwell:brand:specification
borewell water:water source type:specification
ld-20/40:screw number:specification
ss 316:material of construction(contact):specification
hindustan kalra:brand:specification
c&g:brand:specification
all type molding:screw design:specification
10 ltr.:capacity:specification
45kw:power consumption:specification
12 bolt:no. of screws:specification
mayuresh gears:brand:specification
square:bag bottom shape:specification
yesha:brand:specification
endoc:brand:specification
ss ,ms:material:specification
bitumen content determination in bituminous mix:type of testing machines:specification
plastic waste bags lums making machine:snacks type:specification
ld:material:specification
30hp:power consumption:specification
50 - 1000:capacity:specification
akansha extrusion & engineering:brand:specification
na:average productivity:specification
na:wire diameter:specification
na:thickness:specification
see pdf:surface treatment:specification
see pdf:screw torque:specification
see pdf:range:specification
see pdf:phase:specification
see pdf:material:specification
see pdf:screw length:specification
see pdf:wire thickness:specification
see pdf:die size:specification
1:26:l/d ratio:specification
35,'53',60,'62,'71mm screw od:diameter (mm):specification
your scoop:power (v):specification
single and three:phase:specification
bitumen testing in lab or field:usage/application:specification
ss,titanium,borosil glass:body material:specification
999:purity (%):specification
700:weight (kg):specification
horizontal:layout:specification
220-280v:voltage:specification
50-60 hz:frequency hz:specification
as per customer requirement:plunger diameter:specification
ocean rotoflex:brand:specification
jaincolab:brand:specification
1 to 4 kg:capacity:specification
100mm-1500mm:lay flat width range:specification
5500 rpm:speed:specification
415vac, 3 phase, 50hz:voltage:specification
25 to 200kwh:electrical unit consumption:specification
15-20 hp:machine power:specification
220v:voltage supply (v):specification
pratik engineers:brand:specification
s.r engineering works:brand:specification
high torque:screw torque (nm):specification
40-80 mm:max forming depth:specification
4 x 2 x 6 feet (l x w x h):dimension:specification
standard:color:specification
1 hp to 15 hp:power:specification
maruti:brand:specification
standard:body material:specification
305mm (diameter):size:specification
subitek:brand:specification
81.6 kg:weight:specification
yes:driven type:specification
440v:voltage (volt):specification
300 - 600 to 1600 - 2500:lay flat width:specification
borosilicate glass 3.3,mild steel,etc:material:specification
see pdf:diameter:specification
see pdf:screw diameter:specification
see pdf:screw l/d:specification
see pdf:body material:specification
see pdf:line speed:specification
see pdf:weight:specification
see pdf:warranty:specification
borosilicate glass 3.3, mild steel, etc:material:specification
gear driven:driven type:specification
h.e.:brand:specification
paint coated:finishing type:specification
hand operated:power:specification
1.5kw:power:specification
tj 250:model name/number:specification
automatic:automation type:specification
fully automated:automation grade:specification
twin conical screw barrel:type:specification
96 cartridges:capacity:specification
192 samples:capacity:specification
jimkhaas extrusions:brand:specification
ssw:brand:specification
used in food/pharma/chemical industry:usage/application:specification
144 samples:capacity:specification
panchveer engineering:brand:specification
peraallel twin screw:screw design:specification
polycarbonate, abs, pp, pet:plastic processed:specification
rd engineering works:brand:specification
siempre machinery pvt.ltd:brand:specification
1000 kg:machine capacity:specification
assembled:brand:specification
90+60 diameter twin screw:screw design:specification
gasket manufacturing:application:specification
50 cycle:frequency:specification
twin screw parllel not conical ( chainise):screw design:specification
poultry / chicken:type:specification
vew:brand:specification
75kg:weight:specification
plastivo extrusions:brand:specification
mild steel:machine material:specification
super scientific:brand:specification
1 tpd:material:specification
10" to 48":diameter:specification
three pointsuspension hydro extractor:frequency:specification
ac drive:drive motor:specification
ramsons:brand:specification
ss and ms:material:specification
handling system with puller streching and finish cutting machine.:material to be extruded:specification
zen:brand:specification
techno machine india:brand:specification
220v 50 hz:voltage:specification
300ton per month:production capacity:specification
for quantitative determination of bitumen percentage in hot mix paving mixture and pavement samples:usage/application:specification
edr - 1grm:brand:specification
999.9:purity:specification
92%:purity:specification
300w:power:specification
90 kw:power:specification
polypropyline homopolymer:body material:specification
wooden:packing type:specification
1 hp:wattage:specification
sil 10 / 25 / 50 / 100:model number:specification
monthly:frequency:specification
lldpe,ldpe,hdpe:plastic processed:specification
370w:power:specification
24 litre:capacity:specification
customized:range:specification
customized:weight:specification
5000 pounds:weight:specification
100kms/h:line speed:specification
1/2,5/8:die size:specification
as per the size:frequency:specification
2800 rpm:motor power:specification
polypropylene and ms:body material:specification
200-400kg/hr:output:specification
required:surface treatment:specification
surya engineering co:brand:specification
ktech 09:model name/number:specification
100 hp:machine power:specification
sea green:color:specification
4.5 kw:power:specification
2.5 mm:font roll diameter:specification
hexane:diesel consumption:specification
hot rolled:technique:specification
90 kw:voltage:specification
5 bar:pressure:specification
s.s. engineering:brand:specification
50-60 hz:frequency (hertz):specification
lab use:usage/application:specification
the scientific apparatus:brand:specification
500v:voltage:specification
edr-gaf01:brand:specification
wooden bix:packaging type:specification
7.5 hp/ 4.6 kw:motor power:specification
900 mm:drum diameter:specification
3 pahse:phase:specification
poly proplyene, glass and titanium:body material:specification
4000kg:weight:specification
1 year warranty:warranty:specification
2400/day:average productivity:specification
75 mm:diameter:specification
at par size:font roll diameter:specification
tech-g:brand:specification
52x2:size:specification
bromelian extract from pineapple:usage/application:specification
ss 316 / ss 304:material:specification
electrical / steam:power source:specification
manual:usage/application:specification
55x90x85inch (dxwxh):dimension:specification
autotype plc based:automation grade:specification
industrial use:usage/application:specification
ss304&316:material:specification
ss 304&316:material:specification
pp titanium and glass:body material:specification
electric motor driven:driven type:specification
oil extraction:usage/application:specification
rust proof:features:specification
ss:type:specification
300kw:power:specification
15 x 15:dimension:specification
saiclave:brand:specification
food industry:usage/application:specification
titanium, glass,pp:body material:specification
240 kv:voltage:specification
no burner:burner:specification
230 kv:power:specification
3 phase & single phase:phase:specification
pp , ss 304, titanium, grade 1:body material:specification
single & 3 phase:phase:specification
6*6:diameter:specification
yes:dust:specification
1200 - 1500 titanium:temperature:specification
new technolab:brand:specification
titanium / glass/ pp:body material:specification
as per the capacity:dimension:specification
at par capacity:line speed:specification
99.9 and beyond:purity:specification
non dried:is it dried:specification
4mm:thickness:specification
soxtron:model name/number:specification
250 w:voltage:specification
aba rotating die blown film machine:machine type:specification
oeplaba02:model name/number:specification
pp, titanium and glass:body material:specification
double:phase:specification
solvent extraction filtration reaction:usage/application:specification
360v:voltage:specification
24 kw:power:specification
sparktech:brand:specification
stainless steel:coating:specification
qunying:brand:specification
oil milling machine:machine type:specification
masterbatch/pla/biodegradebles:plastic processed:specification
tse 16 mm to tse95 mm:size:specification
erc extractor:suitable for:specification
co-rotating, intermeshing twin screws:screw design:specification
pla, pbat, pe, and other biodegradable polymers:plastic processed:specification
specific engineering automats:brand:specification
able:brand:specification
unity:brand:specification
alluminium section:usage/application:specification
313:screw number:specification
yes:no of unit to be tested:specification
50:brand:specification
electrical motorised:type of testing machines:specification
santec:brand:specification
true sources:brand:specification
pvc/pe/pp/pet:plastic processed:specification
growmax:brand:specification
ss304/ss316:material:specification
electric:burner:specification
no gases:gases:specification
for herbal, floral, spices, colors, phyto chemicals extraction:usage/application:specification
ms structure:body material:specification
yes:certification:specification
make in india:brand:specification
pp, glass , titanium:body material:specification
mulch film, stretch film, garbage bag, liner, stretch film:usage/application:specification
80-90 kg./hr.:production capacity:specification
7.5 / 15 / 7.5 hp:main motor:specification
10 mt per day:average productivity:specification
yes:maintenance:specification
600 kw:power source:specification
nsc180pe:brand:specification
7-70 mts./min.:line speed:specification
98:purity:specification
ral shades:color:specification
depand on size:flange width:specification
1:model name/number:specification
faha industries:brand:specification
semi:automation grade:specification
automatic:calibration type:specification
working pressure 3000bars:vacuum pressure:specification
230v ac:voltage:specification
mirror polish:finishing:specification
80 kgs:weight:specification
patetnt:design type:specification
ud:brand/make:specification
>120:machine power:specification
stainless steel (ss304):body material:specification
fabex:brand:specification
3 kg and 5 kg:capacity:specification
0-0.5 mm:diameter:specification
1.5-2 mm:diameter:specification
30 - 500 tons per day:capacity:specification
life time free:service charges:specification
xxx1:capacity / size:specification
hongqi:brand:specification
1 kg, 2 kg, 3 kg, 5 kg and so on..:capacity:specification
technister:brand:specification
26/1:l/d ratio:specification
3 feet:font roll diameter:specification
edr-250srm:brand:specification
500kg:weight:specification
jainco:brand:specification
industries:usage/application:specification
cable machine:material to be extruded:specification
industrial, agriculture & pharmaceuticals:usage/application:specification
steam:voltage:specification
up to 350 kg/hr:production capacity:specification
120 to 350 kg/hr:capacity (kilogram/hour):specification
7.5 to 10 mpm:line speed (meter/minute):specification
ac 220v:voltage supply:specification
3000r/min:speed:specification
315 v ac:voltage:specification
150 kw:power:specification
64 n/mm2:screw torque:specification
380:voltage (volt):specification
440v:power source:specification
hd/hm/ld/biodegradable:material:specification
50-60:frequency:specification
as per req:micelle concentration:specification
as per req:motor:specification
as per req:oil tank capacity:specification
as per req:electrical unit consumption:specification
yes:design customized:specification
extraction:requirement details:specification
any:service duration:specification
100 to 300 kg/hr:production capacity:specification
mcm:brand:specification
pp:automation grade:specification
chinese machines:brand:specification
220 - 240 v:voltage:specification
from 500ltr - 5000ltr:capacity:specification
10l to 50l:capacity:specification
aarti scientific:brand:specification
220 v-380 v:voltage:specification
100 hp:power consumption (kilowatt):specification
1200 w:power (watt):specification
stainless steel , mild steel:material:specification
electrical & steam supplier:power source:specification
60 kw:rated power (kw):specification
9-100:size:specification
15 & 7.5 hp motor:main drive ac (kilowatt):specification
60 hp:power consumption (kilowatt):specification
28kw:power consumption:specification
ms or ss both:material:specification
ss 304:grade standard:specification
100 scuare feet:size:specification
pe/pp/pa/pc/tpu:plastic processed:specification
rp twin screw extruder:brand:specification
modular structure with 600 rpm made up of 40crnimoa:screw design:specification
65mm:screw number:specification
ms and ss:material:specification
yes:brand:specification
twin screw corotating:screw design:specification
pp/hd/ld/hips/abs/pc/pet/nylon6/nylon66/pbat & all types of engineering plastic:plastic processed:specification
two:screw number:specification
galvanised:surface finishing:specification
a/c drive:driven type:specification
99:purity:specification
fully automatic touch panel:automation grade:specification
flexy glass:material:specification
seven seas:brand:specification
6:die size:specification
440vac:voltage:specification
440:power:specification
100 degree:temperature:specification
gaurav engineering:brand:specification
ss 304 & 316:material:specification
mechotech llp:manufacturer:specification
dried:is it dried:specification
0-1 mm:min finish wire diameter:specification
ss casing:body material:specification
phds260:model name/number:specification
as per rquirement:size:specification
500:line speed:specification
vsel:brand:specification
20 hp:main motor:specification
yes:extraction:specification
blue and grey:color:specification
electric motor:driven type:specification
automation:automation grade:specification
2kw:phase:specification
titanium, glass pph:body material:specification
10 x 10 x 10:font roll diameter:specification
for manufacturing bottle cap liners and epe sheet:usage/application:specification
industrial used:usage/application:specification
230 or 440 v:voltage:specification
0-3 kg:pressure:specification
95 %:purity:specification
kalyan engineering corporation:brand:specification
approx 170 kg:weight:specification
singe phase:phase:specification
high speed mixer:product type:specification
vikas engineering works:brand:specification
aluminium, mild steel:body material:specification
blue/ white:color:specification
ld, hm, biodegradable:material:specification
100 ( micron ):film thickness:specification
110 kg/hr:output:specification
25 hp:main drive ac:specification
500:output:specification
200 - 500 gm/h:output:specification
4-6mm:thickness:specification
280 kg:weight:specification
airtas:brand:specification
0-100 a:output current:specification
28 kw:power consumption:specification
240 to 440 v:voltage:specification
german pp:material:specification
12-15 kg:weight:specification
135 kg:weight:specification
solvent distillation:usage/application:specification
110-1500 kg/hr:capacity (kg):specification
ss316:contact parts:specification
55 inch x 17 feet:size:specification
650-1250:lay flat width:specification
0.5 hp:motor power:specification
single pase /3phase:phase:specification
50-60kg:weight:specification
unitech ultrasonic:brand:specification
kumar solvent extraction plant:design type:specification
mini-45a:model name/number:specification
veendeep:brand:specification
75 kw:power:specification
het110:model name/number:specification
415v / 50 hz:voltage:specification
stainless steel:color:specification
1/2" to 1.5 ":die size:specification
11 ton / day:output:specification
300 x 300 mm:basket diameter:specification
smw:brand:specification
yes:motor:specification
50 to 800 degree celsius:heating range (deg. celsius):specification
titanium,glass,pph:body material:specification
turnkey:design type:specification
99.97:purity:specification
12 kw:motor power:specification
30 hz:frequency:specification
to extract the active ingredient present in the dry herbs/seed powder/root/leaf using a suitable sol:usage/application:specification
rdew 51-105 extruder:size:specification
100 square feet:dimension:specification
415 v:power source:specification
solvent/ water based extraction of different herbs and spices.:usage/application:specification
-5 to 150 deg c:temperature:specification
suman tech engineering:design type:specification
only edible product's:usage/application:specification
2.50%:diesel consumption:specification
280c:temperature:specification
350 tonnes:weight of machinery:specification
pp/ glass and titanium:body material:specification
10hp:power:specification
130kw:power consumption:specification
400-600kh/hr:output:specification
100 kg per batch:frequency:specification
pph, titanium & glass:body material:specification
diamond gear box model:model:specification
annamalaiyar lathe works erode:brand:specification
all extraction machine:usage/application:specification
jay engineers:brand:specification
medicen:usage/application:specification
100 kg/h:production capacity:specification
120 degree celsius:temperature:specification
as per the quantity:line speed:specification
fully automatic and semi automatic:automation grade:specification
220 / 415 v:voltage:specification
10 ton to 100 ton per day:size:specification
tobacco extraction:usage/application:specification
1 ton:weight:specification
ss 316 / ss 304 / ms:material:specification
ldpe,lldpe,hdpe:plastic processed:specification
500 kgs leaves per day:capacity:specification
2liter:bowl capacity:specification
999 to 9999:purity:specification
10mm , 15mm:sheet thickness:specification
7 bar:max design pressure:specification
4 x 2 x 7 feet (l x w x h):dimension:specification
hdpe pp pvdf:material:specification
75kw:voltage:specification
used for the determination of bitumen percentage in hot-mixed paving mixtures and pavement samples.:usage/application:specification
50 rpm:screw speed:specification
350l:oil tank capacity:specification
casting:material:specification
1500g:bowl capacity:specification
unique engineering:brand:specification
15 kg:weight:specification
48:size/dimension:specification
30 bar:pressure:specification
p p structure:body material:specification
singale phase:phase:specification
sox 2:capacity:specification
aluminum:material to be extruded:specification
vksi-058:brand:specification
12 - 15 mm:thickness:specification
cygnet machinery:brand:specification
3000 kg:weight:specification
dc:motor:specification
999+ / 99.99:purity:specification
30 kg:weight:specification
no:power:specification
1500:bowl capacity:specification
gmak industries.:brand:specification
fre:brand:specification
35mm to 150mm:size:specification
depending on size of extruder:packaging size:specification
10 mm:wall thickness:specification
8mm:sheet thickness:specification
730 kg:weight:specification
75 mm:drain size:specification
70:heating range (deg. celsius):specification
upto 50 mm tubes:diameter:specification
150 per minute:speed:specification
cream:color:specification
2-3 mm:min finish wire diameter:specification
xps:material:specification
99/99%:purity:specification
any:die size:specification
na:color:specification
50-60 ton/day:capacity:specification
up to 75 hp:power:specification
1200 kg:weight:specification
99 %:purity:specification
edr-3grm:brand:specification
flavex india:brand:specification
for herbs extraction:usage/application:specification
double phase:phase:specification
custom:form:specification
1.5 kva:power:specification
bvncbn:diesel consumption:specification
50 - 500 tons per day:capacity:specification
130 rpm:line speed:specification
single / three phase:phase:specification
smt:brand:specification
240-300 v:voltage:specification
50 to 250 degree celsius:heating range (deg. celsius):specification
230volt:voltage:specification
48*48*72 inch:dimension:specification
one year:weight:specification
18x20:dimension:specification
ac frequency drive:driven type:specification
1 kg - 500kg:capacity:specification
10 kw:power source:specification
10mm:wire diameter:specification
j. m. industries:brand:specification
na:max. vacuum:specification
mild steel (body):body material:specification
200 kg/hr:output:specification
3 mm:min finish wire diameter (mm):specification
4.5:power (kw):specification
atmospheric:max. vacuum:specification
50-100:output(kg/hr):specification
4.5 kw:power (kw):specification
carmel engineering:brand:specification
90 - 180 kg/hr:output:specification
24kg/hr:average productivity:specification
tp75:model name/number:specification
green:color:specification
0.05%:accuracy:specification
auto heating:heating range:specification
240v:power:specification
installed by company:installation services:specification
shree ganesh enterprise:brand:specification
440v /230v:voltage:specification
500 w:power:specification
1kw:lead:specification
m.s & s.s:body material:specification
the exclusive 7" controlpad(tm) facilitates the set-up and interaction with the extractor.:working area:specification
amv scientific:brand:specification
pp and titanium:body material:specification
24 months:shelf life:specification
10 feet:height:specification
glass:lead:specification
1200:temperature:specification
320:voltage:specification
electrical / wood:power source:specification
fully automatic:automatic grade:specification
110 degreec:heating range:specification
electric 3 phase and singel phase:power source:specification
1/4 hp:motor power:specification
pp me:machine type:specification
40 mpm:line speed:specification
700 mm:die size:specification
8 x 8:font roll diameter:specification
ss & alloys:material:specification
235 kg/h:production capacity:specification
4 ft:max panel width:specification
conical twin:design:specification
8 bar:pressure:specification
1/2 hp 1400 rpm:motor power:specification
pvc shrink film extrusion machine:machine type:specification
single phase / three phase:motor power:specification
the rotation of the liquids outside the rotor:usage/application:specification
4000 kg:weight:specification
up to 65 meter per hour:line speed:specification
nilk:wire diameter:specification
fresh:style:specification
recreational drug, a treatment for addiction tobacco, and as a pesticide:usage/application:specification
industrial and lab grade:usage/application:specification
to concentrate and purify the samples for analysis.:usage/application:specification
jas:brand:specification
glass, titanium, polypropylene:body material:specification
anticorrosive pph (polypropylene):body material:specification
titanium/ pp & glass:body material:specification
10 kw:voltage:specification
60-80:line speed:specification
2hp:power:specification
110:diameter:specification
pharmaceutical:application industry:specification
fluidized aerated reactor:treatment technique:specification
30 hz:frequency range:specification
0.4 kw:air blower power:specification
pp / titanium:body material:specification
cottor plants (india) pvt. ltd.:brand:specification
gurukurpa enterprises:brand:specification
45 kw:power consumption:specification
carbon steel:material:specification
industrial liner & film:usage/application:specification
sgew:brand:specification
polyprelene:body material:specification
titanium / pp / glass:body material:specification
full control:line speed:specification
40-75 kg./hr.:production capacity:specification
220 / 415:voltage:specification
tailor made:design type:specification
175 kw:power consumption:specification
45 degree c:temperature:specification
3 phase ac:power source:specification
single phase/ three phase:phase:specification
bitumin:usage/application:specification
mild steel / pp:body material:specification
0:motor power:specification
grey:color:specification
pci:brand:specification
poly propylene (pp) & titanium:material:specification
packaging details: wooden packing & with bubbles rappers:packaging type:specification
150 bar:pressure:specification
415v:voltage:specification
yes:corrosion resistance:specification
ms - ss:body material:specification
70 hp:total connected load hp approx:specification
medicine:usage/application:specification
37 kw:power:specification
electrical / solid fuel:power source:specification
25 hp:power consumption:specification
blue , silver:color:specification
wooden packing & with bubbles rappers:packaging type:specification
used for turmeric extraction:usage/application:specification
industrail:usage/application:specification
90 to 120 kg/hr:production capacity:specification
ac drive:driven type:specification
vrpec:brand:specification
40 kh:weight:specification
10x10:dimension:specification
stainless steel / mild steel:material:specification
homopolymer:polymer type:specification
5kw:power:specification
110 to 480 ac:power source:specification
max 1:pressure:specification
as per req:temperature:specification
all:technique:specification
pph titanium etc:body material:specification
as per requirement:power:specification
4 tons:weight:specification
blue (base):color:specification
construction:usage/application:specification
50 nb to 200 nb:drum size:specification
standard:drum size:specification
customized:temperature:specification
200 mm:die size:specification
30-35 kgs/hour:production capacity:specification
plastomech:brand:specification
350 w:power:specification
emak makina turkey:brand:specification
35 x 45:size:specification
400 mm:size:specification
15mm:diameter:specification
color coated:surface finish coating:specification
non-cnc:control type:specification
chrome plated:surface finish:specification
95 %:purity (%):specification
yellow:color:specification
5 racks and 108 samples a batch:range:specification
automated solid phase extract:usage/application:specification
ss and ms:body material:specification
fine rhodium:brand:specification
415v,50hz:voltage:specification
100tpd to 500tpd:capacity:specification
mel/20/ex:model name/number:specification
15 kg to 60 kg per batch loading capacity:capacity:specification
high grade plastic and ptfe material.:material:specification
1 kg, 2 kg, 5 kg, 10 kg, 20 kg:available capacity:specification
educational trainer research type:features:specification
98%:purity:specification
kanha instruments scientific:brand:specification
biodegradable film & bags:usage/application:specification
turn key:design type:specification
30 rpm:line speed:specification
1 mm:wire diameter:specification
10 hp:power consumption:specification
glass, titanium pph:body material:specification
as per the capacity:frequency:specification
2mm:sheet thickness:specification
yes:temperature:specification
26" nip roll:roller size:specification
50 kn:capacity:specification
20hz:frequency:specification
typically adjustable; varies by material type:wire thickness:specification
electricity/steam:power source:specification
medicine use:usage/application:specification
10hp:power source:specification
ms & en graded material:body material:specification
3 kg:weight:specification
steel or aluminum (frame construction):body material:specification
70 mm (extrusion die):die size:specification
electrical & steam:power source:specification
textile material:material to be extruded:specification
99.9:purity:specification
plain:pouch pattern:specification
3 h.p:motor:specification
300w/350w/400w/500w:power source:specification
100-300 kg:capacity:specification
415 ac:voltage (v):specification
280v:voltage:specification
polyproplene sheet:body material:specification
round head:shape:specification
420v:voltage supply:specification
cement testing:usage/application:specification
415 v ac:voltage (v):specification
99.90 to 99.99:purity:specification
blue and red:color:specification
plastic:material compatibility:specification
curcumin / turmeric extraction:usage/application:specification
single or phase:phase:specification
fully automatic touch screen operating system:automation grade:specification
sx-9022:model name/number:specification
nitrided alloy steel:body material:specification
90 kg/h:capacity (kilogram/hour):specification
230v, 440v, 50hz, 12kw:voltage:specification
4/4/2006:dimension:specification
machine world:brand:specification
transparent:surface finish:specification
230 v:power consumption:specification
fully autometic:automation grade:specification
5hp:motor power:specification
220v, / 440v:power:specification
oil soluble:solubility:specification
11.25 kw:power:specification
220v/ 440v:power:specification
220v:power source:specification
99.5:purity:specification
230 v:power source:specification
help transform raw ingredients into safe, nutritious, and appealing finished food products.:usage/application:specification
water tank with ss-304:body material:specification
5 hp 3 phage:phase:specification
jje02:model name/number:specification
2kwt:power:specification
white, gray:color:specification
mechotech:brand:specification
tejas engineering:brand:specification
to turn raw plastic pellets or granules into the processed forms:main motor:specification
sami automatic:machine type:specification
400 kwh:power source:specification
30:motor:specification
by steam boiler:steam supply:specification
vfd:driven type:specification
extra:installation services:specification
semi automatic:operation type:specification
single phase / three phase:phase:specification
moter used are of imported quality:motor power:specification
bubbels:packaging type:specification
20000w:power consumption:specification
plastic recycling:usage/application:specification
pp body reactor titanium:body material:specification
bubbles and wodden:packaging type:specification
3mm:sheet thickness:specification
92 mm:diameter:specification
ss304 and ss316:material:specification
no:automation grade:specification
pp & titanium:body material:specification
2.1kw:power:specification
as per the capacity:power:specification
used in oil industry:usage/application:specification
pragati:brand:specification
ss 304 / ss 316:material:specification
herbs extraction:usage/application:specification
bmep:model name/number:specification
3 phase:driven type:specification
determines bitumen content in bituminous mixtures:usage/application:specification
pp ss titanium glass:body material:specification
veriable:frequency:specification
a.c drive:driven type:specification
52/18:model name/number:specification
10 x 10 x10:dimension:specification
natural color extraction:usage/application:specification
ss titanium:material:specification
air pressure:power source:specification
single/three phase:phase:specification
borosilicate 3.3 glass:material:specification
spec12:model name/number:specification
12/24:capacity:specification
royle extrusion systems:brand:specification
seprex:brand:specification
cartoon box:packaging type:specification
lab basket extruder:machine type:specification
1/4 hp 1400 rpm:motor power:specification
yes:computerized:specification
40 hrc:hardness:specification
poly propylene (pp):material:specification
500:production capacity(kg/hr):specification
yes:herbal:specification
labbazaar:brand:specification
metal extraction:usage/application:specification
ore beneficiation:machine type:specification
250 v:voltage:specification
pp sheet:material:specification
complete civil work with installation:installation type:specification
60%:max water recovery rate:specification
ms and ss:body material:specification
20 x 20 x 20:dimension:specification
50 kilogram per batch:frequency:specification
h k:brand:specification
52/2:model number:specification
230 v ac:temperature:specification
ms(body):body material:specification
3hp:motor power:specification
blaze:brand:specification
semi autiomatic:font roll diameter:specification
250:voltage:specification
230v(ac):voltage:specification
stainless steel,carbon steel:material:specification
stainless steel and other metals and non-metals:material:specification
turn key:machine type:specification
customized / tailor made:design type:specification
energy-efficient machinery designed for low operational costs:power source:specification
biswakarma engineering corporation:brand:specification
40kg/75kg/100kg/137kg:height:specification
s. tech:brand:specification
yes:steam supply:specification
vertical:machine type:specification
15 hp:main motor power:specification
carry bag , garbage bag , shopping bag:usage/application:specification
pp (polypropylene):body material:specification
2.5 hp:power consumption:specification
ss304 / 316:material:specification
katha extraction:usage/application:specification
n & t engitech:brand:specification
maniquip:brand:specification
pp or polypropylene:material:specification
90-450kg/hr:output:specification
5 kg:weight:specification
800 kg:weight:specification
pipe with prv:steam supply:specification
for solid phase extraction:usage/application:specification
multiple:size:specification
3 phase:phases:specification
transparent:color:specification
200 ton/month:production capacity:specification
400 kw:power consumption:specification
5 inch:size:specification
pulley belt:driven type:specification
blue and silver:color:specification
single die extruder:power consumption:specification
titanium, teflon, pp:body material:specification
99.9% - 99.99%:purity:specification
150 - 300 ( kg/hr ):output:specification
2phase:phase:specification
singal:layer:specification
belt , chain:driven type:specification
420:voltage:specification
15 to 100:thickness:specification
1 ton per hours:average productivity:specification
oil extract from rice bran by using hexane:usage/application:specification
300:electrical unit consumption:specification
760:max. vacuum:specification
industry level:usage/application:specification
1500 grams:bowl capacity:specification
1500 gms:bowl capacity:specification
semi-automatic:automation type:specification
220v:operating voltage:specification
62mm & 72mm:diameter:specification
blue & grey:color:specification
600mm x 1500mm x 1800mm:dimension:specification
depends on motor size:motor kw:specification
globetrek:brand:specification
240 v:power source:specification
ji:dimension:specification
ss 304 / 316:material:specification
22 kw:machine power:specification
s.s.:body material:specification
atmiya:design type:specification
35 - 150 ( kg/hr ):output:specification
handbag:type of bag:specification
40-60:capacity(pieces per hour):specification
ld / hm / biodegradable:material:specification
300 kg:weight:specification
10 - 100 kg/h:output:specification
svas:brand:specification
customozed:usage/application:specification
custimized:design type:specification
70 hz:frequency:specification
20 kw:power:specification
6 feet:height:specification
extraction plant:usage/application:specification
fs - 25 lab:model name/number:specification
7.5 hp:motor power:specification
varies by application; typically adjustable:line speed:specification
2.5 mm to 10 mm (depends on die size):wire diameter:specification
65/18:model name/number:specification
100-150l/day 200-350l/day 300-500l/day 500-800l/day:capacity:specification
brand n&t engitech pvt ltd:brand:specification
3 to 10 kw:power consumption:specification
multi-color:color:specification
bimetallic:surface treatment:specification
20 x 20:dimension:specification
99.95:purity:specification
not laminated:pouch lamination:specification
all colors available:available colors:specification
no vibration no sound:frequency:specification
4 kg:weight:specification
12mm / 8mm:sheet thickness:specification
electricity / d g set:power source:specification
1kg to 10 kg:capacity:specification
80 degree centigrade:temperature:specification
60- 1200 kg/h:production capacity:specification
3600 rpm:speed:specification
50-600 tph:capacity:specification
eletricity:power:specification
220-440 v:voltage (v):specification
h, 2100mm. w, 650mm. l,2700mm:dimension:specification
white and blue:color:specification
ms ,ss , aluminium:body material:specification
100 bundles per day:average productivity:specification
16 & 20 mm inline & online drip pipe machine:diameter millimeter:specification
10-150 kw:electrical unit consumption:specification
600-1000 kg/hr:capacity:specification
8-12 kg/h:capacity (kg):specification
150 kg:weight:specification
510 mm:drum diameter:specification
pemac projects:brand:specification
oil seeds:material to be extruded:specification
0.25 hp:motor power (hp):specification
200:production capacity (kg per hr.):specification
ss 316l/ss304 l:material:specification
600-1050 mm:lay flat width:specification
chemical industrial processes:usage/application:specification
powder coated paint:surface finishing:specification
20 kgs:weight:specification
ss 304, pu coated gi:material:specification
technocrat:model name/number:specification
mild steel and ss-304:material:specification
semi and auto:automation grade:specification
we provide:installation services:specification
galvanized:surface finish:specification
8to 15mm:sheet thickness:specification
tubes in anodizied aluminium,joints in pp plastic,duct connectors in epdm rubber & minihood in pp:material:specification
high:automation grade:specification
high:frequency:specification
m s plate, ms channel, ms angel and ci casting.:material:specification
50 to 250 degree c:heating range:specification
single and three phase:phase:specification
steam:power source:specification
sm15:model name/number:specification
co extruded:machine type:specification
extrusion plant for zip lock bags:machine type:specification
iot based:automation grade:specification
ss 304 / 316:material body:specification
50-100:capacity:specification
>12 mm:max inlet wire diameter (mm):specification
1-2 mm:min finish wire diameter (mm):specification
100g:bowl capacity:specification
asphalt centrifuge extractor:usage/application:specification
50 kg to 1000 kg:production capacity:specification
20 hp:power:specification
pp, titanium and ss material:body material:specification
vision:brand:specification
ss304:machine type:specification
75 mm:screw diameter:specification
m s:body material:specification
220 / 415 / 380:voltage:specification
educational:usage/application:specification
stand alone:type of instruments:specification
hari om fibre:brand:specification
available in different grade ss 304/ 316 l/ haste alloy/ nickle:material:specification
upto 100 kw:electrical unit consumption:specification
700 mm of hg:max. vacuum:specification
extech process:brand:specification
to insulate the wire core of the wire or to protect the cable:usage/application:specification
450 kg approx:weight:specification
pp material:body material:specification
220 / 415 / 440 v:voltage:specification
fully automatic:driven type:specification
depend on capacity of plant:micelle concentration:specification
used for separation and extraction of bitumen:usage/application:specification
6.5 feet:dimension:specification
99.90 / 99.99:purity:specification
s s 316:material:specification
cadif:brand:specification
blue & yellow:color:specification
230 volts:power:specification
timer:display type:specification
kalinga extrusion technik:brand:specification
380 v ac:voltage:specification
hm, hd, hdpe, ld and lldp:plastic processed:specification
40 inch:screw diameter:specification
75/150 mm:die size:specification
as per reqiurement:oil tank capacity:specification
35 to 100 deg c:temperature:specification
1200 - 1400 rpm:speed:specification
frame :- mild steel, and bowl is aluminium:material:specification
yx-extruder:brand:specification
12 mm:max inlet wire diameter:specification
3 hp 3 pharse:motor:specification
26 l/d:diameter:specification
twin screw segmented:design:specification
up to 25 kg:range:specification
fuel and electricity:power:specification
2000 kg:weight:specification
3500 kg:weight:specification
20 - 150 ( micron ):speed:specification
edr grm:brand:specification
edr-250srm:model name/number:specification
yes:surface treatment:specification
900:screw torque:specification
2 mts:size:specification
fabricated:body material:specification
ss 316,316l:material:specification
5 x 3 x 7 feet (l x w x h):dimension:specification
3mm:font roll diameter:specification
maas:brand:specification
phytochemical industrial:usage/application:specification
extraction plant:design type:specification
as per req:diesel consumption:specification
as per req:steam supply:specification
as per req:thickness:specification
as per req:weight of machinery:specification
as per req:max. vacuum:specification
star whites:brand:specification
for packaging:usage/application:specification
40 mm:diameter:specification
20 v:voltage supply:specification
50-500 tpd:capacity:specification
air cooled:cooling type:specification
230 v ac:voltage:specification
25-250 micron:film thickness:specification
abb:main motor:specification
touch screen:type:specification
108 samples:capacity:specification
ss ms teflon:material:specification
0-7 bar:pressure:specification
108 samples:working capacity:specification
herbal extract:usage/application:specification
cex 100:model name/number:specification
x.x.x.:font roll diameter:specification
gmak industries:brand:specification
packing with bubbles rappers:packaging type:specification
450 mt:production capacity:specification
42" nip roll:roller size:specification
60 kw:power consumption:specification
heaven extrusion:brand:specification
shree ganesh enterprises:brand:specification
iron amd mild steel:material:specification
wpc:material:specification
50 kg:weight:specification
415 v ac:voltage:specification
800 kg to 1200 kg:weight:specification
12" & 18":size:specification
shakti design:design type:specification
0.8 to 2 mm:wire diameter:specification
20hp:main drive ac:specification
0.8 (as per customer requirement):min finish wire diameter:specification
20":max. vacuum:specification
vacuum only:pressure:specification
10 kg:weight:specification
herbal products:usage/application:specification
5/5/8feet:dimension:specification
european technology with proven design.:technique:specification
20 to 63mm:die size:specification
organic:is it organic:specification
20:power source:specification
yes:design type:specification
mechotech for plant:manufacturer:specification
250:power:specification
able engineering:brand:specification
aone:brand:specification
pph, titanium:body material:specification
2.hp:motor power:specification
hot runner:runner:specification
carry bags, shopping bags , bag on roll, garbage bags:usage/application:specification
extraction of herbals:usage/application:specification
ss 304, ss 316:material:specification
ser-158/3:model name/number:specification
42"x24"x60":dimension:specification
100x2:font roll diameter:specification
1-5 kg:capacity:specification
cable extruder:machine type:specification
polished:product type:specification
85 degree celsius:temperature:specification
osaw:brand:specification
as per clients requirement:capacity:specification
230v:power:specification
6:height:specification
50 to 100 kg/hr:capacity:specification
385 kg:weight:specification
mild steel with painting:body material:specification
220 -240 v:voltage:specification
60 hz:frequency (hz):specification
5-50 rpm:screw torque:specification
1.5 hp:power:specification
smeltex:brand:specification
customized:working capacity:specification
w650 x l950 x h1450 mm:size:specification
blue & white:color:specification
200 to 750 kgs/hr:output:specification
80mm:die size:specification
ss:design:specification
nitrogen gas:power:specification
999.50%:purity:specification
as per requirement:frequency:specification
drugs and pharmaceuticals:usage/application:specification
up to 400:diameter:specification
musco alloy material grade:brand:specification
single and double both:speed:specification
hand operated and easy operated:product type:specification
approx 10 kg:weight:specification
all:crude protein:specification
rr:brand:specification
blue paint and silver:color:specification
gear mechanism:driven type:specification
sharmax(ssw)):brand:specification
415v, 50hz:voltage:specification
90 kg:weight:specification
45 - 200:capacity:specification
440 volt:voltage:specification
high:voltage:specification
yes:power:specification
.5 hp:power:specification
to determine the percentage of bitumen in bituminous mixtures:usage/application:specification
ss and pvc:material:specification
industrial:grade standard:specification
skin care & wound care:usage/application:specification
65 mm:lay flat width:specification
yes:oem:specification
360:voltage:specification
pharma industry:usage/application:specification
food flavour:usage/application:specification
pph , titanium:body material:specification
stainless steel grade 316l:material:specification
singal &3 phase:phase:specification
tank 200l:capacity:specification
pp titanium:body material:specification
ss:frequency:specification
0.5v:power source:specification
70:temperature:specification
800 mm:roller size:specification
35 / 45 / 35 mm:screw diameter:specification
pe,ldpe,lldpe,hdpe,hm-hdpe,mdpe,mlldpe,metallocene,polyethylene,polypropylene,eva,pvoh/pa:usage/application:specification
4*4*6 feet:dimension:specification
liner, stretch film, shrink film, garbage bags:usage/application:specification
60-100 kg./hr.:production capacity:specification
15hp & 20hp:main motor:specification
52" nip roll:roller size:specification
ae:brand:specification
ms & ss:material:specification
150 ton/day:capacity:specification
2 kw:motor power:specification
single or three phase:phase:specification
40 kg per hrs:average productivity:specification
55 mm:size:specification
adex 110t:model name/number:specification
packaging film:usage/application:specification
70 kw:power consumption:specification
220 to 440v:voltage:specification
50 to 250 deg c:heating range:specification
polished:finishing:specification
220v,/ 440v:voltage:specification
100 degree c:heating range:specification
jje1000:model name/number:specification
4*6*5:dimension:specification
no:moisture:specification
12*10:diameter:specification
hariom:brand:specification
100%:frequency:specification
9 ft.:height:specification
lasotherm:brand:specification
horizen extrusions:brand:specification
45 mm:screw number:specification
diaphragm vacuum pump:driven type:specification
-700mm hg:max. vacuum:specification
180 ton:production capacity:specification
orange and blue:color:specification
electronic:power source:specification
aprox 17 mt:weight:specification
25-38 kg./hr.:production capacity:specification
220:screw diameter:specification
1.0 hp:power:specification
titanium/pp/glass:body material:specification
27 deg c /0.5 deg c:temperature:specification
100 kgs/hr:capacity:specification
semi auto:automation grade:specification
415+_5%:voltage:specification
conical twin extruder:design:specification
semi continuous:machine type:specification
200 kw:power source:specification
single & triple:phase:specification
12 feet:height:specification
yes:burner:specification
italian:brand:specification
air compresure:filter type:specification
40mm:inlet and outlet:specification
110 - 440 volts:voltage:specification
food processing industries:usage/application:specification
helical:type:specification
380v:power:specification
induction motor:driven type:specification
99.9% to 99.95%:purity:specification
stainless steel (body) and pp:material:specification
1500kg:weight:specification
32 kw:power consumption:specification
ss 304,316:material:specification
80/156:screw number:specification
extruding wires to further form cables after their extrusion:usage/application:specification
220,440v:power:specification
no dust:dust:specification
no gas:gases:specification
3inch (dia):size:specification
50hrc:hardness:specification
4 bar:pressure:specification
35:temperature:specification
40:weight:specification
125 mm:die size:specification
120 mm:thickness:specification
medium:temperature:specification
food grade:grade:specification
auotomatic:automation grade:specification
pvc-wpc foam board:usage/application:specification
55:main motor:specification
upto 35 mm:thickness:specification
chemical processing:usage/application:specification
52mm:size:specification
tech-g kanpur:trademark:specification
raw material to be ground into powder, and washed with a suitable solvent that selectively extracts:usage/application:specification
solvent extract:machine type:specification
99.999:purity:specification
10 ltr,20 ltr,30 ltr,40 ltr:size:specification
65 kg/h:production capacity:specification
52:diameter:specification
65 mm(cable diameter):size:specification
no front roll:font roll diameter:specification
single and three phase both are available:phase:specification
dss engineering works llp:brand:specification
4 x 4 feet:dimension:specification
15 x 20:dimension:specification
fully automactic:heating range:specification
10feet:height:specification
18.5 kw:power consumption:specification
adex 150t:model name/number:specification
aluminium extrusion industry:usage/application:specification
ss 304 std & gmp:body material:specification
100 - 500 kg per/hr.:average productivity:specification
300 rpm:line speed:specification
300 mm - 450 mm:die size:specification
helical gear direct drive:driven type:specification
as per machine design:thickness:specification
sbe300 - sbe450:model name/number:specification
shakti scope:installation services:specification
spectec:brand:specification
oil extraction from oil seeds, doc and rice bran:usage/application:specification
ss(body):material:specification
easy to operate:frequency:specification
220v,/ 440v, 50hz, 12kw:power:specification
sheet:form:specification
sp-1:model name/number:specification
20mm to 110mm:diameter:specification
52 mm:screw diameter:specification
ms body, ss enclosure:material:specification
2 hp:motor:specification
pp, glass:body material:specification
chauhan engineering:brand:specification
a c drive:driven type:specification
pipes:output shape:specification
56 kw:power consumption:specification
10-1000 tpd:capacity:specification
volcano:brand:specification
based on cooling pipe:size:specification
in ccv lines to hold the pressure while cable is coming out of catenarytube.:usage/application:specification
7 kg per cm2:pressure:specification
yes:voltage:specification
sample prep and solid phase extraction:usage/application:specification
10v-15v hp:voltage:specification
carry bag:type of bag:specification
shopping bag:type of bag:specification
laptop bag:type of bag:specification
grain bag:type of bag:specification
20-40:capacity(pieces per hour):specification
60-80:capacity(pieces per hour):specification
146 - 194:connected load:specification
rtd pt-100 type.:temperature:specification
380 - 440:voltage:specification
20 mm - 400 mm:capacity:specification
maild steel:material:specification
blek:color:specification
10mpa:pressure:specification
5-5.30 p:power:specification
45kw:power:specification
extrusion of polymers for cable manufacturing.:usage/application:specification
tqte:brand:specification
5-5 rpm:screw speed:specification
ashok extrusion tech private limited:brand:specification
ps:material:specification
teflon cable:usage/application:specification
xxx:depth:specification
300 degreec - 400 degreec:heating range:specification
10mm:wall thickness:specification
sj:brand:specification
1kw:power:specification
5 kw:voltage:specification
reliable lab equipment c0.:brand:specification
25kg:weight:specification
solvent extarction:usage/application:specification
etts-90/25-56-550:model name/number:specification
mkp:brand:specification
230 v ac / 6 amp:power source:specification
110 kg/hr to 700 kg/hr:production capacity:specification
50 ltr 5000 ltr:capacity:specification
5 kg/hr:capacity:specification
100 - 1500 ton per 24 hours:capacity:specification
50-2000 tpd:capacity:specification
500 - 20000 liters:capacity:specification
50 tpd-1000 tpd:capacity:specification
200 ton per day:capacity:specification
1500 lpm to 5000 lpm:capacity:specification
500 liter per minute to 15000 liter per minutes:capacity:specification
superb technologies:brand:specification
up to 100 kg/hr:production capacity:specification
lab model:capacity:specification
mild steel and stainless steel:material:specification
24:capacity:specification
automatic:usage/application:specification
herbs extraction plant,phytochemicals extraction plant:usage/application:specification
20-200 liters:capacity:specification
customized:brand:specification
customized:usage/application:specification
as per your requirement:machine type:specification
hk:brand:specification
extrusion machine:machine type:specification
mix bituman and sand:material:specification
polypropylene - p p:body material:specification
single / three:phase:specification
230 / 415 v/ac:voltage:specification
complete panel:driven type:specification
no installation charges:installation services:specification
one year warranty:warranty:specification
60:voltage:specification
plastic:material:specification
yes:size:specification
coated:surface finishing:specification
gagan international:brand:specification
25 x 20:dimension:specification
electricity and steam:power source:specification
essential oil, flower extraction, spices extreaction.:usage/application:specification
extraction and solvent recovery:usage/application:specification
supertechno engineers & consultants:brand:specification
batch type:machine type:specification
for rice bran oil extraction:usage/application:specification
4meter:size:specification
external:usage/application:specification
20:10:l/d ratio:specification
real ions:brand:specification
200 to 600 ton per month:production capacity:specification
yes:usage/application:specification
fully automatic, semi automatic:automation grade:specification
europack:brand:specification
440:voltage (v):specification
royal blue:color:specification
75 mm:diameter (millimetre):specification
ss 304:brand:specification
manikarn:brand:specification
rgm:brand:specification
health:usage/application:specification
batch extarctor for spent esrth oil recovery:usage/application:specification
cake oil extraction,spent earth oil extraction,palm kernel shell oil extraction,cashew shell oil ext:usage/application:specification
thermoplastic extrusion blown film machine:machine type:specification
affluent extrusion technik pvt ltd:brand:specification
electric & wood fired:power source:specification
what are the applications of distillation distillation is used in industry for a variety of purpose:usage/application:specification
ss304:high tensile strength:specification
stainless steel:design:specification
rkd engineering:brand:specification
2unit/hr:power consumption:specification
gas handling:application:specification
pharmaceutical:usage/application:specification
screw compressor:compressor type:specification
mech tech solution:brand:specification
10 hp 3 phase:driven type:specification
very easy to be installed:installation services:specification
400 mm:die size:specification
mts:design type:specification
mts be400:model name/number:specification
4 core:min finish wire diameter:specification
400 mm basket extruder:size:specification
400 kg:average productivity:specification
ms heavy duty:body material:specification
continue:line speed:specification
700 mm:lay flat width:specification
yes:main drive ac:specification
450 mm:diameter millimeter:specification
2.5 mm:wire diameter:specification
pgm:brand:specification
240v, 50 hz:voltage:specification
10kg:weight:specification
m.s powder coated:body material:specification
75 kg to 500 kg:capacity:specification
65 degree:max temperature:specification
silver dust:dust:specification
poly propylene (pp):body material:specification
single switch raises and lowers the sample racks and creates an airtight seal:electrical unit consumption:specification
315 v:voltage:specification
30 kwh:power consumption:specification
mega-40:model name/number:specification
blue / green:color:specification
230 volts a.c:power:specification
v- tech:brand:specification
china:brand:specification
yes:eye relief:specification
350 mm lip size:die size:specification
made of alloy steel,ground finish,polished and hard chroem plated:body material:specification
according to machine capability:wire thickness:specification
0.8 mm, 1mm, 2mm, 4mm, 6mm, 8mm etc.:die size:specification
floating fish feed:line speed:specification
aprox 400 kgs:weight:specification
multigrain:material to be extruded:specification
pellet feed:usage/application:specification
copper wire use in all motor and pannel function:wire diameter:specification
no warranty:warranty:specification
160mm(l):size:specification
d2:grade:specification
50:weight:specification
cast iron:body material:specification
5hp:power consumption:specification
3 mm sheet thickness:thickness:specification
power coated / painted / chrome plated:surface finishing:specification
40 kgs:weight:specification
used for a quantitative determination of bitumen in hot mix paving mixtures and pavement samples:usage/application:specification
700 kg.:weight:specification
automatic:heating range:specification
wooden packaging:packaging type:specification
to cook oil bearing seeds for better extraction efficiency:usage/application:specification
vinksons:brand:specification
auto:heating range:specification
800kg.:weight:specification
230 volts:motor power:specification
en 41 b:body material:specification
10 feet x 10 feet:dimension:specification
100 - 200 ( kg/hr ):output:specification
pvc:material to be extruded:specification
en 41 b:material:specification
a/s party requirement:size:specification
wire:material to be extruded:specification
60-1000 tdp:capacity:specification
vaagai wood:material:specification
pullet type:driven type:specification
polycarbonate casing to prevent contamination,the machine has all pneumatic cylinders of festo make:finishing:specification
up to 650mm width:lay flat width:specification
52 kw:power consumption:specification
150 kg/h:production capacity:specification
62inches:lay flat width range:specification
twin:screw diameter:specification
340x350x410mm:size:specification
kcmt-101:model name/number:specification
extraction and purification nucleic acid:working capacity:specification
220-230 v:voltage supply:specification
3:power source:specification
350w:power:specification
herbal extration / nutraceuticals:usage/application:specification
55 hp:voltage:specification
25 ft:size:specification
5 - 15 kg/hr:output:specification
50 mm:die size:specification
powder coated:surface treatment:specification
automatic gold refining machine:font roll diameter:specification
automatic gold refining machine:line speed:specification
automatic gold refining machine:purity:specification
upto 100 m / min.:output:specification
ds surveyors private limited:brand:specification
pp and glass:body material:specification
3ph:phase:specification
steam:driven type:specification
1000kg/hour:production capacity:specification
200-240 v:voltage supply:specification
194 kw:machine power:specification
65 kw:machine power:specification
up to 370 kw:power:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width:specification
mirror polishing, matt polishing:finishing:specification
ms,ss:body material:specification
aluminnium:surface finish:specification
vacuum type:driven type:specification
depends upon uses:electrical unit consumption:specification
lab and pharma application:usage/application:specification
4.5 kw:power consumption:specification
manoj engineering:brand:specification
1000 litres/hr:capacity:specification
m.s:material:specification
1:bowl capacity:specification
45 / 55 mm:screw diameter:specification
20kg:weight:specification
380v to 450v:voltage:specification
hand operator:power:specification
5 ltr:bowl capacity:specification
125 h.p:machine power:specification
glass and stainless steel and ms:material:specification
1-2:range:specification
60-80 kg:weight:specification
na:resistance:specification
ms, ss:material:specification
karat24 gold small refining plant:brand:specification
0.25 hp:capacity:specification
supreme fibre glass private limited:brand:specification
sree:brand:specification
pp +metal:body material:specification
ptfe, ss, ms:material:specification
rufouz hitek:brand:specification
10-200ltrs:capacity:specification
5-100 tpd:capacity:specification
paradise udyog:brand:specification
100 -150 kg:capacity:specification
cca:brand:specification
380 v, 50 hz, 220 v, 60 hz:power consumption:specification
100 - 250 kg/hour:output:specification
500 to 1,00,000 litres:capacity:specification
trimurti enterprises:brand:specification
0-40:machine power (kw):specification
415 volt:voltage:specification
green white:color:specification
35 and 55 meters p/h:line speed:specification
lg engineers:model number:specification
100 coils per days:average productivity (kg/hour):specification
10-150 kw:power consumption:specification
7 kg/cm2:pressure:specification
electric power three phase:power source:specification
m.s fabricated:body material:specification
rsew:brand:specification
yes:is it waterproof:specification
230 volts:voltage (v):specification
ms,borosil glass:body material:specification
180-200 kg/hour:output:specification
1600-2000 kg/hour:output:specification
100 to 110 kg/h:output:specification
150 -300 kg/hour:output:specification
1440:speed (rpm):specification
bharat scientific company:brand:specification
6kl:capacity:specification
100-200:output(kg/hr):specification
41 - 80 kw:machine power (kw):specification
320 kg/hour:production capacity:specification
2 to 3 kg gold refine:capacity:specification
35 litre:capacity:specification
170 kg/hour:production capacity:specification
customised:capacity:specification
on request:usage/application:specification
pvc,ld,pp,abs,nylon,hdpe,pet,pc all type of material:material to be extruded:specification
uses for making rods square and round,pillars etc:usage/application:specification
3lph:capacity:specification
ethanol extraction:usage/application:specification
80 ppp (positive pressure processor) spe unit:capacity:specification
upto 40 kw:machine power (kw):specification
refining crude oil:usage/application:specification
two layer extrusion machine:machine type:specification
third phase:phase:specification
shivangi:brand:specification
a-sky instruments:brand:specification
1200 rpm:screw speed:specification
40 nm:nominal torque:specification
13.2 mm:barrel diameter:specification
all:packaging type:specification
20 mm:barrel diameter:specification
1500 m:height:specification
40-80:machine power (kw):specification
compounding, extrusion of biodegradable polymers, plastic recycling, production of films and sheets:phase:specification
25 kg bag:packaging details:specification
packaging:usage/application:specification
mustard cake and groundnut cake processing:usage/application:specification
400kw:power source:specification
supertechno engineers and consultants:brand:specification
food process industry:application:specification
water:medium used:specification
oil:medium used:specification
12 bar:pressure:specification
carry bag, shipping bag, liner:usage/application:specification
normal lubrication and cleaning as per maintenance chart:maintenance:specification
affluent:brand:specification
premium grade steel:material:specification
ultraautosonic:brand:specification
matte polish & mirror:finishing:specification
480 kg:weight:specification
changer:longitudinal automatic:specification
no:beater:specification
straight:spindle taper:specification
no:cross travel:specification
1200x600x1150:dimension mm:specification
ss 304:contact parts:specification
60:rpm of spindle:specification
600x1200:table size:specification
1150 mm:machine height:specification
6:micro drill:specification
standers:design type:specification
mts:standard:specification
400 kg:maximum load:specification
1.2 mm:mass of machine:specification
lavel:floor space:specification
reverse forwerd:rotation:specification
high:spindle power:specification
yes:reverse rotation:specification
advance:feature:specification
120 kg:max table load:specification
variable speed:is it variable speed:specification
pesticides granules making:usage/application:specification
300 kg per hour:capacity:specification
32 nm:spindle torque:specification
400 m m:size:specification
taper:shape:specification
5 mm:thickness:specification
mts-300:model name/number:specification
200kg:weight:specification
300kg/hour:average productivity:specification
90 rpm:line speed:specification
ms prefreed:body material:specification
600mm:roller size:specification
35mm x 45mm:screw diameter:specification
multilayer:layer:specification
venkat enterprises:brand:specification
mechotechhlp:brand:specification
yes:dimension:specification
normal motor or vfd ( variable frequency with drive ) or servo motor:model name/number:specification
slx foshan sailixin machinery manufacturingco., ltd:brand:specification
230 vac:power:specification
1420 rpm:speed:specification
jdc enterprises:brand:specification
epic test:brand:specification
yes:material:specification
metallic:body material:specification
2100mmx 1500mm x 725mm:dimension:specification
20 mm to 180 mm:die size:specification
ms and sa:body material:specification
170:line speed:specification
manal:machine type:specification
single-phase:phase:specification
220v +-10%, 50 hz ac (110v optional):power:specification
yes:capacity:specification
cpvc:material:specification
132:1:screw l/d:specification
20 to 50mm pipe size:size:specification
40 kw main extruder motor:power:specification
conical twin screw imported bimetallic type:screw torque:specification
900 hp:power source:specification
1 mw to 2 mw:power source:specification
steel and aluminium:material:specification
manual / fully automated control systems with scada/plc integration:machine type:specification
cottonseed and other oilseeds:usage/application:specification
nandt engitech:brand:specification
380/415/440:voltage:specification
maruti plastotech:brand:specification
316 kw:power consumption:specification
ravi engineering works:brand:specification
etlet-70:model name/number:specification
5'x2.5'x3':dimension:specification
28":font roll diameter:specification
sls45-cem:model name/number:specification
sdhp 15:model name/number:specification
raw material production capacity 50 kg:capacity:specification
raw material production capacity 100 kg:capacity:specification
to extract oil from seeds,cakes & other sources using solvent:usage/application:specification
natural extraction plant:usage/application:specification
ss 304 ms:steel grade:specification
used for extraction of solvent:usage/application:specification
h:l/d ratio:specification
pp, titanium, glass:body material:specification
1.75 mm/2.85mm:wire diameter:specification
all vegetable oil:usage/application:specification
25hp + 20hp + 1hp:power consumption:specification
900kg:weight:specification
affluent extrusion technik pvt ltd.:brand:specification
30kgs/hr to 165kgs/hr:production capacity:specification
800mm to 2400mm:lay flate width:specification
grey/red/blue:color:specification
titanium, glass, pp:body material:specification
as per requiremnt:color:specification
h r:brand:specification
210 v:voltage:specification
wdg, pesticides, sulphur, emamectin:material to be extruded:specification
3-phase ac:phase:specification
slx foshan sailixin machinery manufacturing co.,ltd:brand:specification
380/50 hz:frequency:specification
polyethylene:plastic type:specification
pp:plastic type:specification
her ph 170 kg:speed:specification
lldpe:tank material:specification
2:weight (ton):specification
4kw:phase:specification
black:color:specification
20ft:thickness:specification
3mm:wire diameter:specification
ms & ss metal:body material:specification
green, as per choice:color:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ):size:specification
lldpe:material:specification
60:frequency:specification
1200kg/hr:capacity:specification
shakti:brand:specification
longer functional life & easy to maintain:features:specification
om extrusion:brand:specification
any capacity from pilot plant upto 5 tons/day or even more:capacity:specification
150 tubes per minute:capacity:specification
100 - 1500 tons per day:capacity:specification
100grams - 1 kg.:capacity:specification
500 - 2000 liter:capacity:specification
100 tpd and above:capacity:specification
50 kg - 350 kg/hr:production capacity:specification
upto 5 tons/day:capacity:specification
casting & aluminium:material:specification
500 liter per minute to 5000 liter per minute:capacity:specification
wintech industries:brand:specification
48/96/144 samples:capacity:specification
chemical:material to be extruded:specification
2000ml:capacity:specification
to make castor oil derivatives, dco, hco, madicated brands:usage/application:specification
fabricated at our workshop:machine type:specification
ptfe:material:specification
dvc:brand:specification
65 mm:screw diameter:specification
18:1:l.d ratio:specification
50 ml:pack size:specification
baheda extract:name of extract:specification
370x550x550 mm:dimensions:specification
monolayer:no. of layer:specification
1,273 kg/hr:throughput rates:specification
online:payment mode:specification
extruder machine:usage:specification
0.25 hp:electric motor:specification
hind heater:brand:specification
53 rpm:screen speed:specification
22 kw:motor power:specification
refining silver:usage/application:specification
single phase:power (kw):specification
1/2 man easy oparated:driven type:specification
50-60:centrifugal effect(%):specification
twin:number of extruder:specification
oleoresin extraction plants:type:specification
0.05 mm:film thickness:specification
110 rpm:screw speed:specification
aba-4545 s:model number:specification
300 mm:film width:specification
3 x 4 inch pcs:cooling blower:specification
10 zone:temp. controller:specification
polished:surface finihsed:specification
stepper/servo:actuator motor:specification
local area:location:specification
offline:mode of service:specification
10.85 kw:total heating load:specification
20 kg/hour:max extrusion output:specification
18.43 kw:total connected load:specification
25 kg/hour:max extrusion output:specification
b k machines:manufacturer:specification
polypropylene:raw material:specification
paint coated:surface finish:specification
1.5 x 2.5 ft (h x w):size:specification
plc:control type:specification
7kg:25":specification
chemical extrusion:usage/application:specification
mts:brand:specification
pesticides chemical:material to be extruded:specification
10*10:dimension:specification
polypropeline:body material:specification
yes:purity:specification
fibre extraction:usage/application:specification
directive drive:driven type:specification
coated:phase:specification
250 kva:automatic grade:specification
l30xb10xh10:size:specification
250 tons:production capacity:specification
35:power consumption:specification
maruti plastomech:brand:specification
pp - hdpe:material:specification
2800 w:power consumption:specification
40kw:power consumption:specification
60hz:model name/number:specification
1200mm:lay flat width:specification
rmb a45 b55:model name/number:specification
wf-b3000:model name/number:specification
0.5 kg to 50 kg capacity:capacity(kg):specification
100 l:capacity(litre):specification
100grm to.2 kg:machine capacity:specification
air blower:blower type:specification
twist:brand:specification
erose:brand:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ):dimensions:specification
16 x 10 x 12 to 18 x 10 x 14 ( l x w x h ) [ feet ]:dimensions:specification
ss316/ss304:material:specification
100 kw:machine power:specification
20 kw:machine power:specification
raw material production capacity 50kg:capacity:specification
laboratory type:capacity:specification
2.5 kg gold dust can be refined:capacity:specification
250 kgs to 5 tpd:capacity:specification
as per requirement ,50 lit /100 lit/200lit:capacity:specification
i6:model name/number:specification
2 kg/hr:capacity(kg):specification
10kg -100 kg:capacity:specification
30 x 25 x 24 feet:dimensions:specification
sant engineering:brand:specification
natural wholes:type:specification
ld, pp, hm, biodegradable:material:specification
manual gold refinery:product type:specification
51/105:screw number:specification
ms:shaft material:specification
300mm:external diameter:specification
75kg/hr:capacity:specification
120:capacity:specification
sri selvaganapathy engg works:brand:specification
mild steel or stainless steel:material:specification
bm:brand:specification
30kg silver refining per batch:capacity:specification
8 x 8:dimension:specification
280kg:weight:specification
high grade corrosion resistant special alloy:body material:specification
special alloy:body material:specification
p sqaure:brand:specification
pvc/wpc:material:specification
5'x3'x10':dimension:specification
4x2.5x8:dimension:specification
1:font roll diameter:specification
1ml,3ml,6ml:spe cartridge size:specification
48,96,144:no of position:specification
6:no of position:specification
soliid:phase:specification
raw material production capacity 1 ton:capacity:specification
raw material production capacity 100kg:capacity:specification
3 to 5 kg/hr:capacity:specification
new tech auto machine:brand:specification
pet:raw material:specification
sk:brand:specification
aluminium , copper, brass, brazing alloys:material:specification
siddharth:brand:specification
ms or ss:material:specification
350:frequency:specification
250 tons per month:production capacity:specification
50 kva:power consumption:specification
150 feet:size:specification
h 8 feet x l15 feet x 3 w feet:dimension:specification
4 feet:font roll diameter:specification
6 hour:line speed:specification
black & white:color:specification
10900 kg:weight:specification
steel and aluminum:body material:specification
c tech instrument:brand:specification
600w:power:specification
380v:power consumption:specification
250 ton per month:production capacity:specification
1000 litre:capacity:specification
digital:automation grade:specification
12":font roll diameter:specification
24x12:dimension:specification
customers:end uses:specification
750mm:lay flat width:specification
1 ml:standard with equipment:specification
solid phase extraction:phase:specification
1 ml, 3ml, 6ml:spe cartridge size:specification
100 psi:inlet pressure:specification
30 hp:power consumption:specification
90 kg:production capacity:specification
30kg:capacity:specification
100 - 150kg/hr:production capacity:specification
1 tpd:packaging size:specification
bag making machine:type of machine:specification
2 kg gold - 10kg silver.:capacity:specification
kurkure & corn puff extruder:machine type:specification
12kw:machine power (kw):specification
80���100 kg of juice per hour:capacity:specification
granules:machine type:specification
plastic recycling machine:machine type:specification
1hp:power source:specification
pp matrial:body material:specification
12mm:sheet thickness:specification
220 v:power consumption:specification
bet:brand:specification
blue, white, gray, green:color:specification
mass transfer lab:usage/application:specification
6 ton:machine weight:specification
blue, white, gray:color:specification
ldpe, lldpe, hm. biodegradable, ld:material:specification
star trace:brand:specification
1 kw:power (w):specification
w650 x l950 x h1500 mm:size:specification
100-200 kg/hr:output(kg/hr):specification
approx 30 kg:weight:specification
0- 100 psi:pressure:specification
ishan:brand:specification
bluish:color:specification
surekh geotech:brand:specification
bitumen testing:product type:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ):dimension:specification
20 - 30 kg /hr:output:specification
40 - 60 kg /hr:output:specification
goyum extruder:model name/number:specification
48 - 75 ( kw ):power:specification
48 - 75 ( kw ):connected load:specification
ld,pp,hm,biodegradable:material:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width range:specification
labh:brand:specification
fully-automatic:automatic grade:specification
ldpe / lldpe:raw material:specification
100 to 500kgs per hour deoends on the size of machine:production capacity:specification
50-200 tpd:capacity:specification
120kg:capacity:specification
100 kg to 5000 kg per day:capacity:specification
9000 lph:capacity:specification
100 - 500 tons per day:capacity:specification
monthly 10 to 15:production capacity:specification
min 1 ton per batch:capacity:specification
standard design,depending on process:capacity:specification
3000 lit, 5000 lit, 6000 lit, 10,000 lit, 12,000 lit:capacity:specification
pestrisides, insecticide chemical:material to be extruded:specification
1carrd 1000 etrrc tan:frequency:specification
96 ppp (positive pressure processor) spe unit:capacity:specification
automatic and semi automatic:automation grade:specification
solvent extraction of essential oils:usage/application:specification
om sakthi:brand:specification
three layer extrusion machine:machine type:specification
bharti udyam:brand:specification
extraction of vegetable oil:usage/application:specification
continuous solvent extraction plants:machine type:specification
stainless steel and glass:material:specification
230 kw:main electric motor hp/kw:specification
26 mm:screw center distance:specification
0-500 rpm:rotate speed range:specification
600 min-1 pp (pellet) + talk (30% - 50%, fine powder):screw speed range pp:specification
250 - 800 (kg/h):throughput range abs:specification
300 - 500 (kg/h):throughput range pellet:specification
300 - 550 (kg/h):throughput range pc hight molecular weight:specification
900 - 1600 (kg/h) pp (pellet) + gf (30%):throughput range pp pellet:specification
700 - 1100 (kg/h) modified ppo (pellet + powder):throughput range modified ppo:specification
siemens:motor make:specification
fruit:part used:specification
nelumbo nucifera:botanical name:specification
50 mm:screw diameter extruder a:specification
2.2 - 1.5mm:material thickness range max:specification
use in jewellery:suitable:specification
50mm:screw diameter:specification
automatic:grade:specification
yongxin technoplas machinery co--:mark:specification
alpha18:model name/number:specification
40 kg/h:throughput:specification
2000 m:height:specification
1900x700x1800 mm:dimension:specification
0-3 mm:max inlet wire diameter (mm):specification
6-9 mm:max inlet wire diameter (mm):specification
2-3 mm:min finish wire diameter (mm):specification
40-80 kw:power consumption:specification
ss316:material grade:specification
8 hour:process time:specification
30 x 15 x 18 60 x 40 x 20 ( l x w x h ):size:specification
90 feet:size:specification
wire manufacturing:usage/application:specification
biodegradable bag making machine:type of machine:specification
mulch film making:usage/application:specification
extraction systems:usage/application:specification
220/415v:voltage:specification
380/415:voltage:specification
solvent extraction process:usage/application:specification
semi autometic:automation grade:specification
ss304/316:material:specification
16*16*12 feet:size:specification
12 ton:production capacity:specification
100 hp:power consumption:specification
380/415v:voltage:specification
ss 2316:material:specification
extraction of oil from oil seeds,rice bran:usage/application:specification
na:machine type:specification
herbal / spices extraction unit:usage/application:specification
gold:refining material:specification
3 kw to 300 kw:power rating:specification
12 kw:motor:specification
535:width (mm):specification
500:height (mm):specification
guduchi extract:name of extract:specification
1 week:service duration:specification
only new:deals in:specification
5 kg/500mg or 5 kg/100mg or 5 kg/10mg:electronic balance:specification
180 kw:power consumption:specification
wshe 50:model:specification
gold refining:usage:specification
50000-500000 shots:die life:specification
0.12 mm:film thickness:specification
250 mm:film width:specification
pp:raw material:specification
450 mm:film width(max.):specification
30:1 l/d:screw ratio:specification
90 mm:paper code o.d.:specification
1 set:day chamber:specification
ss304, ss316:material grade:specification
banglore:location:specification
mm despro engineering:brand:specification
robot coupe:brand:specification
235:length (mm):specification
11:net weight (kg):specification
stainless steel:main body:specification
output: 120 l/h pulp container: 6.5 ltr:capacity:specification
50-3600 rpm:variable speed:specification
coated:finished:specification
0.5 inch:min pipe diameter:specification
wts 110 to wts 700:model name/number:specification
supreme color coated:surface treatment:specification
50l - 2000l:extraction tank capacity:specification
auto mini series:series:specification
45 mm:screw diameter:specification
28:1 l/d:screw ratio:specification
20 hp:driving a.c. motor + inverter:specification
65+85 mm:die diameter:specification
600mm x 1 pc:embossing roller:specification
20 kg/cm:embossing motor:specification
pp series:series:specification
70 mm:paper core i.d.:specification
ppm-35et:model number:specification
35 (mm):screw diameter:specification
2 (hp):cooling blower:specification
aluminium:material to be streched:specification
single die extruder:type:specification
extruder machine:type:specification
50-60 hrc:hardness:specification
online and offline:payment mode:specification
one time:requirement type:specification
8 kw:power consumption:specification
8 nos.:heating zone:specification
candle:filter:specification
torque:winder drive:specification
74 kw:total connected load:specification
225 mm:main extruder hydraulic screen changer:specification
34kw:total consuming load:specification
7 nos.:heat zone:specification
45 mm:screw die:specification
0-80 rpm:screw speed:specification
25 kw:connecting load:specification
2.2:peak output (kg/unit):specification
2 nos:winders:specification
ss 316 and ss 304:material:specification
250-300 kg/hr:max output:specification
40gm:minimum quantity:specification
42d:length:specification
0.9 kw:drive power:specification
310 m:height:specification
motorised:driven type:specification
tiei:model name/number:specification
online/offline:payment mode:specification
fs-aba-1:model name/number:specification
27:screw ld:specification
helical:gear box:specification
0-90 rpm:screw speed:specification
800 mm:niproll size:specification
1 hp:nip drive ac:specification
3:peak output (kg/unit):specification
stainless:material:specification
55-90 kw:power consumption:specification
0-199.9 deg c:digital temp. controller:specification
80-150 kg per hour production:15 feet height widhth -5 foot:specification
rectangular acrylic cabinet:frame type:specification
27.6x24.4x15.4 inch (wxhxd):dimension:specification
box:pack type:specification
34 kw:total consuming load:specification
110-315 kg/hr:production capacity:specification
74kw:total connected load:specification
twin screw:type of extruder:specification
silver recovery:uses of application:specification
48 - 75 ( kw ):power source:specification
automatic:autoamatic grade:specification
2 layer, 3 layer tank optional:layer of tank:specification
automatic:automation:specification
gold and silver & diamond jewellery:refining material:specification
indiamart:location:specification
india:location:specification
30:1:ld ratio:specification
hm,hdpe virgin raw material:material used:specification
hopper loader with dryer:optional item 1:specification
air compressor:ancillary equipment 1:specification
delta,taiwan or equivalent:ac variable drive:specification
-10 degree c to 40 degree c (14 degree f to 104 degree f):working temperature:specification
24 hours per day:working hours:specification
made up of alloy steel:pelletiser unit blades:specification
sjps:model name/number:specification
12/14 mm:vessel double bottom thickness:specification
single cell with two rinse positions:extraction cell tray:specification
20.0in:height (english):specification
50/60hz:hertz:specification
22.1in:depth (english):specification
56.1cm:depth (metric):specification
lcd 8x45 character:display:specification
up to 200 degreec:temperature control:specification
corrosion resistance:features:specification
blue / white:colour:specification
780-850:rotor speed (r/min):specification
36 inches dia:size:specification
1100kg/h:output:specification
3 phase single phase:phase:specification
clay:material:specification
shanghai daiwai:brand:specification
ldpe,hdpe,lldpe:packaging type:specification
55 mm:screw diameter:specification
55kw:power consumption:specification
20 micron:thickness:specification
no:maintenance:specification
140kw:power consumption:specification
194 kw:power consumption:specification
194kw:power consumption:specification
1200 mm:lay flat width range:specification
ss316/304:material:specification
systems:usage/application:specification
120kw:power consumption:specification
35kw:power consumption:specification
we offer extruders for pvc , xlpe. ,pe,,nylon, pp,teflon coating in various sizes ranging 25 mm to 175 mm screw diameter:material:specification
solvent extraction plant ,cattle feed plant:application:specification
apollo:brand:specification
450:voltage:specification
190kw:power consumption:specification
625 kg/h:production capacity:specification
ocean internatinal:brand:specification
125kw:power consumption:specification
146kw:power consumption:specification
155kw:power consumption:specification
150kw:power consumption:specification
hdpe, ldpe, pe:material:specification
65kg/hr:capacity:specification
athena instruments pvt. ltd.:brand:specification
25 x 20 x 16 to 30 x 25 x 24 ( l x w x h ) [ feet ]:dimensions:specification
for masterbatch and compounding:screw design:specification
aarkay extruder:brand:specification
abb pp pc nylon rp pa pa66 pet pe ld hdpe:screw design:specification
*aar kay:brand:specification
exuding machine:machine type:specification
double screw:screw design:specification
upvc pvc window profile:plastic processed:specification
parreler twin screw & conical twin screw:screw design:specification
single screw extruder:machine type:specification
twin screw and twin conical:screw design:specification
viraj extrusion and keshar extrusion:brand:specification
hindustan plastic:brand:specification
anton paar:brand:specification
ss309:material grade:specification
6 kw:machine power (kw):specification
electrical or motorized:type of testing machines:specification
65/18:screw number:specification
multitech:brand:specification
bitumen extract:type of testing machines:specification
sci-tech:brand:specification
national engineering works:brand:specification
7kw:machine power (kw):specification
basket extruder machine:machine type:specification
pvc resin pipe extruder:plastic processed:specification
solvent extraction plan:machine type:specification
5 kg:steam pressure:specification
1 rpm:rotor speed:specification
3 hours:drying time min:specification
herbal extrac drying:usage/application:specification
1250x1250:drum size:specification
1250:diameter:specification
70:max temperature:specification
singallayer:layer:specification
pp, hd, ld:body material:specification
polypropoleane:material:specification
415 volt 50hz:voltage:specification
frontline:brand:specification
polyproplyne:body material:specification
shakti enterprises:brand:specification
used of extraction of spices, herbals, alkaloids & natural colours & gums:usage/application:specification
2000 l:capacity:specification
120 degree c:temperature:specification
use in herbal and solvent extraction plant and phytochemical industry for recovery of solvent with i:usage/application:specification
sls:brand:specification
yes:automatic grade:specification
as per requetment:size:specification
220 voltage:voltage:specification
ac:power consumption:specification
440 v ac:voltage:specification
350 kg:weight:specification
semi aiutomatic:design type:specification
semi extraction plant:machine type:specification
pesticide insecticide:features:specification
mts 21:brand:specification
approximately 100:weight:specification
wdg, pesticides, emamectin, sulphur:material:specification
customize both:phase:specification
flower bud:part used:specification
aritha extract:name of extract:specification
automatic,semi auto:auto grade:specification
36 x 16 x 21 inch:machine body dimension:specification
20 to 630 mm:molding range:specification
600*600*700mm:dimensions:specification
color coated:surface finish:specification
20-40 hr:production:specification
75 inch:screw diameters:specification
11 kw:heating power:specification
3" x 2pcs:cooling blower:specification
1:color printed:specification
85:printing speed(max)(m/min):specification
700 mm:printed length(mm):specification
18.5~110kw:power consumption:specification
pvc/wpc for conical twin screw extruder:raw material:specification
2:number of layer:specification
hhpep series:series:specification
42 kw:whole power required:specification
600 x 220 x 420 cm:overall dimension:specification
450 mm:roller width:specification
40 to 250 mm:film width:specification
1 hp:co- extruder motor a.c.:specification
135 mm:double profile die size:specification
280 v:input voltage:specification
30 to 75 mic:film thickness:specification
5 kw (a.c. freq.):motor drive:specification
1 hp:blower:specification
1 hp:additional take up a.c. motor:specification
360 cm:take up height:specification
130/180 mm:single profile die size:specification
200 kg/hr:max capacity:specification
elshaddai engineering equipments:elshaddai:specification
lab equipments:manufacturer of:specification
80 (mm):ff screw diameter:specification
3 (kw):ff motor power:specification
65 inch:screw diameters:specification
30-50 hr:production:specification
industrial:usage:specification
am2pm:brand:specification
yes:customised:specification
on request:model name/number:specification
28 - 280 ( kg/hr ):production capacity:specification
19.6 mm:screw diameter:specification
150 ml:max volume extraction cup:specification
5 to 15 g:sample quantity:specification
50 to 75%:solvent recovery:specification
30 to 100 ml:solvent volume:specification
100 to 260 degree c:working temperature:specification
700 mm:width:specification
50gm:min batch quantity:specification
600mm:width:specification
max 40 hp:power comsumption:specification
100 kg/hr:min capacity:specification
71mm:screw dia.:specification
reactor:type:specification
20 inch height * 16 inch diamtere:dimension:specification
0.15-0.25 unit per kg:power consumption:specification
industrial:application:specification
ms,ss:material:specification
electric:powe source:specification
masterbatch extruder machine:model name/number:specification
co-rotating twin screw extruder:title:specification
2-3 tones:weight of machinery:specification
1.5 liters per hour:diesel consumption:specification
up to 75%:micelle concentration:specification
5-52 rpm:screw speed:specification
11.25 kw:motor power:specification
20 mm:pipe range single die:specification
19 mm:pipe range twin die:specification
as per product:packaging size:specification
6 hour:process time:specification
400 v:power supply:specification
steel:material of construction:specification
1100 - 2300 mm:maximal width of finished products:specification
2900 rpm:max rotating speed:specification
0-50 , 50-100, 100-300, 300-600:production capacity (kg per day):specification
0-3 mm, 3-6 mm, 6-9 mm, 9-12 mm:max inlet wire diameter (mm):specification
22:1:l/d ratio:specification
2 l/min:cooling water:specification
29:number of programs:specification
ss, alloy steel, etc.:material:specification
450 kg/hr:capacity:specification
corrosion proof:features:specification
wooden box:pack type:specification
consulation services:deal in:specification
provide services according to the need of people:deal:specification
ll / ldpe / hm / hdpe:polymer:specification
20 to 150:micron range:specification
550mm - 1600mm:lay flat range:specification
45 mm to 150 mm:diameter::specification
100 m/min:linear speed of machinery:specification
80-100:machine power (kw):specification
100-120:machine power (kw):specification
closed circuit works by vacuum:transfer of acid:specification
180 kg:weight:specification
7-9 kw:power consumption:specification
hwvm - 12 kg:model name/number:specification
gearbox:driven type:specification
automatic:design:specification
industrial/commercial:application:specification
30-75kw:main motor power:specification
used for gold separation.:usage/application:specification
h 24" * w 14" * l 24":dimensions:specification
16 kw:total connected load:specification
1 hp auto cut:compare sure:specification
115:volume(l):specification
155:capacity(kg):specification
1008:g-force:specification
1800x1050x1140:overall size(l*w*h) (mm):specification
200kg:72x4x4inch:specification
240 v:input voltage:specification
50 kg/h:output:specification
40 h.p:power required:specification
within 1 week:duration:specification
140kg/h:capacity:specification
2:number of cookie per row:specification
35mm:screw die:specification
solace terran:brand:specification
48kw:power consumption:specification
146 kw:power consumption:specification
145kw:power consumption:specification
n maintenance:maintenance:specification
ss 304 / ss 316 / ms:material:specification
15&16:electrical unit consumption:specification
170kw:power consumption:specification
blue, white. gray. green:color:specification
for all purposes:usage/application:specification
c.c.p consultant:brand:specification
500 ton per month:production capacity:specification
500 kva:power consumption:specification
6 mtr finish:size:specification
26:1:l/d ratio:specification
mildsteel:material:specification
55hp:voltage:specification
144 ppp (positive pressure processor) spe unit:capacity:specification
9999+:purity:specification
9,500,000:voltage:specification
pp + metal:body material:specification
solvant extraction:usage/application:specification
horizontal:inclination:specification
10hp:motor power:specification
380/420:voltage:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x x h ):overall dimension:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h):overall dimension:specification
50 kg/hr t:production capacity:specification
174kw:power consumption:specification
1 to 10 kw:machine power (kw):specification
vasai:service location:specification
10kw:machine power (kw):specification
14kw:machine power (kw):specification
gas fired wood fired:power source:specification
commercialy:usage/application:specification
11.5kw:power:specification
5 x 5 x 5 to 22 x 8 x 12 ) l x w x h ):overall dimension:specification
apex:brand:specification
museco:brand:specification
palak machinery:brand:specification
75 kwh:power consumption:specification
borocillicate 3.3 glass:material:specification
10l - 300l:size:specification
2 year:warranty:specification
jay-tex:brand:specification
5 x 5 x 5 to 22 x 8 x 12:overall dimension:specification
3 hp 3-phase motor:motor:specification
30mm:size:specification
new:design:specification
micro mpt tse-30:model name/number:specification
5 feet ( h ):dimension:specification
as per the application need:power:specification
gold and silver:material:specification
82kw:power consumption:specification
titanium:steel grade:specification
as per coustomer size:weight:specification
52kw:power consumption:specification
10 micron:film thickness:specification
6hp:power:specification
5rpm:speed:specification
automation / semi automatic:automation grade:specification
plastic:body material:specification
2.5 kg:wire thickness:specification
20 mm minimum:wire diameter:specification
as per machine:weight:specification
ms material:body material:specification
pp, ms:body material:specification
polypropylene homopolymer:body material:specification
approx. 50 kw:power consumption:specification
45 / 55 / 65 mm (customized):screw diameter:specification
abb - switzerland or equivalent:main motor:specification
ldpe, lldpe, hdpe, caco3, virgin raw material:material:specification
50 hertz:frequency:specification
15 hp:motor:specification
silver refinery:model name/number:specification
derive the extracts from various herbs, seeds, leafs, twigs, roots, fruits, buds, bark and kernel.:usage/application:specification
9,300,000:voltage:specification
200 kg/hour:capacity:specification
skfe-004:model name/number:specification
sheet protector rawmaterial:usage/application:specification
60kw:power consumption:specification
srs jewelkon:brand:specification
pu:material:specification
herbal extraction process:usage/application:specification
seiko:brand:specification
2.2kw:power:specification
semi automactic:machine type:specification
blown flim plant:usage/application:specification
fixed connection, supply via drive unit:voltage:specification
semiautometic:machine type:specification
ysage:usage/application:specification
mech o trch llp:brand:specification
essential oil distillation plant:usage/application:specification
ss 304/316:material:specification
3 phase:power source:specification
42kw:power consumption:specification
delta or crompton ac drive:main drive ac:specification
g.g industries:brand:specification
168 kw:power consumption:specification
50kw:power consumption:specification
46kw:power consumption:specification
200kw:power consumption:specification
stainless steal:material:specification
220 volts:voltage:specification
10 feet x 4 feet:dimension:specification
fabricated body:material:specification
wooden case packing:packaging type:specification
single phase 220 volts:power:specification
gii:brand:specification
vihaana:brand:specification
415v:power consumption:specification
60 degree celsius:heating range:specification
220 bolt:power:specification
singhal phase:phase:specification
40":font roll diameter:specification
1:line speed:specification
singal fess:phase:specification
42":font roll diameter:specification
1 to 2 hp:motor:specification
st.steel:material:specification
1/2" - 12":size:specification
950mm adjustable:center height:specification
1410 x 790 x 1580:overall dimensions (lxbxh) (mm):specification
single screw:screw:specification
20 ratio 1:ld ratio:specification
water,htf,air:barrel cooling system:specification
5 to 10 mm:sheet thickness:specification
304, 304l, 316, 316l:material grade:specification
60 to 160 rpm:speed motor:specification
gurukrupa enterprise:brand:specification
plastic:pen material:specification
sset 52/18v:model:specification
10 kg ,20 kg ,50 kg,100 kg:available capacity:specification
200kg/hr:output range:specification
mini series:series:specification
hdpe:raw material:specification
mini-45:model no:specification
9 kw:heating power:specification
1/2" x 1 pc:cooling blower:specification
4 zone:temp. controller:specification
40 kw:whole power required:specification
8.5 x 2 kw:heating power:specification
sfc-isr-02:model number:specification
vertical:type:specification
80 kg/hour:capacity:specification
socs plus:brand:specification
d:finish:specification
semi automatic:automation type:specification
scs 6 r:model:specification
20d:model:specification
semi automatic:type:specification
2 nos.:number of extruder:specification
120 kg/hr:peak output:specification
8.7 kw:heater capacity:specification
from 30 to 100 ml:solvent volume:specification
from 0 to 999 minutes:immersion time:specification
24:center distance:specification
25 micron:thickness of film:specification
20:1:l/d ratio:specification
0.25 kva:power:specification
1000 - 2500 kg/hr:output (kg/hr):specification
1100 mm:niproll size:specification
60 kw:connecting load:specification
25 kw:heating load:specification
5.2:peak output (kg/unit):specification
100-200 mm:max bag length:specification
twin screw gear boxes:product:specification
10mm:shell thickness:specification
1-100 mm:max bag length:specification
200-300 mm:max bag length:specification
0.75 hp:driving motor power:specification
0.33 kw:winder motor:specification
2.0 x 2.0 x 2.8 meter:space requirement ( lxwxh):specification
titanium:reactor material:specification
vmosa 3040-1000,vmosa 3045-55-1250,vmosa 3050-60-1500,vmosa 3050-60-1700:model:specification
650-1000,750-1250,750-1500,900-1700 mm:film width:specification
2 station winder:winder:specification
30 ul-1000 ul:process volume:specification
#ERROR!:recovery rate:specification
automatic, semi-automatic:grade:specification
cv<=3%:stability:specification
uv sterilization:pollution control:specification
si 90:model number:specification
37-45kw:power of main motor:specification
up to 2500 ton per day:production capacity:specification
soybean,sunflower,cottonseed,mustard,groundnut,rice bran etc:suitable oil:specification
extraction process:plant process 2:specification
desolventising process:plant process 3:specification
pouch packing:primary packaging option 1:specification
big tin packing:primary packaging option 3:specification
siemens,japan or equivalent:plc control:specification
about 100 kw:connected load:specification
zv72:model number:specification
40 kg/hr:maximum output:specification
om-3050-60-1500:model number:specification
3 layeer die:die type:specification
40 inch:lay flat width and diameter:specification
twin screw:extruder type:specification
seed preparatory process:plant process 1:specification
distillation process:plant process 4:specification
meal finishing process:plant process 6:specification
bottle packing:primary packaging option 2:specification
10000 mm:height requirement:specification
siemens,japan or equivalent:hmi:specification
bonfiglioli - italy or equivalent:main gear box:specification
omron,japan or equivalent:digital temperature controller:specification
schneider - france or equivalent:switch gears:specification
up to 90 percentage:working humidity:specification
20 kw:power consumption:specification
8:channel:specification
up to 550 kg/hr:output up to depends on material:specification
160-240 kg/hr:capacity:specification
220 kg/hr:maximum output:specification
this machine is giving production with using raw material as pvc resin and pvc scrap also:advantage:specification
450 kg:net weight:specification
(uniphase) 220 v 50-60 hz:power supply:specification
45mm:size:specification
27 l/d:screw ratio:specification
twinex 78:model:specification
multi color:color:specification
boston matthews:brand:specification
pp, glass:material:specification
silver refining:usage:specification
0.24 - 0.26 units / kg:power consumption:specification
specifiq:brand:specification
108.5-190.5 kw:power consumption:specification
20 kg/1 days:capacity:specification
paint coated:finishing:specification
rubber:material to be extruded:specification
3 sec:response time:specification
70 micron:thickness	 o:specification
45 h.p:power required:specification
for washing:usage:specification
breakfast cereal corn flakes:material to be extruded:specification
extrusion machine:type:specification
reaction purpose:usage/application:specification
non organic:is it organic:specification
455 kg/h:production capacity:specification
5 x 5 x 5 to 22 x 8 x 12 ( l x w x h ):power consumption:specification
monolayer blown film machine:type:specification
30kg/hr:power consumption:specification
monolayer blown film making machine:machine type:specification
mask making machine:type:specification
180kw:power consumption:specification
78kw:power consumption:specification
142kw:power consumption:specification
as per application:dimension:specification
inlet 75 psi:pressure:specification
it is a chromatographic technique used to prepare samples:usage/application:specification
pharmaceutical / chemical industry:usage/application:specification
380 / 415:voltage:specification
385/420:voltage:specification
filim packaging:packaging type:specification
extraction plant:herbal:specification
extraction process:usage/application:specification
as per size of refinery:dimension:specification
it depends:line speed:specification
semi auto:machine type:specification
22 x 8 x 12 ( l x w x h )mmm:overall dimension:specification
79kw:power consumption:specification
20kw:power consumption:specification
175kw:power consumption:specification
twol layer:layer:specification
172kw:power consumption:specification
with two decades of experience in the field, we specialize in solvent extraction plants that consist:usage/application:specification
1:dimension:specification
manul:automatic grade:specification
edible oil extraction from soybean, sunflower, rice bran, cottonseed, etc.:usage/application:specification
48"x48"x72":dimension:specification
10l-300l:size:specification
continuous solvent extraction plant is an efficient platform to extract edible oil:usage/application:specification
admech:brand:specification
48":font roll diameter:specification
5o hz:frequency:specification
starfish:brand:specification
350 mm to 650 mm:lay flat width:specification
30:1:screw l/d:specification
heat exchanger bimetallic screw & barrel set:optional item 2:specification
two station surface winder:optional item 3:specification
440 volts,50 hz,a.c.,three phase with neutral (can also be designed as per specific requirement):power supply:specification
500 rpm:rotate speed range:specification
65-132mm:screw diameter:specification
37.5kw:drives:specification
25 : 1:l.d. ratio:specification
extraction of solid and semisolid samples:for use with:specification
compatible with a wide range of organic and aqueous solvents:extraction fluids:specification
34kg:weight (metric):specification
14.0in:width (english):specification
35.6cm:width (metric):specification
menu operated. method and schedule editor and storage.:keyboard:specification
pan india:plant location:specification
twin screw barrel:design:specification
twin screw barel:design:specification
20 mm to 400 mm pipe size:range:specification
1440:rpm:specification
1kw monophase compressor:cooling unit:specification
180 v:input voltage:specification
800mm x 1000mm x 1150mm:dimension:specification
20-35 kg/hr:output:specification
solvent extraction groundnut refined oil:product type:specification
45%:protein oil max:specification
sle-cct-19:product code:specification
pharma pellets:material to be extruded:specification
juice:material to be extruded:specification
automatic, semi-automatic:automation grade:specification
0-1 mm, 1-2 mm, 2-3 mm:min finish wire diameter (mm):specification
vallabh:brand:specification
140-200 kg/hr:capacity:specification
125 kg/hr:capacity:specification
5 - 9 feet:height:specification
sant engineering industries:power(w):specification
65mm:screw diameter:specification
pvc, pe, lszh, xlpe:material to be extruded:specification
>120:machine power (kw):specification
own brand:brand:specification
extraction:groundnut:specification
2.50%:sand silica max:specification
16%:fiber max:specification
10 per month:capacity:specification
48-75 kw:power consumption:specification
low:power consumption:specification
50 - 100 kg:weight:specification
15 inch full color, touch screen mosaic microprocessor control:touch screen:specification
55-125 ( kg/hr ):capacity:specification
25 - 80 ( kg/hr ):output:specification
20 x 5 x 9 to 28 x 8 x 14 ( l x w x h ):dimensions:specification
150 - 300 ( kg/hr ):capacity:specification
0-3 mm, 3-6 mm, 6-9 mm:max inlet wire diameter (mm):specification
0.01-7ml/min:flow rate:specification
hand operated:operation mode:specification
zip lock extruder:type of machine:specification
mono yarn extrusion plant:service type:specification
solvent extraction plant:product type:specification
twin screw extruder:type of extruder:specification
rice bran:raw material:specification
28x28:model number:specification
screw extruder machine:type:specification
two layer:no. of layer:specification
mild steel:product material:specification
aba three layer extruder machine:type:specification
45mm:bag width:specification
50 kw:machine power (kw):specification
cable extrusion:type:specification
2kl:capacity:specification
200 l:capacity(litre):specification
500ltrs:capacity:specification
100 tpd to 1000tpd:capacity:specification
120/240 v ac:voltage:specification
40 x 32 x 35 cm:size:specification
determination of carbon and sulfur in cement, ores, coke, catalysts, ceramics, graphite, refractorie:usage/application:specification
powder-coated steel & abs housing with magnetic bead separation module:material:specification
3 k.w:heating range:specification
2000 w:power (w):specification
99.90%:purity (%):specification
150kg:weight (kg):specification
box:packing type:specification
75kw:power consumption:specification
415 v:material:specification
color coated:surface treatment:specification
132 kw:power:specification
pp & titanium:material:specification
oil:usage/application:specification
72kw:power consumption:specification
20 ton:capacity:specification
to efficiently produce insulated and sheathed electrical cables:usage/application:specification
1 +1 year extended warranty:warranty:specification
200v:power:specification
700 ton:capacity:specification
engineering:design type:specification
bet':brand:specification
3 phase 50 hz:power:specification
food:usage/application:specification
s.s and m.s:material:specification
metal pp:body material:specification
rajesh india:brand:specification
yes:motor power:specification
yes:phase:specification
1800mm x 1800mm:dimension:specification
1ph or 3ph:phase:specification
used for extraction of spices, herbals, alkaloids, natural colors and gums:usage/application:specification
120 kw:power (kw):specification
440 v:voltage (v):specification
2000 kg/hr:production capacity:specification
500 ml:pack size:specification
rhizome:part used:specification
root:part used:specification
1300 x 1850 x 960 mm (l x d x h):dimensions:specification
315 mm:pipe diameter:specification
laboratory:type:specification
automatic,semi automatic:auto grade:specification
nitrogen:gas:specification
yes:accuracy:specification
220-250 v:voltage:specification
rotameters-2nos. (one each for solvent & solute):flow measurement:specification
cv<5%:stability:specification
1~10:throughput:specification
ambient temperature~120 degreec:healting for lysis tube:specification
0.03 - 0.22mm:film thickness:specification
1000mm adjustable:center height:specification
12.5 (hp):main motor:specification
6 (in):pelletizer size:specification
candour technology:brand:specification
150-600 mm:film width:specification
43 hp:connected load:specification
40 & 45 mm:screw diameter:specification
500-800 mm:film width:specification
jewellery industry:usage:specification
i = 2.5 - 5:transmission:specification
44-64:screw l/d ratio:specification
62.4 mm:screw diameter:specification
blue,white,gray:color:specification
auto acid filling:feature:specification
yes:icmr(govt) approved:specification
well plate 96:samples:specification
plate spe:96 well:specification
11 to 56 kw:main drive power:specification
awg 20 - 6 (0,5 - 10 mm2):typ conductor size:specification
solid/ flexible:conductor type:specification
7.5 hp:main drive:specification
2 nos.:heating zone:specification
astm:standard:specification
99.50%:purity:specification
30 pcs/minute:capacity:specification
extractor:product type:specification
ss304:material grade:specification
bio-degradable films,ldpe / lldpe / hdpe / hm/ pp/ bopp/ polyster films,paper and pvc film,bio-degradable films,ldpe / lldpe / hdpe / hm/ pp/ bopp/ polyster films,paper and pvc film:plastic processed:specification
ml 32:model no:specification
28:1:l or d ratio:specification
30-40 kg:output per hr:specification
high:quality:specification
chemical process:process:specification
aba se3hr 1350-45/55:model number:specification
550-1250 mm:layflat width:specification
beta b:model name/number:specification
3800 mm:length:specification
1255 m:height:specification
1 - 10 kg/h:max output:specification
1000w:power:specification
up to capacity:power consumption:specification
2 to 90 mm:screw diameter:specification
for food processing:general use:specification
35 mm:screw die:specification
0.9 kw:power:specification
morinda citrifolia:botanical name:specification
raphanus sativus:botanical name:specification
vacha extract:name of extract:specification
9 min:result time:specification
2 hp:power consumption:specification
32mm:screw size:specification
oorja system:brand:specification
1.03kg / l:density:specification
free stand:installation type:specification
rotary extractor:type:specification
220/380v:voltage:specification
mel / ex / 50:model name/number:specification
used for gold refining:usage/applications:specification
double scrubber:no of scrubber:specification
limelightit:brand:specification
wifi:network:specification
servotech:brand:specification
frk making machine:fortified rice machine:specification
industry:usages:specification
mumbai:service location:specification
dispersion of pigments and additives into thermosetting resins for powder coatings:usage/applications:specification
online:paymnet mode:specification
180-240 kg/hr:production capacity:specification
spiral:die type:specification
8kgs:peak output:specification
two layer:type:specification
28x2x8mm:dimension(l*w*h):specification
yes:rust resistance:specification
25:total electrical (kw):specification
water:barrel cooling medium:specification
online \offline:payment mode:specification
2.1x0.88x1.2 m:dimensions:specification
machenical:driven:specification
3000 kg/shift:capacity:specification
mp/ex-gf-dan-110:model name/number:specification
38mm:screw diameter:specification
syn/mbgp/125 ac:model number:specification
syn/mbgp/100 ac:model number:specification
550 kg/hr:capacity(kg/hr):specification
aba three layer extrusion blown film machine:name:specification
100 litre:storage capacity:specification
aba two layer extruder machine:type:specification
rotating extruder machine:type:specification
35mm:bag width:specification
th-044:model:specification
refining plant:usage:specification
high pressure:pressure:specification
low pressure:pressure:specification
medium pressure:pressure:specification
blue base:color:specification
450 v:voltage:specification
one:phase:specification
45/55 mm:screw diameter:specification
plastic industry:usage/application:specification
nc11:model:specification
pharma , chemical , food:usage/application:specification
220 v, 50 hz:voltage:specification
430x350x450mm:dimension:specification
karthik:brand:specification
own manufacturing:brand:specification
3x2x6:dimension:specification
99.9 & 99.99 %:purity:specification
0.5 - 5 hp:power:specification
mts-915:model:specification
950 rpm:speed:specification
100inch:screw length:specification
140mm:screw diameter:specification
metal:reactor material:specification
1 kw monophase compressor:cooling unit:specification
no smell,no smoke:exhausted gas:specification
paint coated:surface:specification
27:01:00:ld ratio of screw:specification
e.n. 41b nitrated grove feed:berrel and screw:specification
75 mm - 150mm:die size:specification
packaging films such as agricultural seed,liquid, electrostatic protection film and many others.:usage:specification
0.25 kw:cutter rate:specification
gi - 50:model name:specification
90 rpm:screw speed:specification
1400 rpm:speed:specification
415 c approx 25 a tpn:mcb for drive:specification
stainless steel food grade:material:specification
r:list no.:specification
40mm:thickness:specification
plastic film:usage:specification
pp and teflon:material:specification
soybean oilseeds:raw material:specification
solvent extraction using hexane:extraction method:specification
advanced horizontal extractor, desolventizer-toaster, distillation and solvent recovery s:technology:specification
includes training, maintenance, and a reliable supply chain for spare parts:after-sales support:specification
rapeseed oilcake:raw material:specification
advanced horizontal solvent extractor and desolventizer-toaster, evaporation systems, and:technology:specification
nnt-se-rs:model number:specification
3hp:power:specification
iso, ce and asme compliance for durability and reliability:design standards:specification
1,3 up to 3m3 /h:flow rate:specification
ion exchange resin:treatment:specification
manual / fully automated control systems with scada/plc integration:automation:specification
mild steel as well as high-grade stainless steel for durability and corrosi:material of construction:specification
iso, ce and asme-certified designs for durability and reliability:design standards:specification
titanium:power soreactor material	urce:specification
horizontal extractor, desolventizer-toaster, distillation systems, and meal conditioning:technology:specification
mild steel as well as high-grade stainless steel for corrosion resistance a:material of construction:specification
meets global standards for emissions and waste management:environmental compliance:specification
25hp:motor power:specification
5 inch:diameter:specification
seven seas enterprise:manufactured by:specification
(kg/9h),3kg:refining capacity:specification
r12:dimension:specification
80 degree c:max temperature:specification
grooved nozzles:connections:specification
3 zone:heating zone:specification
7 kw:connecting load:specification
17 kw:heating load:specification
ex-j type:extractor type:specification
energy-efficient machinery for reduced operational costs:power consumption:specification
manual / fully automated systems with scada/plc integration:automation:specification
box:packagingtype:specification
55 - 125 9 kg/hr ):production capacity:specification
55 - 125 ( kg/hr ):production capacity:specification
55 - 125 ( kg/hr ):capacity:specification
40-100 kg/hr:capacity:specification
coating on 0.2 to 2 mm bare condutor to 50 mm bunched.:capacity:specification
pvc, pp:material:specification
1ph/3ph:phase:specification
depends on machine capacity:voltage:specification
depends on capacity of machine:dimension:specification
approximately 500-800 kg (varies by design):weight:specification
220-440 volt:voltage:specification
5-125mm:thickness:specification
2 - 3 hp:motor:specification
320 - 440v:voltage:specification
80 - 150 mm:screw diameter:specification
10 - 100 micron:film thickness:specification
20 - 100 ( micron ):film thickness:specification
10 - 100 ( micron ):film thickness:specification
28 - 280 ( kg//hr ):production capacity:specification
146 - 194 kw:power consumption:specification
600 - 1250 to 11400 - 2100 ( mm ):lay flat width range:specification
10 - 100 mm:screw diameter:specification
20 - 150 ( micron ):range of thickness of wall ceiling panels:specification
146 - 194 kw:voltage:specification
20 - 150 ( micron ) [ as per customer ]:range of thickness of wall ceiling panels:specification
80 - 150mm:screw diameter:specification
10 - 100 micoron:film thickness:specification
35-45 kw:power consumption:specification
35 - 45 kw:power consumption:specification
10 - 100 ( micron ):thickness:specification
250 degree celsius:heating range:specification
provided:installation services:specification
4.5 liter:capacity:specification
high gred plastic:body material:specification
plc hmi base:features:specification
use for pvc/upvc/rpvc/cpvc pipe making machine:usage/application:specification
compression testing machine:type of testing machines:specification
designed to extrude samples having �� 4��� and 6���:usage/application:specification
999.90%:purity:specification
metal:material compatibility:specification
1.5 kw:power:specification
semiautomatic:working type:specification
for making window glass seal profile:usage:specification
100 micron:thickness of film:specification
62.1 kw:total connected load:specification
30 micron:thickness of film:specification
5 to 15 kg:production capacity:specification
75 x 59 x 62 cm; 40 kg:product dimensions:specification
e m f:brand:specification
automatic pc compatible auto sequencing regular six place solvent extraction system:description:specification
single die:die:specification
90 kg/hr:max output:specification
up to 190 kg/ hr:production capacity:specification
15gm:sample weight:specification
80%:solvent recovery:specification
rajesh india manufacturing private limited:brand:specification
1hp 440 voltage rpm 1440:vacuum pump:specification
230 - 280 v:voltage:specification
energy-efficient systems to minimize operational costs:power consumption:specification
adheres to international safety and emission standards:environmental compliance:specification
iso-certified , ce and adhering to asme regulations:design standards:specification
more than 500 kg/hr:capacity:specification
1-200 kg:capacity:specification
20-300 tons per day:capacity:specification
1-2 kg.:capacity:specification
10-16 samples per run:no of unit to be tested:specification
28 - 280 ( kg/hr ):power consumption:specification
ptfe rod extruder:capacity:specification
300 ton perday:capacity:specification
iron:product type:specification
20 ton/day:capacity:specification
12 lpm:capacity:specification
30 to 500 tons per day:capacity:specification
cgt140:model name/number:specification
cgt200:model name/number:specification
cgt550:model name/number:specification
cumin oleoresin extraction:machine type:specification
rice bran solvent extraction plant:usage/application:specification
thymus vulgaris:botanical name:specification
96 postions:capacity:specification
automatic and semi automatic:machine type:specification
cross-flow type:air-flow direction:specification
steel:material to be coated:specification
monolayer:layer:specification
coating wire extruder:machine type:specification
nylon:raw material:specification
175 kg:capacity:specification
co rotating:screw type:specification
250 kg to 5tpd:capacity:specification
three layers:number of layers:specification
gold:material processed:specification
aqua regia:processing method:specification
herbal extraction plant:usage/application:specification
500 kg per day:capacity:specification
helix:company:specification
18:1:l/d ratio:specification
236 m/min:max. speed:specification
1200 mm:bed width:specification
1200 mm:bed height:specification
50 kg - 350 kg/hr:capacity:specification
nilkanth:screw design:specification
nilkanth:brand:specification
depends on plant capacity:power source:specification
depends on plant capacity:voltage:specification
semi automatic:usage/application:specification
50 kg - 350 kg/hr:average productivity:specification
n:weight:specification
n:usage/application:specification
n:phase:specification
naa:driven type:specification
n:pressure:specification
n:temperature:specification
n:frequency:specification
naa:power source:specification
mech o tech llp:model:specification
naa:na:specification
top loading:machine type:specification
top loading:design type:specification
manual:power source:specification
powder coated:finishing:specification
65x40x36 cm:size:specification
hand operated:type:specification
aba series:series:specification
white:colour:specification
0.25 hp:motor power:specification
600 mm:width of lay flat:specification
3.1 x 2.7 x 4.9 meter:space requirement ( lxwxh):specification
35/45 mm:screw diameter:specification
3.5 kw:air blower:specification
80-130kg/hr:capacity:specification
20-80 mm:sheet thickness:specification
4 kw:heater capacity:specification
silver filter:filter system:specification
25.5 kw:connected load:specification
48"60:size:specification
51 h.p:power required:specification
20 micron:film thickness:specification
800 mm:nip roll size:specification
40 mm:screw barrel size:specification
2kw:#gold refining machine 5kg:specification
24 kg/h:output:specification
16":maximum size:specification
38":size:specification
cost effective:features:specification
single scrubber:no of scrubber:specification
for epe cutting:usage:specification
nitride treatment:surface treatment:specification
28 kg/hr:max. extrusion output:specification
80 mm:take up speed:specification
2.0 x 2.0 x 3.5 m:space requirement:specification
15 hp:main motor drive power:specification
2.25kw:power load:specification
45 kg/hr:peak output:specification
27.6x24.4x15.4 inch (wxhxd):size:specification
38crmoaia/42crmoaia/w302:base material:specification
15hp:motor:specification
6000 gms:capacity:specification
1 ph:phase:specification
new:latest technology:specification
100kg:ouput ::specification
32 kw:power:specification
maharashtra:location:specification
offline:service mode:specification
45 hp:power:specification
installation service:service type:specification
55 mm:screw barrel size:specification
alpha projects:brand:specification
aria:brand:specification
pvc & xlp:material to be extruded:specification
monolayer:film layer structure:specification
1:india:specification
gold refining:purpose:specification
skxd-jy01:model:specification
fluoropolymer extruder:machine types:specification
stand alone extruder:machine type:specification
blown film:type:specification
2500mm:film width:specification
liquid extraction in packed bed:product name:specification
blown film extrusion:usage/application:specification
gold:refinery material:specification
40mm:bag width:specification
capacity 100 kg:capacity:specification
3kl:capacity:specification
60 kg:capacity(kg):specification
200 liter:capacity:specification
100l:capacity:specification
60:capacity:specification
ms & ss 304:material:specification
3000 g:capacity:specification
co-roatating:screw design:specification
masterbatch:plastic processed:specification
clove oleoresin extraction:machine type:specification
coriander oleoresin extraction:machine type:specification
30 kg model (28x12 inches):model name/number:specification
144 position:capacity:specification
hydro extractor:product type:specification
line-m-ext-ps:model:specification
pvc pipe:material type:specification
500 gms:capacity:specification
fe500:material grade:specification
clay:material to be extruded:specification
tube extrusion:usage:specification
6000 gm per charge:waste per charge:specification
5100:model no.:specification
100-250:capacity:specification
vikas industries:brand:specification
exm 3000:model name/number:specification
compact mini:machine type:specification
rmb a65 b75:model no:specification
300 ton:products capacity:specification
3000mm:film width:specification
twin screw extrusion plant:type:specification
syn/mbgp/90 ac:model number:specification
solid-liquid extraction (bonnoto type):product name:specification
twin screw extrusion plant:type.:specification
80kw:machine power (kw):specification
film making machine:type:specification
100tpd-1200tpd:capacity:specification
500 kg:production capacity:specification
5kg:capacity(kg):specification
2000 gm.:capacity:specification
1 l:capacity:specification
250 kg - 5 tpd:capacity:specification
1 ton:capacity:specification
brown:color:specification
co roatating:screw design:specification
ss65:model name/number:specification
ajwain oleoresin extraction:machine type:specification
cinnamon bark oleoresin extraction:machine type:specification
800kg - 2ton/day:production capacity:specification
20 kg/hr:production capacity:specification
2 ton/hr:capacity:specification
extraction:type:specification
precious metals:processed material type:specification
500 ltr:capacity:specification
250 kg to 5 tpd:capacity:specification
monolayer extruder:machine types:specification
2.5 mm:width:specification
silver:metal type:specification
refining:process type:specification
gold:refining machine:specification
syn/it-50:model number:specification
gilson:brand:specification
10kg:capacity:specification
25 mm:screw diameter:specification
2:winders:specification
volumes under 300l:flowrate:specification
65kg/hr:peak output:specification
65 kg / hr:peak output (kg/unit):specification
omron - japan or equivalent:programmable logic controller:specification
omron - japan or equivalent:human machine interface:specification
1500 mm:lay flat width:specification
1500 mm:film width:specification
no smell,no smoke,ph7,no nitrogen oxide:exhausted gas:specification
450 mm x 350 mm x 500 mm:dimension:specification
1500000:1 ton:specification
future tech:brand:specification
301 l/d:screw ratio:specification
37 kw:driving motor:specification
1625 mm:nip roll size:specification
23.1 kw:total heating load:specification
40 kg:item weight:specification
45 lpm:oil free vacuum pump:specification
12x75mm, 13x100mm, 16x100mm:size:specification
450 mm:lay flat width:specification
32 mm:screw diameter:specification
7.5 hp:driving motor power:specification
gold industries:usage:specification
150 mm:film thickness:specification
dan-6t-02:model:specification
six samples:no. of positions:specification
35 degreec (ambient) to 300 degreec:temperature control range:specification
pesticides:material to extrude:specification
555 mm (22 inch):nip roll size:specification
90 m/min:take up speed:specification
230 v, single phase:voltage supply:specification
135 kg/hr:max extrusion output:specification
150 litres cold water(+1degree c) capacity:convection cooler:specification
with vacuum system,150 litres tank capacity:liquid filtration:specification
200 l:reactor capacity:specification
pp (polypropylene):material used:specification
mtba-03a:model:specification
global extrusion technik:brand:specification
indore (m.p.):location:specification
5kw:power consomption:specification
80 ml:solvent cup volume:specification
0.1 to 8 gms (depending on the type of sample):sample size:specification
integrated auto sequencing programs with 12 desirable sequence ramp / steps of time and temp. domain:ramp and hold:specification
water pipe type (it has 4 column) it works under vacuum:filtration system:specification
300 capacity cube meter:vacuum system:specification
gold refining use:usage/application:specification
kneader extruder plant:type:specification
aluminum:material for construction:specification
300:6/4/2006:specification
52 mm:screw dia:specification
gold jewellery industries:usage:specification
20 kg/psi:ss vacuum gauge:specification
12 port:acrylic chamber:specification
one way 12 nos:stopcocks:specification
p p regulator value set:regulator:specification
0-5:power:specification
20 - 40 ( kw ):power consumption:specification
10 - 60 ( micron ):thickness:specification
65-132:model name/number:specification
1-20 ft:length:specification
0-1 m/s:speed:specification
300 - 600 to 1600 - 2500:lay flat width range:specification
10 - 100 micorn:film thickness:specification
550 - 1600 mm:lay flat width range:specification
120 - 200 kg / hr (depends on extruder's size):production capacity:specification
20 - 150 microns:film thickness:specification
20-630:size:specification
100-150kg/h:capacity:specification
fixed or variable speed (up to 3600 rpm depending on model):speed:specification
up to 10000 tons per years:production capacity:specification
1-10kg:capacity:specification
70- 80 ton/day:capacity:specification
35-170 kgs/hr:capacity:specification
more than 500 kg:capacity:specification
up to 1500 grams (1.5 kg):capacity:specification
10 - 100 ( micron ):range of thickness of wall ceiling panels:specification
manual:driven type:specification
manual:type:specification
leplcwcm:model name/number:specification
leplcwcm:model:specification
3000 litre:storage capacity:specification
25 litre:storage capacity:specification
available:production capacity:specification
available:type:specification
available:screw design:specification
1500 ml:capacity:specification
available:surface treatment:specification
available:size:specification
1500 ml:bowl capacity:specification
32mm:screw diameter:specification
32mm:diameter mm:specification
as per your requirement:capacity:specification
other:capacity:specification
as per requirements:size:specification
cutomized:design type:specification
customized:automation grade:specification
as per requirement:power source:specification
as per requirement:extraction method:specification
as require:screw diameter:specification
na:electrical unit consumption:specification
na:power source:specification
na:driven type:specification
as per requirement:machine type:specification
as per requirement:raw material:specification
as per requirement:design type:specification
as per requirement:material:specification
as per requirement:temperature:specification
nil:motor rating:specification
nil:air pressure:specification
nil:voltage supply:specification
standard:model name/number:specification
mild steel and stainless steel corrosion-resistant materials as per require:material of construction:specification
stainless steel,mild steel:material of construction:specification
33 x 80 mm (65 ml):thimble size:specification
60-70%:solvent recovery:specification
galvanised:surface treatment:specification
m s:material:specification
color coated:coated:specification
3 layer:film layer structure:specification
extruder a-45 mm (inner & outer layer) extruder b-55 mm (middle layer):screw size:specification
4.5x4x5 meters:dimensions:specification
1450 rpm:drive speed max.:specification
35 kw:installed heating capacity:specification
1250000:price:specification
ms:material used:specification
new:i deal in:specification
35kw:installed capacity:specification
herbal extraction:type:specification
cnc:control:specification
industrial use:usage:specification
100 kg per hour:capacity:specification
automatic,semi automatic:automation grade:specification
1000 mm:film size:specification
semi automatic:grade:specification
92:diameter:specification
0.75kw:cutting motor:specification
25 ml.:sample max. volume:specification
30-60 mi:extraction speed:specification
mtl 2022:model:specification
8x6x8 meters:dimemsion:specification
9,000,000:usage/application:specification
solvent extractions machine:machine type:specification
depend on the requirement:automation grade:specification
powder/liquid/mud:body material:specification
led:display type:specification
lab care equipment:brand:specification
1 liter:capacity:specification
1.3 kw:power:specification
0.1-100 % fett:measuring range:specification
14.5 kw:total connected load:specification
coated:finish:specification
550 mm:nip roll size:specification
25 kg/hour:max output:specification
edf/ind-cba-15:model no:specification
simona:color:specification
ms:machine material:specification
normal 300 deg:temperature control:specification
designed for minimal energy consumption:energy efficiency:specification
mustard seed oilcake:raw material:specification
comprehensive service, including training and spare parts supply:after-sales support:specification
online, offline, upi:payment method:specification
to create moderate barrier films for agricultural department.:usage:specification
iso, ce and asme-certified designs for durability and reliability:design compliance:specification
advanced horizontal extractor, desolventizer-toaster, distillation, and recuperation systems:technology:specification
manual / fully automated with scada/plc controls:automation:specification
energy-efficient design for optimized power usage:power consumption:specification
mild steel as well as high-quality stainless steel for durability and corrosion resistance as per th:material of construction:specification
50-100 hp:power consumption:specification
1-25kg:capacity:specification
55-125 ( kg/hr ):production capacity:specification
70- 250 kg/hr:production capacity:specification
80 -150 kg/hr:production capacity:specification
it uses low pressure nitrogen or argon gas to force solvent through various filter materials to remo:usage/application:specification
52-18:screw number:specification
60-65 hp:power consumption:specification
1-10 kw:power (w):specification
upgradable from 1 to 7 solvents:capacity:specification
8-12kg/h:output:specification
52-18:model name/number:specification
0.32-0.43 kwh/kg:power consumption:specification
1-400 rpm:line speed:specification
50 to 2000 tpd (customizable based on client requirements):capacity:specification
designed to meet global standards for emissions and environmental safety:environmental compliance:specification
900-1200 mm:lay flat width:specification
barrier : 50-200, non-barrier : 40-200:flim thickness range:specification
1-10 kgs:capacity:specification
1-2 kg/hr:production capacity:specification
200-500 kg:capacity:specification
8 ton/day:capacity:specification
pet:material processed:specification
gold:processed material:specification
karcher:brand:specification
puzzi 8/1:model:specification
bitumen:material extracted:specification
herbal extraction and distillation:usage/application:specification
50 liters to 2000:capacity:specification
50 hz:voltage:specification
stainless steel:inner & outer drum body material:specification
rew:brand:specification
rew:design type:specification
stainless steel:machine type:specification
1200 mm:lay flat width:specification
1200 mm:film width:specification
500 litre:storage capacity:specification
1000 litre:storage capacity:specification
38mm:diameter mm:specification
customised:motor power:specification
fixed:type:specification
robust:design type:specification
as per req.:motor power:specification
best quality:heavy duty and highly efficient:specification
customized:frequency:specification
customized:phase:specification
standard:bis:specification
standard:nabl:specification
standerd:phase:specification
standerd:power source:specification
p square:brand:specification
55mm - 250mm:size:specification
6ft x 14ft x 6ft:packaging size:specification
nitrogen gas:power source:specification
sheets:output shape:specification
900-1000hv:surface hardness:specification
german:made in:specification
brassica oleracea var. capitata:botanical name:specification
20 micron:thickness of film:specification
1kg, 5kg, 25kg:packaging size:specification
35 c (ambient) to 300 c:temperature control range:specification
+- 0.5 degree c:temperature accuracy / precision:specification
2000 watts.:power consumption:specification
100 mm:film thickness:specification
l/c (letter of credit),d/a,d/p,t/t (bank transfer):pay mode terms:specification
3600 r.p.m.:speed:specification
50kg:weight:specification
65 kg/hr:capacity:specification
silver:colour:specification
horizontal extractor, desolventizer-toaster, distillation units, and recuperation system:technology:specification
based on project:service duration:specification
2500000:1:specification
approx 1500kg:100 mm screw and 82 inch barrel:specification
gold jewelry industries:usage:specification
55 kw:drive power:specification
mtl 2023:model:specification
casted aluminium alloy heaters:heater source:specification
800 mm:film size:specification
5000000:1:specification
anti- microbial, moisturizer, anti- wrinkle.:effects & properties:specification
offline and online:payment mode:specification
labstac:brand:specification
time rendered:features:specification
mts-915:model number:specification
horizontal:style:specification
yes:automatic:specification
auto filtration with vacuum pump:filtration system:specification
50-500tpd:capacity:specification
5 - 50 m3/hr:range:specification
pe 52-25:model name/number:specification
20-60 degree:temperature:specification
130-150 kg/hr:capacity:specification
2-4 bar:pressure:specification
0.31-0.42kwh/kg:power consumption:specification
55-125 kg/hr:capacity:specification
10 - 100mm:screw diameter:specification
80 - 150 m:screw diameter:specification
10 - 100 mciron:film thickness:specification
80 - 150 ( mm ):screw diameter:specification
10 - 100 micton:film thickness:specification
5-100 m3/hr:capacity:specification
75-165kgs/hr:production capacity:specification
6:1 - 16:1:l/d ratio:specification
ss aba/35-45/800:model:specification
up to 1500 g (1.5 kg) of bituminous mix:capacity:specification
upto 3000 (stitch/min):max sewing speed:specification
less than 40 db:noise level:specification
up to 3600 rpm (manual, depending on crank speed):speed:specification
more than 100 kw:machine power (kw):specification
150-200kg/h:production capacity:specification
2-100 ton:capacity:specification
10-300 l:capacity:specification
100-150 kg/hr:production capacity:specification
more than 500 kg/hr:production capacity:specification
up to 235 kg/ hr:production capacity:specification
automatic:machine type.:specification
45kg/hr:peak output:specification
electrolytic:processing method:specification
electrolytic:process type:specification
6000 litre:storage capacity:specification
500 tpd:production capacity:specification
m.s:construction:specification
1000 mm:film width:specification
1000mm:layflat width:specification
45kg:production capacity:specification
45kg:weight:specification
standard:quality:specification
new only:deals in:specification
as per requirement:dimension:specification
as per requirement:voltage:specification
all types:extrusion type:specification
all types:screw diameter:specification
all types:material processed:specification
all types:max output:specification
all types:application:specification
all types:l d ratio:specification
all:material grade:specification
40mm:pipe diameter:specification
u-shaped:design:specification
7:heating zone:specification
16 kw:heating load:specification
33 kw:total connecting load:specification
2 piece:set content:specification
normal 300 degree:temperature control:specification
230 v, 50 hz, single phase, a.c:power supply:specification
pp:material used:specification
wat 500kg full automatic gold refining unit:7 fat hight 5fit lenth 5feet writh:specification
50 mm:screw od:specification
helical 160 cd:gear box:specification
5" to 22":lay flat tubing:specification
hope/llop:suitable material:specification
15 hp:main motor:specification
50 kg:production:specification
50-100 kg/hr:production capacity:specification
146 - 194 ( kw ):production capacity:specification
1:approximate order value:specification
144 individually regulated:no of position:specification
1 ml,3ml:spe cartridge size:specification
55mm:screw dia:specification
888:model name/number:specification
foam-elp-lps-90-114/1100:model number:specification
yes:portable:specification
spiral:die:specification
50 tph:minimum capacity:specification
45 hp:power consumption:specification
220v:power consumption:specification
100 rpm:speed:specification
5 lit:reagent:specification
1 kg:coasted soda:specification
2kg:uria flter pad:specification
tm-071h:model name/number:specification
powder coated:finish:specification
extraction machine:machine type:specification
230 to 430 v:voltage:specification
no:floor area:specification
yes:control panel:specification
no:elbow:specification
no:gate valve:specification
spe 144:model:specification
spe 96 144:model number:specification
athena grey:ss:specification
on patended siebec cartridge:filtration:specification
greater than 20 kw:power:specification
55 kg/hr:peak output:specification
27 kw:contacting load:specification
10.5 kw:heating load:specification
20 hp:main drive:specification
65 kg/hr:peak output:specification
single stn:surface type:specification
electric and air operated:power type:specification
10 to 1 ton:capacity(kg):specification
1.5 litre:capacity:specification
three layer:layer type:specification
solvent extraction plant:model name/number:specification
gold:material capability:specification
100 liters:capacity:specification
ira corporation:brand:specification
22 kg:capacity:specification
48 kg:capacity (kg):specification
college / laboratory:usage/application:specification
50 litres:capacity:specification
gold and silver:material capability:specification
cnc:cutting:specification
1000:drum rpm:specification
stainless steel 304 grade:inner drum:specification
stainless steel 304 grade:outer drum:specification
mild steel sheet:base cover:specification
1000:rpm:specification
mild steel sheet:base plate:specification
stainless steel 304 grade:control box:specification
cnc:bending:specification
stainless steel 304 grade:back cover:specification
1:ss304:specification
75 kw:machine power (kw):specification
electric:usage/application:specification
75kw:main motor power:specification
1 ton:machine weight:specification
abc:m tech jewel equipment:specification
elshaddai:brand:specification
elshaddai:make:specification
chemical:process type:specification
chemical:process:specification
three phase:phase type:specification
three layer:film layer:specification
3kg:capacity(kg):specification
required:foundation:specification
20-30 units per month:brand:specification
20-30 units per month:capacity:specification
8:1:screw ratio:specification
750 mm:max lay width:specification
20 kw:thickness range micron:specification
kg-35-45:model number:specification
on site:service location:specification
48/96/144:no of position:specification
1ml:spe cartridge size:specification
no:standard with equipment:specification
48:spe cartridge size:specification
96:well plates:specification
processor:spe:specification
athenas:color:specification
for lcmsms:model number:specification
spe48 spe96 spe144:model:specification
spe processor:ss:specification
ss pipe,glass:material:specification
manual and semi-automatic:automation grade:specification
silver:refining material:specification
100 mm:main extruder screw diameter:specification
twin screw extruder 75 mm:model name/number:specification
frhe 50:model name/number:specification
600 mm:door opening:specification
scs 8 r ts:model:specification
laboratory:usage:specification
gold refining systems are ideal for old gold jewelry buyers,bullion suppliers,gold smithies,jewel:usage/application:specification
5 year:flow sysytem:specification
30 hp:sub extruder motor power:specification
180 mm:sub extruder hydraulic screen changer:specification
micro:brand name:specification
granulex-100ds:model no:specification
40 hp:main extruder motor power:specification
35 mm:screw size:specification
cost effective:feature:specification
75 kw:driven type:specification
100kw:power:specification
209 l:drum volume:specification
350 mm:drum depth:specification
1800x1575x1050 mm:dimension:specification
spe 48:model:specification
ms powder coating:coating:specification
steam and electricity:power source:specification
3000000:hep:specification
1kw:99.99:specification
120 mm:sub extruder scew diameter:specification
gold refining service:service type:specification
800 rpm:drum speed:specification
approx. 15 psi:pressure:specification
1 ml 3 ml and 6 ml:column formats:specification
220-415 v:voltage:specification
30-40 kw/ ton of material processed:power:specification
200gm-10kg/hour:production capacity:specification
techno biobase:manufacturer:specification
100 kg/day:capacity:specification
20pcs:capacity:specification
10 tpd 1000 tpd:capacity:specification
3 to 4 kg per hour:capacity:specification
upto 50 kg/hr:capacity:specification
plastic bag making machine:type of machine:specification
as per requirement:airflow (m3/h or cfm):specification
upto 30 kg/hr:capacity:specification
helical:gear type:specification
300 l:capacity:specification
up to 5 ton/day:capacity:specification
5kg:capacity:specification
180kg/hour:capacity:specification
300kg/hours:capacity:specification
500 mm:nip roll:specification
balaji engineering works:brand:specification
60", 48", 36", 24", 18" , 12":model name/number:specification
40 mm:screw die:specification
10 hp:main drive:specification
18.kw:power:specification
rsep 066:model name/number:specification
bio fertilizer:industry type:specification
hb64.25:model name/number:specification
40mt - 100mt kettles:capacity:specification
50hz/60hz:frequency:specification
scs 2 as dls ts:model:specification
athena:color:specification
spe96:model:specification
230 to 480v:voltage:specification
20" x 30":dimensions:specification
1 kg. ( also available in 4 kg capacity and custom made on required specification):refining capacity:specification
balaji:brand:specification
750 rpm:drum speed:specification
60 l:drum volume:specification
930x800x1150 mm:dimension:specification
20", 24", 30" & 36":capacity:specification
dewatering and etc:usage\applicaation:specification
ssm/tfe-75:model name/number:specification
65-70 degreec:temperature of top:specification
65 - 68 degree c:reflux operates at:specification
68 - 65 degree c:vent condenser operates:specification
45 kw:power:specification
410 mm:drum depth:specification
frhe 15:model name/number:specification
350 mm:door opening:specification
yes:installation:specification
300:capacity:specification
ac 220/110v 50/60 hzs:power supply:specification
1 kw:power consumption:specification
spe144:model:specification
12:no of rows:specification
processor:96spe:specification
3 hour:recovery time:specification
spt - 01 - 10:model no:specification
max 70 degreec:fume temperature:specification
as per load:design:specification
ase:model:specification
738 x 405 x 930mm:package size wxdxh:specification
total whit 60kg:7fight length 3feet 2feet writh:specification
paint coated:finish:specification
processor:spe144:specification
220/250 v:voltage:specification
2-10 kw:power consumption:specification
60 db(a) at 110 m3/h:noise level (db(a)):specification
50:extraction arm diameter (mm):specification
50 - 110:airflow (m3/h):specification
electric bitumen extractors are used for determination of bitumen percentage in hot mixed paving mix:uses:specification
electricity supply: 1 phase, 220 v ac, 3 kw.:power source:specification
1000 ml:size:specification
tlj250 tlj300 tlj350 tlj400:model:specification
1500gms of removable aluminum rotor bowl:capacity:specification
0.35 m2:condenser:specification
5000-13000 pcs/hr:capacity:specification
1000 mm:niproll size:specification
12 kw:heating load:specification
cartridges, manifolds, vacuum pump, glass chamber & ptfe cap.:standard with equipment:specification
10 / 20 samples position:no of position:specification
floor mounted:mounting type:specification
gold and silver,diamond,jewellery,dust .e.t.c:refining material:specification
3 nos.:heating zone:specification
90 kg/hr:peak output:specification
36 kw:contacting load:specification
25 hp:main drive:specification
fs-s55:model name/number:specification
na:layer of tank:specification
mixture, tanki, panel, holup, cutter,tiffin, normal printing machine:set contain:specification
ac power:power source:specification
3000 mt:vegetable oil per day.:specification
galvanized:surface:specification
380 v/440 v:voltage:specification
55 mm:screw die:specification
4.5:peak output (kg/unit):specification
14 inch:diameter:specification
1, 3 & 6 ml:spe cartridge size:specification
llu10:cat ref:specification
230 volt ac:voltage:specification
white athena:color:specification
5a:output current:specification
75 tpd:capacity:specification
up to 50 tpd:capacity:specification
30 kw:connecting load:specification
from 2,400 to 3,600 rpm:speed control:specification
comprehensive training, spare parts availability, and regular maintenance suppor:after-sales support:specification
nnt-se-ca:model no:specification
1:moq:specification
22x2x4mm:dimension(l*w*h):specification
15 kw:drive motor:specification
3hp:main drive:specification
12 kgs:peak output:specification
300 mm:niproll size:specification
mtl 2024:model:specification
advanced solvent extraction, desolventizer-toaster, distillation systems and solvent recovery sectio:technology:specification
energy-efficient machinery ensuring optimized power usage:power consumption:specification
manual / fully automated with scada/plc systems:automation:specification
comprehensive training, maintenance, and spare parts supply:after-sales support:specification
with vacuum system:liquid filtration:specification
5 feet:height:specification
global industries:brand:specification
50 mm:screw die:specification
600 mm:niproll size:specification
single:surface type:specification
150 kg/ hr:production capacity:specification
to mix, compound, and process various materials, particularly plastics and food components:use:specification
30 ul 1000 ul:process volume:specification
hepa filter:filtration:specification
siebec:brand:specification
threaded, grooved nozzle:connection:specification
castor seeds:raw material:specification
iso, asme, and ce certifications for quality and reliability:design standards:specification
mild steel as well as high-quality stainless steel and corrosion-resistant:material of construction:specification
25mm:screw die:specification
1.1:peak output (kg/unit):specification
matt:aone scientific:specification
5kg gold:refine capacity:specification
shapet:brand:specification
on/off switch, mains indicator:standard make:specification
rtd pt-100 type:temperature sensor:specification
1 phase, 220 v ac, 1.5 kw.:electricity supply:specification
30ltrs:solvent:specification
10kg:solid:specification
15 hp:driving motor power:specification
210 kg/hour:output:specification
33.1 kw:total heating load:specification
65/75 mm:screw diameter:specification
jrd:brand:specification
rishikesh:brand:specification
labments equipments:brand:specification
athena:brand:specification
max 10 lpm:flow:specification
ss316:moc:specification
180:max line speed:specification
oil painted:surface finish:specification
5.9 kg:weight:specification
mono layer:layer type:specification
150 kg /hr:capacity of production:specification
20 mm to 250 mm:diameter:specification
90 mm:mother extruder screw dia.:specification
55 mm:babby extruder screw dia.:specification
50 hp:extruder power (hp):specification
glass agencies:manufacturer name:specification
oil soluble:material:specification
1 kg:size:specification
315 mm:pipe dia:specification
water soluble:material:specification
25 kg:size:specification
depends on size of machine:machine power (kw):specification
25 mm to 50 mm:diameter:specification
12 mm to 600 mm:diameter:specification
25 mm to 175 mm:screw diameter:specification
6:number of head:specification
extrusions plant machinery:type:specification
4000 kg:machine capacity:specification
35 days:service duration:specification
twin screw extrude:type:specification
pneumatic operation raises and lowers sample rack:operation:specification
includes waste reservoir that can be emptied between each waste step if desired:waste collection:specification
siemens - japan or equivalent:main motor:specification
air cooling:type of cooling:specification
bonfiglioli - italy or equivalent:gear box:specification
to produce medical tubes for various applications:function:specification
pvc and other non-toxic materials for sanitary use:extruded material:specification
titanium & pp:material:specification
1 ltr:bottle capacity:specification
rpm meter:digital:specification
4:bottle no.:specification
50:rpm:specification
digital:digital timer:specification
metal:brand:specification
excellent and best:heavy duty:specification
customized:packaging size:specification
customized:packaging type:specification
customized:pulses type:specification
standard:motor:specification
cost effective and reusable of jewellery:usage/application:specification
2,400 to 3,600 rpm:speed control:specification
230 v a.c:power supply:specification
1530 mm:width of layflat:specification
gry:color:specification
made in india:origin of country:specification
95:total connected load:specification
45kw:installed capacity:specification
0.25 hp:motor:specification
24 inch hydro machine:280kg.:specification
use electrochemical processes to purify gold:usage:specification
barrier:design:specification
300m/min:max wire speed:specification
teflon:lid:specification
lldpe,hdpe:material used:specification
21.7:screw dia:specification
150 kg/hr:maxi o/p:specification
13kw:power consumption:specification
industrial:ussge/ application:specification
500:extuder machin:specification
kurkure:material to be extruded:specification
25 tons:weight:specification
250 kw:power consumption:specification
pp, hips, hdpe, ldpe:application:specification
pcb:control panel:specification
helical extension:spring:specification
71:drum volume in liter:specification
limit switch:door open cut off:specification
mild steel:nuts, bolts and connectors:specification
395:door open dia in mm:specification
turret punch press:perforation:specification
starfish engraving with led lights:logo:specification
gloss with powder coated:overall finish:specification
800 x 1000 x 1050:over all dimension in mm:specification
15:dry weight in kg:specification
2.25:motor power in kw:specification
01:04.5:liquor ratio:specification
electrical:breaking:specification
specially designed by us:motor brand:specification
stainless steel 304 grade with lock:door:specification
directly connected with bearing:drum with motor:specification
screw rod:spring adjustment:specification
laser/mig/tig:welding:specification
300:weight in kgs:specification
65:drain outlet in mm:specification
laboratory:application/use:specification
polsihed:surface finished:specification
adjustable:extrusion speed:specification
twin screw extruder:extruder type:specification
380v:voltage compatibility:specification
155 kw:power:specification
20kg:65:specification
20500 kg:weight:specification
190 mpm:max line speed:specification
420 kg/hr:production capacity (kg/hr):specification
tpq38:model number:specification
125 mm:mother extruder screw dia.:specification
75 mm:babby extruder screw dia.:specification
65 mm:babby extruder screw dia.:specification
100 mm:mother extruder screw dia.:specification
bbb:aaa:specification
rsep 066 b:model name/number:specification
amv-bae-5006:model name/number:specification
0-90%:feeding concentration:specification
5 yers:flow sysytem:specification
iso certified:is it iso certified:specification
60 degree c:max temperature:specification
1,8 to 3 m cube per hour:flowrate:specification
15 hp:main drive:specification
75 mm:die size:specification
fs-s45s:model name/number:specification
2.6 kw:peak output (kg/unit):specification
30 kw:contacting load:specification
11.5 kw:heating load:specification
50hp:power (hp/kw):specification
xxx:question:specification
850 mm:nip roll:specification
single station:winder:specification
28 kw:connected load:specification
3 kw:machine power:specification
namkeen:snacks type:specification
200kg:capacity:specification
masala chana:type of namkeen:specification
50-75:power:specification
gold refinery:usage / application:specification
no:bend:specification
280-320 v:voltage:specification
4 ml vials:controller type:specification
fs-s50:model name/number:specification
2.8:peak output (kg/unit):specification
pcb recycling machine:type:specification
15 - 30 kw:power:specification
99.95%:purity:specification
cost of plant 3cr:od-3, id-1.1mm, load -20-30kg/mtr:specification
from 50 tpd to 2000 tpd:capacity ranging:specification
high temperature:temperature:specification
250 tph:maximum capacity:specification
300 ml:reagent:specification
over 100 %:recovery rate:specification
no:stop watch:specification
positive pressure manifold:type:specification
threaded - grooved nozzle:connection:specification
as per costomers requirement:capacity:specification
500 l:storage capacity:specification
more than 500 ton:clamping force:specification
100 -1000 ton per day:capacity:specification
more than 5000 tpd:capacity:specification
1000l:storage capacity:specification
single die extruder:production capacity:specification
150-200 kg/hr:production capacity:specification
350-400kg/h:production capacity:specification
50-150 kg:capacity:specification
90-100 kg/hr:capacity:specification
30 kg/hour:capacity:specification
80 to 100 kg/hr:capacity:specification
golden technologies:brand:specification
gpps:material to be extruded:specification
operated bitumen extractor:type of testing machines:specification
all:industry type:specification
stainless steel & mild steel:material:specification
30/70:heating range:specification
6 to 9 months:delivery time:specification
30 hp:main motor drive:specification
6f:ok:specification
24x2x4mm:dimension(l*w*h):specification
500 mm:width of lay flat:specification
4 inch:cutting disc size:specification
65 mm:screw dia mm:specification
230 v a.c. single phase:power supply:specification
30 days:service duration:specification
extruder a 35 mm (inner and outer layer) extruder b 45 mm (middle layer):screw size:specification
cottonseed and other oilseeds:raw material:specification
condenser:cooling unit:specification
edf/ind-cba-17:model no:specification
555 mm:nip roll size:specification
22 meter:length of line:specification
20-100 mm:film thickness:specification
tube well casting, industrial waste & chemical drain domestic plumbing:application:specification
22:1:l/d:specification
well drained:soil specific:specification
230v,50 hz (1 phase) or 440v,50 hz (3 phase):power supply:specification
1250 mm:nip roll size:specification
42.5 kw:connected load:specification
based on extruder size:production capacity:specification
ie2, ie3:motor type:specification
2% - 5%:tds%:specification
sky blue or apple green or other color:colour:specification
yes:imported:specification
prefers regular watering:watering requirement:specification
16 mm:diameter:specification
24 inch:maximum height:specification
42crmo4,38crmoala,41craimo7,16mncr5,31crmov9,34craini7,etc:base material:specification
bimetallic,nitrided,hard-facing,chrome-plated,etc:surface treatment:specification
manual / semi automatic:grade:specification
4x3.5x4.8 meters:dimensions (lxwxh):specification
ra0.4:surface roughness:specification
0.015mm:surface straightness:specification
110 mm:max pipe size:specification
ornamental plant:usage:specification
pilea cadierei:plant botanical name:specification
50 to 800 deg c:heating range:specification
1800 mm:film size:specification
160 kg/hr:production capacity:specification
ss hd/ld-450:model:specification
700 mm:film size:specification
semi-automatic:grade:specification
32 : 1:l/d ratio:specification
3 nos:heat zone:specification
gas nitriding:treatment:specification
2hp + 40hp:heating load:specification
7.5 hp:blower:specification
55 inch:nip roll:specification
16mm:diameter:specification
dark grey:color:specification
electronic speed control:speed control:specification
25hp:power:specification
amrut:brand:specification
10000 kgs:weight:specification
extraction unit:preparatory section:specification
fully automatic:functional:specification
28 mpa:system pressure (mpa):specification
+-0.5% fs:force accuracy:specification
+-0.1 mm:displacement accuracy:specification
90mm:screw diameter:specification
3.7kw:main motor kw:specification
gold refining from old jewelleries and from dorebar.:usage/application:specification
polypropylene chamber 12 / 24 port:moc:specification
24 nos:teflon lid:specification
oil free vacuum pump 45 lpm:vacuum pump:specification
glass test tube 18 x 150mm:glass test tube:specification
rectangular acrylic cabinet:acrylic chamber:specification
500 gm:size:specification
12:heating capacity(kw):specification
915:roller width(mm):specification
5:water ring (pc):specification
5 kg:size:specification
41 mm:screw dia:specification
metro plastic:brand:specification
depends on size of cable:output(kg/hr):specification
2 hp:a.c drive motor:specification
70 hp:power consumption:specification
akd polymers:brand:specification
ms:available material:specification
plc, hmi touchscreen for real time monitoring:control system:specification
masterbatch, filler, engineering plastics, recycling:application range:specification
pp:material versatility:specification
plc with hmi touchscreen for full process automation:control system:specification
ss304:grade:specification
500 kg:weight:specification
1 hp:motor:specification
75 x 180 mm:barrel:specification
hexane-based solvent extraction system:extraction process:specification
installation, training, maintenance, and spare parts supply:support services:specification
high efficiency with minimal oil residue in extracted meal:oil recovery rate:specification
2500000:1 ton:specification
edf/ind-cba-16:model no:specification
lidding film, vaccum bags, edible oil, medical, uht milk, dairy products.:usage/ application:specification
new only:i deals in:specification
horizontal solvent extractor, desolventizer-toaster, distillation unit, and recuperat:key components:specification
nnt-se-ms:model number:specification
7.1 kw:total heating load:specification
150kg/hour:capacity:specification
single/three:phase type:specification
demand machines:brand:specification
22kw:main motor:specification
ldpe, hdpe,surlyn, eva,evoh & pa:polymers:specification
43 mm:diameter:specification
3 kw.:power source electricity supply:specification
blue/ ivory:colour:specification
frequency control:motor speed:specification
3 layer (a/b/c):film layer structure:specification
hexane is commonly used,while other solvents like ethanol or isopropanol may also be used:solvent type:specification
1+1 years extended warranty:warranty:specification
abb - or equivalent:main motor:specification
elecon - or equivalent:gear box:specification
schneider - or equivalent:switch gears:specification
preparation,extraction,distillation:plant processes:specification
oil seeds,oil cakes & other sources such as corn germ,rice bran etc..:raw material:specification
blown film plants:usage:specification
45hrc:product hardness:specification
500 liter:capacity:specification
200 kw:power consumption:specification
3 metric ton:capacity:specification
deccan dynamics:brand:specification
general purpose film, liner bag, shrink film, stretch film, mulch film, courier bag:application:specification
nomal lubrication as well as cleaning as per maintenance chart:maintenance:specification
powder coating:surface treatment:specification
780 mm:plunger diameter(mm):specification
21:system pressure (mpa):specification
135*750 mm:billet diameter(mm):specification
180 mm:side cylinderdiameter(mm):specification
28 mpa:working pressure:specification
250 to 300 kw:total power:specification
for use in college and university level civil engineering and polytechnic laboratory:use/application:specification
20 ton:lengh 150 feet:specification
rectangle:shape:specification
. spray extraction column:product name:specification
yes:insatallation service:specification
hpmc 51/105:machine model:specification
180:max plasticizing capacity (kg/hr):specification
150:max outout (kg/hr):specification
3:heating die(kw):specification
18.5:main drive kw:specification
15:heating barrel (kw):specification
12 mm:screw diameter:specification
175 kg (with support frame):weight:specification
2 x 15 nm:max. screw torque:specification
20 kg:size:specification
10 kg:size:specification
95 mm:screw diameter:specification
1000 mm:die width:specification
130 kw:total power:specification
10 kgs:max design pressure:specification
size vary as per selected refinery:we build as per specific need of client:specification
bonfiglioli - or equivalent:gear box:specification
1350 to 3000 mm:lay flat width range:specification
25 to 250 microns:film thickness range:specification
75 / 95 / 100g mm diameter:extruder screw size:specification
ss316:grade:specification
cross head extruder:machine type:specification
ion exchnage system:type:specification
mild steel:moc:specification
13000mm:length:specification
3 hp:main drive motor:specification
pbl:gear make:specification
balaji manufacturing:manufacturing:specification
continuous:type:specification
inline planetory:gearbox:specification
1400:1:gear ratio:specification
2018:year of manufacturing:specification
18 inch:dia. of outer bucket:specification
45 kg:capacity/round:specification
3 hp:main motor:specification
16 inch:dia. of inner bucket:specification
150kg:hight 60inch lenth 48 inch and depth 26 inch:specification
50 hp:main motor:specification
120 inch:screw diameters:specification
26.1 l/d:ration:specification
300kw:power (kilowatt):specification
155 kw:power (kilowatt):specification
415v:voltage (volt):specification
96 sample:no of position:specification
steam sterilized:purity:specification
800 mm:film width:specification
3 kw:motor power:specification
5 kg/hr:production capacity:specification
110 kw:motor power:specification
154 w:power:specification
box:packaging size:specification
d station:winder:specification
tari:brand:specification
352 l:drum volume:specification
800 mm:door opening:specification
980 rpm:drum speed:specification
a.r.m.k:brand name:specification
new one only:i deal in:specification
5 ton:weight:specification
100 -105 degreec.:temperature of bottom:specification
415:current:specification
54 kgs:gross weight:specification
650 x 320 x 715mm:external size wxdxh:specification
fully automatic:work mode:specification
0.2-100 t/h:capacity:specification
coated:surface finish:specification
99.90%:yield:specification
60 cycle:cycle:specification
ss, pvc, ms:material:specification
electric:source:specification
semi automatic:automation:specification
new:deals in:specification
indoor:installations:specification
7.5hp:power (hp/kw):specification
frhe 30:model name/number:specification
2100x1750x1200 mm:dimension:specification
320 mm:drum depth:specification
stb-08:model number:specification
32 -37 degree c:cooling water circulation:specification
12 -17 degreec:chilling water circulation:specification
68 - 65 degree c:condenser operates:specification
50-150 kg/hr:capacity:specification
250 ml,500 ml,1000 ml,5 lit:capacity:specification
polished:surface finished:specification
380 kg per hour:capacity:specification
200kg/perhours:capacity:specification
50 kg/hour:capacity:specification
300-400kg/h:production capacity:specification
powder coating machine:type of machine:specification
1 kg:material loading capacity:specification
upto 100 liters:capacity:specification
50 tpd to 1000 tpd:capacity:specification
2000 bph:production capacity:specification
iron:coating material:specification
3000 litre:capacity:specification
8 to 30 kgs / hr:capacity:specification
10-20 tph:capacity:specification
steer:brand:specification
all:automation grade:specification
extractor:type of testing machines:specification
self:brand:specification
5-5000 kg / hr:capacity:specification
52 mm to 92 mm:screw number:specification
single phase:motor type:specification
up to 400 g of filler per test:capacity:specification
15kw:power:specification
commercial expeller:machine type:specification
biobase:brand:specification
c & g:brand:specification
250kw:power:specification
1 ton:packaging size:specification
priflow scientific glass industry:brand:specification
kronoplast formaly known as wintech industries:brand:specification
up-to 4":size:specification
ram extruder:machine type:specification
3000 kg/hr:capacity:specification
compostable:material processed:specification
two layer:layer type:specification
carry bag:application:specification
liner bag:application:specification
agriculture film:application:specification
packaging film:application:specification
shrink film:application:specification
ldpe:material processed:specification
single screw:machine type:specification
granules:application:specification
pharma power:material processed:specification
as per machine:plastic processed:specification
oleo resin extraction plant:usage/application:specification
mech otech:brand:specification
fenugreek oleo resin extraction plant:usage/application:specification
electric and steam:power source:specification
turnkey project:machine type:specification
garlic soluble:solubility:specification
65 mm:capacity:specification
500:diameter:specification
18mm to 150mm:screw number:specification
kke:brand:specification
eie instruments:brand:specification
25, 50,100, 200 kgs per day:capacity:specification
50- 200 ton:capacity:specification
15-75 kg:capacity:specification
agrogen:brand:specification
nylon:type:specification
specific:brand:specification
50-80kg/ hr:capacity:specification
spp:brand:specification
unlimited:storage:specification
all:packaging size:specification
sres:brand:specification
penguin:brand:specification
25mm to 150mm:size:specification
all:screw type:specification
full automatic:automation grade:specification
innsale technik:brand:specification
30 tonne:capacity:specification
12,18,20,24,30,36,42 inches:capacity:specification
aar kay:brand:specification
extract rapidly 15-60 minutes , 32 samples can be extracted at the same time:result time (rapid kits):specification
oral swab:sample type:specification
crushing of oil seeds and oil seed cakes:usage/application:specification
h v jay:brand:specification
shri ram engineering works:brand:specification
200 gm per min:capacity:specification
lasertech international:brand:specification
supertuff:brand:specification
1.5 l:capacity:specification
50tpd - 1000 tpd:capacity:specification
medh:brand:specification
automatic solvent/fat extractor:usage/application:specification
analytical grade:grade standard:specification
1440 rpm:drive motor:specification
125 kwh:power consumption:specification
bitumen testing machine:type of testing machines:specification
screw rendom extruder:brand:specification
screw rendom extruder:phase:specification
screw rendom extruder:plastic processed:specification
extruder / cutting / printing / winding:usage/application:specification
vivaan:brand:specification
polyflex:brand:specification
rice bran solvent extraction plant:machine type:specification
no:icmr(govt) approved:specification
80 kg/h:capacity:specification
40 kg/h:capacity:specification
r:diameter:specification
70-350 kg/hr:production capacity:specification
parovi:brand:specification
special, high-temperature, engineering plastics:material:specification
motorized:type of testing machines:specification
48/96:no of unit to be tested:specification
customised:machine type:specification
unity engineers limited:brand:specification
for co-rotating twin screw extruder:screw design:specification
extruder - tyre industry:usage/application:specification
good:production capacity:specification
chine:screw design:specification
10:screw number:specification
dia. 25 mm to 150 mm and 400 mm length to 5000 meter length:diameter:specification
40 - 175 kw:power consumption:specification
100/kg per hour:capacity:specification
green tools:brand:specification
250kg/hour:capacity:specification
extrusion machinery:machine type:specification
35 kg (max.):capacity:specification
aulukya:brand:specification
150 tpd 2500 tpd:capacity:specification
mud n soil:material to be extruded:specification
500 mt/day:capacity:specification
100tpd-700tpd:capacity:specification
soya bean oil exraction plant:usage/application:specification
h. k.:brand:specification
solvent extraction continious plant:machine type:specification
sprctec:brand:specification
75 ltr:capacity:specification
230 v:power:specification
20 kg:weight:specification
civil lab:usage/application:specification
herbal medicine extraction plant in indore madhya pradesh:power source:specification
chemical industry:usage/application:specification
shakti engineering works:brand:specification
tea extraction:usage/application:specification
220 / 380 / 440 v:voltage:specification
380 / 440 v:voltage:specification
natural sweet extraction:usage/application:specification
natural sweetner extraction:usage/application:specification
whole leaf:cut size:specification
12 months:shelf life:specification
used for the determination of bitumen percentage in bituminous mixtures.:usage/application:specification
lpg:burner:specification
extraction of plant-based proteins, polyphenols, and antioxidants for dietary supplements.:usage/application:specification
380 /440 v:voltage:specification
380 / 415 v:voltage:specification
used for extracting, purifying, and processing quinoline-based alkaloids for pharmaceutical, chemica:usage/application:specification
50 to 1000 tones per day:capacity:specification
50 t0 1000 tones per day:capacity:specification
minimum 25 liters & onward as per requirement:capacity:specification
51-100 kg/hr:capacity:specification
20-60 ton/day:capacity:specification
10 tpd 100 tpd:capacity:specification
300 kg/hr:capacity:specification
1 kg/hr:capacity:specification
150 kg/hour:capacity:specification
48 kg/hour:capacity:specification
5kg/13min:material loading capacity:specification
1000 - 3500 rpm:capacity:specification
hdpe bag:material to be extruded:specification
150 kg/h:capacity:specification
sbm:brand:specification
sli:brand:specification
all types:plastic processed:specification
any:production capacity:specification
bright roto:brand:specification
polyamide:material:specification
ldpe:material to be extruded:specification
automated or semi-automatic:automation grade:specification
twin screw barrel:screw design:specification
1000ml,1500ml,2000ml:capacity:specification
50 hp to 135 hp:power consumption:specification
lab equipment:industry type:specification
50 to 400 kg per hour:capacity:specification
6 kw:drive motor:specification
100 t:material loading capacity (t):specification
gold melting:usage/application:specification
2 l:capacity:specification
extarction purpose:usage/application:specification
extraction of non ferrous metals:usage/application:specification
15 l:capacity:specification
multiseed oil extraction:material:specification
100gtam to 500:capacity:specification
accurate engineering works:brand:specification
adew:brand:specification
pinyang:brand:specification
puller,rough cutter ,belt conceyor,stretcher,finish cutting:material to be extruded:specification
50 ml, 100ml, 250ml:packaging size:specification
vented extruder machine:type:specification
mevented:brand:specification
herb:usage/application:specification
herbal extract:machine type:specification
60-250 kw:power consumption:specification
r p industries:brand:specification
300 mt/month:plant capacity:specification
mustard oil, ricebarn oil , sunflower , soyabean:usage/application:specification
25 to 5000 tons/day:capacity:specification
stretch & cling film,garbage bag film,shade net,banana bag film,shopping bag film etc:application:specification
vmosa:brand:specification
ve-bfex-01:model no.:specification
30 micron:film thickness:specification
2800 rpm:fan blower speed:specification
centrifuge hydro:extractor type:specification
sadguru enterprise:manufacturer:specification
125 kg/hour:output:specification
2:no. of layer:specification
2800 rpm:speed:specification
12 kg:weight: net weight:specification
��� automatic pulp ejection ��� non-drip spout ��� reverse function:features:specification
suitable for extracting juice from a variety of fruits and vegetables in commercial settings:applications:specification
5 kg/min:output:specification
340 mm (w) �� 270 mm (d) �� 360 mm (h):dimensions:specification
14 kg:gross weight:specification
80 hz:frequency:specification
30 hp:main motor:specification
90 inch:screw diameters:specification
60 hp:main motor:specification
140 inch:screw diameters:specification
ac drive and motor:driven type:specification
300 mm:die size:specification
as per reqquirement:capacity:specification
for bitumen test:type of testing machines:specification
oil mixing:usage/application:specification
bitumen testing equipment / asphalt testing machine:type of testing machines:specification
1.	���electrical bitumen extractor ��� accurate bitumen content testing machine��� 	2.	���high-speed electrical bitumen extractor for asphalt mix testing��� 	3.	���durable and efficient bitumen extraction machine for road construction labs��� 	4.	���lab-grade electrical bitumen extractor with variable speed control��� 	5.	���reliable bitumen testing equipment for quality asphalt analysis���:capacity:specification
tktts:brand:specification
tktts1001010:brand:specification
1:mould cavity:specification
1600 kw total power:power consumption:specification
115*9*4m:dimension:specification
aar kay engineering:brand:specification
parallel co-roatating:screw design:specification
70 kg/hr:capacity:specification
ms:basket material:specification
240 volt:voltage:specification
800 to 1000 rpm:speed:specification
electrc /wood:power source:specification
agarwood absolute:usage/application:specification
tailore made:design type:specification
used for extracting and purifying piperidine alkaloids for pharmaceutical and chemical intermediate:usage/application:specification
318/420:voltage:specification
semi auto metic:machine type:specification
used to extract high-purity peanut protein for food, nutraceutical, pharmaceutical, and feed applica:usage/application:specification
used for producing standardized papaya leaf extract (10���40% glycosides) for pharmaceutical, nutraceu:usage/application:specification
ayurvedic medicine manufacturing, herbal & botanical extract production, nutraceutical ingredients:usage/application:specification
herbal & ayurvedic extract manufacturing ,catechu/kattha/cutch extraction units ,natural dye & colou:usage/application:specification
herbal extract manufacturing ayurvedic formulations nutraceutical powders & capsules:usage/application:specification
herbal extract manufacturing , ayurvedic medicine production , nutraceutical formulations , cough sy:usage/application:specification
ayurvedic extract manufacturers, herbal & botanical processing units, nutraceutical ingredient pro:usage/application:specification
mechotech llp offers a state-of-the-art amla extract extraction plant, engineered for efficient:usage/application:specification
mecho tech llp:brand:specification
ayurvedic & herbal extract manufacturing , medicinal plant processing , nutraceutical:usage/application:specification
herbal extract manufacturing ,ayurvedic extracts (water & hydro-alcoholic) ,nutraceutical ingredient:usage/application:specification
catechu (kattha) manufacturing ,cutch/tannin extraction, ayurvedic & herbal extract production, natu:usage/application:specification
ayurvedic extract manufacturing, herbal & botanical processing, nutraceutical ingredient production:usage/application:specification
used for extracting high-purity tropane alkaloids such as atropine, scopolamine, and hyoscyamine fro:usage/application:specification
ayurvedic medicine and herbal formulation manufacturing, pharmaceutical resin extraction, nutraceuti:usage/application:specification
andrographis paniculata (kalmegh) extraction , herbal extract production , ayurvedic and botanical p:usage/application:specification
herbal andrographis extract production , kalmegh phytochemical processing , herbal immunity booster:usage/application:specification
herbal & ayurvedic extraction, nutraceutical and dietary supplement manufacturing:usage/application:specification
andrographis leaf extract manufacturing , kalmegh extract processing , herbal immunity booster extr:usage/application:specification
continuous:machine type:specification
aditya:brand:specification
stabdard:design type:specification
to extract oil from various raw material by using hexane as solvent:usage/application:specification
andrographis paniculata extract manufacturing, herbal & ayurvedic medicine processing, immunity-boos:usage/application:specification
annatto pigment extraction (bixin & norbixin), natural food color production:usage/application:specification
oil free vacuum pump 45 lpm:vacuum pump-:specification
acrylic chamber 12 / 24 port:moc-:specification
one way on/off:stopcocks-:specification
1:minimum order quantity:specification
as pre requetment:delivery time:specification
1800 x 600 x 1500 mm:dimension:specification
die size + 50 mm:max. opening (mm):specification
5 hp:cycle time:specification
2600 kn/260 t:crimping force (t):specification
55 mm:master die shoe length:specification
100 gm:size:specification
81 mm:screw dia:specification
2 layer:layer:specification
s:material:specification
25 mm to 150 mm:screw diameter.:specification
45:power(w):specification
vertical mounted:structure:specification
durable, latest technology:heavy duty:specification
customized as per need:power:specification
customized as per application:frequency:specification
construction,automotive,aerospace,electronics etc.:applications:specification
used in gold refining plants:usage/application:specification
fully automatic:automation:specification
single phase 220 watt:power supply:specification
10*10 sq. ft.:suitable for:specification
exact specifications may vary and shall be made available upon specific request.:note:specification
twin loader with dryer:optional equipment 1:specification
440 volts, 50 hz, a.c., three phase with neutral (can also be designed as per specific requirement):power supply:specification
water chiller:optional equipment 2:specification
two station pneumatic winder / fully automatic winder:optional equipment 6:specification
to produce extruded blown films:function:specification
heat exchanger:optional equipment 4:specification
panasonic - japan or equivalent:servo motor:specification
hdpe / ldpe / lldpe:final product:specification
30:1 (customized):screw l/d ratio:specification
corona treater:optional equipment 3:specification
extrusion process control:optional equipment 5:specification
-10 degreec to 40 degreec ( 14 degreef to 104 degreef ):working temperature:specification
ip54:ip protection class:specification
1/2 to 2.5 inch:pipe diameter:specification
hbk 140:gear box:specification
plc with hmi touchscreen interface:control system:specification
plc with hmi:control system:specification
masterbatch, compounding, r and d:application range:specification
plc, hmi touchscreen with automation features:control system:specification
pp:material compatibility:specification
automation grade:grad:specification
220 to 380v:voltage:specification
varsha enterprises:brand:specification
foam bags , foam rolls , packaging sheets , agricultural produce protection:application:specification
1500 mm:height:specification
50 mm:diameter:specification
304:material grade:specification
stainless steel. mild steel:material:specification
noodle extrude:uses:specification
32 kg approx.:weight:specification
dimensions: �� 300x500 mm:dimension:specification
400 mm:film width:specification
40 mm:screw diameter:specification
11 kw:motor power:specification
18.5 kw:motor power:specification
90 kw:motor power:specification
114 mm:screw diameter:specification
7.5 kw:motor power:specification
xlpe:material:specification
economy process solutions:brand:specification
usage:usage/application:specification
gle:brand:specification
4:number of cones:specification
no:diesel consumption:specification
solvent plant equipment:usage/application:specification
pragya:brand:specification
heavy-duty steel construction for durability:material:specification
h.b. lab instruments:brand:specification
vinksons india private limited:brand:specification
100=10000tpd:capacity:specification
ddgs:material:specification
antimalarial, antibacterial, anticancer, anti-inflammatory, antiviral and antifungal, cns agents:usage/application:specification
production of plant-based protein powders, meat analogues, and vegan food formulations:usage/application:specification
food, flavor, fragrance, pharmaceutical, and cosmetic industries:usage/application:specification
solvent recovery system:machine type:specification
3 ph x 240 v:power source:specification
cappro equipment:brand:specification
designed for efficient extraction and isolation of vinblastine used in anticancer drug manufacturing:usage/application:specification
ayurvedic medicine formulation, herbal extracts and tinctures, essential oils and oleoresins, nutr:usage/application:specification
applications nutraceuticals: immunity boosters, antioxidant supplements pharmaceuticals: digestive:usage/application:specification
ayurvedic extract manufacturing ,herbal liquid & powder extract production ,nutraceutical ingredient:usage/application:specification
herbal & botanical extracts, ayurvedic medicine production, nutraceutical raw materials, essential:usage/application:specification
mechotech llp offers a premium-grade amla extractor machine specially designed for efficient extract:usage/application:specification
ayurvedic & herbal extraction units,nutraceutical ingredient processing, cosmetic & personal care:usage/application:specification
extraction of phytochemicals and plant bio-actives, ayurvedic medicine formulations, herbal & nutr:usage/application:specification
herbal & botanical extract manufacturing ,ayurvedic extract production , nutraceutical ingredient p:usage/application:specification
semi auomatic:machine type:specification
seperate:control panel:specification
10 to 120 rpm:speed:specification
easy to operate, highly reliable:operate:specification
plastics for packaging, insulation, or other applications:usage.:specification
varsha enterprise:brand:specification
plasma:type of instruments:specification
spe positive pressure manifold:color:specification
lcmsms:model number:specification
40 hp:main motor:specification
100 inch:screw diameters:specification
b011:model name/number:specification
144 samples:spe cartridge size:specification
52/18:model number:specification
1 kg to 5 kg:capacity:specification
800kg - 2ton/day:capacity:specification
6:number of tray:specification
10 mm-250 mm:screw diameter:specification
plastic extruder machine:machine type:specification
550 mm:diameter:specification
water/solvent extraction:usage/application:specification
axial extruder:machine type:specification
pp, hdpe, pvc, nylon, ps, abs, pu:plastic processed:specification
2 (opposite rotation):screw number:specification
co roating:screw design:specification
2:number of shelves:specification
rudra industries:brand:specification
850 rpm:speed:specification
3:number of spindles:specification
cable extruder machine:machine type:specification
3 ton:capacity:specification
electric source:power source:specification
ss 316/304:machine type:specification
curcumin oleoresin extraction plant:usage/application:specification
mecho techh llp:brand:specification
herbal extract production , ayurvedic medicine manufacturing , nutraceutical ingredient formulation:usage/application:specification
herbal extract manufacturing , ayurvedic formulations , nutraceutical ingredients ,cough syrup & bro:usage/application:specification
ayurvedic and herbal extracts, nutraceutical powders, natural dye and tanning industries, food addit:usage/application:specification
370/415 v:voltage:specification
ayurvedic & herbal medicine manufacturers , nutraceutical & dietary supplement producers , cosmetic:usage/application:specification
ac 20 hp:main drive ac:specification
rzm machinery:brand:specification
���	ayurvedic resin processing, pharmaceutical extraction of boswellia serrata, nutraceutical and herb:usage/application:specification
boswellia serrata (salai guggul) extract production, ayurvedic formulation manufacturing:usage/application:specification
ayurvedic extract manufacturing ,botanical & phytochemical production ,natural food-grade color & fl:usage/application:specification
herbal & ayurvedic extract manufacturing, phytochemical & botanical extraction, nutraceutical, dieta:usage/application:specification
cutosmized:design type:specification
extraction of annatto pigments and oleoresins for industrial use, natural food color production:usage/application:specification
industrial-scale annatto pigment and oleoresin extraction, herbal and botanical extract production:usage/application:specification
industrial extraction of natural colors and pigments, food color production for beverages, dairy:usage/application:specification
andrographis paniculata extract manufacturing , ayurvedic & herbal immunity-booster production , nut:usage/application:specification
phytochemical extraction and concentration , herbal and botanical extract manufacturing , nutraceuti:usage/application:specification
kalmegh extract manufacturing, ayurvedic & herbal formulation processing, immunity-boosting herbal i:usage/application:specification
���	natural food color extraction, herbal and botanical extraction units:usage/application:specification
herbal immunity booster production, ayurvedic medicine manufacturing, nutraceutical & wellness suppl:usage/application:specification
andrographis paniculata extract manufacturing, kalmegh herbal extract production units, ayurvedic me:usage/application:specification
kalmegh herbal extract manufacturing , ayurvedic medicine & immunity-booster formulation units, nutr:usage/application:specification
ayurvedic medicine manufacturing, herbal extract production (kalmegh extract), nutraceutical & dieta:usage/application:specification
350 t:weight:specification
28 inches:basket diameter:specification
guru nanak mechanical workshop:brand:specification
7hp:power:specification
5000kg:production capacity:specification
330 v:voltage:specification
gas/wood:power source:specification
ellagic acid extraction:usage/application:specification
7x10x3:dimension:specification
s.s ( stailness steel):material:specification
edr-asm05:model name/number:specification
veterinary formulations for its parasympathomimetic properties, promoting digestion and improving ga:usage/application:specification
used for extracting, isolating, and purifying pyrrolizidine alkaloids from pa-rich medicinal plants:usage/application:specification
380 / 440:voltage:specification
traditional medicines for digestive disorders, muscle relaxation, and stress relief:usage/application:specification
used in nutraceuticals, functional foods, beverages, pharmaceuticals, animal feed, plant-based meat:usage/application:specification
used for extracting high-purity styrax benzoin absolute from natural gum and resin for perfumery, co:usage/application:specification
herbal & ayurvedic extracts, plant & root extraction, spice oleoresins, natural food colors:usage/application:specification
mech o tech llpele:brand:specification
herbal & ayurvedic extract manufacturing ,pan masala & gutkha ingredient industry ,natural dye & tan:usage/application:specification
ayurvedic medicine manufacturing, herbal & botanical extract production, nutraceutical ingredient:usage/application:specification
catechu (kattha) production , cutch manufacturing ,tannin & polyphenol extraction , herbal & ayurved:usage/application:specification
cutch (katha by-product) extraction ,tannin & polyphenol extraction, natural dye & wood-based extrac:usage/application:specification
extraction of ayurvedic and herbal drugs, nutraceutical and dietary supplement production, herbal:usage/application:specification
ayurvedic & herbal medicine manufacturing , nutraceutical & dietary supplement units , food, flavor:usage/application:specification
herbal & ayurvedic leaf extracts, nutraceutical ingredient processing, cosmetic & personal care form:usage/application:specification
ayurvedic & herbal medicines, nutraceutical extracts, cosmetic & personal care formulations:usage/application:specification
frankincense resin extract production, ayurvedic and herbal medicine manufacturing, nutraceuticals:usage/application:specification
catechu (kattha) manufacturing ,cutch extract production ,tannin & polyphenol extraction ,herbal & a:usage/application:specification
ayurvedic extract manufacturing , herbal and botanical processing , nutraceutical ingredient product:usage/application:specification
kalmegh extract manufacturing , andrographis paniculata extraction , immune-booster herbal extract:usage/application:specification
s.s.:material:specification
ayurvedic medicine manufacturing, pharmaceutical herbal extraction, nutraceutical and herbal supplem:usage/application:specification
���	herbal extract manufacturing, ayurvedic medicine production, nutraceutical formulation, pharma-gra:usage/application:specification
boswellia serrata resin extraction, ayurvedic extract manufacturing, herbal & botanical extraction:usage/application:specification
ai35:model name/number:specification
ayurvedic medicine manufacturing, herbal & botanical extraction, nutraceutical ingredient production:usage/application:specification
ayurvedic medicine manufacturing, pharmaceutical herbal extraction, nutraceutical production, resear:usage/application:specification
ayurvedic medicine production, pharmaceutical resin extraction, herbal and nutraceutical manufacturi:usage/application:specification
boswellia serrata resin extraction, ayurvedic and herbal formulation manufacturing:usage/application:specification
extract oil from oil seed/ oil cakes and rice bran:usage/application:specification
andrographis paniculata (kalmegh) extract production, ayurvedic immunity-booster formulations, herba:usage/application:specification
annatto oleoresin extraction (bixin), natural food color manufacturing, spice & herbal extract:usage/application:specification
���	industrial-scale annatto pigment and oleoresin extraction, natural food color production, cosmetic:usage/application:specification
annatto seed processing and pigment extraction, natural food color production (bixin & norbixin):usage/application:specification
extraction of annatto oleoresins for industrial use, natural food color production for dairy:usage/application:specification
extraction of natural annatto pigments and oleoresin, natural food color production for beverages:usage/application:specification
compounding:application:specification
masterbatch:application:specification
sheet extruder:machine type:specification
food:material processed:specification
sheet:application:specification
800 kg/hour:production capacity:specification
500 mm diameter, 6 m height:size:specification
stainless steel, mild steel, carbon steel:material:specification
pharmaceutical & chemical manufacturing:usage/application:specification
oleoresin extraction process:usage/application:specification
usafe:usage/application:specification
red:color:specification
semi automized:automation grade:specification
natural food color production, herbal and botanical pigment extraction, textile dye extraction:usage/application:specification
boswellia serrata (salai guggul) resin extraction, herbal & botanical extract manufacturing:usage/application:specification
herbal and botanical extract production, natural pigment and color extraction, essential oils:usage/application:specification
���	extraction of natural bixa orellana pigments (bixin & norbixin), food color production:usage/application:specification
extraction of natural dyes for industrial and food-grade applications, production of herbal:usage/application:specification
herbal medicine manufacturing , ayurvedic extract production , poly-herbal and single-herb formula:usage/application:specification
industrial extraction of annatto oleoresin, natural food color and pigment production, cosmetic:usage/application:specification
semi automized:machine type:specification
extract oil from oil seed / cake / rice bran:usage/application:specification
���	industrial extraction of annatto pigments and oleoresin, natural food color manufacturing:usage/application:specification
oil extraction plant:usage/application:specification
natural food colorant extraction, pharma-grade pigment processing, cosmetic ingredient manufacturing:usage/application:specification
annatto seed pigment extraction, natural food colors manufacturing, spice and herbal processing:usage/application:specification
natural food color manufacturing, spice and herbal extract processing:usage/application:specification
annatto herbal extract production, natural food color manufacturing, botanical & herbal extraction:usage/application:specification
andrographis/kalmegh extract manufacturing, herbal & ayurvedic medicine production, nutraceutical &:usage/application:specification
ayurvedic immunity booster formulations, herbal extract production, nutraceutical & phytomedicine in:usage/application:specification
medicinal plant extract manufacturing, ayurvedic & siddha medicine production, nutraceutical & herba:usage/application:specification
kalmegh extract manufacturing, herbal & ayurvedic medicine production, immunity-booster extract plan:usage/application:specification
applications kalmegh herbal extract manufacturing , ayurvedic medicine & immunity-booster formulatio:usage/application:specification
alfa:brand:specification
herbal & ayurvedic extract manufacturing, botanical & phytochemical processing, nutraceutical and di:usage/application:specification
11 kw - 40 kw:main drive ac:specification
twin screw extruder:design type:specification
20 mm - 25 mm - 32 mm:diameter millimeter:specification
1 year manufacturing defect:warranty:specification
wts 90 wts 110 wts 170 wts 200 wts 250 wts 52/18 wts 52/25 wts 65/18 wts 65/22:model name/number:specification
depend on output:line speed:specification
as per isi norms & non isi also:thickness:specification
pvc pipe:material to be extruded:specification
free of cost - no extra cost for installation:installation services:specification
ss 304 316:material:specification
fluidhydro:brand:specification
250w:power:specification
used in formulations with anti-inflammatory, antioxidant, and detoxifying properties:usage/application:specification
hypertension (high blood pressure) cerebral ischemia and vascular disorders vertigo and circulatio:usage/application:specification
flavor extracts, colorants, and herbal infusions, extraction of therapeutic compounds:usage/application:specification
ayurvedic manufacturing units, herbal extract production, nutraceutical ingredient processing, pha:usage/application:specification
4*7*3:dimension:specification
herbal & ayurvedic extracts, nutraceutical ingredient processing, cosmetics & personal care:usage/application:specification
herbal & ayurvedic medicine manufacturing , nutraceutical ingredients production , pharmaceutical ra:usage/application:specification
herbal extract manufacturing, ayurvedic medicine production, nutraceutical ingredient processing:usage/application:specification
mech o tech llp offers a high-performance adhatoda vasica (vasaka) extraction plant designed for eff:usage/application:specification
khair wood extraction , catechu (kattha) production ,cutch manufacturing , tannin & polyphenol extra:usage/application:specification
herbal extract manufacturing ,ayurvedic medicine production ,food & nutraceutical industries, tannin:usage/application:specification
ayurvedic medicine formulations, boswellia serrata extract production, nutraceuticals and dietary:usage/application:specification
4:number of rollers:specification
granules:form:specification
blow film:usage/application:specification
80%:purity:specification
ayurvedic formulation manufacturing, herbal & botanical extract production:usage/application:specification
extraction of medicinal and herbal plants , ayurvedic and botanical extract manufacturing , phytoch:usage/application:specification
semi automatiuc:machine type:specification
ayurvedic and herbal medicine production, pharmaceutical extraction of medicinal compounds, nutraceu:usage/application:specification
ayurvedic & herbal extract manufacturing, nutraceutical ingredient processing:usage/application:specification
tirupati:brand:specification
tube:frequency:specification
1 ton per day:capacity:specification
viahva glabalx:brand:specification
s.r asia-pacific:brand:specification
constructions:type of testing machines:specification
1-50l/h:capacity:specification
pvdf:material:specification
saini:brand/make:specification
pingaxh:brand:specification
6-10 kg:capacity:specification
up 20 kg:capacity:specification
1.2 kg per min:capacity:specification
outdoor:usage/application:specification
ctk biotech:brand:specification
compounding & reprocessing:plastic processed:specification
fast growth:other necessities:specification
120 kg/hour:capacity:specification
pvc,ld,pp,abs,nylon,hdpe,pet,pc all type of material:material:specification
12 inches to 60 inches:capacity:specification
350 cylinder filling capacity of 7nm3:flow rate(lpm)/(nm3/hr):specification
as per customer requirement:screw design:specification
1 to 500kg:capacity:specification
mechno tech:brand:specification
97+-3%:purity of oxygen:specification
techmks:brand:specification
ss/mild steel:material:specification
s.s. engineering works:brand:specification
650 kg:machine weight:specification
jagdish exports:brand:specification
home:suitable for:specification
elecon:brand:specification
customized models:capacity:specification
sunflower seeds, cotton seeds, soyabeen seeds, palm oil seeds etc:usage/application:specification
chinese:brand:specification
2-5 hp:power consumption:specification
p r industries:brand:specification
kumar manufacturing company:brand:specification
wire and cable machinery for house hold cable manufacturing:usage/application:specification
ss engineering workd:brand:specification
100-200kg per hour:capacity:specification
10 kg to any:capacity:specification
customised:production capacity:specification
dev industries:brand:specification
automatic,semi-automatic:machine type:specification
kalinga:brand:specification
110 kw:power consumption (kw):specification
50 kg/round:capacity:specification
10 tpd to 500 tpd:capacity:specification
100 kg/hour:capacity:specification
200 kw per hour (approx.):power consumption:specification
m.s.and s.s.:material:specification
12 kg/hour:production capacity:specification
hasmukh engineering works:brand:specification
slach:brand:specification
60 kgs/hr:production capacity:specification
12kw:power:specification
ms body:material:specification
25 - 50 kg:capacity:specification
3 kg in per min:capacity:specification
mono layer blown film machine:machine type:specification
extraction of herbal bioactive compounds and essential oils, production of herbal medicines:usage/application:specification
extraction of herbal and botanical colors for food and beverages, production of natural pigments:usage/application:specification
natural herbal extract production , botanical and phytochemical extracts , nutraceutical and dietar:usage/application:specification
natural medicine extraction, ayurvedic & herbal formulation manufacturing, nutraceutical & health su:usage/application:specification
oil cooling:usage/application:specification
���	natural food color extraction, herbal and botanical dye production, textile dye extraction:usage/application:specification
kalmegh extract production, herbal and ayurvedic formulations, nutraceutical bioactive extraction, p:usage/application:specification
mechtech llp:brand:specification
andrographis paniculata (kalmegh) extract manufacturing, herbal and ayurvedic extract production, nu:usage/application:specification
ss:automation grade:specification
100 hp:power source:specification
ashwagandha extract:usage/application:specification
60 hp:power source:specification
ss-304l:brand:specification
ss extractor:machine type:specification
50 to 100 degree celsius:heating range:specification
to make electric wire:application:specification
polished:finished type:specification
digital:display:specification
only new:i deal in:specification
50 kg .:weight:specification
150kg:4.,5:specification
botanical plastics pvt ltd:brand:specification
botanical plastics pvt. ltd.:brand:specification
food & packaging:usage/application:specification
1600 kw:voltage:specification
12~50 micron:film thickness:specification
10000 l:capacity:specification
depends on capacity---- range starts from rs 15,00,000:price range:specification
melts the raw plastic material (such as ldpe, lldpe, or hdpe).:extruder:specification
shapes the molten plastic into a tube as it is forced out.:circular die::specification
films for food, textiles, heavy-duty industrial packaging, and bags for various products.:packaging::specification
greenhouse films, seed packaging films, and plant protection sleeves.:agriculture::specification
films for wrapping pallets, creating shrink wrap, and express bags.:logistics::specification
loose:pack type:specification
277:voltage::specification
p-n:phase::specification
refining raw gold:usage:specification
jeweltech recycling solutions private limited:brand:specification
7 kg:capacity:specification
floating fish feed:material to be extruded:specification
mds:brand:specification
30 kg to 250 kg:capacity:specification
pest control and pest repellent in all crops:usage/application:specification
up to 300 kg / hr:capacity:specification
steel:material to be extruded:specification
big bull:brand:specification
1:screw number:specification
30 kg/hrs:production capacity:specification
educational trainer:usage/application:specification
any type:profile type:specification
70 to 500 tpd:capacity:specification
factory:usage/application:specification
100 kg - 4000 kg:capacity:specification
extractor:machine type:specification
jgi:brand:specification
floatiing fish feed:usage/application:specification
velos:brand:specification
fressia macross japan:brand:specification
3:screw number:specification
wire straightening:usage/application:specification
local area:service location:specification
arkchem:brand:specification
various:capacity:specification
pvc compounding extruder:usage/application:specification
220kg per hour:capacity:specification
komal plastic:brand:specification
xps foam board:material to be extruded:specification
ruby plastic:brand:specification
2hp:capacity:specification
50hp:machine power:specification
100 litter input to as per req:capacity:specification
aba:material to be extruded:specification
400 tpd:capacity:specification
1000 lph:capacity:specification
solvent extraction plants:brand:specification
depend on the project:capacity:specification
5 to 200kg:capacity:specification
400 g:capacity:specification
150 kg per hour:capacity:specification
making carry bag and plastic bag:usage/application:specification
packaging products:usage/application:specification
for extracting oil from cake and soybean:usage/application:specification
dana plant:type:specification
sp70:screw number:specification
50 hrc:hardness:specification
110 kg:weight:specification
windsor:brand:specification
0-40 kw:machine power (kw):specification
double-screw:screw design:specification
depend on the project:brand:specification
depend on the project:usage/application:specification
depend on the project:machine type:specification
steel:cooler material:specification
prime margo:brand:specification
compact countertop heating courses with insulated firebrick walls to maintain high temperatures:type of furnace:specification
1 kg to 100 kg per day:capacity:specification
1 kg per day:capacity:specification
ms, ss, etc:material:specification
turn key solution:business / industry type:specification
5 kg gold:capacity:specification
250kg:capacity:specification
effective separation of fines from miscella:usage/application:specification
up to 200 kg:capacity:specification
1 kg,2kg,3kg,5kg,10kg,15 kg,20kg,25kg,50kg,100 kg:capacity:specification
400 - 700 kg/h:production capacity:specification
blown film machine:machine type:specification
bulpower:brand:specification
the toxicity characteristic leaching procedure (tclp) is a soil sample extraction procedure for chem:usage/application:specification
35kg:weight:specification
mild steel + stainless steel:material:specification
naaa:electrical unit consumption:specification
naaaa:max. vacuum:specification
20 1:screw l d ratio:specification
electric:heating mode:specification
natural products extraction:usage/application:specification
electrical, solid fuel:power source:specification
50hz, 60hz:frequency:specification
6 bolt:no. of screws:specification
110 / 220 / 380 / 440 v:voltage:specification
ss, glass, pp:material:specification
3 phase, 30 hp, 1440 rpm:expeller motor:specification
8'6" x 4'1" x 8'8":dimension (lxbxh):specification
goyum mk 3:model:specification
4200 kgs:weight:specification
dia 6" x 33" long:chamber size:specification
5.52 rpm:screw speed:specification
25:1:l/d ratio:specification
15 kw:motor power:specification
135 kg/hr:max. output pvc:specification
180 kg/hr:max. output pvc:specification
91 mm:screw diameter:specification
520 kg/hr:max. output pvc:specification
60 kw:motor power:specification
110 mm:pipe range single die:specification
63 mm:pipe range twin die:specification
powder coated:surface finish:specification
plastic industry,processing machinery,rubber and thermoplastics:application:specification
industrial application:usage:specification
90mm:die size:specification
24v:voltage:specification
eco / evolve / elevate:series available:specification
800kg - 2ton/day:production capacity.:specification
800kg - 2ton/day:capacity.:specification
non ibc se3hr 900:model number:specification
cable:application:specification
pvc:material processed:specification
rice brand, cotton seed, mustard seeds, all types:brand:specification
comercial:usage/application:specification
asha engineering works:manufactured by:specification
100kg plant:capacity:specification
100kg per hour:capacity:specification
fishing net:filament application:specification
bird net:filament application:specification
drying garment:usage/application:specification
4kw:power:specification
160kw:power consumption:specification
zv92:model number:specification
shree bhavani engineering:brand:specification
78 hp:motor:specification
zv30:model number:specification
export packing:packaging type:specification
electric source:power:specification
80 degree c:heating range:specification
can be used in gold industry:uses:specification
liquid-liquid:extraction type:specification
solvent:extraction method:specification
10kg/hr:production capacity:specification
285:packaging size:specification
food packaging:usage/application:specification
100 - 30 kg/hr:capacity:specification
automatic aba two layer blown film machine:machine type:specification
cosmetic packaging,diapers,heavy duty sacks,milk/water pouch,lamination,masking film etc:application:specification
metal recycling plant:type:specification
5 (ton/hr):capacity:specification
55 hz:frequency:specification
jinan lijiang automation equipment co., ltd.:capacity:specification
apet:material:specification
1 kg gold:capacity:specification
5 kg/hour:capacity:specification
1kg to 3kg:capacity:specification
k.g enterprise:brand:specification
55 kg:capacity:specification
extraction of oxide sulphide:usage/application:specification
excellent:capacity:specification
ss steels 314:plastic processed:specification
350 kg to 400 kg:production capacity:specification
500 - 5000 lits:capacity:specification
20:capacity:specification
mini expeller:machine type:specification
upvc:plastic processed:specification
vital force:brand:specification
5480:production capacity:specification
electrolyte:assays:specification
2kg to 20kgs:capacity:specification
south india mat machineries:brand:specification
5 to 6 kg/hr:capacity:specification
1-2 kw:power consumption:specification
2litre:capacity:specification
prasad plast:brand:specification
15 kg per day:capacity:specification
1 kg to 200 kg:capacity:specification
1kg 10kg:capacity:specification
italian model:brand:specification
30,000.00:plastic processed:specification
kear:brand:specification
all over india:service location:specification
1kg-100kg:capacity:specification
carbon steel/stainless steel:material:specification
200-400kg/hr:capacity:specification
60 to 65 kg/hr:capacity:specification
kiran extrusion:brand:specification
neelam:brand:specification
rosendahl:brand:specification
100-1000:capacity:specification
pp plastic:type:specification
10 gram to 20 kg:capacity:specification
500 gram to 50 kg:capacity:specification
500 ltrs.:capacity:specification
1000g~1500g:capacity:specification
dhruv fabrotech:brand:specification
2300rpm:capacity:specification
soil:type of testing machines:specification
400 kg to 450 kg:capacity:specification
ss:machine type:specification
cr12mov:screw number:specification
stainless steel:material to be extruded:specification
mulch film , mulching sheet , pond liner, ldpe tarpaulin, and other applications:usage/application:specification
100 to 250 kg /hr:production capacity:specification
tyre building machine:machine type:specification
best engineering:brand:specification
1.5kg:capacity:specification
extrusion:welding type:specification
5:1:l/d ratio:specification
noble engineering:brand:specification
infiniti extrusion technik:brand:specification
normit:brand:specification
min 100 kg to 200 kg:capacity:specification
continuous and batch type:machine type:specification
15 kg/hour:capacity:specification
30hp:machine power:specification
0.8w:input voltage:specification
fully automatic:operation mode:specification
electericalfr:power source:specification
kalmegh extract manufacturing , ayurvedic and herbal medicine processing ,i mmunity-booster extract:usage/application:specification
andrographis extract manufacturing, herbal medicine & ayurvedic formulation units, nutraceutical and:usage/application:specification
annatto seed cleaning and pre-processing, natural color extraction industry, spice processing units:usage/application:specification
ayurvedic medicine manufacturing, herbal supplement and nutraceutical production, botanical & phytoc:usage/application:specification
natural food color extraction and production, herbal and botanical pigment manufacturing:usage/application:specification
ayurvedic & herbal medicine extraction, nutraceutical raw material production:usage/application:specification
extraction of annatto pigments (bixin & norbixin), herbal and botanical extract production:usage/application:specification
���	industrial-scale extraction of annatto pigments and oleoresins, natural food color product[on:usage/application:specification
botanical extract manufacturing , ayurvedic & herbal extract production , phytochemical processing u:usage/application:specification
ayurvedic & herbal medicine production ,nutraceutical & health supplement manufacturing , phytochemi:usage/application:specification
electrial:power source:specification
ayurvedic & herbal extract manufacturing, phytochemical and botanical extraction units, nutraceutica:usage/application:specification
ayurvedic and herbal medicine manufacturing, botanical and phytochemical extract production, nutrace:usage/application:specification
ayurvedic & herbal extract manufacturing, botanical & phytochemical processing, nutraceutical ingred:usage/application:specification
extraction of copper from its ore:usage/application:specification
vertical:design type:specification
440volt:voltage:specification
sde:brand:specification
3mm to 25mm:sheet thickness:specification
single phase,3 phase:phase:specification
pp material:material:specification
wet type:feed type:specification
50 mm:die diameter:specification
24 1:screw l d ratio:specification
hpel:brand:specification
three layer cable extruder:machine type:specification
250 kw:machine power (kw):specification
150hz:frequency:specification
silver and red:colour:specification
no display:display:specification
fuel and electricity:power source:specification
portable:type:specification
purification:application:specification
tj-750d:model:specification
900mm:roller length:specification
85:weight:specification
aquamat 10.1:model name/number:specification
5kg/13min:capacity:specification
150kg per hour:capacity:specification
50hp:power consumption:specification
2500kg:capacity:specification
6tpd:capacity:specification
chemical:usage/application:specification
1:number of filling heads:specification
6 kg:air consumption:specification
fully automatic:filling system:specification
as per requirement:usage/application:specification
80 -150 kg/hr:capacity:specification
full automatic:machine type:specification
50 -60 hz:frequency:specification
twin extruder machine:machine type:specification
26/36/48:capacity:specification
up to 5kg:capacity:specification
stainless steel, mild steel:material:specification
innotech machines:brand:specification
depends on material:capacity:specification
hyway:brand:specification
300 mm - 2000 mm:capacity:specification
vikrant industries:brand:specification
200 -10000:capacity:specification
as per requirement:filling material:specification
as per region and requirement:voltage:specification
1.5litre:capacity:specification
150ton/hour:capacity:specification
60000l/h:capacity:specification
1-5 ton/day:capacity:specification
on request:machine type:specification
on request:packaging type:specification
10 x 3 = 30 packages:capacity:specification
300 kgs:capacity:specification
50 - 200 kg/hr:capacity:specification
premium quality paint:finishing:specification
on request:frequency:specification
abc film:material to be extruded:specification
three phase electric motor:drive motor:specification
220/min:capacity:specification
5000 litre:capacity:specification
3 tons oil seeds per day:capacity:specification
abb or fuji:frequency:specification
ms/ss/rubber line/hallar etc:material:specification
100-150 kg/hr:capacity:specification
caprolactam extraction:usage/application:specification
120 kg:capacity:specification
biodegradable:material:specification
pvc, pp, hdpe, ldpe:plastic processed:specification
25 - 80 ( kg/hr ):capacity:specification
0.5 - 5 kg/hr:capacity:specification
1200 kg per hour:capacity:specification
15 tph:capacity:specification
20 tph:capacity:specification
standard:automation grade:specification
standard:screw number:specification
grocery:usage/application:specification
12 kg:capacity:specification
stenless steel:material:specification
70-100 tpd:capacity:specification
industrial:machine type:specification
plastic recycling machine:type:specification
continuous type:machine type:specification
aspl:brand:specification
industrial:industry type:specification
plc base:automation grade:specification
ld foam film benner, ld foam wed, ld foam liner:application:specification
lldpe:material processed:specification
hdpe:material processed:specification
costumized:capacity:specification
rajesh enterprises:brand:specification
pvc:application:specification
conical:screw type:specification
twin screw:machine type:specification
200 degree c:temperature:specification
extraction & solvent recovery:usage/application:specification
vacuum:pressure:specification
cosmetics, pharmaceuticals:usage/application:specification
extratcion:machine type:specification
1000 kg:weight:specification
spiral 2l:die type:specification
2x15mm:main motor:specification
2x65mm:screw diameter:specification
tje 32:model number:specification
monofilament plant:line type:specification
4kw:power consumption:specification
aqua regia:chemical method:specification
pp/mild steel:material:specification
inflatable blower:blower type:specification
1500:speed(rpm):specification
1 kg to 100 kg:capacity(kg):specification
316 ss:material:specification
4 v:voltage:specification
8 watt:power:specification
electric blower:power source:specification
1to100kg:capacity:specification
simonia:color:specification
aadhira enterprises:brand:specification
13mm:font roll diameter:specification
12mm:font roll diameter:specification
60 to 85:heating range:specification
1600 kg to 2000 kg:weight:specification
1500 sq ft:dimension:specification
900 sq ft:dimension:specification
80 hp:power source:specification
bubble packaging:packaging type:specification
bubbles:packaging type:specification
18 liter:capacity:specification
150 mm:thickness:specification
24:1:l/d ratio:specification
50 rpm:speed:specification
11.5 kw:motor power:specification
65 mm:screw size:specification
ebonite,or nitrile ebonite:rubber type:specification
p.p:bottles:specification
silver and blue:color:specification
8.6 mtr:width:specification
starting from 50 tons/day:capacity(ton/day):specification
12~50:film thickness:specification
600 mm:film width:specification
1300 mm:roller size:specification
ashok:brand:specification
20:film thickness:specification
2 layer aba:layer:specification
99.80%:purity:specification
1200 rpm:speed:specification
21.5 mm:screw diameter:specification
skid mounded:mounting:specification
pa6, pa66, abs,pbi, peek, pp:plastic processed:specification
pp:plastic processed:specification
rrbd:brand:specification
seed extractor:type of machines:specification
300 c:temperature deg celsius:specification
india:place of origin:specification
continous:frequency:specification
820 mm:screw length:specification
40:screw l/d:specification
75 nm:screw torque:specification
zv20:model name/number:specification
zv62:model name/number:specification
390 v:voltage:specification
agriculture:usage/application:specification
l650mm*w300mm*h500mm:machine dimensions:specification
infinite speed regulation, automatic tensioning:control method:specification
16*2mm:screw diameter:specification
250w:motor power:specification
m k engineering works:brand:specification
5 hp:power in hp:specification
solid-liquid:extraction type:specification
swami vessels:brand:specification
500 gm:capacity(kg):specification
herbal products:application type:specification
solvent-based:machine type:specification
24 samples:capacity:specification
aleena test:brand:specification
500 kg:capacity:specification
custimised:design type:specification
1000tan:capacity:specification
power cable:application:specification
house wire:application:specification
control cable:application:specification
data cable:application:specification
automotive wire:application:specification
insulation:application:specification
xlpe:material processed:specification
fr/hr:material processed:specification
aspl make:brand:specification
50 degree c:temperature:specification
gmp:design type:specification
as per capacity:steam supply:specification
customzed:design type:specification
industrioal:usage/application:specification
16:no of position:specification
5ml:spe cartridge size:specification
no smell, no smoke:exhausted gas:specification
pump:filtration system:specification
80rpm:screw speed:specification
500 mm:niproll size:specification
d 45:model name:specification
ld27:screw:specification
15 kw:heating load:specification
pan india:location:specification
industrial:application type:specification
1 kg to 1000 kg:capacity(kg):specification
chemical:recovery method:specification
electrical / solid fuel:power consumption:specification
ss 316 / ss 304 / ms:machine body material:specification
35mm-45mm:screw diameter:specification
ylem energy:brand:specification
30 x 30 x 30:dimension:specification
export quality:ylem energy heavy duty:specification
15kg/hr:production capacity:specification
700 mm:film width:specification
aqua regia:refining method:specification
cyclone separator:filtration:specification
yes:vacuum system:specification
10 tons:capacity:specification
25 kgs:no of unit to be tested:specification
air purifier:type:specification
380���415v, 50hz, three-phase:voltage:specification
lab-scale to industrial-scale:size:specification
botanical / herbal extraction, oleoresin extraction, api intermediate extraction, specialty chemical:usage/application:specification
cta:brand:specification
extractors (8 kl), slurry tanks, solvent tanks:material:specification
100 mm:die diameter:specification
based on capacity:motor:specification
pp, hdpe, ldpe:material:specification
tr/tp/75:model no:specification
146.4 kw:power consumption:specification
as per power:voltage:specification
tje 38:model number:specification
90 mm:screw diameter:specification
zipper, industrial brush, artificial hair, broom, etc.:usage/application:specification
plc:control:specification
singal phase:phase:specification
gold only:material capability:specification
10 l:tank capacity:specification
wet and dry:type:specification
1000 w:input power:specification
4 bar:pump pressure:specification
1kg to 1000kg:capacity(kg):specification
signal phase:motor power:specification
2kw:power:specification
10to100kg:capacity:specification
indian make:brand:specification
1 kg to 1000 kg:capacity:specification
10to1000kg:capacity:specification
plastic:tank material:specification
40 l/s:air flow:specification
workshop:application:specification
99.999 %:purity:specification
750 sq ft:dimension:specification
240 kw:voltage:specification
for silver refining:usage:specification
300 kg hourly:sphegetti extruder:specification
6000kg:weight:specification
0.52 mpa:electrowinning tank pressure:specification
industrial:application/usage:specification
12kw:voltage:specification
440v:power:specification
20kw:machine power(kw):specification
yes:recyclable:specification
18":max bag width:specification
24 kw:connected load:specification
yes:drive system:specification
2":die size:specification
42":roller size:specification
38 hp:power consumption:specification
120 microns:film thickness:specification
500gm:capacity:specification
titanium, pp and borosilicate glass:body material:specification
seed conditioning / cooking machine:product type:specification
gold & silver:material processed:specification
hand operated:power source:specification
soybean:raw material:specification
single or three:phase:specification
45 mm:screw diameter (mm):specification
tumbler type:machine type:specification
yes:fume control system:specification
250 kg - 5tpd:capacity:specification
high purity curcumin extraction:usage/application:specification
150 mm:film thickness (micron):specification
110 degree c:temperature:specification
based on the requirement:voltage:specification
52mm ckts-110 ,125 & 65mm ckts-150, 170:screw number:specification
extraction of copper:usage/application:specification
10 to 500tph:capacity:specification
packet:packaging type:specification
extruder:screw design:specification
multicolor:color:specification
radhekrishna standard:screw design:specification
500gram, to 100 kg:capacity:specification
twin screw design:screw design:specification
chemical industry:industry type:specification
electric:type:specification
120 ml:capacity:specification
up to 600 kg / batch:capacity:specification
1 kg,5 kg,20 kg:packaging size:specification
hdpe bottle:packaging type:specification
jakplast:brand:specification
rse:brand:specification
1liter:capacity:specification
kj:machine type:specification
pharmaceutical machines:model name/number:specification
chemical, acid, water:storage material:specification
gold refine process:usage/application:specification
swastic:brand:specification
paavan:brand:specification
200 ton:capacity:specification
1000g - 1500g:capacity:specification
kl:frequency:specification
nsaw:brand:specification
3kg per day:capacity:specification
70-1000 tpd:capacity:specification
die/ aluminium:material to be extruded:specification
ms (body):material:specification
rcv:brand:specification
nomoto:brand:specification
pck:brand:specification
2 screws:screw number:specification
1 to 5 kg:capacity:specification
1 to 100kg / day:capacity:specification
soyabean extraction plant:usage/application:specification
kumar solvent extraction plant:machine type:specification
see pdf:screw number:specification
150 gram:capacity:specification
100-200 kg per hour:capacity:specification
star plastic machinery:brand:specification
35 kg/hr:capacity:specification
siddhivinayak infrastructures:brand:specification
innovative research equipment:brand:specification
gold refining:capacity:specification
100 gm 3kg hour:capacity:specification
mumbai and dubai:service location:specification
bitumen extractor - hand operated & electrically operated:type of testing machines:specification
2 liter:capacity:specification
up to 100 kg:capacity:specification
2kg/shift:capacity:specification
30ltr:capacity:specification
90/25:screw number:specification
8 kg/shift:capacity:specification
500 kg:material loading capacity (t):specification
monolayer blown film machine:machine type:specification
pvc pipe making machine:machine type:specification
pilot to commercial scale:capacity:specification
primetech:brand:specification
120 kg/hr,150 kg/hr,200 kg/hr,250 kg/hr:capacity:specification
soyabean extraction plant:machine type:specification
kumar solvent extraction plant:usage/application:specification
8 tpd:capacity:specification
50tpd to 500tpd:capacity:specification
1-1.5 kg:capacity:specification
1-3000l/h:capacity:specification
500 sq ft:dimension:specification
steam distillation:extraction method:specification
boxes:packaging type:specification
stainless stell:frame material:specification
3250:nil:specification
export quality:ylem energy heavy duty machine:specification
film plant, sheet plant &:line type:specification
50 kg\hr to 300 kg\hr:production capacity:specification
25mm:screw diameter:specification
electrowinnig silver refining machine:model name/number:specification
1400 mm:film width:specification
biodegradable:material processed:specification
nitride alloy steel:body material:specification
ss aba/45-55/1000:model:specification
0-30 mpa:pressure range:specification
ss 3l/45-55-45/1000:model:specification
0-200 degreec:temperature:specification
0.8-1.5 litres of solvent per kg of oil extracted:solvent consumption:specification
95-98% oil extraction rate:extraction efficiency:specification
0.4 kg - 5-6 kg:production:specification
200 - 850 mm:working width:specification
0.008 - 0.03 mm:coating thickness:specification
2.5 - 3 mm:conductor diameter:specification
12-30 mm:finished wire size:specification
150-250 hr:production:specification
250- 500 kw:power source:specification
380-440:voltage:specification
4-45 rpm:screw speed:specification
5-50 rpm:screw speed:specification
500-800mm:layflat width:specification
0.14-0.20 mm:filament denier range:specification
3-5 hp:motor power:specification
380 - 440 v:voltage:specification
up to 280 kg/hr:output capacity:specification
100-1000tpd:capacity:specification
8 - 10 ton in 24 hours:capacity:specification
plastic, mild steel:body material:specification
pipe extruder, profile extruder:type:specification
34kw:power consumption:specification
3 zones:barrel cooling zones:specification
35.001:total gear reduction:specification
92mm parallel:screw dia:specification
for rpvc pipes:usage:specification
2-90-25v (bex):model:specification
55 (kw-ac):extruder drive:specification
2 x 90 mm:screw:specification
25 d:effective screw length:specification
75 (kw-ac):extruder drive:specification
8kw:power consumption:specification
1000-1500:capacity (bricks per hour):specification
120 v:input voltage:specification
30 mpa:pressure range:specification
300 degree celsius:temperature:specification
11.7:motor powe:specification
800:heating power:specification
1.55:d di:specification
3.2:channel depth:specification
industrial:usage / application:specification
melange grey:color:specification
4xl:size:specification
solid/granules:state of matter/chemical form:specification
industrial grade:grade/standard:specification
core rotating twin screw extruder lab scale:deal in:specification
stainless steel:meterial:specification
highly durable:type:specification
heavy duty:feature:specification
thermo fisher:brand:specification
28 kg:weight:specification
up to 3 hp:power:specification
1-12ton:weight:specification
mtd:model name/number:specification
230v:power supply:specification
1900 mm:outer shell diameter:specification
steam:platform:specification
global:region:specification
jewelry making:application type:specification
1to1000kg:capacity:specification
22mm:depth:specification
500 sq ft:diameter:specification
brand a:brand:specification
850 sq ft:dimension:specification
single phase:material:specification
no smell,no gas:exhausted gas:specification
9.5 ( 7.5 + 2 ) hp:motor power:specification
144 samples unattended:capacity:specification
lakshmi:brand/make:specification
b.a. engineering:brand:specification
industrial / chemical / laundry / etp:usage/application:specification
700kg:weight:specification
pp / titanium / glass:body material:specification
250mm:screw diameter:specification
pestiside for former:material processed:specification
200 mm:film width:specification
2 to 5 kg/hr:capacity:specification
centrifuge:machine type:specification
5 ltr:capacity:specification
25 kg:capacity (kg):specification
used to purify gold and silver:usage:specification
55 kw:motor power:specification
environmental and clinical samples (kit dependent):sample source:specification
magnetic bead:technology:specification
96 preps, other:number of reactions:specification
recycling:application:specification
20 ul to 200 ul:working volume:specification
covid-19 test, genomics and proteomics, target identification, forensics, etc.:usage/application:specification
24 or 96:plates per deck:specification
68 cm:width:specification
60 cm:depth:specification
38 cm:height:specification
designed to meet global environmental and safety standards:environmental compliance:specification
adheres to international safety and environmental standards:environmental compliance:specification
6-7 hours:cycle time:specification
0-4 bar gauge:pressure:specification
100-150 hr:production:specification
250-350 hr:production:specification
25-55 kg/hr:capacity:specification
16-20 kw:voltage:specification
220-240 volt ac:voltage:specification
8-60 micron:micron:specification
220-380v:voltage:specification
4-8 hours:duration:specification
5000 - 50000 mm:extruder screw dia.:specification
100-240v ac:voltage:specification
1 kg to 100 kg:capacity:specification
pp+metal:body material:specification
24kw:power:specification
mild steel/pp:body material:specification
vihas:brand:specification
1200 w:power:specification
ira corporation:brand.:specification
motorized:power source:specification
bhalaji associates:brand:specification
2 ltr.:capacity:specification
shade net film:application:specification
220 - v / ac:power:specification
2 ltr:bowl capacity:specification
8 kg:capacity(kg):specification
6 kw:power:specification
30mm & 35mm:screw diameter:specification
5 hp and 7.5 hp:motor power:specification
lldpe/hm/biodegradable:material processed:specification
13 ft:tower height:specification
one no of 50mm adjustable:cooling ring:specification
27:1 (30), 32:1 (35):l/d ratio:specification
30mm + 35mm groove feed:extruder:specification
3 nos:heating zone:specification
26":nip roll:specification
made of nitriding steel (en41b musco):screw:specification
3 hp high capacity:blower:specification
one no of single station surface type winder:winder:specification
gas nitrating:treatment:specification
one no 75 mm lip size:die:specification
5.5 kw + 6.5 kw:heating load:specification
5 hp + 7.5 hp ac varriable frequency (crompton motor & abb make ac drive):main drive:specification
one lakh fruit fom. in 12 hours:production capacity:specification
single or three phase:power source:specification
automatic fom machine:machine type:specification
220v or 415v:voltage:specification
bitumen:usage/application:specification
primetek:brand:specification
analogue:display type:specification
ss-75-1800:model:specification
20-90 m/min:take up speed:specification
5-50 rpm:screw speed rpm:specification
30-40:output/hr:specification
1-100 mm/min (adjustable):compression speed:specification
0-200 mm:stroke range:specification
200-700mm:product effective width:specification
0.02-0.12mm:thickness:specification
45-52 mm twin screws for effective compounding:screw diameter:specification
50-90 kw motor for high torque and throughput:motor power:specification
7-10 barrel heating zones with precision control:heating zones:specification
52-65 mm twin screw size for optimized flow:screw diameter:specification
90-160 kw high torque motor for heavy-duty performance:motor power:specification
8-10 precision controlled heating zones:heating zones:specification
110-180 hr:production:specification
25-60 kg/hr:capacity:specification
20-40 kw:machine power (kw):specification
7-40 micron:thickness:specification
20-110 mm:pipe diameter:specification
18-1 l/d:l d ratio:specification
60-90 kg/h:max output:specification
20-25 kg:weight:specification
20kn (customizable up to 50kn):max compression force:specification
up to 150 mm:screw diameter:specification
up to 110 rpm:screw speed:specification
up to 750 mpm:output speed:specification
l/d ratio 18:1 upto 24:1:screw design:specification
120-250:production capacity:specification
100 - 2000 tpd:capacity:specification
80-1200kg/hr:production capacity:specification
180-200:capacity:specification
180-200:production capacity:specification
100 inch:height:specification
egsm001 egsm002 egsm003:model:specification
160-800 t:die casting machine:specification
pt3/8 inch:air pressure inlet:specification
70 kg/h:output:specification
3":minimum size:specification
20 h.p:power required:specification
60 micron:thickness:specification
0.7 hp:power:specification
20" inch:machine nip roller size:specification
10-12 feet:tower height:specification
hm/hdpfe/ ldpe/bio/ld:material to be processed:specification
3 layer:layer:specification
600-900 mm:sheet width:specification
450mm:tray width required:specification
s l tools:brand:specification
100 ton per day:capacity:specification
plastic extruder:machine type:specification
50-500 ton per day:capacity:specification
benefits:brand:specification
max:capacity:specification
extruder:welding type:specification
100kg to 500kg/hr:production capacity:specification
lab, r & d:usage/application:specification
50hz for electric model:frequency:specification
175 kg per hour / 0.75 upto 50 square mm:capacity:specification
taski:brand:specification
siddham extrusion services:brand:specification
allm:material:specification
500 kg in 2 hrs:capacity:specification
100 kg in 2 hrs:capacity:specification
20kg-200kg:capacity:specification
fusion induction:brand:specification
100 kg/hrs:production capacity:specification
vaidik:brand:specification
1-3 kg:capacity:specification
incredible extrusion convertors:brand:specification
cold press oil:usage/application:specification
35 - 50 kg/hrs.:capacity:specification
oil expeller cold press:machine type:specification
other:type:specification
60hp:machine power:specification
custom made:production capacity:specification
20kg to 500kg:capacity:specification
hand opp machine:type of testing machines:specification
a clean club machinery:brand:specification
1200 watt:motor power:specification
180 mbar:suction power:specification
balaji thinfilm technologies:brand:specification
custom:packaging type:specification
oem:brand:specification
50 kg plc opreted:capacity:specification
1500 gram:capacity:specification
ankita:brand:specification
use in business set up:usage/application:specification
1-100 kg:capacity:specification
depends on the extrusion press tonnage:capacity:specification
vm:brand:specification
10 to 25 kg:machine capacity:specification
mechanical:driven type:specification
conical, parallel, twin and single:screw design:specification
roy:brand:specification
all:type:specification
as per customer requirement:packaging size:specification
making cable wire:usage/application:specification
solvent plant:usage/application:specification
>20:power:specification
80-120 kg/hr:capacity:specification
extruder:type:specification
300 ton/hrs:capacity:specification
extract oil from rice bran:usage/application:specification
300-500kg/h:capacity:specification
food products:material to be extruded:specification
200kgs/hour up to 800kgs/hour:capacity:specification
dg:brand:specification
200 kg /hr:production capacity:specification
yaxing:brand:specification
1000kg/hour:capacity:specification
10 grms to 100kg:capacity:specification
110 kg/hr to 250 kg/hr:production capacity:specification
ud technologies:brand:specification
for production of color masterbatch:plastic processed:specification
3ton:weight:specification
yx-pvc construction template extrusion line:brand:specification
abb:frequency:specification
boc:packaging type:specification
200-1000kg/h:production capacity:specification
oswal engg:brand:specification
copper:type:specification
dolphin labware:brand:specification
pvc pipe machine:plastic processed:specification
up to 200 l:capacity:specification
used for fortification:machine type:specification
rice extruder:product / goods details:specification
100grm 1kg:capacity:specification
printec:brand:specification
80 kg:capacity:specification
depend on specifications:capacity:specification
gungunwala:brand:specification
plastic or food processing machine used:plastic processed:specification
5ltr to 1 ton:capacity:specification
pvc, rpvc:plastic processed:specification
radhe krishna make:screw design:specification
uropion brand:plastic processed:specification
10kg /hours:production capacity:specification
75 kg/hr:capacity:specification
india roto:brand:specification
50 - 100 mm:capacity:specification
0.50 mt/day to 10 mt/day:capacity:specification
kumar metal industries:brand:specification
1ton/day:capacity:specification
r. p. industries:brand:specification
vincitore:brand:specification
crown extractor model iii 703:usage/application:specification
crown extractor model iii 703:machine type:specification
6000:capacity:specification
rk:brand:specification
jaiko:brand:specification
hydraulic:machine type:specification
rice extruder machine repair service:type of service:specification
pan india:location/city:specification
myung:brand:specification
1 to 1000 kg:capacity:specification
bottle:packaging type:specification
herbal oil extraction:usage/application:specification
depends:capacity:specification
up to 5 kg/batch:capacity:specification
customized:screw number:specification
60-110kg/hr:capacity:specification
sainath extrusions:brand:specification
cci:brand:specification
250 kg/batch:capacity:specification
pvc/cpvc:plastic processed:specification
150-270 kgs/hr:capacity:specification
15 ltr:capacity:specification
chemical, textile, plastic industry:usage/application:specification
sharpenn:brand:specification
polypropylene,pp,pptq,pe,ldpe,lldpe,hdpe,hm-hdpe,polyethylene,eva,pvoh/pa:usage/application:specification
this instrument is used for determination and checking of bitumen percentage in bituminous mix:type of testing machines:specification
for finding bitumen content:type of testing machines:specification
sundex:brand:specification
industral:usage/application:specification
hdpe/pp /pv:material:specification
250kw:power consumption:specification
extrusion:plastic processed:specification
40ltr:capacity:specification
motor testing:type of testing machines:specification
pvc extruder machine:machine type:specification
soybean oil:usage/application:specification
2.5kg:capacity:specification
laboratory use:usage/application:specification
1 kg:weight:specification
70:frequency:specification
150 kg/h:max output:specification
anticorrosive pph (polypropylene):material used:specification
color coated:finishing type:specification
40 ton:loading capacity:specification
index:brand:specification
1kg to 1000kg:capacity:specification
8 mm:sheet thickness:specification
petro chemical:department:specification
closed circuit works by vacuum 200l:transfer of acid:specification
maahi extrusion:brand:specification
100 to 240v:voltage:specification
herbal extraction / ark extraction:usage/application:specification
titanium / polypropylene:body material:specification
50kg +50kg - double dissolution tank and ppt:capacity:specification
fumes acid:refinery type:specification
electric heater:heating fuel:specification
f z engineering hub:brand:specification
dust refining:feedstock:specification
with scrubber:fume control system:specification
4000 cfm:capacity:specification
1 kw:cooling unit:specification
20-120 rpm:screw speed:specification
0-60 min controlled by pcb:extraction time:specification
70-75:centrifugal effect (%):specification
adjustable drum rotation 0-1000 rpm:vfd (optional):specification
89304-44855:m:specification
2-3 hp:motor:specification
3-5 hours:processing time:specification
35-40 mm screws:screw diameter:specification
typically 75-120 mm for high throughput:screw diameter:specification
200-300 kw for powerful, continuous operation:motor power:specification
10-12 zones for precise barrel temperature control:heating zones:specification
0-100m/min:laminating speed:specification
900-1600 mm:layflat width:specification
110-120 vac or 220-240 vac:voltage:specification
up to 100 mm:profile thickness:specification
up to 5000 lph:cooling capacity:specification
up to 3000 tons:extrusion press capacity:specification
up to 8 meters per minute:extrusion speed:specification
up to 80 dba:noise level:specification
up to 144 samples unattended:capacity:specification
15 l:product capacity:specification
3" hm:die size:specification
quick setup:features:specification
0.8 kg:capacity:specification
b k machines:brand:specification
1-3 ton/day:production capacity:specification
indian product:brand:specification
1 to 2 kg:capacity:specification
500 kg/day:capacity:specification
1 ton/day:capacity:specification
making granules:usage/application:specification
vk group:brand:specification
alratech:brand:specification
twin screw:type:specification
twin-screw:machine type:specification
ge momentive performance materials:brand:specification
3.5kw:power consumption:specification
50 /60 hz:frequency:specification
200 kg/hrs:capacity:specification
30 kw:power source:specification
10-50 kg:capacity:specification
1:usage/application:specification
sni:brand:specification
full:drive motor:specification
500 ltrs to 50000 ltrs:capacity:specification
to extract oil from oil seeds and oil cakes:usage/application:specification
25 tons - 1500 tons:capacity:specification
best:screw design:specification
upto 50kg:capacity:specification
united:brand:specification
welding:usage/application:specification
rubber feed extruder:brand:specification
all:appliance:specification
to find the binder content in mix design of bitumen and aggregate mix.:type of testing machines:specification
pp bags:packaging type:specification
powder:material:specification
electric:machine type:specification
jinan lijiang automation equipment co., ltd.:brand:specification
butyl:material to be extruded:specification
extract oil:usage/application:specification
1500 ml, 2000mml, 1000 ml, etc as per required by the party:capacity:specification
plastic making:usage/application:specification
100-2000kg per hour:capacity:specification
50 grams to 1 kg'':capacity:specification
prescription:prescription/non prescription:specification
(sars-cov-2) pcr:test method:specification
hospital and lab:industry type:specification
extract rapidly 15-60 minutes , 32 samples can be extracted at the same time:no of unit to be tested:specification
upto 300 kg/hr:capacity:specification
film extrusion machine:machine type:specification
10 to 100 kl:capacity:specification
0.2-100t/h:capacity:specification
for college:industry type:specification
500l:storage capacity:specification
25 mm to 250 mm:size:specification
twin screw gear boxes:material:specification
full:capacity:specification
1kg to 5kg:capacity:specification
for pp mat use ony:machine type:specification
to produce long continuous products such as tubing and tire treads:usage/applications:specification
90 inch:height:specification
used to make baby dana:uses:specification
1000hv:surface hardness:specification
ra 0.4:surface roughness:specification
d80ppvcext:model no.:specification
cast aluminium:rotor bowl material:specification
20 hp frequency variable drive of abb standard make heaters:frefrequency control:specification
316:material grade:specification
25 to 30 kg./hr:maximum output:specification
50 micron:film thickness:specification
600 mm:maximum sheet width:specification
2 to 20 const torque, 25 max const power:screw rpm:specification
460 x 700 (phi x l mm):roll size:specification
45 m/min:roll speed:specification
50 ton:weight:specification
mellcon:brand:specification
used for determination and checking of bitumen percentage in bituminous mix:usage/application:specification
12:warranty month:specification
yes:rust proof:specification
50mm:thickness:specification
snalco:brand:specification
600 - 1250 to 1140 - 2100 ( mm ):lay flat width:specification
motor driven:driven type:specification
32 inch:winder width:specification
approx 150 kg:weight:specification
twinex 114r:model:specification
10 to 25 mtrs/sec:liner winding speed:specification
packaging industry:usage:specification
181:l and d ratio:specification
55/65 mm:screw diameter:specification
600 mm:lay flat width:specification
45 kw:connected load:specification
80 micron:film thickness:specification
45/45 mm:screw diameter:specification
27 mm:screw ratio:specification
95 kg/hour:output:specification
261:l and d ratio:specification
20-150 micron:thickness range:specification
ksa- semi automatic:winder type surface:specification
ket-35647:model:specification
281:l and d ratio:specification
ket-34955:model:specification
3 x 55 mm:screw diameter barrier:specification
301:l and d ratio:specification
25-200 micron:thickness range:specification
sec-8010:model name/number:specification
1800:weight((kg)):specification
180 x 7.5 x 150 cm:dimensions:specification
2-65-18v (bex):model:specification
18 d:effective screw length:specification
appl/cdl-65 ac:model name/number:specification
basu:brand:specification
750 kg/hr:max output upvc profile:specification
2-90-25v:model:specification
minimax:brand name:specification
3 x 15 (ac) (kw):main drive:specification
130 kg/hr:maximum output:specification
1100 mm:nip roller size:specification
three layer plant:plant:specification
70 hp:power:specification
gold and silver refining service:service type:specification
used to complete the extrusion process.:usage:specification
5.75 kw:diving motor:specification
120 kg/hrs max:out put:specification
5.5 kw:heating load:specification
19 mm to 160 mm:pipe dia:specification
37- 250 kg/ hr:production capacity:specification
20 - 75 hp:motor power:specification
ms, ss:available material:specification
75 kg/hour:output:specification
145 kg/hour:output:specification
worldwide:location:specification
50-110 mm:biscuit diameter:specification
more than 65-95 kgf:pulling force:specification
ground mounting/fixed mounting:mounting method:specification
0.09 mpa:inner pressure:specification
2-5 hp:power:specification
pe:material:specification
22.1 kw:heater capacity:specification
rmb a45 b45:model no:specification
25-30kg/hr:maximum output:specification
7.5:power(kw):specification
25-75kw:power consumption:specification
1100 mm:diameter:specification
diesel fired:burner:specification
500-600 mg/nm3:dust:specification
1150 mm:diameter:specification
50 kg/hour:max output:specification
automatic:work mode:specification
13 kw:machine power (kw):specification
2ton/24hours:extruder capacity:specification
2hpx4p:driving motor:specification
polypropylene:material to be used:specification
1250 mm:height:specification
5.0 hp:stirrer motor power:specification
960 rpm:stirrer motor speed:specification
508 mm:nip roll size:specification
400-750 w:motor power:specification
5000 l:tank volume:specification
1040:foaming ratio:specification
50mpa:output pressure:specification
0-60 r/min:rotating speed:specification
ss:material of hopper:specification
250kg:6x6:specification
5 hp:power load:specification
5' 0" x 2' 1" x 4' 0":dimensions:specification
40kw:machine power (kw).:specification
0.25 kw:cutter rate power:specification
4:test point:specification
2-5 kg/hrs:production capacity:specification
upto 200 mm:automatic cutting unit:specification
up to 130 kg / hour:output speed:specification
up to 30 mm:tubes outer diameter:specification
up to 3600 rpm (variable):speed:specification
greater than 1 micron:particle size:specification
greater than 95%:collection efficiency of particles:specification
home:usage:specification
32 h.p:power required:specification
1400 kg /hr.:5800 *1000*2200 mm:specification
260 g:weight:specification
ractangle:shape:specification
iron steel:material:specification
polish:finish:specification
24":maximum size:specification
t-shirt bag, garbage bag, carry bags, grocery bags, etc.:to produce:specification
used to produce long continuous products such as tubing, tire treads, and wire coverings:usage:specification
65 kg/h:output:specification
high tensile strength accurate dimensions easy usage:features:specification
silver refining plant:product type:specification
45 - 65 ( mm ):screw diameter:specification
two station:winder:specification
wide:range:specification
220v:voltage::specification
11,500 rpm:rotation speed:specification
25:max extrusion output(kg/hr):specification
india:origin:specification
9-12 mm:max inlet wire diameter (mm):specification
touch:screen:specification
uni-mech:brand:specification
425 mm:die size:specification
200 kg/hr:maximum output:specification
1450 mm:nip roller size:specification
1300-2200 mm:lay flat width:specification
180-200 kg/hr:maximum output:specification
gold:material refining:specification
5.5:low boltes:specification
2 x 68 mm:screw:specification
1800mm:length:specification
rajlaxmi enterprises:manufacture by:specification
lq-fh1250	lq-fh1750	lq-fh2000	lq-fh2300	lq-fh2500:model:specification
2-135-28v:model:specification
ket-32755*:model:specification
40-150 micron:thickness range:specification
600-1380 mm:lay flat width:specification
ksw - semi automatic:winder type surface:specification
3 x 22 (ac) (kw):main drive:specification
20-200 micron:thickness range:specification
cable extuder:application:specification
100 to 1000 tpd:capacity:specification
95 deg c to 50 deg c:temperature:specification
0.5~0.8mpa:air pressure:specification
d45vext:model no.:specification
-20 to 50 deg c:operating temperature:specification
3000 mm to 10000 mm:length:specification
1000 mm to 2500 mm:width:specification
22hp:power consumption:specification
100-110 kg./hr.:capacity:specification
3-6 mm:max inlet wire diameter (mm):specification
0-1 mm:min finish wire diameter (mm):specification
20 hp:ac motor:specification
1 hp for product outing:dc motor:specification
50-60 deg c:temperature:specification
fumes and dust:gases:specification
350 mm:flange width:specification
1260 mm:height:specification
8-18kg/ltr:fuel consumption range:specification
60-80 deg c:temperature:specification
less than 10 mg/nm3:lead:specification
40 mm:outlet valve size:specification
1170 mm:diameter:specification
less than 50 mg/nm3:dust:specification
40 kg/hr:output:specification
8":minimum size:specification
organic:organic:specification
herb:part type:specification
leaf:part type:specification
dnz:model no.:specification
single phase:type:specification
brahmi extract:name of extract:specification
bacopa monneiri:botanical name:specification
leaves:part used:specification
pranus persica:botanical name:specification
semi automatic:driven type:specification
15hp:motor power:specification
220v/380v:input:specification
filter cartridge dust collector:type:specification
plastic:raw material:specification
75 mm:size:specification
100 kgs/hrs:productions:specification
rle- 501:model name/number:specification
v r enterprises:manufacturer:specification
rustproof:feature:specification
ss-304:material:specification
750000:flow sysytem:specification
650 - modified ppo (pellet + powder):screw speed range modified ppo:specification
450 - 800 pa5 (pellet) + gf (30%):throughput range pellet:specification
500 - 800 pc (powder, hight molecular weight):throughput range pc hight molecular weight:specification
electrcity:power source:specification
0-3600 rpm:speed control:specification
pipe plants:tripping chutes:specification
380 v:power:specification
6 mm, 10mm and 20mm:pipes approx:specification
manual:grade:specification
three separate screws:screw design:specification
0.8-3mm:sheet thickness:specification
jatamansi extract:name of extract:specification
nardostachyas jatamansi:botanical name:specification
175 ml:pack size:specification
symplocos racemosa:botanical name:specification
p p natural:brand:specification
100 - 300 kg / h, 500 kg / h, 1000 kg / h, 2000 kg / h:capacity:specification
1800x780:drum size (dxa):specification
1450:capacity (lb):specification
3:power (kw):specification
3500:weight (kg):specification
hydraulic starting:starting form:specification
1100:capacity (lb):specification
3000:weight (kg):specification
3.5 kw:power:specification
1-8 kw:power:specification
s p s gold rifainury system:brand:specification
220 v/60 hz, 500 w:power:specification
1 kg to 5000 kg:capacity:specification
80kg/h-800kg/h:capacity range:specification
22kw:speed of screw:specification
40mmx1m,50mmx1m,80mmx1m,100mmx1m:vapour line:specification
2000:speed(rpm):specification
sunflower seed solvent extraction:application:specification
5959:model name/number:specification
10-100 l:reactor capacity:specification
60 m/min:take up speed:specification
welding electrode:material to be extruded:specification
220 vac:power source:specification
24:no of position:specification
65 kg./hr.:peak output:specification
own (italy type):brand:specification
tc 55:series:specification
200-400p/m:capacity:specification
36 inch:chamber length:specification
3600 mm x 2135 mm x 1980 mm:cooker size:specification
use in herbal and solvent extraction plant and chemical industry:usage:specification
7 days:service duration:specification
buyer side and supplier side:material procurement:specification
220v 50hz:power supply:specification
365x400mm:dimension:specification
100-170 kg/hr:output rpvc filled:specification
15 ac kw:extruder drive:specification
refining silver:usage:specification
45 (kw ac):extruder drive:specification
371:l d ratio:specification
45-90g:model:specification
spe-48,spe-96 & spe-144:model name/number:specification
less than equal 85%:relative humidity:specification
3000kg:weight:specification
extraction plant installation:service type:specification
1 hp:vacuum pump	power:specification
spe system:athena:specification
pressure manifold:positive:specification
automatic:fully:specification
0-99 min:time:specification
0-100r/min:rotating speed:specification
8:track:specification
32 kgs:weight:specification
amrit:brand:specification
india:service location:specification
1500 g and 3000 g:available capacities:specification
counter-rotating:direction of rotation:specification
45 kw:motor rating:specification
51 kw:heating capacity:specification
1400 mm:width:specification
60 kw:motor rating:specification
1750 rpm:motor base speed:specification
2xl:size:specification
mustard yellow:color:specification
local:location:specification
ppcp:material:specification
edr-srm2:model:specification
40 hp:power:specification
2000000:1:specification
50 mm:screw die (mm):specification
28 micron:thickness of film:specification
18kw:power consumption:specification
1000mm:cebtral height:specification
1-3kg/h:maximum capacity:specification
cement,chemicals,fly ash:storage material:specification
cotton seed extraction:usage::specification
23 kw:heating load:specification
5.5:peak output (kg/unit):specification
raw oil production oil processing:applications:specification
bainite:brand:specification
900 mm:maximum sheet width:specification
315 x 740 x 1200 mm:screw size:specification
9000 kg/hr:output:specification
120 to 180 litre:suitable for mixer capacity:specification
110 kw:extruder motor:specification
260 x 640 x 950 mm:screw size:specification
500 x 1070 (phi x l mm):roll size:specification
40 m/min:roll speed:specification
bitumen:penetration kit:specification
bar:application:specification
pe:plastic processed:specification
hydraulic:power source:specification
150kg/h 250kg/h 350kg/h:capacity:specification
pvc, hffr, xlpe:cable compounds:specification
10 to 75 kw:power consumption:specification
20 to 400 mm:size:specification
120 to 350 kg/hr:output:specification
electric motor:power source:specification
ac or dc:motor type:specification
single head / double head:head:specification
2-110-28v:model:specification
90 (kw-ac):extruder drive:specification
450 kg/hr:max output upvc profile:specification
2000-2200 kg/ hour:output:specification
2-65-18v:model:specification
380 v/220 v/415 v:voltage:specification
37 kw:power(w):specification
28:l and d ratio:specification
450-550 kg/hr:output spvc unfilled:specification
75 ac (kw):extruder drive:specification
2-92-28v:model:specification
twinex 78r:model:specification
600 kg/hr:max output upvc pipe:specification
twinex 93r:model:specification
560 kw ac:extruder drive:specification
55 kw-ac:extruder drive:specification
ts 92:model:specification
15 (kw-ac):extruder drive:specification
am industries:brand:specification
6 kw:heating power:specification
extrusion:technique:specification
1500g/3000g:material bowl capacity:specification
20 - 80 kg/hour:output:specification
2 x 52 mm:screw:specification
2-92-28v (bex):model:specification
92 mm:screw diameter:specification
0.5- 0.8mpa:air pressure:specification
21m/min:work speed:specification
6 - 20 mm:aluminum spacers width:specification
billet heating:features:specification
industrial:use:specification
5 h.p:motor power:specification
g. p. industries:brand:specification
4.0 kw:rated power:specification
construction:application:specification
15mm:thickness:specification
110 to 315 kg/hr:production capacity:specification
220 v / 380 v:voltage:specification
electric:power supply:specification
biology lab equipment:product type:specification
32" nip roll:lay flat width:specification
ne:model:specification
benkelman:beam apparatus:specification
si-bl-1500:model:specification
star material:brand:specification
0-10 feet:height of silo:specification
0-50 ton:storage capacity:specification
steel:material::specification
granules,polymer compound:application:specification
tsrd 9t:model:specification
150 kw:extruder motor:specification
500 x 1150 (phi x l mm):roll size:specification
3 to 12 mm:roll gap:specification
9.5mm:steel ball diameter:specification
2800w:power:specification
7 kw:power consumption:specification
uniforce:brand:specification
16-450 mm:pipe range:specification
silicone and synthetic rubber:suitable for:specification
polished:surface:specification
depends on material:power consumption:specification
depends on material:frequency:specification
50kg/hour:capacity:specification
ss:brand:specification
3500 r.p.m:capacity:specification
film:material to be extruded:specification
fish feed:usage/application:specification
1000gms:capacity:specification
lemison:brand:specification
5 machine per month:production capacity:specification
extrutech:brand:specification
for squeezing water from clothes.:usage/application:specification
copper:types of metal:specification
mechanical:type:specification
fix:type of furnace:specification
pe general purpose films, hdpe pick up bag, shade-net film, shrink film, tarpaulin films:usage/application:specification
10 kg - 50 kg:capacity:specification
1000-10000 l:capacity:specification
60kg:capacity:specification
manual and elecrical:type of testing machines:specification
as per is:capacity:specification
6007 cs:type:specification
bak:brand:specification
85 kg/hour:capacity:specification
as customer requirement:capacity:specification
screw type testing machine:type of testing machines:specification
bitumen extractor electrically operated:type of testing machines:specification
r.r. fabricator's:brand:specification
4mm:glass thickness:specification
4,"to9"inch(diameter):size/dimension:specification
phr:brand:specification
50 kg/hrs:capacity:specification
fish feed extruder:model name/number:specification
24 port:capacity:specification
15 kg:rated capacity:specification
50 - 5000 kg/h:capacity:specification
20kg per day:capacity:specification
customizable:capacity:specification
80 kg/hour:production capacity:specification
pck:screw design:specification
wire and cable:usage/application:specification
300 - 500 kg/hr:production capacity:specification
accurate engg. works:brand:specification
truck tyres:capacity:specification
5kg to 30kg:capacity:specification
2 litre:capacity:specification
manual operation:type of testing machines:specification
50 ton:capacity:specification
stainless steel,mild steel:material:specification
snacks line:type:specification
extruded snacks:type of namkeen:specification
1.5 tonne per hour:capacity:specification
aawadkrupa plastomech private limited:brand:specification
standard:plastic processed:specification
5000 l:capacity:specification
400 meter / hour:frequency:specification
500mm - 700mm:bag size:specification
100 piece/hour:capacity:specification
yo:brand:specification
bitumin:type of testing machines:specification
archana:brand:specification
0.5 to 10 kg/hr.:production capacity:specification
organic & inorganic catalyst:material to be extruded:specification
available in1 kg,4 kg:capacity:specification
0.5 ton:capacity:specification
dhiman:brand:specification
depends on size of machine:power:specification
hispec engineering:brand:specification
900 w:power consumption:specification
2 kg in per min:capacity:specification
unique machinery:brand:specification
analog tachometer:type of tachometer:specification
0.1 rpm:resolution:specification
shilp machines:brand:specification
pvc blown film making:usage/application:specification
ss ms:material:specification
kkls:brand:specification
lg extrusion:brand:specification
pragati engineers:brand:specification
acme:brand:specification
separation capacity:capacity:specification
electro mechanical:machine type:specification
30 litre:container capacity:specification
drip pipe manufacture machine:usage/application:specification
kalika:brand:specification
75 - 85 kg/hr:capacity:specification
polyethylene (hdpe):type:specification
s.g.:brand:specification
vcbcbv:machine type:specification
solvent:material:specification
2 kg per day:capacity:specification
3kg per hour:capacity:specification
distillation in solvent extraction:usage/application:specification
1kg to 50 kg:capacity:specification
round:head shape:specification
bsi make 450-mm:brand:specification
wdg pesticides:material to be extruded:specification
600 kg 750 per hours depending on soft material and hard material:capacity:specification
extruding machine:machine type:specification
front loading:loading type:specification
customized:screw design:specification
2 inch:screw size:specification
25-35 kg/hr:capacity:specification
10-50 kg/hr.:capacity:specification
50 - 60:frequency:specification
samrika flexi tech industries:brand:specification
edr-tgrm-2:capacity:specification
hdpe. ldpe:type:specification
uvr:brand:specification
wire and cable pvc insulation machine:machine type:specification
wooden packing only:packaging material:specification
1000g to 1500g:capacity:specification
acorus calamus:botanical name:specification
320kg per hour:capacity:specification
100 min:capacity:specification
50 kg per days:capacity:specification
electronic waste:type:specification
aluminium extrusion:plant type:specification
architecturer,rail .transpot,elecrtical,electronics and solar:industry application:specification
online:mode of repairing:specification
50kgs:capacity:specification
20kgs:capacity:specification
40kg/hour:production capacity:specification
biometrics:brand:specification
a a enterprise:brand:specification
7 kg per min:material loading capacity:specification
5kg to 100kg:capacity:specification
tilt:type of furnace:specification
70 kgs/hr:production capacity:specification
allsheng:brand:specification
1000:no of unit to be tested:specification
500 litre:capacity:specification
200 ml:packaging size:specification
any where in india:project location:specification
vegetable oil and spice oleoresins:usage/application:specification
sokhi extrusion:brand:specification
100 gram to 5 kg:capacity:specification
jewellery industry:usage/application:specification
for making carry bag, grocery bag, trash bag and liner bag:usage/application:specification
icata:brand:specification
industrial & domestic:usage/application:specification
1010:screw number:specification
all:capacity:specification
enpoc:brand:specification
twinscrew:screw design:specification
f&b engineering:brand:specification
100-500kg/h:capacity:specification
arun:brand:specification
pelleting if rice bran or soyabean pellet for extracting o.:usage/application:specification
150kw or more:power:specification
ms blown film:machine type:specification
36 samples:no of unit to be tested:specification
innovative research equipments:brand:specification
oil plant:machine type:specification
6 liters:capacity:specification
200-600kgg/h:capacity:specification
twin screw-65-80-92-95:screw number:specification
all:location:specification
all:delivery locations:specification
5218:screw number:specification
1 ton:material loading capacity (t):specification
70 kg/h:capacity:specification
extraction purpose:type of testing machines:specification
hdpe:material to be extruded:specification
75 kg:capacity:specification
single phase, 3 phase:phase:specification
800 mm:diameter:specification
100 l:volume:specification
85 %:humidity:specification
5xl:size:specification
1500 g:rotor bowl capacity:specification
600w:motor power:specification
algae decanter centrifuge:product type:specification
soya milk decanter centrifuge:product type:specification
150mm:size:specification
hdpe, pp:material:specification
online and offline:payment type:specification
extraction plant amc:service type:specification
gz-1100:model:specification
200x1850x1350:overall dimension (lxwxh) mm:specification
made in usa:coo:specification
230 v, 50 hz / 60 hz:power rating:specification
cotton seed solvent extraction:application:specification
over 98 %:recovery rate:specification
nucleic acid extraction:applications:specification
18.28 kw,22.25 kw,37.25 kw,45kw:main motor power:specification
gak:brand:specification
110-400 v:voltage:specification
25 - 80 ( kg/hr ):production capacity:specification
150 - 300 9 kg/hr ):production capacity:specification
150 - 300 9 kg/hr ):output:specification
dbl:brand:specification
3100x930x1850:size:specification
120-150:capacity (kilogram per hour):specification
hydraulic pressure:method:specification
23 kw:power:specification
415 ( kw ):voltage:specification
230 v, 50 hz:voltage:specification
20 - 40 ( kw ):machine power:specification
color plated:surface treatment:specification
600 - 1250 to 11400 - 2100 ( mm ):lay flat width and diameter:specification
15:centerline distance mm:specification
18:screw outer diameter:specification
1,100:centerline height:specification
11.3:power density:specification
extrusion machine:brand:specification
180-200 kgs/hr:out put:specification
48 - 7 5 ( kw ):power consumption:specification
36 kw-ac:extruder drive:specification
45 kw-ac:extruder drive:specification
300-330 kgs/hr:out put:specification
kex 926:model:specification
2-52-25v:model:specification
ansl:brand:specification
2 x 92 mm:screw:specification
28 d:effective screw length:specification
monolayer:screw design:specification
22kw:motor power:specification
230 v:input voltage:specification
25-100:film thickness:specification
10-50 microns:film thickness:specification
pm-ex40c:model name/number:specification
25-100 microns:film thickness:specification
115 hp:connected load:specification
62mm conical:screw dia:specification
dsk 62:model:specification
251:l and d ratio:specification
qc - 23:item code:specification
2714:hsn code:specification
300t/d:capacity:specification
water filtaration:usage/application:specification
gfcp:brand:specification
soap, charcoal, feed mills:material to be extruded:specification
700 kgs per hour:capacity:specification
ms powder coated:material:specification
300 per hr:capacity:specification
danline extrusion:type:specification
100kilogram:capacity:specification
70kg:capacity:specification
jumbo bag:type of bag:specification
cable industries:usage/application:specification
5480:capacity:specification
ldpe:plastic processed:specification
as per requirment:capacity:specification
kumar mfg co.:brand:specification
3000 bricks per hour:capacity:specification
esse pvt ltd:brand:specification
en:material:specification
open:packaging type:specification
250 kg/hour:capacity:specification
pet:material:specification
m/s mech tech solution:brand:specification
membrane:brand:specification
upto 1250 tons/day (24 hours):capacity:specification
9 min:result time (rapid kits):specification
blood:sample type:specification
rice:material to be extruded:specification
sk - the design studio:brand:specification
die steel:material:specification
4850mm *1000mm *2200mm:screw design:specification
3 inch:screw size:specification
fully autoamtic:machine type:specification
bitumen & asphalt testing:type of testing machines:specification
5 kg scrap refining:capacity:specification
30:frequency:specification
185 kg/hr:production capacity:specification
300kr/hr:capacity:specification
extraction of edible oils & meals:usage/application:specification
screw rendom extruder:screw design:specification
two phase:phase:specification
2kg/:capacity:specification
lab grade vertical extruder:machine type:specification
vp:brand:specification
velp scientifica:brand:specification
pvc pipe twin screw extruder machine:machine type:specification
sine sizer:brand:specification
40m/hour:production capacity:specification
polyethylene film making plant:usage/application:specification
snacks:type of namkeen:specification
screw rendom extruder:automation grade:specification
1.5:capacity:specification
extraction of cobalt:usage/application:specification
5 kn:capacity:specification
0.7- 3.0 mm:job thickness:specification
clay diya:type of diya:specification
10-60 mm:triple co extrusion:specification
10 kg/m:max cable weight:specification
11. 5m:height of building:specification
105 - 300 ( kg/hr ):production capacity:specification
1300 mm:height:specification
200 mm:depth:specification
5 hp:stirrer motor power:specification
900 rpm:stirrer motor speed:specification
32-96kw:power consumption:specification
horizontal:direction:specification
met ab:model:specification
printed:feature:specification
odourless:feature:specification
corrugated:feature:specification
golden:brand:specification
sre-1 & sre-2:model:specification
nanjing juli chemical machinery co.,ltd.:brand:specification
600 min-1 abs (powder):screw speed range abs:specification
600 min-1 pp (pellet) + talk (30%, 5 - 10um):screw speed range pp talk:specification
700 min-1 modified ppo (pellet + powder):screw speed range modified ppo:specification
250 - 600 (kg/h):throughput range pc powder low molecular weight:specification
150 - 600 (kg/h):throughput range a pet flake:specification
200 - 750 (kg/h):throughput range pp talk:specification
100 - 350 (kg/h):throughput range pp:specification
250 - 400 (kg/h):throughput range modified ppo:specification
600 min -1 pp (pellet) + gf (30%):screw speed range pp pellet:specification
750 - 1400 (kg/h) pa5 (pellet) + gf (30%):throughput range pellet:specification
500 - 1800 (kg/h) pp (pellet) + talk (30%, 5 - 10um):throughput range pp talk:specification
3200x930x2000:size:specification
iso 9001: 2008:certification:specification
sugfab:brand:specification
toshiba:brand:specification
41ss:model number:specification
600 min-1 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
700 min-1 pc (powder, hight molecular weight):screw speed range pc hight molecular weight:specification
350 - 550 (kg/h):throughput range pp pellet:specification
58ss:model number:specification
500 min -1 abs (powder):screw speed range abs:specification
600 min -1 pc (powder, hight molecular weight):screw speed range pc hight molecular weight:specification
500 min -1 pp (pellet) + talk (30%, 5 - 10um):screw speed range pp talk:specification
500 min -1 pp (pellet) + talk (30% - 50%, fine powder):screw speed range pp:specification
650 - 2000 (kg/h) abs (powder):throughput range abs:specification
600 - 1450 (kg/h) pc (powder, low molecular weight):throughput range pc powder low molecular weight:specification
400 - 1450 (kg/h)a-pet (flake, non-dry):throughput range a pet flake:specification
230 - 850 (kg/h) pp (pellet) + talk (30% - 50%, fine powder):throughput range pp:specification
non portable:is it portable:specification
gokshur extract:name of extract:specification
tribulus terrestris:botanical name:specification
flower:part used:specification
extrusion cutting:usage:specification
aluminium:material to be cut:specification
1440 rpm:motor base speed:specification
cast aluminum:material:specification
40 m/min:max tractive speed:specification
2. 5mpa:pressure:specification
12-60 mm:double co extrusion:specification
300 kg/hr:max output upvc profile:specification
850 kg/hr:max output upvc pipe:specification
solex120-40:model:specification
401:l and d ratio:specification
iron, stainless steel, metal:material:specification
1/2 hp:electric motor:specification
6inch:wheels size:specification
132kw:model number:specification
extraction, liquefaction and emulsification:application:specification
20mpa:pressure:specification
nitrogen or compressed air:air supply:specification
75 psi:inlet pressure:specification
1800 min-1:screw speed:specification
1300 mm x 475 mm x 1075 mm:dimension:specification
3.1/2" x 20" inch:chamber size:specification
240 v:power supply:specification
single and also available in three phase:phase:specification
amt:brand:specification
22mm-95mm:size:specification
batch solvent extraction unit:machine type:specification
98.99 %:extractaion ratio:specification
no:portable:specification
70 l:oil tank capacity:specification
cabbage extract:name of extract:specification
150 ml:pack size:specification
120mpa:pressure:specification
hdpe, ldpe, pp:material:specification
as per model:model number:specification
90 mm:size:specification
soybean oil:usage:specification
1. filter paper disc (packet of 100 nos.) 2. benzene:accessories:specification
22000*1500*2200:size:specification
twin screw extruder:brand:specification
drives:driven type:specification
construction line, building line:application:specification
600-800rpm:output speed:specification
3 ph. 415 v, 50 hz.:power consumption:specification
sp-65-iii:model number:specification
bharaj:brand:specification
38crmoal:screw material:specification
bricks form:screw form:specification
0-30 mpa:range pressure:specification
1mpa:precision pressure:specification
0.18 kw:feed rate:specification
granules, polymer compounding:application:specification
pp pe pet ps abs pa pvc caco3 etc.:raw material:specification
gold refining plant:use:specification
palm fruit oil:usage:specification
gold and silver refining plant:use:specification
2400-3600 rpm:speed (rpm):specification
4000 v:voltage:specification
chemical,pharmacy:application:specification
1100:weight (kg):specification
industrial:uses:specification
1250-1450rpm:input speed:specification
automatic:mode:specification
jjez0106e:model no:specification
toptul:brand:specification
automatic for conical twin screw extruder:automatic grade:specification
120 kg per hour:capacity:specification
kse:brand:specification
400v:power consumption:specification
grace:brand:specification
230 v:operating voltage:specification
as per the client need:capacity:specification
portable:feature:specification
0.08 mm to 3 mm:film thickness:specification
125kw:power:specification
5 - 6 feet:height:specification
fully automatic:control panel:specification
415 v:electric supply:specification
netafim:brand:specification
30 to 300 gsm:thickness range:specification
svm agro processor:brand:specification
3200 kg:weight:specification
jay metals:brand:specification
low to high throughput:feature:specification
10 mm:outlet wire diameter:specification
neutralizing section, bleaching plant, deodorizing section:process:specification
automatic,semi-automatic,manual:grade:specification
liquid:application:specification
industrial, laboratory:usage:specification
1-2 hp:power consumption:specification
recyclable:is it recyclable:specification
max.4000mm:layflat width:specification
upto 2000mm:die diameter:specification
smt52/18v - smt 92/28v:model range:specification
50:the maximum diameter of the product(mm):specification
800:average productivity (kg/h):specification
0-40, 40-80:machine power (kw):specification
up to 3,000 kilograms per hour:capacity (kilogram/hour):specification
320 kg/hour:capacity:specification
corn, maize, grain, gram, millet:material to be extruded:specification
automatic, semi-automatic, fully-automatic:automation grade:specification
hydraulic:operation type:specification
1500 grams bowl capacity:capacity:specification
6 mm dia., 10mm dia. and 20mm dia:pipes approx:specification
pu,pvc:plastic processed:specification
gold refining:application:specification
35 mm:screw diamete:specification
food processing machines division:product group:specification
vapour recovery process:plant process 5:specification
200 square meters:floor space requirement:specification
festo,germany or equivalent:pneumatic:specification
siemens,japan or equivalent:main motor:specification
25000 kg. (approx.):total weight:specification
exact specifications may vary and shall be made available upon specific request:note:specification
industrial grade:material grade:specification
solvent oil extraction plant:product name:specification
15:skilled men power requirement:specification
20:unskilled men power requirement:specification
440 volts,50 hz,a.c.,three phase with neutral ( can also be designed as per specific requirement:power supply:specification
-10 degreec to 40 degreec (14 degreef to 104 degreef ):working temperature:specification
450 mm:film width:specification
10-100 micron:film thickness:specification
50-60-50 mm:screw diameter:specification
30:1:l/d:specification
750-1500 mm:film width:specification
20-150 micron:film thickness:specification
pneumatic type:jaw opening:specification
mono layeer machine:model name/number:specification
groupfit barrel:screw design:specification
tc 86:series:specification
tp 75:series:specification
120 kg:max output:specification
exturding machine:processing type:specification
pipe extrusion:application:specification
40x48:question:specification
20 l cold water:convection cooler:specification
milacron parallel twin screw extrusion system:product type:specification
180kg/hr:output capacity:specification
200:model name/number:specification
root:part type:specification
2 inch:size/diameter:specification
3 inch:size/diameter:specification
500 to 1500mm:sheet width:specification
0.2 to 1.5mm:sheet thickness:specification
less then +- 3 %:sheet thickness variation:specification
heat and shear sensitive materials:ideal for:specification
sliver, white:color:specification
up to 125 hp:power consumption:specification
sx-6518:model name/number:specification
22 kw:drive power:specification
18:1:l/d:specification
gtla-008:model name/number:specification
ballpoint pen:pen type:specification
11 kw ac:extruder drive:specification
16-110 mm:pipe range:specification
multilayer - aba three layer:film layer:specification
45+55mm:screw diameter:specification
28/1:screw l/d ratio:specification
255 x 180 x 300 cm:overall dimension:specification
2000 kg:net weight:specification
1 set:air ring:specification
0.1 mm:film thickness:specification
80 kg/hr:extruding output:specification
3000 kg:net weight:specification
45x2 mm:screw diameter:specification
30:1 l/c:screw ratio:specification
120 rpm:screw speed:specification
hand operated extractor:product type:specification
7.5:electric power (hp):specification
30,40,30 hp:main motor:specification
225kg/hr:max output:specification
single station:surface winder:specification
compact:model type:specification
10-50micron:film thickness:specification
43hp:connected load:specification
60-1200 kg/hr:output:specification
200-1000 mm:lay flat width:specification
50-1000 ml:sample volume:specification
40 to 60 min:processing time:specification
one:no of handle:specification
herbal industry:usage:specification
tp 115:series:specification
conical screw extrusion system:product type:specification
5500r.p.m/11000 r.p.m:speed:specification
1-2 months:duration:specification
ss-bt-4009:model name/number:specification
12*5*2.2 m:external dimension:specification
180-230 kg/hr:capacity:specification
45 + 55 mm:screw die:specification
15+25 hp:main drive:specification
40 to 50 hz:frequency:specification
80-100 cuts/min (d/f pen barrel) or 200-250 cuts/min (polo barrel):o/p:specification
0.20 to 0.24 unit / kg:energy consumption:specification
55 kw-160 kw:machine power (kw):specification
co-rotating screw twin extruder:model name/number:specification
co-rotating screw twin extruder:material:specification
hdpe,ldpe, lldpe plastic film:raw material:specification
sacm-465:screw material:specification
145 ( kw ):power consumption:specification
ld/ pp/ hm/ biodegradable:raw material:specification
600 mm:lay flat width and diameter:specification
50 kg/hr:max. film output:specification
30 kw:whole power required:specification
hdpe / caco3 / lldpe:raw material:specification
450 x 300 x 430 cm:overall dimension:specification
20 hp x 2 pcs hp:driving a.c. motor + inverter:specification
2.1:power (kilowatt):specification
123-456-123:model name/number:specification
x.:good:specification
ac single phase:phase:specification
u0 to 36 inch wide:size:specification
100-kg:capacity:specification
100 kg to 10tph:capacity:specification
single/double:machine type:specification
bitumin testing machine:type of testing machines:specification
shree radhekrishna extrusions pvt.ltd.:brand:specification
92/28:screw number:specification
22 - 25 tons/day:production capacity:specification
doors,windows:thickness:specification
pc:material:specification
radhekrishna:screw design:specification
fortified rice:plastic processed:specification
auto and semi auto both:machine type:specification
65kw:power consumption:specification
370 kw:power consumption:specification
2 kg/hrour:capacity:specification
ser 158/3 21 samples/day/unit:capacity:specification
automatic gold refining machine:capacity:specification
mild steel:casing material:specification
tube extrusion machine:type:specification
universal gears:brand:specification
for processing all edible seeds and cake:usage/application:specification
ltr:capacity:specification
ss 304:material of construction:specification
prime margo:warranty:specification
ss, ms:material:specification
lelesil:brand:specification
2 kg per transaction:capacity:specification
5 kg per transaction:capacity:specification
pla/pbat:plastic processed:specification
in ltr:capacity:specification
25 kgf:capacity:specification
yx-construction template extrusion line:brand:specification
500 ltrs and above:capacity:specification
mild still:material:specification
abdul:brand:specification
dalfab designer pvt ltd:design:specification
as per customer chojce:design:specification
round drip pipe machine:type:specification
50-2000 kg per day:capacity:specification
70:screw number:specification
tailor-made:capacity:specification
two type machine high speed and low speed:capacity:specification
special purpose machine:machine type:specification
aepl:brand:specification
not mentioned:brand:specification
up to 1 kg:capacity:specification
laboratory,pharma industries:usage/application:specification
100 ton/day and above:capacity:specification
upto 2500 tpd:capacity:specification
distillation in solvent extraction:machine type:specification
rajkot:service location:specification
hmpl:brand:specification
corn grit, corn flour, rice flour, multi grain:material to be extruded:specification
cable machining:machine type:specification
all type wire:material to be extruded:specification
depends:no of unit to be tested:specification
96 well:capacity:specification
50 tpd- 1000 tpd:capacity:specification
1500:capacity:specification
1000 g - 1500 g:capacity:specification
air-cooled:type:specification
s s engineering works:brand:specification
1kw:power consumption:specification
spice oleoresins:usage/application:specification
for car:surface recommendation:specification
extraction of metals like copper:usage/application:specification
en41b:material:specification
4 bolt:no. of screws:specification
bbn:brand:specification
very good:capacity:specification
parallel screw:screw design:specification
bakery:usage/application:specification
infinity khushi:brand:specification
100g/apromx1kg:capacity:specification
extraction unit:machine type:specification
999+-:purity:specification
sas agrotech:brand:specification
modern:brand:specification
500gm to 100kg:capacity:specification
minimum 5 kg and maximum 25 kg:capacity:specification
oil industry, edible oil industry:usage/application:specification
200:capacity:specification
1 (hp):die face drive:specification
85-130 kg/hr:output spvc unfilled:specification
bex 2-68-28v:model:specification
230-380 volt:voltage:specification
150 -170 kg:product capacity:specification
40 hp:power consumption:specification
9.2:main drive ac (kw):specification
1-5hp:motor power:specification
220- 440 v:voltage:specification
0.35 - 2.50 hta m2:condenser:specification
3-9 kw:bath:specification
450 rs per kg:refining cost:specification
1225 mm:height:specification
poe:material to be extruded:specification
datong:brand:specification
atico:brand:specification
used for the production of a wide range of packaging films:usage:specification
parth plastomech:brand:specification
650 pa5 (pellet) + gf (30%):screw speed range pellet:specification
400 - 1100 abs (powder):throughput range abs:specification
350 - 800 pc (powder, low molecular weight):throughput range pc powder low molecular weight:specification
250 - 800 a-pet (flake, non-dry):throughput range a pet flake:specification
150 - 500 pp (pellet) + talk (30% - 50%, fine powder):throughput range pp:specification
spring conveyor type,container type:hopper loader:specification
300 - 1000 pp (pellet) + talk (30%, 5 - 10um):throughput range pp talk:specification
tubing and pipes:vacuum tanks:specification
100mm dia x 0.5m2:size:specification
avocado extract:name of extract:specification
persea americana:botanical name:specification
2 bar, 0.5 cfm:compressed air:specification
3000g:volume:specification
3000r/min:rated rotation speed:specification
ce:certification:specification
22-75kw:power consumption:specification
500-3000 rpm:speed:specification
testing machine:type:specification
1 hp:vacuum pump power:specification
220 v:power supply:specification
single / double:phase:specification
up to 350 kg/ hr:production capacity:specification
online and offline:mode of payment:specification
800-1500mm:pack size:specification
liquid extraction:process:specification
110kw:power:specification
50 to 800 degree celsius:heating range:specification
0.75-2.2kw:motor power:specification
5500 rpm/11000 rpm:speed:specification
carton pallet:packaging type:specification
2135 mm x 2135 mm x 3180 mm:kettle size:specification
1440 rpm:motor speed:specification
manmach machines:brand:specification
20~40 min/time:extraction time:specification
aquarius:brand:specification
240:capacity (lb):specification
11:power (kw):specification
1550x650:drum size (dxa):specification
457 x 457 x 457 mm:dimensions:specification
as shown in pic:design:specification
steel:chamber material:specification
3:no of chamber:specification
170 h.p:power consumption:specification
depending on quantity:reagent:specification
mild steel powder coated:material:specification
20-110 mm:pipe range:specification
fiber&glass:body material:specification
50mm to 110mm:pvc pipe size:specification
b011:model:specification
480x330x530 mm:size:specification
130 kw:power consumption:specification
ce:certifications:specification
manual self-start and self-stop | no exposed moving parts | built-in residual-current device (rcd):safety features:specification
1100/1:model:specification
45kg:capacity:specification
gold silver refinery 1kg to 10 kg:capacity:specification
100 kg - 1000 kg:capacity:specification
tocotrienol extraction:machine type:specification
bizpression:brand:specification
30 kg/h:capacity:specification
10kw:capacity:specification
plastic:machine type:specification
53 kg:weight:specification
upto 20 kg/hr:capacity:specification
1.2 kg/hour:capacity:specification
gce05:model name/number:specification
water removal machine:usage/application:specification
40hp:machine power:specification
pvc extrusion machine:machine type:specification
2 - 10 kg. /hr.:production capacity:specification
acts:brand:specification
20 kgs/30-60 kgs/upto 1000kgs:production capacity:specification
cryogenic:technology used:specification
industrial / medical:application:specification
twin screw extruder:type:specification
turmeric:usage/application:specification
sme:brand:specification
solvent extraction (edible oil):usage/application:specification
28kg/hr:capacity:specification
pharma,nuracticl:usage/application:specification
gmp:machine type:specification
oil refinery:usage/application:specification
3-6 mm:max inlet wire diameter:specification
margo:brand:specification
pipe extruder machine:machine type:specification
all india:service location:specification
for extrusion:usage/application:specification
mild steel:material to be extruded:specification
5 kl:capacity:specification
plodder cum extruder machine:machine type:specification
pipe extruder:machine type:specification
tandem extruder:machine type:specification
250 kg/hr:capacity (kg per hour):specification
twin screw conical:screw design:specification
150kg per hour:production capacity:specification
500 kgs per hour:capacity:specification
1 to 3 kg:capacity:specification
470 kg/hour:capacity:specification
500kg/hour:capacity:specification
pvc, hdpe, llpde, pp:plastic processed:specification
30 kgs:capacity:specification
200 -12000:capacity:specification
as per require:material:specification
lldpe making:usage/application:specification
hand operated bitumen extractor:type:specification
4kg:capacity:specification
lab/pilot scale:machine type:specification
wire insulation:snacks type:specification
extractor machine:type of testing machines:specification
3.5 kg/hour:capacity:specification
3.5kw:capacity:specification
m seal ,soap, adhasive etc.:material to be extruded:specification
400kg/hour:production capacity:specification
alp:brand:specification
see pdf:screw design:specification
shriram engineering:brand:specification
100gram,to 2 kg:capacity:specification
high automation:automatic grade:specification
vsf30:model name/number:specification
8 mm to 25 mm:diameter:specification
1 0-1 00 r/min:screw speed:specification
1 kg,2 kg,5 kg,10 kg,20 kg:available capacity:specification
tractor pto shaft:power source:specification
0:voltage:specification
3 tons:17 feet by 6 feet:specification
35 hp:total power:specification
rt - 105 degree c:elution temperature:specification
terminalia belerica:botanical name:specification
natural:colour:specification
55 kw:motor rating:specification
140 kn:continuous load:specification
smew-0165:model:specification
yes:after sale service:specification
medical tubes, automobile tubes, garden pipes:tube:specification
8-15 kg/h:output:specification
380 v / 50 hz:power supply:specification
jec- 685555 52d:model number/name:specification
300-400 mm:max bag length:specification
400-500 mm:max bag length:specification
automatic and semiautomatic:operation mode:specification
100-800kgs/hr:output:specification
10-18mm:thickness:specification
silver refinery:usage:specification
15:machine power (kw):specification
50-60 kg:weight:specification
checking of bitumen percentage in bituminous mix:usage:specification
35-45,40-55,45-55,50-60-50 mm:screw diameter:specification
120,220,240 kg/hr:maximum output:specification
one year:warranty::specification
ac 220v 50hz:voltage::specification
gold refining systems are ideal for old gold jewelry buyers, bullion suppliers, gold smithies:usage:specification
375 x 415 x 440 mm:dimensions:specification
gold dust can be refined:feature:specification
3 hrs:processing time:specification
2 x 65:screw:specification
78 mm; 34:1:throughput kg/hr:specification
250 - 300:output (kg/hr):specification
4 banks of 12 positions:no of positions in each row:specification
1ml,3ml,6ml,10ml or 15ml:spe cartridge size:specification
different test tube racks can be configured:test tube rack:specification
223 kn:short term load:specification
new:condition::specification
ce/ tuv/ sgs, iso 9001: 2008:certification::specification
engineers available to service machinery overseas:after-sales service provided::specification
pal kernel extraction industry:usage::specification
napro:brand:specification
1/2 inch,1 inch,4 inch,>4 inch:size/diameter:specification
280 kg/hr for pvc:output:specification
s.i.:brand:specification
500-2000 mm:film width:specification
30-35kg/hr:max output:specification
24 hp:connected load:specification
20hp:main motor:specification
22 d:effective screw length:specification
65:screw diameter:specification
25:l d ratio:specification
190-250 kg/hr:output spvc filled:specification
140-190 kg/hr:output spvc unfilled:specification
30 ac kw:extruder drive:specification
corrective maintenance:maintenance type:specification
55,65,55 mm:screw diameter:specification
150-400mm:film width:specification
55-60kg/hr:max output:specification
single/two station:surface winder:specification
tower structure:model type:specification
bitumen extractor hand operated:model name/number:specification
pressure always provided to bank 1. pressure supply to banks 2-4 individually controlled:default row:specification
3-4 mm:min finish wire diameter (mm):specification
kolsite:brand:specification
25 ( kww ):power consumption:specification
90-320 kg/hr:production capacity:specification
ac:motor type:specification
750 - 1200:lay flat width:specification
45 kw:extruder motor:specification
260 x 540 x 700 mm:screw size:specification
36 m/min:roll speed:specification
180 kw:extruder motor:specification
415 x 790 x 1330 mm:screw size:specification
370 to 440 litre:suitable for mixer capacity:specification
12000 kg/hr:output:specification
800:diameter(mm):specification
60:power consumption:specification
0.5 to 5.0 mm:screen sizes:specification
75-112 k.w.:energy:specification
1.8 x 1.4 m:size:specification
0.25 kw:cutter power:specification
30:screw diameter:specification
0-500rpm:rotate speed range:specification
11.6/12.7/23:pathway rate:specification
electric heat and water cooler:temperature control:specification
frequency control:feed control:specification
rust proof coating:finishing:specification
appl/dl-90 ac:model no:specification
150 kgs/hrs:productions:specification
sunflower oil:usage:specification
cotton seed oil:usage:specification
125kg/hr:max output:specification
40hp:main motor:specification
20-100 micron:film thickness:specification
75hp:connected load:specification
10 to 50 mic:thickness range:specification
800mm:working width:specification
20 to 80 mic:thickness range:specification
210-240v:voltage:specification
single:screw design:specification
to make lamination film:usage:specification
bex 2-92-28v:model:specification
5000-8000 pcs/hr:capacity:specification
120kg/hr:max output:specification
automatic:automatic grade::specification
1000 , 1500 rpm:input speed:specification
automatic, semi-automatic:machine type:specification
1000g-1500g:capacity:specification
1200 kg/hr:max output upvc pipe:specification
3 x 47 mm:screw diameter barrier:specification
2-168-28v:model:specification
200 (kw-ac):extruder drive:specification
40 - 130 kg/hour:output:specification
2 x 65 mm:screw:specification
40 - 100 kg/hour:output:specification
hdpe, ldpe, pe, pp:material:specification
52 mm, 65 mm, 75 mm, 90 mm:extrudes:specification
sewage drainage and rain water, micro irrigation:usage:specification
ket 35340:model:specification
35 & 40:screw diameter (mm):specification
26:01:00:screw l/d ratio:specification
ket - 32360:model:specification
screw dia (mm):screw dia (mm):specification
5.5 kw:main power:specification
220v/380v:voltage:specification
220 - 415 v:voltage:specification
22 kw:power:specification
round,striped:insulation material make up:specification
automatic stripe feeder:feeding:specification
80 kg/m:max. cable weight:specification
core / hot / cold:diameter gauge:specification
rwh / rwt / auf:take up:specification
color coated:surface treatmentr:specification
380 v:voltage::specification
500 to 800 mm:reel diameter:specification
360 v:power consumption:specification
10 - 240 mm2:product diameter:specification
peroxide cross linked silicone:insulation material:specification
25 kw ir-shock oven,9 x ir-ovens:cross linking method:specification
rwh / rwt / auf:pay off:specification
roca 1220 / 1620 / 2520 / 3020:caterpillar input:specification
roex 45.24 / roex 60.24:auxiliary extruder:specification
sps gold refinery plant:brand:specification
3 layer:no. of layer:specification
20h.p:main motor:specification
35 x 45mm:screw dia:specification
2 x 40 & 45mm:screw dia:specification
1300mm:working width:specification
130 mm:die width:specification
22mx2.3mx2.2m:equipment dimension:specification
8.5 ton:equipment weight:specification
0-60mpa:pressure panel:specification
90 x 160 mm:spiral tube diameter:specification
hand operated:model name/number:specification
no:design type:specification
300-2000 kg/hr:production capacity:specification
54 m:vulcanize length:specification
floor mounted:mounted type:specification
98.99 %:extraction ratio:specification
galvanized:surfase finishing:specification
700 min-1 pa5 (pellet) + gf (30%):screw speed range pellet:specification
700 min-1 pp (pellet) + gf (30%):screw speed range pp pellet:specification
600 min-1 a-pet (flake, non-dry):screw speed range a pet flake:specification
600 min -1 pa5 (pellet) + gf (30%):screw speed range pellet:specification
500 min -1 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
500 min -1 a-pet (flake, non-dry):screw speed range a pet flake:specification
600 min -1 modified ppo (pellet + powder):screw speed range modified ppo:specification
800 - 1600 (kg/h) pc (powder, hight molecular weight):throughput range pc hight molecular weight:specification
0-300 degree c:temperature:specification
-0.098mpa:vacuum degree:specification
12-20:foaming rate:specification
110 ml:pack size:specification
harde extract:name of extract:specification
terminalia chebula:botanical name:specification
lotus extract:name of extract:specification
220v/50hz:voltage:specification
10 feet:4 feet:specification
4-40 ton/day:output:specification
three phase 380v/50hz:power supply:specification
0.021-0.038 w/m.k:thermal conductivity:specification
120w:power:specification
4 hr/kg:refining time:specification
single & three:phase:specification
pvc foam board:material to be extruded:specification
20-110 mm & 63-200 mm:size:specification
250-450 kg/hr:output:specification
2 x 52:screw:specification
60 to 160 rpm:motor speed:specification
blown film extrusion plant:brand:specification
500kg:capacity (kilogram/hour):specification
use in herbal and solvent extraction plant and chemical industry:usage/application:specification
200 kw:rated power:specification
25000*7000*3000 mm:external dimension:specification
540/1080 mm:width of sheet:specification
150-200 kg/h:output:specification
interior:position:specification
technochem engineers:brand:specification
40 kw:power:specification
1ml,3ml:spe cartridge size:specification
bex 2-52-18v:model:specification
11:extruder drive:specification
bex 2-65-18v:model:specification
extraction unit:preparatory section::specification
2 screws:number of screws:specification
1 to 40 rpm:speed range:specification
65 kw:motor rating:specification
420 kn:short term load:specification
1220 mm:width:specification
troika:brand:specification
single phase:motor phase:specification
75 (kw ac):extruder drive:specification
herbal plant:type:specification
up to 8 liter:reagent:specification
230 volts:operation:specification
50":die size:specification
58 mm:casement window system size:specification
blue white:color:specification
ss 304, ss 316:material grade:specification
36m:cooling zone length:specification
10-80 mm:single extrusion:specification
alloy steel hardened:material:specification
10 to 100 kg:capacity:specification
bio analytical:usage/application:specification
20 kg/hour:capacity:specification
meking palestesizer:usage/application:specification
solvent extraction plants:usage/application:specification
20kg/h:capacity:specification
sami autometic:machine type:specification
10000l:capacity:specification
prime margo machines:brand:specification
90ml:capacity:specification
other:brand:specification
act engineering:brand:specification
250l:capacity:specification
ajay machine tools:brand:specification
18kg per day:capacity:specification
chemical industry:usage:specification
count:capacity:specification
electric:tilting arrangement:specification
5 - 20 tons:capacity:specification
50-500 gm:capacity:specification
440 volt:power consumption:specification
atishenggworks:brand:specification
100 tons:capacity:specification
manual testing machine:type of testing machines:specification
gayatri:brand:specification
85 mm:screw design:specification
twin type:screw design:specification
saef:brand:specification
where oil is extracted from oil seeds like soybean, sunflower, cottonseed, other oil seeds:usage/application:specification
trident:brand:specification
electric:voltage supply:specification
arch:style:specification
floating fish feed:plastic processed:specification
1441:screw number:specification
rpvc/upvc:plastic processed:specification
4mm to 180mm:capacity:specification
phyto chemical extraction plants:usage/application:specification
colour masterbatches ,all engineering plastics and compounding:plastic processed:specification
gb:brand:specification
uts:60:screw number:specification
50 kg/shift:capacity:specification
2 kg to 200 kg:capacity:specification
2:no of unit to be tested:specification
bitumen content in bituminous mix:type of testing machines:specification
16-250mm:pipe range:specification
500 - 2000 mm:film width:specification
etp,dhp,dap,dlp:standard:specification
new only:deal in:specification
bronze:colour:specification
do/di of 1.55, the zsk mc18:strikes:specification
48 - 75 ( kw 0:machine power:specification
230v, 50hz, 600w:power supply:specification
up to 100 g of filler per test:extractive capacity:specification
product/material specific:line speed:specification
1 to 50 rpm:speed range:specification
320 kn:short term load:specification
single and also available in three:phase:specification
2-68-28v:model:specification
37 (kw-ac):extruder drive:specification
gold:metal type:specification
recovery and refining:service type:specification
kvp - semi automatic:winder type surface:specification
3 x 30 (ac) (kw):main drive:specification
1800 mm:nip roller size:specification
ket-34855:model:specification
ket-35555*:model:specification
1400 mm:nip roller size:specification
4.5kw:power:specification
micro:brand:specification
2-68-28v (bex):model:specification
10-350 (m/min):line speed:specification
mc18:zsk:specification
zsk mc plus:modernize:specification
maximum:flexibility:specification
high energy:consumption:specification
two different pressure settings for extraction and column washing/drying:dual pressure regulators:specification
40 kw:connected power:specification
preventive maintenance:maintenance type:specification
1 to 12 samples:throughput:specification
43 kg:weight:specification
source business:brand:specification
screen changer/air knife/hopper loader with dosing unit/silo with blower in option:feature:specification
8 - 80 mpm:line speed:specification
centrifugal blower:blower type:specification
kemper india:brand:specification
stainless steel:material of construction:specification
plc:system control:specification
380v 50hz:voltage:specification
digital:display unit:specification
longer service life:specification:specification
10~25 mpa:extruding pressure:specification
4 mm:thickness:specification
chrome coated:finishing:specification
fruit juice decanter:product type:specification
10ml-1 ltr:pack size:specification
mehandi extract:name of extract:specification
lawsonia inermis:botanical name:specification
leaf:part used:specification
peach extract:name of extract:specification
to extrude screw components:usage:specification
32-35 kw:power:specification
vikas:brand:specification
35 kw:total power:specification
27 l/d:srcrew ratio:specification
6000 rpm:speed:specification
365 mm x 400 mm:main unit:specification
aqua cold process:process:specification
concentrate solutions, especially with heat sensitive components:usage/application:specification
u type:shape:specification
38 x 38 x 58.4 cm:dimensions:specification
easy to follow instructions | manual self-start and stop via hand pressure on the lid.:operating features:specification
automatic:automation grade::specification
9100:model no,:specification
190 kn:continuous load:specification
automatic/ semi autimatic/ manual:mode of operations:specification
extration:solid phase:specification
8:tube of digital control pump:specification
2350x2100x1500:overall size (lxwxh) mm:specification
inverter starting:starting form:specification
1000x400:drum size (dxa):specification
1100:rotor speed (r/min):specification
2100x1600x1050:overall size (lxwxh) mm:specification
2000:weight (kg):specification
gye-1550:model:specification
10:power (kw):specification
50:2:specification
solvent plant maintenance:service type:specification
3500 rpm:speed (rpm):specification
bex 2-52-25v:model:specification
130-170 kg/hr:output spvc filled:specification
2.5hp:power:specification
ananya enterprises:brand:specification
plc control:control system:specification
or mass output used widely in agro chemical, pesticide & chemical industries.:uses:specification
10 kw:power consumption:specification
55 kg per hour:min production capacity:specification
45-45:model:specification
ac inverter:driven type:specification
jewecast machinery:brand:specification
j 80 ultra:model:specification
700 watt:power:specification
1443 mm:width:specification
single control zone:temperature control zones:specification
318 kn:continuous load:specification
470 kn:short term load:specification
5:no. of layer:specification
lab:grade:specification
t- 58, t-164:aasho:specification
coal:raw material:specification
55-110 kg/hr:capacity:specification
3 phase:motor:specification
10%:moisture max:specification
50-100 kg:weight:specification
5 - 8 feet:height:specification
300-1000mm:film width:specification
a-b-a 35-45:model name/number:specification
225-600 mm:film width:specification
a-b-a 45-55:model name/number:specification
45,55,45 mm:screw diameter:specification
160kg/hr:max output:specification
italy design:design:specification
37 kw-ac:extruder drive:specification
electricity:fuel type:specification
85-90kg/hr:max output:specification
60hp:connected load:specification
35 & 45 mm:screw diameter:specification
45 & 55 mm:screw diameter:specification
150kg/hr:max output:specification
20,30,20 hp:main motor:specification
90 (kw ac):extruder drive:specification
0-50%:feeding concentration:specification
10-50 l:extraction vessel:specification
10-100 l:extraction vessel capacity:specification
ket - 33835:model:specification
35 x 26 d:screw dia (mm):specification
1,660 x 600 x 1,850:main dimensions:specification
72:barrel length:specification
38:nm shaft:specification
1,200:max output factor:specification
cwl50-m:model name/number:specification
ser 158 series:model:specification
70 x 29 x 71 cm:dimensions:specification
48ss:model number:specification
650 pp (pellet) + gf (30%):screw speed range pp pellet:specification
650 pc (powder, low molecular weight):screw speed range pc powder low molecular weight:specification
550 - 900 pp (pellet) + gf (30%):throughput range pp pellet:specification
450 - 600 modified ppo (pellet + powder):throughput range modified ppo:specification
with dryer:blender mixer:specification
blown film plants:universal bubble guide baskets:specification
250 ml:pack size:specification
lodhra extract:name of extract:specification
bark:part used:specification
110-380 v:voltage:specification
0.75-15 kw:power:specification
30-40times/min:max forming speed:specification
ir:fluid sensors:specification
300-400 g:max quantity of filler:specification
automatically & manuel:driven type:specification
9 models designed to meet throughput rates to 1,273 kg/hr:variety:specification
120w max:power consumption:specification
160 rpm:motor speed:specification
sm-481:model no.:specification
45mm:screw dia:specification
60 to 70 kg/hr:output:specification
15 x 20 h.p:main motor:specification
stainless steel:material type:specification
tsrd 3t:model:specification
50 to 90 litre:suitable for mixer capacity:specification
60kg/hr:output:specification
150 kw:calender motor:specification
240 mm:screw diameter:specification
2500 hp:motor power:specification
350 v:voltage:specification
brassica oleracea:botanical name:specification
vetiveria zizanioides:botanical name:specification
98.70%:purity:specification
ac supply:power supply:specification
jeweltech international:brand:specification
2 kw:heating power:specification
gz-750:model:specification
730x320:drum size (dxa):specification
4:power (kw):specification
1600x1150x850:overall size (lxwxh) (mm):specification
ll / ldpe:polymer:specification
500mm - 1350mm:lay flat range:specification
45/45/45 mm:screw diameter:specification
90-100 kg/hr:max. output:specification
45-60 hrc:hardness:specification
up to 3,000 kilograms per hour:very high capacities:specification
220v-240v:voltage:specification
0-50 kg/hr, 50-100 kg/hr:output:specification
120-200kg/h:output:specification
100 kg / hr 2 tons / hr:capacity:specification
48 - 65 ( kw ):machine power:specification
2 hp:horse power:specification
used in labs:application:specification
automatic,semi-automatic:automatic grade:specification
2-5 kw:power watt:specification
khus extract:form:specification
pp:material to be extruded:specification
45-90mm:screw diameter:specification
tightening nut:cap:specification
40-80kw:power:specification
2300 kg:weight:specification
raypa:brand:specification
5 zone 5 zone parameter:panel:specification
45mm:screw outer diameter:specification
1/2 h.p.:blower:specification
bex 2-90-25v:model:specification
180-200 kg/hr:max. output:specification
50 mm:inlet wire diameter:specification
600 kg (approx):machine weight:specification
refining converters:product type:specification
electrotherm:brand:specification
dm:brand:specification
omega20:model name/number:specification
30 nm:nominal torque:specification
ms 20:model name/number:specification
19mm:screw diameter:specification
1250 mm:length:specification
13nm/cm3:specific torque:specification
500g:min batch quantity:specification
herbal extraction plant:product type:specification
5 hp ac 1440 rpm 440 volts/50 htz:main motor:specification
corn:material to be extruded:specification
clarion:brand:specification
400 w:power supply:specification
syzygium aromaticum:botanical name:specification
8-15 mm:sheet thickness:specification
a-b-a 55-65:model name/number:specification
180kg/hr:max output:specification
pm-ex45c:model name/number:specification
a-b-a 40-55:model name/number:specification
15 & 20 hp:main motor:specification
waste collection tray included in standard equipment:waste collection:specification
55 & 65 mm:screw diameter:specification
500-1500 mm:film width:specification
120 hp:surface winder:specification
100kg/hr:max output:specification
72 hp:connected load:specification
upto 2907 nm per output shaft:rated torque:specification
20.5 - 78 mm:center distance:specification
1500 rpm:input speed:specification
48 individually regulated:no of positions:specification
12:no of positions in each row:specification
1ml:standard with equipment:specification
32 ton:weight:specification
240 to 305 litre:suitable for mixer capacity:specification
5 to 12 mm:sheet thickness:specification
3-4 hrs.:time taken:specification
mild steel:wire material:specification
80 rpm:speed:specification
ld/ hm/ biodegradable:material:specification
300 - 600 to 1600 - 2500:lay flat width and diameter:specification
120 - 150 ( micron ):thickness:specification
80-250 kg/hr:power consumption:specification
1-30mm:thickness(mm):specification
wear-resisting:feature:specification
polished and galvanised:surface treatment:specification
230 volts a.c:voltage:specification
gold refining services:service type:specification
galvanized:surface treatment:specification
jlab:brand:specification
11.3 nm/cm3:specific torque:specification
panchveer extrusion technik:brand:specification
gpps granule:applicable materials:specification
1-4 mm:thickness of sheet:specification
50-83 kg/m3:bulk weight of product:specification
ac:power supply:specification
zsk mv plus:modular design:specification
encapsulation processes:typical areas:specification
24:torque per shaft:specification
plastics:engineering:specification
degassing & reaction:devolatilization:specification
7.2 nm/cm:specific torque:specification
40 mm:screw diameter extruder b:specification
polished:finishing type:specification
material borosilicate glass, dia 55 mm, height 750 mm (approx).:extraction column:specification
material stainless steel (2nos.), cap. 20 ltrs.:feed tanks:specification
11 (kw-ac):extruder drive:specification
2-52-18v (bex):model:specification
530-700 kg/hr:output spvc filled:specification
450-700:output rpvc filled:specification
fume scrubber system, filter:set content:specification
30 & 40 hp:main motor:specification
25-100 micron:film thickness:specification
3000 x 650 x 1000mm:overall dimensions:specification
110 - 160 degree c:extruding temperature:specification
10 - 15mpa:extruder pressure:specification
ld/hdpe:plastic processed:specification
2400-3600rpm:speed limit:specification
0-0.8mpa:water pressure range:specification
ce/sgs:certification:specification
engineers available to service machinery overseas:aftersales service:specification
1w:question:specification
rounak:brand:specification
ppm-50e:model number:specification
50 (mm):screw diameter:specification
40-50 (kg/hr.):production:specification
22:extruder drive:specification
bitumen extractor hand operated:type of testing machines:specification
high temperature:dispenser type:specification
graco:brand:specification
pp, frp:material:specification
2 kg (as per requirement):capacity:specification
40kg:capacity:specification
indian oil:brand:specification
steel alloy:material:specification
10 ltr:capacity:specification
s.s engineering works:brand:specification
hard chromed screw elements:screw design:specification
applicxable:capacity:specification
1, 3, 6 ml spe cartridge manifold system for mobile phase solvent:capacity:specification
copper:melting material:specification
barkat:brand:specification
1000 ton:capacity:specification
herbal, spices, phyto chemicals:usage/application:specification
used for determination and checking of bitumen percentage:usage/application:specification
grade 1:grade:specification
rotary:type:specification
na:material to be extruded:specification
more than 100 kw:machine power:specification
non mesh type:screw design:specification
kumar:machine type:specification
varsha:brand:specification
rotary extraction plant:usage/application:specification
6200*1030*1300 mm:screw design:specification
selver:material to be extruded:specification
dryer:usage/application:specification
cotton seed extraction:usage/application:specification
team thermoformings & allieds:brand:specification
220 - 440:voltage (volt):specification
teleios automation:brand:specification
999.5/- 9999:purity (%):specification
on premises:installation services:specification
depend on capacity of plant:dimension:specification
250:diameter:specification
52:screw torque:specification
5.5:weight (ton):specification
3 phase:voltage (volt):specification
8-12kg/h:capacity:specification
15c to 50c:operating temperature:specification
food process:plastic processed:specification
85 mm:screw number:specification
one:packaging size:specification
15-20 hp:driven type:specification
acid w:usage:specification
m tech:brand:specification
fume:type:specification
nozzle:type:specification
dg-70:model name/number:specification
wpc door frame die:grade of material:specification
indoor:type:specification
1500gms:bowl capacity:specification
for squeezing the waste oil:usage/application:specification
ss316,ms304:material:specification
apc:brand/ model number:specification
vacuum:usage/application:specification
40kg:weight:specification
50 kgs / hr:production capacity:specification
10 - 100 microns:film thickness:specification
nu:brand:specification
hdpe film making:usage/application:specification
20 c - 110 c:heating range:specification
as per order:capacity:specification
electric and also available in diesel:power source:specification
50 hz:thickness:specification
60- 80 ton/day:capacity:specification
80/156:diameter:specification
100-150kg/h:average productivity:specification
depending on application:line speed:specification
no:electrical unit consumption:specification
no:temperature:specification
used for determination and checking of bitumen percentage in bituminous:usage/application:specification
bitumen:brand:specification
1/2 l:bowl capacity:specification
up to 235 kg/ hr:capacity:specification
230 - 460 v ac:voltage:specification
38mm - 120 mm:size:specification
after one year:maintenance:specification
l/d-52:diameter:specification
600rpm:screw speed:specification
15 - 25 kg:capacity:specification
chemical laboratory:application:specification
bottle:design type:specification
mumbai and delhi:service location:specification
analog:display type:specification
max 1tpd:capacity:specification
90 kw:screw number:specification
500g:capacity:specification
50kg. up to 400kg./hr.:capacity:specification
25-100:frequency:specification
solvent:usage/application:specification
steam oprted:machine type:specification
60 hrc:hardness:specification
lalitha oil extraction process:brand:specification
coatwell:brand:specification
fully automatic:plastic processed:specification
syam engineers food process:brand:specification
50kg to 100kg:capacity:specification
350kg/hour:capacity:specification
plant:machine type:specification
100-150 kg:capacity:specification
aluminium,aluminium:material to be extruded:specification
gma:brand:specification
100 ml:packaging size:specification
1 to 10kg:capacity:specification
100/kg/hour:capacity:specification
1000 kg:capacity:specification
namkeen:material to be extruded:specification
ksj:brand:specification
plastic/food/pharma:type:specification
plastic/food/pharma:material to be extruded:specification
lab / pilot scale:automation grade:specification
engineering product/ nylon glassfill 6.6,a.b.s:plastic processed:specification
bitumen extractor hand opertor:type of testing machines:specification
subi:brand:specification
1kg-500kg:capacity:specification
s s:material:specification
8inch:length:specification
ss/ ms:material:specification
zwm:brand:specification
sm:brand:specification
sheive:type of testing machines:specification
ubr:brand:specification
10 to 100tph:capacity:specification
shankar scientific works:brand:specification
smengg:brand:specification
3 kg per round:capacity:specification
used for pre-drying in the textile processing industry:usage/application:specification
ss302:grade:specification
bitumen extractor hand:type of testing machines:specification
1kg:packaging size:specification
lcmsms:shape:specification
1440 rpm:frequency:specification
45 hp:machine power:specification
10 gram plating:capacity:specification
15 kg to 60 kg per batch:capacity:specification
600/hr:capacity:specification
bhuller:brand:specification
manually:voltage:specification
no:driven type:specification
r121:material:specification
220-440v:voltage:specification
50-60:frequency (hz):specification
9999%:purity:specification
durga:brand:specification
500 watt:power:specification
200:font roll diameter:specification
3:line speed:specification
fiber:material:specification
100 v:voltage:specification
l -10ft w- 4ft h-6ft:diameter:specification
190:power:specification
standered steel:material:specification
50z:frequency (hz):specification
100%:surface:specification
single & twin screw barrel:usage/application:specification
en41b:grade:specification
6x2 ft:dimension:specification
p.p materials:brand:specification
ms amd ss:material:specification
8kg:pressure:specification
upto 50 ton/hour:capacity:specification
45mm screw:size:specification
full:automation grade:specification
z78:installation services:specification
25mm:thickness:specification
gi:brand:specification
upto 350 kg /hr:production capacity:specification
titanium, borosilicate glass, pph:body material:specification
cowin cht-65:model name/number:specification
3.6 x 3.6 x 2.0 mts:chamber size:specification
unique:design:specification
aluminium:body material:specification
50-60 hz:frequency (hz):specification
titanium & glass:body material:specification
6135 nm:screw torque:specification
15 mm:thickness:specification
single tank:number of tanks:specification
36 meter:single piece length:specification
55 mm:available extruder dia:specification
4-6.5 kgf/cm2:wind pressure source:specification
borunte:brand name::specification
single-screw:screw design:specification
custom:color:specification
6:no of process:specification
3 days:service duration:specification
powder:physical state:specification
bex 2-65-22v:model:specification
150-250 kg/hr:output rpvc filled:specification
bex 2-90-22v:model:specification
red , silver:color:specification
ss-bt-4008:model name/number:specification
resposeindia:brand:specification
500 mm:nip roll size:specification
ncr:site location:specification
onsite:service mode:specification
hexagonal:shape:specification
local area:loctaion:specification
screw:material to be extruded:specification
asphalt content in the bituminous mixture:usage/application:specification
5-7.5hp:power:specification
appl/dl-75 ac:model no:specification
processing of plastics:application:specification
18 nm/cm3:torque:specification
0-40kw:machine power:specification
28:1:l/d ratio of screw:specification
3.5 ton:weight:specification
tc 86:model:specification
160 (kw-ac):extruder drive:specification
200/400:die head:specification
220-240 kg/hr:maximum output:specification
low boltes and good:brand:specification
145 hp:connected load:specification
150-800 mm:film width:specification
110~160 degree c:extruding temperature:specification
stainless steel/mild steel:material:specification
30:extruder drive:specification
shri dhanshree enteprise:brand:specification
850:basket revolution (rpm):specification
75:drainage (mm):specification
bex 100:model name/number:specification
220v-320v:voltage:specification
meal finishing section:recuperation unit:specification
1 - 6 inch:size:specification
standard:delivery:specification
mild steel with c.i. housing,ss304 shaft,spring steel blades,and ss 304 bucket:material:specification
all purpose:usage/application:specification
led:material:specification
kriimpas:brand:specification
silver refining plant:capacity:specification
1kg to 10kg:capacity:specification
aluminium section:material to be extruded:specification
100 kg /shift:capacity:specification
herbal extraction and pharmaceutical:usage/application:specification
500kg:capacity:specification
industrial, hospital ,hotel:usage/application:specification
pp, wpc:material:specification
centrifuge extractor:type of testing machines:specification
250 gm/hour:capacity:specification
pr:brand:specification
cosmetics, pharma:usage/application:specification
acon laboratories:brand:specification
one:no of unit to be tested:specification
fvsdf:brand:specification
gbdf:usage/application:specification
tm-071m:model name/number:specification
liner:brand:specification
as per size:screw number:specification
20 kg /shift:capacity:specification
150 tpd:capacity:specification
1kl-12kl:capacity:specification
nscbord:brand:specification
medium:working pressure:specification
1to 2kg per batch:capacity:specification
500 kg - 5000 kg:capacity:specification
industiral:usage/application:specification
10kgs to 100kgs:capacity:specification
testing:usage/application:specification
good:capacity:specification
domestic expeller:machine type:specification
gold refining plant:capacity:specification
35 kw:power consumption:specification
process industry:usage/application:specification
helical:screw design:specification
60mm:screw design:specification
xlpe:plastic processed:specification
120kw:power:specification
used for extraction of oil from seeds, cakes or oil-bearing material.:usage/application:specification
as per req.:capacity:specification
rectangular:style:specification
stainless steel centrifuge extractor machine:material:specification
1kl- 10kl:capacity:specification
15 to 550 kg:capacity:specification
ss / ms / rubber lined:material:specification
cast aluminium:material:specification
112kw:installed power:specification
260 kw:motor power:specification
up to 80 kg per hour:capacity:specification
10 micron to 50 micron:micron thickness:specification
1800 x 1800 x 1500 mm ( l x w x h,approx. ):machine dimension:specification
automatic twin die hdpe blown film plant:machine name:specification
single:film layer:specification
water chiller:ancillary equipment 2:specification
12500 kg. (approx.):machine weight:specification
3600 rpm:speed rating:specification
hem - dd15:model number:specification
gamma y:model name/number:specification
4175x900x1800 mm:dimension:specification
41-122f (5-50c):process temperature:specification
41-122f (5-50c):ambient temperature:specification
stem:part used:specification
0.3mpa:water pressure:specification
10 mm:shell thickness:specification
asphalt extraction testing:usage:specification
white:blue:specification
bom:brand:specification
1070x400:drum size (dxa):specification
5.5:power (kw):specification
1700x1700x1000:overall dimension (lxwxh) mm:specification
3-9 kw:bath kw:specification
0.35 - 2.50:condenser hta m2:specification
380-440 v:voltage:specification
10-100 l:extraction vessel:specification
ss 316:steel grade:specification
scrubber:product type:specification
nex-75,nex-90,nex-100,nex-120:available model:specification
10 kg,20 kg,50 kg,100 kg:available capacity:specification
10 (hp):main motor:specification
55 mm:output size:specification
sec-02bc:model:specification
45 mm:piggyback extruder:specification
2 1/2" x 1 pc:cooling blower:specification
pp-45:model number:specification
0.10 mm:film thickness:specification
25 kg/hr:extruding output:specification
1800 kg:net weight:specification
7.5 kw:heating power:specification
160 rpm:screw speed:specification
5 zone:temp. controller:specification
30hp:main motor:specification
15-100micron:film thickness:specification
10 & 20 hp:main motor:specification
85kg/hr:max output:specification
65 hp:connected load:specification
40-45kg/hr:max output:specification
33 hp:connected load:specification
20 & 30 hp:main motor:specification
500-1200 mm:film width:specification
90 hp:connected load:specification
300-1300mm:film width:specification
llu:product code:specification
sa009:model name/number:specification
20 inch x 10 inch x 50 inch(50.8 cm x 25.4 cm x 127 cm):dimensions:specification
i 100-110 psi:instrument air:specification
88-132 vac/176-264 vac, 50/60hz:power required:specification
indo plast:brand:specification
35 + 45 cm:screw die:specification
7.5/15 hp:main drive:specification
20 kw:heating load:specification
depends on machine:model name/number:specification
f-d45:model name/number:specification
2 nos:die:specification
50 mm:max. film output:specification
255 x 280 x 300 cm:overall dimension:specification
20 kw:whole power required:specification
5.7 x 1.8 x 3.7	cm:overall dimension:specification
20 hp:driving v.s. motor:specification
2" x 2pcs:cooling blower:specification
720x2 or 4pcs mm/pc:winding shaft:specification
lab extruder machine:model name/number:specification
5-layer sleeve:level:specification
20gm:batch quantity:specification
10.5 mm to 48 mm:center distance:specification
100 kg/h:throughput:specification
3 points and 4 point:suspension of size:specification
80 kg/hr:peak output:specification
40 kw:connecting load:specification
powder coated:coated:specification
lab extruder machine:material:specification
tinospora cordifolia:botanical name:specification
cover for hear protection:barrel provide:specification
150l cold water (+1degree c) capacity:convection cooler:specification
200 gm to 1 mg:analytical weight box:specification
1750:weight (kg):specification
90 mm:screw dia:specification
ppm-sdf43:material name/number:specification
1; 5; 10; 22; 34; 66; 100ml:extraction cells:specification
50.8cm:height (metric):specification
70ml/min:pump flow:specification
90 mm 14 l/d water cooled:extruder:specification
max 300 / 150 / 100 / 20 m/min:line speed:specification
pvc,lsoh,pe,hdpe:jacketing materials:specification
roex 120.24 / roex 150.24:extruder:specification
volumetric:dosing unit:specification
air wipes / cable dryer:drying system:specification
max 5,000 / 4,000 / 3,200 / 3,600 / 2,800 / 2,500 mm:reel size:specification
awg 20 - 6 (0.5 - 10 mm2):typ. conductor size:specification
customized:colour:specification
oil:heat type:specification
70-80 degree celsius:tempreture:specification
6-8 hours:time to refine:specification
compact size with pollution control system:features:specification
28:l/d ratio:specification
300-650 kg/hr:out put:specification
45-127kw:total connected load:specification
380 x 380 x 600 mm:dimension:specification
2-4 sq. ft. area:suitable for:specification
rugged design, durability, perfect finish:features:specification
drum type filter:type:specification
45 rpm:screen speed:specification
0.25 to 0.28 mm:thickness of flakes:specification
1400 rpm:motor speed:specification
650-1500 kg:weight:specification
5500r .p.m/11000 r.p.m:speed:specification
65 (mm):screw diameter:specification
30 (kw):main motor:specification
2 (kw):water pump:specification
300mm:die size:specification
35 kg/hr:extruding output:specification
140 rpm:screw speed:specification
75 mm:paper core i.d.:specification
1000 mm:film passing width:specification
400l/h:cooling water flow rate:specification
50 inch:screw diameters:specification
normal ~300 degree:temperature:specification
collect control:control mode:specification
inner cyc:lubricant mode:specification
300-1000 mm:film width:specification
44 , 55 , 75.35 mm:center distance:specification
voltage supply:voltage:specification
good service:good quality:specification
elshaddai:satisfaction products in:specification
100 kw:power consumption:specification
800 x 500 mm:inner basket size:specification
stct 4a:model name/number:specification
determination of bitumen percentage in bituminous mixtures:usage:specification
500 and 3000 rpm:speed:specification
multipack machines:brand:specification
fish feed:material to be extruded:specification
aluminum,copper:conductors:specification
straight / multipass:cooling trough:specification
roca 1220 / 1620 / 2520 / 3020:caterpillar exit:specification
max 50 / 20 / 16 / 12 / 5 tons:reel weight:specification
max. 50 / 80 / 100 / 120 / 200 mm:diameter over insulation:specification
n&t:brand:specification
peanut oil:usage:specification
50 h.p:power consumption:specification
160:capacity (lb):specification
1.5 kg:rotor bowl capacity:specification
2 persons can operate entire plant:man power:specification
28.1 l/d:screw ratio:specification
7.5 hp (a.c.):main motor:specification
8 kw:heating power:specification
2 sets:locking device:specification
720x120x360 cm (lxwxh):dimension:specification
18 ton:weight:specification
tsrd 12t:model:specification
on request:screw design:specification
33:1 - 36:1:length by diameter ratio:specification
0.02-030 mm:thickness of finished products:specification
coated:surface treatment:specification
1%:reproducibility:specification
20-100 mm:thickness:specification
hdd 15:model number:specification
0.2 mm:film thickness:specification
(150-460)x2 or (460-950)x1 mm:film width:specification
40 hp:driving v.s. motor:specification
90&120(changeable) mm:die diameter:specification
95 mm:paper code o.d.:specification
2 set:auto temp. controlled hot sealer:specification
950 mm:printed width(mm):specification
1450 x 1150 x 1080 mm:machine size:specification
45 x 45 mm:size:specification
33 hp:power consumption:specification
mp ii:model name/number:specification
0.9kw:motor:specification
1600 mm:lwngth:specification
1(kg/h):throughput:specification
150tpd - 2000 tpd:capacity:specification
6 cubic meter:shipment volume:specification
diesel engine:power source:specification
10-15 degree c:oil temperature:specification
800 mm:width:specification
2300 mm:length:specification
14.6nm/cm3:specific torque:specification
55 / 65 mm:screw diameter:specification
110 kg/hr:max. output pvc:specification
na:power consumption:specification
na:automatic grade:specification
sea weed extract:usage/application:specification
25 kg/h:average productivity (kg/hour):specification
0.60 unit/kg:power consumption:specification
6000 mm width x 1375 mm length x 1800 mm height:dimension:specification
100-650kg/hr:production capacity:specification
220-380 v ac:voltage (volt):specification
100-400 kg/hr:output:specification
alternative treatment in case of numerous side effects and drug resistance:usage/application:specification
width 50mm to 2500mm. lenth unlimited.:size (inch x inch):specification
glass - ptfe:material:specification
atms:pressure:specification
steam boiler - fire wood:power source:specification
500 liter:oil tank capacity:specification
250:capacity (kg):specification
pp, ss:material:specification
650-700 kg/hour:output:specification
na:power:specification
pp, titanium:body material:specification
karat 24 project:brand:specification
300gm to 150kg:capacity:specification
yes:variable speed control:specification
up to 1000 degree c:heating range:specification
2-2300 kg/hr:production capacity:specification
wire twisting:usage/application:specification
200/300:capacity:specification
borosilicate glass 3.3 and ptfe:material:specification
upto 80 mtr/min.:line speed:specification
include:installation services:specification
206 kg.:weight:specification
230v:voltage supply (v):specification
25 ltrs to 500 ltrs.:capacity:specification
dc:power:specification
atmospheric:pressure:specification
60:frequency (hz):specification
25kg based on density of 560 kg/m3:capacity:specification
1 unit:capacity:specification
400:average productivity (kg/hour):specification
450:capacity (kilogram/hour):specification
120:diameter (millimeter):specification
hq-120t:model number:specification
40 - 100:output:specification
0-2 kg/cm2. bourdon type, 0-2 kg/cm2:pressure:specification
stainless ateel:material:specification
25kg/hour:capacity:specification
hdpe pp ldpe hips abs:material:specification
solvent extractor plant:model name/number:specification
100 grm to 2 kg:capacity:specification
150 w:machine power:specification
37-45 kw:machine power:specification
18 inch:drum size:specification
1kg,2kg,5kg:capacity:specification
1.5-1000kg/h:production capacity:specification
230 v:voltage (v):specification
ac:driven type:specification
1100mm:lay flat width:specification
rolls:finish type:specification
12 tone:weight (ton):specification
elpie:design:specification
na:font roll diameter:specification
220-230 kg/hr:average productivity (kg/hour):specification
220 kw:machine power (kilowatt):specification
ldpe/hdpe:material:specification
hover:brand:specification
panchal india:brand:specification
40 hp:machine power:specification
90 mm:thickness:specification
140 to 150 ton:capacity:specification
jsi:brand:specification
metal:product type:specification
compostable:material to be extruded:specification
raul:brand:specification
1000 kg/hr:output:specification
220 vac:voltage supply:specification
220:power (kw):specification
230:voltage supply (v):specification
bronto:brand:specification
soybeans, rapeseed, sunflower, lupine and other grain crops:material to be extruded:specification
de dietrich:brand:specification
6 kw type 316 ss:voltage (v):specification
4.5kw:power (kw):specification
5500r.p.m/11000 rpm:speed (rpm):specification
50hz:frequency (hz):specification
stainless steel, carbon steel:material:specification
sat:brand:specification
na:design type:specification
15 kg approx:weight:specification
customize:thickness:specification
variable:diameter:specification
2-3 kw:power consumption:specification
see pdf:power:specification
see pdf:design:specification
see pdf:wire diameter:specification
220v,440v:voltage:specification
aditya:brand/make:specification
230 v ac / 6 amp:voltage:specification
230 v ac / 6 amp:electrical unit consumption:specification
0.5 kw:power (kw):specification
220 to 380 v:voltage:specification
stainless steel 304 / 316:material:specification
tppl:brand:specification
polypropylene, ms, titanium:body material:specification
food & beverage, bakery & confectionery, pharmaceutical & nutraceutical, personal care & oral hygien:usage/application:specification
herbal medicine manufacturing , ayurvedic and botanical extract production , nutraceutical ingredien:usage/application:specification
rotary:machine type:specification
thermo scientific:brand:specification
herbal extract production:usage/application:specification
batch:process mode:specification
tobbacco:raw material:specification
profile:application:specification
pipe:application:specification
wpc:application:specification
51/105 conical:screw diameter:specification
250 w:power:specification
advance:brand:specification
prasad lab:brand/make:specification
4 to 8 botel:capacity:specification
mechanical:machine type:specification
road construction:usage/application:specification
midas technologies:brand:specification
compostable polymers and ld, hm:material processed:specification
centpro:brand:specification
wastewater:material processed:specification
5tph:capacity:specification
diesel:power source:specification
imported:brand:specification
15-30 kw:power:specification
customised:model:specification
standard:production capacity:specification
170 kg/hr:production capacity:specification
15:motor power:specification
counter rotating:screw type:specification
dia 65:screw number:specification
rpvc:plastic processed:specification
chandra:brand:specification
upto 20 tpd:capacity:specification
aqua regia:process type:specification
37 kw:power consumption:specification
steel:color:specification
1000k:weight:specification
45-75:model:specification
tsrd 6t:model:specification
settling tank:tank type:specification
20 m x 2.5 m x 2.2 m:dimension(lxwxh):specification
not detectable:gases:specification
1200 mm:diameter:specification
5kg and 10kg:capacity:specification
9.5 mm:steel balls diameter:specification
2400 - 3600 rpm.:range of speed i:specification
40 ( kg/hr ):output:specification
55 kw:power(w):specification
yes:site installation:specification
150kg/hr:maximum output:specification
heat resistance smooth functioning easy maintenance:features:specification
50 mm:screw length:specification
150 w:power:specification
industrial:general use:specification
integrated extraction for tea, coffee and beverages:type:specification
35 mm:screw dia:specification
15 kw:contacting load:specification
6 kw:heating load:specification
1 nos.:number of extruder:specification
5 nos.:heating zone:specification
8 kw:connecting load:specification
ser 158/3 358x546x450 mm - 14x21,5x17,7 inch:dimensions (wxhxd):specification
0.1-100%:measurement range:specification
ser 158/3 115/230 - 50/60 v-hz:power supply:specification
660 mm:nip roll size:specification
80:max extension output(kg/hr):specification
rmb a40 b45:model no:specification
40/45 mm:screw diameter:specification
7/4 kw:heater capacity:specification
85 kg/hour:output:specification
sr:model:specification
230v ac 1kw:power supply:specification
vertical orientation:features:specification
17.5 hp:main drive:specification
1.08 kw:winder motor:specification
760 mm:width of lay flat:specification
75 m/min:take up speed:specification
34.75 kva:installed capacity:specification
food packaging, construction, agriculture, and medical industries:usage:specification
plastic:product material:specification
15kw:heating barrel (kw):specification
building and construction:usage:specification
mild steel, ci casting:material:specification
7" color touch screen:display:specification
titanium (velp patent pending):condensers:specification
810 mm:nip roll size:specification
27.1 kw:total heating load:specification
90 kg/hour:max extrusion output:specification
63mm:screw size:specification
for pvc /upvc material:usage:specification
extractor machine:type:specification
grey:colour:specification
1200'c:max operating temperature type:specification
digital pid:temperature control:specification
25 hp and 15 hp:motor power:specification
5 kg:silvet gold refine machine:specification
2000:1:specification
70 rpm:screw speed:specification
pvc / upvc:extruder material:specification
used to produce polymer films used by packaging industries:usage:specification
+80 degree c:temperature:specification
bitumen/centrifuge extractor - motorized:model name/number:specification
5.5 ~6.5:ph:specification
1000 mt:capacity / size:specification
contract operation of plant,technical consultency:other services offered:specification
snacktech gtl-120:brand:specification
hpde:plastic processed:specification
asi535:model:specification
78 mm:screw design:specification
1000kg:capacity:specification
2000 kg/hr:capacity:specification
floral concrete and absolute:usage/application:specification
fish feed extruder:plastic processed:specification
unique:screw design:specification
1000l:capacity:specification
electronics:usage/application:specification
cold press:machine type:specification
nitrogen gas:power supply:specification
8 hours:line speed:specification
100 - 150 kg:capacity:specification
stainless steel.mild steel:material:specification
single phase / three phase:power source:specification
100 tpd to 1000 tpd:capacity:specification
5 acres of land and more:working area:specification
230v ac:power source:specification
999.99:purity:specification
ss316l, food grade:material:specification
m s (mild steel):body material:specification
425 v:voltage:specification
rudra extrusion technik:brand:specification
180 deg. c:temperature:specification
3 hr:line speed:specification
industrial effluent:water source:specification
kg40:model name/number:specification
karat 24 projects:brand:specification
2.5 metre:hose length:specification
25w:power:specification
as per requirement:finishing:specification
10 ton:weight:specification
as per design:altimeter:specification
nil:resistance:specification
liquid liquid extraction:usage/application:specification
lavang(clove) extract:name of extract:specification
liquorice extract:name of extract:specification
glycyrrihiza glabra:botanical name:specification
sapindus trifoliate:botanical name:specification
97%:purity:specification
plastic:material to be extruder:specification
100-250 kg/h:maximal extrusion capacity:specification
5 to 100 tph:capacity:specification
22 (kw-ac):extruder drive:specification
asphalt testing:usage/application:specification
depends on size of machine:power(w):specification
1000-1700 mm:lay flat width:specification
ksa - semi automatic:winder type surface:specification
240 kg/hr:maximum output:specification
0.25 hp:motor hp:specification
10 m:cable length:specification
440 v:input voltage:specification
rmb 45:model no:specification
2-65-22v (bex):model:specification
30 (kw-ac):extruder drive:specification
2-90-22v (bex):model:specification
2 to 5 days:service duration:specification
automatic, semi-automatic:automatic grade:specification
55 to 60 kg/hr:output:specification
20 to 150 mic:thickness range:specification
40,45,40 mm:screw diameter:specification
15,20,15 hp:main motor:specification
95hp:connected load:specification
300-1250mm:film width:specification
i = 20 , 25:transmission:specification
from 2200 to 8400 nm per output shaft:rated torque:specification
50 tpd to 1000 tpd:capacity ranging:specification
120 w:power:specification
110 mm:diameter of screw:specification
customised:design:specification
40:power consumption:specification
twin cylinder:number of cylinder:specification
15-50 kw:power:specification
we will assit you in buying most appropriate co-rotating twin screw extruder machine by providing co:description:specification
ppm-65ffe:model name/number:specification
mirror polishing:finishing:specification
6 zone:digital pid. temp. controller:specification
4 sets:air rings:specification
0.5 hp:winder torque motor:specification
20 mm:co- extruder screw diameter:specification
450 mm:corona treater:specification
75 kw-ac:extruder drive:specification
5 to 18 kg/hr:capacity:specification
460 mm:width of lay flat:specification
40 micron:thickness of film:specification
271 l /d:screw ratio:specification
25 hp:main motor:specification
50-80 hr:production:specification
cylindrical:shape:specification
up to 450 mm:lfw:specification
1240 mm:height:specification
160-230 kg/hr:capacity:specification
lpde, gms, talc, butane gas:raw material:specification
380v 50hz 3phase:power supply:specification
0.5-3.5mm:sheet thickness:specification
800-1600mm:sheet width:specification
ac37kwx4p:motor:specification
steam:distillation:specification
solvent extraction plants repairing:service type:specification
1250 mm:lay flat width:specification
7hp:power consumption:specification
5 kw:induction capacity:specification
3hp:air blower:specification
rmb a35 b45:model no:specification
rmb a55 b65:model no:specification
34 mm:screw diameter:specification
floor mount:mount type:specification
100 kg/hr:production capacity.:specification
ss316 & ss304:material:specification
65-90 mm /d ratio:screw diameter:specification
en-41-b nitriding alloy steel duly nitrided and hard chromium electroplated and groove fe:material:specification
20 hp a.c. kirloskar / abb make a.c.:main drive:specification
nscbord:model name/number:specification
1100-1450 mm:width of fixed mold:specification
less than 250-400 mm:distance of pulling direction:specification
4-6.5 kgf/cm2:input air pressure:specification
more than 3.5 - 8 kg:extracting weight:specification
170kg/hr:capacity:specification
120 x 70 mm:size:specification
28:screw diameter:specification
ayurvedic medicine manufacturing , herbal drug formulation units , nutraceutical & dietary supplemen:usage/application:specification
550 -:screw torque:specification
tft:product type:specification
as per customer force:injection pressure:specification
125 hp:machine power:specification
110-380v:voltage (volt):specification
blue and yelow:color:specification
130hp:machine power:specification
15 inch:diameter:specification
10 to 45 degree c:temperature:specification
500 kgs per hour:average productivity:specification
30 lt:capacity:specification
grey and silver:color:specification
25:weight:specification
smps 24vdc:power source:specification
glass and titanium:body material:specification
industrial disposal:usage/application:specification
230 v, 50 hz:voltage supply:specification
60*60*72 inch:dimension:specification
carton:packaging type:specification
1.8 kw:power:specification
ud:brand:specification
stainless steel, all metals and non-metals:material:specification
cellwood machinery:brand:specification
40kgs:weight:specification
2:bowl capacity:specification
rice powder:material to be extruded:specification
10kg to 500kg:capacity:specification
3-30 kg per day:capacity:specification
3 or 6 positions:capacity:specification
230 volt:voltage supply (v):specification
24 kw:rated power (kw):specification
100-300 kg/hour:capacity (kilogram/hour):specification
220 v-380 v:voltage (volt):specification
25-28 kg:weight:specification
chemical:types:specification
600kg:weight:specification
pp tiatanium:body material:specification
80 ( mpm ):line speed:specification
25 kw to 300kw:motor power:specification
225mm dia x 5 itr capacity vessel:capacity:specification
for determination and checking of bitumen percentage in bituminous mix:usage/application:specification
3000tpa:production capacity:specification
430:voltage:specification
wooden if require:packaging type:specification
6 k.w.:power consumption:specification
40 to 65 kgs/hour.:production capacity:specification
pp, teflon and titanium:body material:specification
1 mm to up to requirement:min finish wire diameter:specification
manual, semi automated, fully automated:automation grade:specification
protien powder extraction:usage/application:specification
18 kg:weight:specification
medium:size:specification
65hrc:tempering hardness:specification
depending on extruder size:power:specification
450w:power:specification
7 hp:motor power:specification
blue (body):color:specification
28kg:weight:specification
5 mm:extruder drive:specification
2 kg/cm2:pressure:specification
1070 mm:drum diameter:specification
2 hp/ 1.5 kw:motor power:specification
50 mm:drain size:specification
ss 304 / 316:body material:specification
hdpe, ldpe:material to be extruded:specification
7 x 2 x 8 feet (l x b x h):dimension:specification
4 hours par baich:line speed:specification
singhal:phase:specification
10mm:sheet thickness:specification
15000kg:weight:specification
18.5 kw:power:specification
51/105:size:specification
2,400 to 3,600 rpm:speed:specification
heico:brand:specification
400 kg:capacity:specification
99.95:distillate quality:specification
pipe reyacatar tetaneyam:body material:specification
shegal face:motor power:specification
1000 piece/hour:production capacity:specification
150kg:capacity:specification
ayurvedic and herbal medicine production, herbal extracts for nutraceuticals and dietary supplemen:usage/application:specification
2 hp:power source:specification
food grade:material grade:specification
custom:ore type:specification
custom built:brand:specification
industrial scale:plant type:specification
gravity separation:processing method:specification
ms with rubber lining:material:specification
250 kw:power:specification
annato seeds, turmeric:raw material:specification
mixer-settler:column type:specification
counter-current:design type:specification
chemical:refining method:specification
1000 w:power:specification
220,440v:voltage:specification
vacum:power source:specification
electrolytic:recovery method:specification
aqueous:solvent type:specification
10���50 l/hr:recovery capacity:specification
electrical:heating source:specification
laboratory:application type:specification
internal grinding machine:type of grinding machine:specification
steel:grinding material:specification
25 kg per hr:working capacity:specification
pp ( polypropylene):body material:specification
film:application:specification
30 mm:screw diameter:specification
28 1:screw l d ratio:specification
2.5 ton:weight:specification
50000-100000 kg:weight:specification
500-1000 tph:capacity:specification
20-500 l:capacity:specification
1-5 kw:power:specification
up to 90 %:recovery efficiency:specification
25-50 kg per hr:capacity:specification
95���98 %:recovery efficiency:specification
steel slag:material processed:specification
bulk solvent:solvent type:specification
domestic:brand:specification
upto 500 tph:capacity:specification
microtest:brand:specification
51/105:screw diameter:specification
130-150 kg/hr:output:specification
130-150 kg/hr:production capacity:specification
arcl:brand:specification
5 l:capacity:specification
120 mm:screw diameter:specification
pp:material processed:specification
solid fuel:power source:specification
fs-s35:model name/number:specification
28 kg/hr:peak output:specification
1.7:peak output (kg/unit):specification
8 inch:niproll size:specification
45 mm:screw die (mm):specification
2 no.:heating zone:specification
75 hp:connected load:specification
noni extract:name of extract:specification
peel:part used:specification
1500 mm:width:specification
1575 mm:width:specification
3840 mm:length:specification
1200 rpm:maz screw speed:specification
alpha a:model name/number:specification
2.5 kw:moter:specification
10 kg/h:throughput:specification
industrial:usage application:specification
tc 80:model:specification
bitumen test:usage:specification
mooli extract:name of extract:specification
carton pallet:packaging:specification
125ml- 1l:flask capacity:specification
110 kg/h:capacity:specification
180kg/hr:maximum plasticizing capacity:specification
18.5kw:main drive:specification
3kw:heating die (kw):specification
20 (kw):total power:specification
18.5 mm:screw diameter:specification
5.5 kw:motor:specification
3850x700x1800 mm:dimension:specification
8.7 nm/cm3:specific torque:specification
5.46nm/cm3:specific torque:specification
37rpm:screw speed variation (rpm):specification
hpmc 51/105:model number:specification
75 hp:power:specification
1730 x 905 x 1820:overall dimensions (lxbxh) (mm):specification
all type of material:material:specification
130-140 kg/hr:max. output:specification
checking of bitumen percentage:use:specification
7.2m:length of cable:specification
rasching rings, material borosilicate glass:packing:specification
material stainless steel (1 each), cap. 10 ltrs.:extract and raffinate tanks:specification
by compressed air:feed circulation:specification
261:ld ratio:specification
10 (kw):heating load:specification
1 (hp):pelletizer motor:specification
80 micron:thickness of film:specification
hm-hdpe / ldpe / lldpe / biodegradable bag/carry bag/shopping bag:usage:specification
1800 mm:vacuum:specification
>95%:collection efficiency:specification
uv light:pollution control:specification
goyum 240:model:specification
1kw:question:specification
hdpe container:packaging type:specification
lakshmi advance bio- tech:manufactured by:specification
26 mm:output size:specification
high efficiency:feature:specification
electrically operated bitumen extractor:title:specification
an electric motor coupled to the gearbox to rotate the shaft and the drive through a step pulley:usage:specification
1:good quality:specification
80 - 400 mm:width:specification
30 : 1:screw ratio:specification
low waste:refinery:specification
50mm (hm/hdpe) 100 (ld/ldpe):die:specification
500 mm:web width upto:specification
grooved feed:feed section:specification
4 days:service duration:specification
600 - 1250 to 1400 - 2100 ( mm ):lay flat width and diameter:specification
industrial use:application:specification
20 kg/hr,5.0 bar min pressure:steam supply:specification
all kinds extarction solutions:deal in:specification
nc-50:model name/number:specification
100 copy sample positive rate>95%:purification accuracy:specification
lysis,sample binding,washing and elution:extraction steps:specification
200-2000mtpd:capacity:specification
5000:capacity:specification
15 kg.:rajkamal brand:specification
15 kg.:capacity:specification
variable:frequency:specification
optional:vacuum system:specification
50 tons/day:capacity:specification
250ml:capacity:specification
vijay industries:brand:specification
cable:usage/application:specification
75 mm:extruder size:specification
customized:film thickness:specification
customises:type:specification
as per requirement:design:specification
customised:size:specification
customize:packaging size:specification
food industry, pharma,ayurvedic:usage/application:specification
cinnamon, blackpepper, clove, onion, chilly, turmeric, ginger, etc:raw material:specification
pe:material processed:specification
price : 5500000 to 7500000:round drip pipe making machine:specification
200 kgs/hr:extruder capacity:specification
33 1:screw l d ratio:specification
55 mtrs/min to 95 mtrs/min:line speed:specification
pe pipe:application:specification
commercial and isi:quality:specification
single layer, two layer and three layers:layer:specification
food material:usage/application:specification
unisoft / devika:brand:specification
1 years:warranty:specification
ss 316:body material:specification
762:film width:specification
15 hp:power consumption:specification
compostable film blowing machine:usage/application:specification
silver grey:color:specification
cylinderical:shape:specification
4" x 6":size:specification
3kgs and 5kgs:capacity:specification
sb 265 gr.2:material grade:specification
no:vacuum system:specification
gtaw:technique:specification
wire and cable machine part:usage/application:specification
lszh:material processed:specification
99.9 %:purity:specification
50kg - 500 kg:capacity:specification
10 kw:power (w):specification
20mm to 150mm:diameter:specification
3:weight:specification
30 1:screw l d ratio:specification
all herbal extracts:usage/application:specification
industrial scale:machine type:specification
as per load:power:specification
as per load:screw torque:specification
3 mm:wall thickness:specification
iso:certification:specification
700 rpm:speed:specification
three phase:operating phase:specification
2kb wat:power:specification
96 12x75:dimensions:specification
wooden paking:packaging type:specification
999%:purity:specification
customized:font roll diameter:specification
32-40:screw l/d:specification
bharat emporium:brand:specification
110:line speed:specification
80kg to 250kg/hr.:production capacity:specification
40mm (diameter):die size:specification
gear pinion/ hollow shaft gearbox:driven type:specification
herbal plant extraction process:usage/application:specification
5kg:pressure:specification
less than 60 db:noise level:specification
ulpa filter:filtration:specification
10 metre:cable length:specification
stainless steel:container material:specification
mingsheng:brand:specification
320 kv:voltage:specification
50 bar:pressure:specification
bvncbv:power source:specification
2 kw:voltage:specification
customize:design:specification
2 ton:weight:specification
26 1:screw l d ratio:specification
1:20:l/d ratio:specification
special grade:material:specification
ptfe:material processed:specification
100 m/min:line speed:specification
1kg to 100 kg:dimension:specification
1-100 tpd:capacity:specification
12-32 mm:tube diameter range:specification
200-500 kg/hr:production capacity:specification
10-30kg:capacity:specification
up to 10 square mm:size:specification
ms powered coated epoxy paint:body material:specification
sladjana sales corporation:manufacturer:specification
electrical operated:operated type:specification
2 kwh:power consumption:specification
440 v/230 v:voltage:specification
single:packaging type:specification
solvent extraction:extraction method:specification
rice bran:input material type:specification
customise:machine type:specification
standard:brand category:specification
arh engineering works:brand:specification
3 l:capacity:specification
edible oil processing:application type:specification
5 tph:capacity:specification
20 hp:power source:specification
used for metal recovery:usage:specification
precious metal:material processed:specification
tei04958:model:specification
no:power source:specification
casting iron:material:specification
2 litre:drum size:specification
tei:brand:specification
19483:model number:specification
industrial:automation grade:specification
kishmish:grape type:specification
15 inch:size:specification
rkh15:model name/number:specification
s s.:material:specification
solvent:expander type:specification
250mm:tube od range:specification
alloy steel:roll material:specification
hips:material processed:specification
abs:material processed:specification
new:machine condition:specification
17m/min:line speed:specification
1:number of motor:specification
200 m/min:line speed:specification
nitride alloy steel and glass nitride:body material:specification
turmeric / curcumin extract:usage/application:specification
sulphuric acid plant:type of chemical plant:specification
2 tons/day:output capacity:specification
99.99 %:purity:specification
electrolytic:refining method:specification
upto 1 ton:capacity:specification
upto 500 iph:printing speed:specification
pp plastic:body material:specification
electricity:energy:specification
10 x 10 x 15 feet:dimension:specification
600 kgs:weight:specification
shraj:brand:specification
500:drum size:specification
ss+ms / ss304 / ss316 / msrl:material:specification
sew:brand:specification
solvent & aqueous based:technique:specification
depending upon the capacity.:wall thickness:specification
automotive cable:application:specification
6 sqmm:wire size range:specification
sicon:brand:specification
silicon:material processed:specification
extruder line:machine type:specification
copper:conductor material:specification
100 ton/day:plant capacity:specification
solvent extraction:process type:specification
100 kw:power:specification
ms with ss contact:body material:specification
continuous type:plant type:specification
30 kw:motor power:specification
125mm:screw diameter:specification
all size:size:specification
chain drive:driven type:specification
double action:design type:specification
profile extrusion:machine type:specification
electric-hydraulic:power source:specification
sms:brand:specification
copper:material to be extruded:specification
as required:frequency:specification
"""
# ============================================================================
# END OF ATTRIBUTE DATA SECTION
# ============================================================================

def parse_attribute_dataset(raw_data):
    """Parse the attribute dataset into a structured format"""
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    
    # Remove placeholder text
    lines = [line for line in lines if not line.startswith('PASTE_YOUR') and not line.startswith('EACH_LINE')]
    
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
    """Create prompt with full attribute dataset"""
    
    # Build attribute reference (compressed format)
    attr_reference = "Available Attributes for Industrial Extraction Plants and Extruder Machines:\n\n"
    for attr_name, values in attr_dict.items():
        # Limit to first 20 values per attribute to save tokens
        value_list = ' | '.join(values[:20])
        if len(values) > 20:
            value_list += f" ... (+{len(values)-20} more)"
        attr_reference += f"- {attr_name}: {value_list}\n"
    
    prompt = f"""{attr_reference}

Extract product attributes from the query below using ONLY the attributes listed above.

IMPORTANT RULES:
1. Use ISQ format: attribute_value:attribute_name:attribute_type
2. attribute_type is always "specification"
3. Only extract attributes that match the available list
4. If an attribute value is mentioned but not in the list, still extract it
5. Return as a Python list format

Examples:

Query: "440V three phase automatic extruder"
Output: ['440 v:voltage:specification', 'three phase:phase:specification', 'automatic:automation grade:specification']

Query: "stainless steel paint coated extraction plant"
Output: ['stainless steel:body material:specification', 'paint coated:surface finishing:specification']

Now extract attributes for this query:

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
                    time.sleep(2)  # Wait before retry
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
                time.sleep(2)  # Wait before retry
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
            print(f"  Estimated time remaining: {((total_queries-i)*0.1/60):.1f} minutes")
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
