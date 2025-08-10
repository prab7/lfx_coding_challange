// C source for generated_lw

#include <stdio.h>
#include <string.h>
#include "generated_lw.h"

static void format_multiline_string(char* buffer, size_t buffer_size, size_t* offset, 
                                   const char* key, const char* value) {
    *offset += snprintf(buffer + *offset, buffer_size - *offset, "%s: |\n", key);
    
    // Split the string by newlines and indent each line
    char temp[1024];
    strncpy(temp, value, sizeof(temp) - 1);
    temp[sizeof(temp) - 1] = '\0';
    
    char* line = strtok(temp, "\n");
    while (line != NULL && *offset < buffer_size - 1) {
        *offset += snprintf(buffer + *offset, buffer_size - *offset, "  %s\n", line);
        line = strtok(NULL, "\n");
    }
}

const char* generated_lw_to_yaml(void) {
    static char yaml_buffer[4096];
    const generated_lw_t* data = get_generated_lw_data();
    
    size_t offset = 0;
    yaml_buffer[0] = '\0';
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "$schema: %s\n", data->_schema);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "kind: %s\n", data->kind);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "name: %s\n", data->name);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "long_name: %s\n", data->long_name);
    format_multiline_string(yaml_buffer, sizeof(yaml_buffer), &offset, "description", data->description);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "definedBy: %s\n", data->definedby);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "assembly: %s\n", data->assembly);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "encoding: %s\n", data->encoding_data);
    offset += snprintf(yaml_buffer + offset, sizeof(yaml_buffer) - offset, "access: %s\n", data->access_data);
    format_multiline_string(yaml_buffer, sizeof(yaml_buffer), &offset, "operation()", data->operation__);
    format_multiline_string(yaml_buffer, sizeof(yaml_buffer), &offset, "sail()", data->sail__);

    
    return yaml_buffer;
}

int main(void) {
    printf("%s", generated_lw_to_yaml());
    return 0;
}
