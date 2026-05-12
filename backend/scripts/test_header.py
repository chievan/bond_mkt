import pandas as pd
import sys
import os

# Mock the parser functions
def find_header_row(df):
    header_keywords = ['期限', '收益率', '利差', '基差', '分位数', '代码', '名称', '指标', '变动', '水平']
    max_matches = -1
    best_row = 0
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        matches = sum(1 for val in row.values if any(kw in str(val) for kw in header_keywords))
        print(f"Row {i} matches: {matches} - Content: {row.values}")
        if matches > max_matches:
            max_matches = matches
            best_row = i
    return best_row

excel_path = "1-成交情况与利差基差V2.xlsx"
df = pd.read_excel(excel_path, sheet_name="收益率曲线", header=None)
# Filter empty
df = df.dropna(how='all').dropna(axis=1, how='all')

# Find first chunk
empty_rows = df.isnull().all(axis=1)
df['group'] = (empty_rows).cumsum()
chunks = df[~empty_rows].groupby('group')

for g, chunk in chunks:
    chunk = chunk.drop(columns=['group'])
    print(f"\n--- Analyzing Chunk {g} ---")
    h_idx = find_header_row(chunk)
    print(f"Best header row index: {h_idx}")
    break
