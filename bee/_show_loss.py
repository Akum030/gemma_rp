import re, sys
with open('/home3/indiamart/gemma_4/training_v4.log','rb') as f:
    txt = f.read().decode('utf-8','replace')
txt = txt.replace('\r','\n')
hits = re.findall(r"\{[^{}]*?loss[^{}]*?\}", txt)
for h in hits:
    print(h)
