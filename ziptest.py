# Compress the Alivewatch.csv file to a .gz

import pandas as pd

df = pd.read_csv('Alivewatch.csv', encoding='utf-8')
df.to_csv('Alivewatch.csv.gz', compression='gzip', index=False)

