import yaml
import requests
from pathlib import Path
from datetime import datetime
import sys
import re


def get_extension_folders():
    """Fetch RISC-V extension folder names (I, M, C, etc.) using GitHub API."""
    api_url = "https://api.github.com/repos/riscv-software-src/riscv-unified-db/contents/spec/std/isa/inst"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        folders = [
            item["name"] for item in response.json() 
            if item["type"] == "dir" and not item["name"].startswith(".")
        ]
        return folders
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch extensions: {e}")
        return []


def sanitize_c_name(name):

    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"

    return sanitized.upper()

def is_multiline_string(s):
    return isinstance(s, str) and '\n' in s


def yaml_to_c_representation(value, depth=0):
    
    if isinstance(value, dict):
        if depth > 2:
            return "/* Complex nested structure omitted */"
        
        items = []
        for k, v in value.items():
            safe_key = sanitize_c_name(k)
            c_val = yaml_to_c_representation(v, depth + 1)
            items.append(f'    .{safe_key.lower()} = {c_val}')
        return "{\n" + ",\n".join(items) + "\n}"
    
    elif isinstance(value, list):
        if not value:
            return "{}"
        
        if all(isinstance(x, (str, int, float, bool)) for x in value):
            c_values = [yaml_to_c_representation(x, depth + 1) for x in value]
            return "{" + ", ".join(c_values) + "}"
        else:
            return "/* Complex array omitted */"
    
    elif isinstance(value, str):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    
    elif isinstance(value, bool):
        return "1" if value else "0"
    
    elif isinstance(value, (int, float)):
        return str(value)
    
    elif value is None:
        return "NULL"
    
    else:
        return f'"{str(value)}"'

def generate_c_header(yaml_data, instruction_name):

    header_guard = f"{sanitize_c_name(instruction_name)}_H"
    
    header = f"""#ifndef {header_guard}
#define {header_guard}

// C header for : {instruction_name}

#include <stdint.h>

"""
    
    # Generate structure definition
    struct_name = f"{sanitize_c_name(instruction_name).lower()}_t"
    
    header += f"/* Structure for {instruction_name} instruction data */\n"
    header += f"typedef struct {{\n"
    
    for key, value in yaml_data.items():
        safe_key = sanitize_c_name(key).lower()
        
        if isinstance(value, str):
            header += f"    const char* {safe_key};\n"

        elif isinstance(value, bool):
            header += f"    int {safe_key};\n"

        elif isinstance(value, (int, float)):
            if isinstance(value, int) and value >= 0:
                header += f"    uint32_t {safe_key};\n"
            else:
                header += f"    int32_t {safe_key};\n"

        elif isinstance(value, list):
            if value and isinstance(value[0], str):
                header += f"    const char* {safe_key}[{len(value)}];\n"
            else:
                header += f"    const char* {safe_key}_data;\n"  # Serialize complex data
        else:
            header += f"    const char* {safe_key}_data;\n"  # Serialize complex data
    
    header += f"}} {struct_name};\n\n"
    
    # Generate data initialization
    header += f"/* Data for {instruction_name} instruction */\n"
    header += f"static const {struct_name} {instruction_name.lower()}_data = {{\n"
    
    for key, value in yaml_data.items():
        safe_key = sanitize_c_name(key).lower()
        
        if isinstance(value, list) and value and isinstance(value[0], str):

            # string arrays
            array_values = ", ".join(f'"{item}"' for item in value)
            header += f"    .{safe_key} = {{{array_values}}},\n"
        elif isinstance(value, (dict, list)) and not (isinstance(value, list) and value and isinstance(value[0], str)):

            # Serialize complex structures as strings using flow style
            serialized = yaml.dump(value, default_flow_style=True, width=1000).strip().replace('"', '\\"')
            header += f'    .{safe_key}_data = "{serialized}",\n'
        else:
            c_value = yaml_to_c_representation(value)
            header += f"    .{safe_key} = {c_value},\n"
    
    header += "};\n\n"
    
    # Add getter functions
    header += f"/* Getter functions for {instruction_name} */\n"
    header += f"static inline const {struct_name}* get_{instruction_name.lower()}_data(void) {{\n"
    header += f"    return &{instruction_name.lower()}_data;\n"
    header += "}\n\n"
    
    # Add YAML recreation function declaration
    header += f"/* Function to recreate YAML (implement in .c file) */\n"
    header += f"const char* {instruction_name.lower()}_to_yaml(void);\n\n"
    
    header += f"#endif /* {header_guard} */\n"
    
    return header



