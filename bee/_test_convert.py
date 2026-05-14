import sys, json
sys.path.insert(0, "/home3/indiamart/gemma_4")
from finetune_gemma4_v4_priority import convert_file

n_in, n_out = convert_file("/home3/indiamart/gemma_4/cat74_train.jsonl",
                           "/tmp/_test_nested.jsonl")
print("train:", n_in, "->", n_out)
with open("/tmp/_test_nested.jsonl") as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        r = json.loads(line)
        print("--- SAMPLE", i, "---")
        print("INSTR:", r["instruction"][:220])
        print("OUT  :", r["output"][:600])

# token length distribution sample
try:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("/home3/indiamart/gemma_4/models/gemma-4-e4b-it")
    lens = []
    with open("/tmp/_test_nested.jsonl") as f:
        for i, line in enumerate(f):
            if i >= 300:
                break
            r = json.loads(line)
            text = ("<start_of_turn>user\n" + r["instruction"]
                    + "<end_of_turn>\n<start_of_turn>model\n" + r["output"]
                    + "<end_of_turn>")
            lens.append(len(tok(text)["input_ids"]))
    lens.sort()
    print(f"\nTOKEN LEN (n={len(lens)}): min={lens[0]} p50={lens[len(lens)//2]} "
          f"p90={lens[int(len(lens)*0.9)]} p99={lens[int(len(lens)*0.99)]} max={lens[-1]}")
    print(f"  >1024: {sum(1 for l in lens if l>1024)}/{len(lens)}")
except Exception as e:
    print("tok stats failed:", e)
