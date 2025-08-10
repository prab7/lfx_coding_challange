## Overview

### 1. `main.py`
- **Functionality**:
  - Scans `spec/std/isa/inst` directory in riscv-unified-db
  - Downloads YAML instruction files grouped by extension (I, M, C, etc.)
  - Generates:
    - C header files (`.h`) with instruction data structures
    - C source files (`.c`) with YAML serialization logic
- **Output Structure**:
  ```
  output/
  ├── inst-headers/   # Generated C headers
  ├── inst-src/       # Generated C sources
  └── inst/           # Downloaded YAMLs
      ├── I/
      ├── M/
      └── ...
  ```

### 2. `validate.py`
- **Verification Process**:
  1. Executes generated C code to reproduce YAML
  2. Re-parses the output through the same pipeline
  3. The emitted YAML file matches the generated YAML file.

## Usage

```bash
# Generate C implementations
python3 main.py
cd inst-src
gcc -o ../lw lw.c
cd ..
./lw > generated_lw.yaml

# change path
python3 validate.py
gcc -o validated_lw generated_lw.c
./validated_lw > validated_lw.yaml

```
