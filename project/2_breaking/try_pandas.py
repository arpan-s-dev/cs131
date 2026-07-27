"""
CS 131 - Phase 2: Breaking pandas.

This does what you would normally do with a small CSV: read it with
pandas so the whole table sits in memory. Here it cannot work. The
machine has 15.3 GB of RAM; the 121 Gaia files are about 120 GB when
uncompressed. We load one file at a time and keep it, printing how much
memory Python is using after each, until it runs out and crashes with
MemoryError.

Run it from the project root (Z:\\CS 131 project) so that data/ is found:
    python cs131/project/2_breaking/try_pandas.py
"""

import glob
import time
import pandas as pd

# psutil lets us print the memory used after each file. If it isn't
# installed, the script still runs - just watch Task Manager instead.
try:
    import psutil
    process = psutil.Process()
    def ram_used_gb():
        return process.memory_info().rss / 1e9
except ImportError:
    def ram_used_gb():
        return float("nan")

files = sorted(glob.glob("data/*.csv.gz"))
print(f"Found {len(files)} files. Trying to load all of them into memory.\n")

tables = []
total_rows = 0
start = time.time()

for i, path in enumerate(files, start=1):
    # comment="#" skips the 1000 metadata lines at the top of each file.
    # pandas reads the .gz directly (it detects gzip from the extension).
    table = pd.read_csv(path, comment="#", low_memory=False)

    tables.append(table)          # keep it - this is what fills up RAM
    total_rows += len(table)

    print(f"file {i:3d}/{len(files)}   "
          f"rows loaded: {total_rows:>12,}   "
          f"RAM used: {ram_used_gb():5.1f} GB   "
          f"({time.time() - start:4.0f}s)")

# We should never reach this line - RAM runs out first.
everything = pd.concat(tables, ignore_index=True)
print(f"\nLoaded all {len(everything):,} rows. (If you see this, the data fit "
      f"in memory - it should not have.)")
