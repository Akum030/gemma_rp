import json
lines = open("/home3/indiamart/gemma_4/agent/v3_results.jsonl").readlines()
ok = sum(1 for l in lines if json.loads(l)["ok"])
print("OK:", ok, "/", len(lines))

# Show first 3 OK with raw
n=0
for l in lines:
    r = json.loads(l)
    if r["ok"]:
        print("---OK---", r["query"])
        print("RAW:", repr(r["raw"]))
        n += 1
        if n >= 3: break

# Show first 5 FAILED
n=0
for l in lines:
    r = json.loads(l)
    if not r["ok"]:
        print("---FAIL---", r["query"])
        print("RAW:", repr(r["raw"]))
        n += 1
        if n >= 5: break
