import pandas as pd

# Configuration
INPUT_CSV = "your_attributes.csv"  # Your 11k attribute CSV file
OUTPUT_TXT = "attributes_isq_format.txt"  # Output ISQ format

def convert_to_isq():
    """Convert attribute CSV to ISQ format"""
    
    print(f"Reading attributes from: {INPUT_CSV}")
    
    # Read CSV - assuming columns are unnamed or named differently
    # We'll just use the first two columns
    df = pd.read_csv(INPUT_CSV, header=None)
    
    # If your CSV has headers in first row, use this instead:
    # df = pd.read_csv(INPUT_CSV)
    # Then rename below accordingly
    
    print(f"Total rows: {len(df)}")
    
    # Column 0 = attribute name (key)
    # Column 1 = attribute value
    attr_name_col = df.iloc[:, 0]  # First column (A)
    attr_value_col = df.iloc[:, 1]  # Second column (B)
    
    # Create ISQ format: value:name:specification
    isq_list = []
    
    for attr_name, attr_value in zip(attr_name_col, attr_value_col):
        # Skip empty rows
        if pd.isna(attr_name) or pd.isna(attr_value):
            continue
        
        # Clean up values
        attr_name = str(attr_name).strip()
        attr_value = str(attr_value).strip()
        
        # Create ISQ format
        isq = f"{attr_value}:{attr_name}:specification"
        isq_list.append(isq)
    
    print(f"Converted {len(isq_list)} attributes to ISQ format")
    
    # Remove duplicates
    isq_list_unique = list(dict.fromkeys(isq_list))
    print(f"Unique ISQs: {len(isq_list_unique)}")
    
    # Save to file
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        for isq in isq_list_unique:
            f.write(isq + '\n')
    
    print(f"\n[DONE] ISQ format saved to: {OUTPUT_TXT}")
    print(f"\nFirst 10 ISQs:")
    for isq in isq_list_unique[:10]:
        print(f"  {isq}")
    
    print(f"\n[NEXT STEP]")
    print(f"1. Open {OUTPUT_TXT}")
    print(f"2. Copy ALL lines")
    print(f"3. Paste into gemini_with_dataset.py in the ATTRIBUTE_DATASET section")

if __name__ == "__main__":
    convert_to_isq()
