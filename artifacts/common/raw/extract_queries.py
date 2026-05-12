import pandas as pd

# Read the full dataset
df = pd.read_csv('synthetic_validation_dataset.csv')

# Extract just the query column
queries_df = df[['query']]

# Save to new file
queries_df.to_csv('validation_queries.csv', index=False)

print(f'Created validation_queries.csv with {len(queries_df)} queries')
