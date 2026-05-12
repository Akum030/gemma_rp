"""
Gemma V4 Batch Inference - Process 1000 queries FAST
Run on GPU server: python gemma_1000_inference.py --input queries.csv --output gemma_v4_results.csv

Output CSV columns:
  query, success, unique_value_count, total_key_count, raw_output, attributes_json
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import json
import csv
import time
import argparse
import os

MODEL_PATH = "./isq-gemma2-9b-finetuned-v4-priority"
BASE_MODEL = "google/gemma-2-9b-it"

INSTRUCTION_TEMPLATE = """Extract product attributes from the search query and provide them in JSON format with multiple key alternatives and priorities.

Query: {query}

Output format:
{{"attributes": [{{"attribute_key": "key_name", "value": "extracted_value", "key_priority": 1-4, "attribute_priority": 1-N}}]}}"""


def load_model():
    print("Loading model...")
    t0 = time.time()

    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_compute_dtype=torch.float16
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

    model = PeftModel.from_pretrained(base_model, MODEL_PATH)
    model.eval()  # Set to evaluation mode to reduce memory overhead

    print(f"Model loaded in {time.time() - t0:.1f}s")
    return model, tokenizer


def predict(model, tokenizer, query):
    instruction = INSTRUCTION_TEMPLATE.format(query=query)
    messages = [{"role": "user", "content": instruction}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,  # Balanced: enough for JSON, faster than 512
            do_sample=False,     # Greedy decoding (fastest)
            num_beams=1,         # No beam search
            use_cache=True,      # Enable KV cache
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    
    # Clear GPU memory to prevent accumulation
    del inputs, outputs
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return response.strip()


def parse_output(raw_output):
    """Parse model output into structured attributes."""
    try:
        if '{' in raw_output and '}' in raw_output:
            json_start = raw_output.find('{')
            json_end = raw_output.rfind('}') + 1
            json_str = raw_output[json_start:json_end]
            parsed = json.loads(json_str)

            attributes = parsed.get('attributes', [])
            unique_values = set()
            for attr in attributes:
                unique_values.add(str(attr.get('value', '')).strip().lower())

            return {
                'success': True,
                'unique_value_count': len(unique_values),
                'total_key_count': len(attributes),
                'attributes': attributes,
                'parsed_json': json.dumps(parsed)
            }
    except (json.JSONDecodeError, Exception):
        pass

    return {
        'success': False,
        'unique_value_count': 0,
        'total_key_count': 0,
        'attributes': [],
        'parsed_json': ''
    }


def read_queries(filepath):
    """Read queries from CSV or text file."""
    queries = []
    try:
        # Try CSV first
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'query' in (reader.fieldnames or []):
                for row in reader:
                    q = row['query'].strip()
                    if q:
                        queries.append(q)
                return queries
    except:
        pass

    # Fall back to line-by-line
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line and line.lower() != 'query':
            queries.append(line)

    return queries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='76cat_queries.csv', help='Input queries file')
    parser.add_argument('--output', default='gemma_v4_1000_results.csv', help='Output CSV file')
    parser.add_argument('--start', type=int, default=0, help='Start index (for resume)')
    parser.add_argument('--limit', type=int, default=0, help='Max queries to process (0=all)')
    args = parser.parse_args()

    # Read queries
    queries = read_queries(args.input)
    print(f"Total queries: {len(queries)}")

    if args.limit > 0:
        queries = queries[:args.limit]

    if args.start > 0:
        queries = queries[args.start:]
        print(f"Starting from index {args.start}, remaining: {len(queries)}")

    # Load model
    model, tokenizer = load_model()

    # Process queries
    output_json = args.output.replace('.csv', '.json')
    results = []
    success_count = 0
    total_time = 0

    # Open CSV for writing (append mode for resume)
    csv_mode = 'a' if args.start > 0 else 'w'
    csv_file = open(args.output, csv_mode, newline='', encoding='utf-8')
    writer = csv.writer(csv_file)

    if args.start == 0:
        writer.writerow(['query', 'success', 'unique_value_count', 'total_key_count', 'raw_output', 'attributes_json'])

    print(f"\nProcessing {len(queries)} queries...")
    print("=" * 80)

    for idx, query in enumerate(queries):
        actual_idx = idx + args.start
        t0 = time.time()

        try:
            raw_output = predict(model, tokenizer, query)
            parsed = parse_output(raw_output)

            row = [
                query,
                parsed['success'],
                parsed['unique_value_count'],
                parsed['total_key_count'],
                raw_output,
                parsed['parsed_json']
            ]

            writer.writerow(row)
            csv_file.flush()  # Flush after each write for crash safety

            results.append({
                'query': query,
                'raw_output': raw_output,
                **parsed
            })

            elapsed = time.time() - t0
            total_time += elapsed

            if parsed['success']:
                success_count += 1

            avg_time = total_time / (idx + 1)
            remaining = avg_time * (len(queries) - idx - 1)

            print(f"[{actual_idx + 1}/{len(queries) + args.start}] "
                  f"{'OK' if parsed['success'] else 'FAIL'} "
                  f"| {parsed['unique_value_count']} vals, {parsed['total_key_count']} keys "
                  f"| {elapsed:.1f}s "
                  f"| ETA: {remaining / 60:.0f}min "
                  f"| {query[:60]}")

        except Exception as e:
            elapsed = time.time() - t0
            total_time += elapsed
            print(f"[{actual_idx + 1}] ERROR: {e} | {query[:60]}")

            writer.writerow([query, False, 0, 0, f"ERROR: {e}", ''])
            csv_file.flush()

            results.append({
                'query': query,
                'raw_output': f"ERROR: {e}",
                'success': False,
                'unique_value_count': 0,
                'total_key_count': 0,
                'attributes': [],
                'parsed_json': ''
            })

        # Save JSON checkpoint and clear CUDA cache every 50 queries
        if (idx + 1) % 50 == 0:
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"  >> Checkpoint saved: {len(results)} results | GPU cache cleared")

    csv_file.close()

    # Save final JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 80)
    print(f"DONE! Processed {len(queries)} queries in {total_time / 60:.1f} minutes")
    print(f"Success rate: {success_count}/{len(queries)} ({success_count * 100 / max(1, len(queries)):.1f}%)")
    print(f"Avg time per query: {total_time / max(1, len(queries)):.2f}s")
    print(f"CSV saved: {args.output}")
    print(f"JSON saved: {output_json}")
    print("=" * 80)


if __name__ == "__main__":
    main()
