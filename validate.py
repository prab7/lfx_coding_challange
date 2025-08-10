import yaml
from main import *
from pathlib import Path
import sys


yaml_file = "generated_lw.yaml"
with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

# Generate C header
instruction_name = yaml_file.replace('.yaml', '')
header_content = generate_c_header(data, instruction_name)
header_file =  f"{instruction_name.lower()}.h"

with open(header_file, 'w') as f:
    f.write(header_content)

print(f"Generated C header: {header_file}")

# Generate C source
source_content = generate_c_source(data, instruction_name)
source_file = f"{instruction_name.lower()}.c"

with open(source_file, 'w') as f:
    f.write(source_content)

print(f"Generated C source: {source_file}")