# disassemble_capstone.py
"""
Disassembles a binary file using the Capstone library and outputs to console and a file.
Targeted for 16-bit x86 assembly (8086).
"""

import capstone
import os

# Configuration
BINARY_FILE_PATH = "../forth46bytes.bin"  # Relative to this script in the python/ directory
OUTPUT_ASM_FILE = "forth46bytes_capstone.asm"  # Output in the python/ directory

def disassemble_binary(filepath, output_filepath):
    """
    Disassembles the binary file and writes the output to console and a file.
    """
    print(f"Disassembling '{filepath}' using Capstone (x86 16-bit)...")
    disassembly_lines = []

    try:
        with open(filepath, "rb") as f:
            code = f.read()

        # Initialize Capstone for x86 16-bit mode
        # For 8086, we use CS_MODE_16. CS_ARCH_X86 is for the broader x86 family.
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

        # Capstone can provide instruction details if needed, e.g., md.detail = True
        # For simple disassembly, we iterate through instructions.
        # The base address for disassembly can be set if known, defaults to 0.
        # Here, we assume the code is loaded at address 0x0000 for disassembly purposes.
        base_address = 0x0000

        for insn in md.disasm(code, base_address):
            line = f"0x{insn.address:04x}:\t{insn.mnemonic}\t{insn.op_str}"
            disassembly_lines.append(line)
            print(line)

        # Write to output file
        with open(output_filepath, "w", encoding="utf-8") as out_f:
            out_f.write(f"; Disassembly of {os.path.basename(filepath)} using Capstone (x86 16-bit)\n")
            out_f.write(f"; Base address: 0x{base_address:04x}\n")
            out_f.write(";\n")
            for line in disassembly_lines:
                out_f.write(line + "\n")
        print(f"\nDisassembly also written to '{output_filepath}'")

    except FileNotFoundError:
        print(f"Error: Binary file '{filepath}' not found.")
    except capstone.CsError as e:
        print(f"Error: Capstone disassembly failed: {e}")
    except IOError as e:
        print(f"Error writing output file '{output_filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure paths are relative to the script's location if it's run directly from python/
    # For this script, BINARY_FILE_PATH is already relative to the script's dir.
    # OUTPUT_ASM_FILE will be created in the same directory as the script.
    disassemble_binary(BINARY_FILE_PATH, OUTPUT_ASM_FILE)
