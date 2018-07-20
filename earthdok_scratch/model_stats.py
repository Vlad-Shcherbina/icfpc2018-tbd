from os import listdir
from os.path import isfile, join
from collections import defaultdict

models_dir = '../problemsL'

model_files = [join(models_dir, f) for f in listdir(models_dir) if isfile(join(models_dir, f)) and f.endswith('.mdl')]

rs = defaultdict(lambda: 0)

for path_to_file in model_files:
  with open (path_to_file, 'rb') as f:
    r = f.read(1)[0]
    full_or_void = f.read((r * r * r) // 8)
    full_count = sum(bin(byte).count('1') for byte in full_or_void)
    print(path_to_file, r, full_count)
    rs[r] += 1

print(sorted(rs.items()))