def generate_c_source(yaml_data, instruction_name):

    source = f"""// C source for {instruction_name}

#include <stdio.h>
#include <string.h>
#include "../inst-headers/{instruction_name.lower()}.h"

static void format_multiline_string(char* buffer, size_t buffer_size, size_t* offset, 
                                   const char* key, const char* value) {{
    *offset += snprintf(buffer + *offset, buffer_size - *offset, "%s: |\\n", key);
    
    // Split the string by newlines and indent each line
    char temp[1024];
    strncpy(temp, value, sizeof(temp) - 1);
    temp[sizeof(temp) - 1] = '\\0';
    
    char* line = strtok(temp, "\\n");
    while (line != NULL && *offset < buffer_size - 1) {{
        *offset += snprintf(buffer + *offset, buffer_size - *offset, "  %s\\n", line);
        line = strtok(NULL, "\\n");
    }}
}}

const char* {instruction_name.lower()}_to_yaml(void) {{
    static char yaml_buffer[4096];
    const {sanitize_c_name(instruction_name).lower()}_t* data = get_{instruction_name.lower()}_data();
    
    size_t offset = 0;
    yaml_buffer[0] = '\\0';
"""
    
    for key, value in yaml_data.items():
        safe_key = sanitize_c_name(key).lower()

        if isinstance(value, str):
            if is_multiline_string(value):
                # Use the helper function for multiline strings
                source += f'    format_multiline_string(yaml_buffer, sizeof(yaml_buffer), &offset, "{key}", data->{safe_key});\n'
            else:
                # Handle regular strings
                source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "{key}: %s\\n", data->{safe_key});\n'

        elif isinstance(value, bool):
            source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "{key}: %s\\n", (data->{safe_key} ? "true" : "false"));\n'

        elif isinstance(value, (int, float)):
            source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "{key}: %d\\n", data->{safe_key});\n'

        elif isinstance(value, list) and value and isinstance(value[0], str):
            source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "{key}: [");\n'
            for i, item in enumerate(value):
                if i > 0:
                    source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, ", ");\n'
                source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "%s", data->{safe_key}[{i}]);\n'
            source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "]\\n");\n'
        else:
            # Use the flow-style serialized data
            source += f'    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "{key}: %s\\n", data->{safe_key}_data);\n'
    
    source += f"""
    
    return yaml_buffer;
}}

int main(void) {{
    printf("%s", {instruction_name.lower()}_to_yaml());
    return 0;
}}
"""
    
    return source

def download_and_process_yaml_files(find_these_files):

    base_url = "https://raw.githubusercontent.com/riscv-software-src/riscv-unified-db/main/spec/std/isa/inst/"
    
    extensions = get_extension_folders()
    
    output_dir = Path("inst")
    output_dir.mkdir(exist_ok=True)
    
    header_dir = Path("inst-headers")
    header_dir.mkdir(exist_ok=True)

    source_dir = Path("inst-src")
    source_dir.mkdir(exist_ok=True)
    
    found_files = set()
    
    for yaml_file in find_these_files:
        found = False
        
        for ext in extensions:

            file_url = f"{base_url}{ext}/{yaml_file}"
            
            try:
                head_response = requests.head(file_url)
                if head_response.status_code != 200:
                    continue
                
                ext_dir = output_dir / ext
                ext_dir.mkdir(exist_ok=True)
                
                local_path = ext_dir / yaml_file
                
                response = requests.get(file_url)
                response.raise_for_status()
                
                with open(local_path, 'w') as f:
                    f.write(response.text)
                
                with open(local_path, 'r') as f:
                    data = yaml.safe_load(f)


                # Generate C header
                instruction_name = yaml_file.replace('.yaml', '')
                header_content = generate_c_header(data, instruction_name)
                header_file = header_dir / f"{instruction_name.lower()}.h"
                
                with open(header_file, 'w') as f:
                    f.write(header_content)
                
                print(f"Generated C header: {header_file}")
                
                # Generate C source
                source_content = generate_c_source(data, instruction_name)
                source_file = source_dir / f"{instruction_name.lower()}.c"
                
                with open(source_file, 'w') as f:
                    f.write(source_content)
                
                print(f"Generated C source: {source_file}")
                
                found = True
                found_files.add(yaml_file)
                break
            
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {yaml_file}: {e}")
            except yaml.YAMLError as e:
                print(f"Failed to parse {yaml_file}: {e}")
            except OSError as e:
                print(f"Failed to write file: {e}")
        
        if not found:
            print(f"Could not find {yaml_file} in any extension")
    
    # Summary
    print("\nOverall...")
    print(f"Found {len(found_files)}/{len(find_these_files)} files")
    if len(find_these_files) - len(found_files) > 0:
        missing = set(find_these_files) - found_files
        print("Missing files:", ", ".join(missing))


if __name__ == "__main__":
    these_files = [
        "add.yaml",
        "sub.yaml",
        "andn.yaml",
        "xor.yaml",
        "and.yaml",
        "lw.yaml",
        "sw.yaml",
    ]
    
    download_and_process_yaml_files(these_files)
