import pandas as pd

df = pd.read_excel("Correcciones GRO.xlsx", sheet_name=0, dtype=str)
print("Exact column names:")
for i, col in enumerate(df.columns):
    print(f"  [{i}] '{col}'")