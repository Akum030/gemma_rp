# fix_compressed_isq.py
INPUT = "compressed_attributes_isq.txt"
OUTPUT = "compressed_attributes_isq_fixed.txt"

with open(INPUT, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all backslashes with forward slashes
fixed_content = content.replace('\\', '/')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print(f"Fixed! Now use: {OUTPUT}")
print("Copy content from compressed_attributes_isq_fixed.txt")
