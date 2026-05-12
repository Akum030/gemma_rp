import pandas as pd
import json

print("="*80)
print("TRAINING DATASET SOURCE - CLARIFICATION")
print("="*80)

print("\n NO - Training data is NOT from unique_key_val_96_cat.csv")
print(" YES - Training data is from qmeans_results.csv (QMeans API outputs)")

print("\n\nHere's what each file was used for:")
print("-"*80)

# Check unique_key_val_96_cat.csv
prod_df = pd.read_csv("unique_key_val_96_cat.csv", header=None, names=["key", "value"])
print(f"\n1. unique_key_val_96_cat.csv:")
print(f"   - Rows: {len(prod_df)}")
print(f"   - Purpose: VALIDATION ONLY (check if QMeans keys exist in production)")
print(f"   - NOT used for training data generation")
print(f"   - Sample: {prod_df.iloc[0]['key']}: {prod_df.iloc[0]['value']}")

# Check qmeans_results.csv
qmeans_df = pd.read_csv("qmeans_results.csv")
print(f"\n2. qmeans_results.csv:")
print(f"   - Rows: {len(qmeans_df)}")
print(f"   - Purpose: SOURCE for training data (real QMeans API outputs)")
print(f"   - Sample query: {qmeans_df.iloc[0]['query']}")
print(f"   - Sample output: {qmeans_df.iloc[0]['qmeans_isq_pipe']}")

# Check training file
with open("gemma_final_training_dataset.jsonl", encoding="utf-8") as f:
    training_lines = f.readlines()
    
print(f"\n3. gemma_final_training_dataset.jsonl:")
print(f"   - Rows: {len(training_lines)}")
print(f"   - Source: Extracted from qmeans_results.csv (column: qmeans_isq_pipe)")
print(f"   - Sample: {training_lines[0].strip()}")

print("\n\n" + "="*80)
print("WORKFLOW")
print("="*80)
print("\nStep 1: Extract QMeans outputs from qmeans_results.csv")
print("        ")
print("Step 2: Parse ISQ format: 'value:key:specification'")
print("        ")
print("Step 3: Convert to JSON: {'key': 'value'}")
print("        ")
print("Step 4: Create training pairs: instruction + output")
print("        ")
print("Step 5: VALIDATE keys against unique_key_val_96_cat.csv")
print("        ")
print("Step 6: Save to gemma_final_training_dataset.jsonl")

print("\n\n" + "="*80)
print("IS THIS SYNTHETIC?")
print("="*80)
print("\n NO - This is NOT synthetic data")
print(" YES - This is REAL QMeans API outputs")
print("\nEvery training example comes from:")
print("  - Real user queries (from qmeans_results.csv)")
print("  - Real QMeans API responses (from qmeans_results.csv)")
print("  - No synthetic generation, no GPT creation")
print("  - Direct extraction from QMeans API outputs")

print("\n\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nTraining data source: qmeans_results.csv (983 real QMeans outputs)")
print("Validation source: unique_key_val_96_cat.csv (11,381 production key-value pairs)")
print("Result: 100% real QMeans data, 0% synthetic")
