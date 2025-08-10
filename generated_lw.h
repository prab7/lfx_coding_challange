#ifndef GENERATED_LW_H
#define GENERATED_LW_H

// C header for : generated_lw

#include <stdint.h>

/* Structure for generated_lw instruction data */
typedef struct {
    const char* _schema;
    const char* kind;
    const char* name;
    const char* long_name;
    const char* description;
    const char* definedby;
    const char* assembly;
    const char* encoding_data;
    const char* access_data;
    const char* operation__;
    const char* sail__;
} generated_lw_t;

/* Data for generated_lw instruction */
static const generated_lw_t generated_lw_data = {
    ._schema = "inst_schema.json#",
    .kind = "instruction",
    .name = "lw",
    .long_name = "Load word",
    .description = "Load 32 bits of data into register `xd` from an\naddress formed by adding `xs1` to a signed offset.\nSign extend the result.\n",
    .definedby = "I",
    .assembly = "xd, imm(xs1)",
    .encoding_data = "{match: '-----------------010-----0000011', variables: [{location: 31-20, name: imm}, {location: 19-15, name: xs1}, {location: 11-7, name: xd}]}",
    .access_data = "{s: always, u: always, vs: always, vu: always}",
    .operation__ = "XReg virtual_address = X[xs1] + $signed(imm);\nX[xd] = $signed(read_memory<32>(virtual_address, $encoding));\n",
    .sail__ = "{\n  let offset : xlenbits = sign_extend(imm);\n  /* Get the address, X(xs1) + offset.\n     Some extensions perform additional checks on address validity. */\n  match ext_data_get_addr(xs1, offset, Read(Data), width) {\n    Ext_DataAddr_Error(e)  => { ext_handle_data_check_error(e); RETIRE_FAIL },\n    Ext_DataAddr_OK(vaddr) =>\n      if   check_misaligned(vaddr, width)\n      then { handle_mem_exception(vaddr, E_Load_Addr_Align()); RETIRE_FAIL }\n      else match translateAddr(vaddr, Read(Data)) {\n        TR_Failure(e, _) => { handle_mem_exception(vaddr, e); RETIRE_FAIL },\n        TR_Address(paddr, _) =>\n          match (width) {\n            BYTE =>\n              process_load(xd, vaddr, mem_read(Read(Data), paddr, 1, aq, rl, false), is_unsigned),\n            HALF =>\n              process_load(xd, vaddr, mem_read(Read(Data), paddr, 2, aq, rl, false), is_unsigned),\n            WORD =>\n              process_load(xd, vaddr, mem_read(Read(Data), paddr, 4, aq, rl, false), is_unsigned),\n            DOUBLE if sizeof(xlen) \n",
};

/* Getter functions for generated_lw */
static inline const generated_lw_t* get_generated_lw_data(void) {
    return &generated_lw_data;
}

/* Function to recreate YAML (implement in .c file) */
const char* generated_lw_to_yaml(void);

#endif /* GENERATED_LW_H */
