# execute_unicorn_8086.py
"""
Uses the Unicorn emulation framework to load and run forth46bytes.bin for x86 16-bit.
"""

import os
import toml
from unicorn import *
from unicorn.x86_const import *

# Configuration
CONFIG_PATH = "config.toml"
DEFAULT_BINARY_FILE_PATH = "../forth46bytes.bin" # Fallback if config fails

# Memory setup
MEMORY_ADDRESS = 0x0000  # Often BIOS loads bootloaders at 0x7c00, but 0x0000 is simpler for direct code execution
MEMORY_SIZE = 2 * 1024 * 1024  # 2MB
# Stack grows downwards. For simplicity, place it high in mapped memory.
# Ensure stack segment (SS) and code segment (CS) are set appropriately.
# If CS=0, then SS can also be 0 for a flat-like model within the mapped 2MB.
STACK_ADDRESS = MEMORY_ADDRESS + MEMORY_SIZE
INITIAL_SP = 0xFFFE # Word-aligned, near the top of the segment

def load_app_config():
    """Loads configuration from the TOML file."""
    try:
        # Assuming config.toml is in the same directory as this script (python/)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file '{CONFIG_PATH}' not found. Using defaults.")
    except toml.TomlDecodeError:
        print(f"Warning: Could not decode TOML from '{CONFIG_PATH}'. Using defaults.")
    return {}

# --- Unicorn Hooks ---
def hook_code(uc, address, size, user_data):
    """
    Hook called for each instruction executed.
    Prints current CS:IP, instruction bytes (optional), and registers (optional).
    """
    cs = uc.reg_read(UC_X86_REG_CS)
    ip = uc.reg_read(UC_X86_REG_IP) # IP will be the address of the *next* instruction after current one

    print(f"TRACE: CS:0x{cs:04x} IP:0x{address:04x} (Instruction at 0x{address:04x})")

    # Optional: Print instruction bytes
    # try:
    #     instruction_bytes = uc.mem_read(address, size)
    #     print(f"       Bytes: {' '.join(f'{b:02x}' for b in instruction_bytes)}")
    # except UcError:
    #     print("       Bytes: <error reading memory>")

    # Optional: Print all general purpose registers (can be very verbose)
    # regs = {
    #     "AX": uc.reg_read(UC_X86_REG_AX), "BX": uc.reg_read(UC_X86_REG_BX),
    #     "CX": uc.reg_read(UC_X86_REG_CX), "DX": uc.reg_read(UC_X86_REG_DX),
    #     "SI": uc.reg_read(UC_X86_REG_SI), "DI": uc.reg_read(UC_X86_REG_DI),
    #     "BP": uc.reg_read(UC_X86_REG_BP), "SP": uc.reg_read(UC_X86_REG_SP),
    #     "SS": uc.reg_read(UC_X86_REG_SS), "ES": uc.reg_read(UC_X86_REG_ES),
    #     "DS": uc.reg_read(UC_X86_REG_DS), "FLAGS": uc.reg_read(UC_X86_REG_EFLAGS) # EFLAGS for x86
    # }
    # reg_str = ", ".join([f"{name}:0x{val:04x}" for name, val in regs.items()])
    # print(f"       Regs: {reg_str}")


def hook_io_in(uc, port, size, user_data):
    """ Hook for IN instruction. """
    # For now, just acknowledge and return a dummy value (e.g., 0xFF for 1 byte)
    # This needs to be more sophisticated for real interaction.
    val = 0xFF
    if size == 2:
        val = 0xFFFF
    elif size == 4: # Should not happen in 16-bit mode often
        val = 0xFFFFFFFF
    print(f"IO IN: Port 0x{port:04x}, Size {size}, Read: 0x{val:x}")
    return val

def hook_io_out(uc, port, size, value, user_data):
    """ Hook for OUT instruction. """
    print(f"IO OUT: Port 0x{port:04x}, Size {size}, Value 0x{value:04x}")
    # Example: If it's COM1 (0x3F8), print char if printable
    if port == 0x3F8 and size == 1:
        if 32 <= value <= 126:
            print(f"       COM1 Output: '{chr(value)}'")


def emulate_code(code_bytes):
    """
    Initializes Unicorn, loads code, sets up hooks, and runs emulation.
    """
    try:
        # Initialize emulator for x86 16-bit mode
        mu = Uc(UC_ARCH_X86, UC_MODE_16)

        # Map memory
        mu.mem_map(MEMORY_ADDRESS, MEMORY_SIZE)
        print(f"Mapped {MEMORY_SIZE // (1024*1024)}MB memory from 0x{MEMORY_ADDRESS:08x}")

        # Write code to memory
        mu.mem_write(MEMORY_ADDRESS, code_bytes)
        print(f"Loaded {len(code_bytes)} bytes of code at 0x{MEMORY_ADDRESS:04x}")

        # Initialize registers
        # For 16-bit mode, CS and IP determine the starting address.
        # If code is loaded at MEMORY_ADDRESS = 0x0000, and CS is 0, then IP is 0.
        # If code is loaded at 0x7c00 (like a bootloader), CS might be 0, IP=0x7c00,
        # or CS could be 0x07C0 and IP = 0x0000.
        # For simplicity with MEMORY_ADDRESS = 0, we use CS=0, IP=0.
        mu.reg_write(UC_X86_REG_CS, 0x0000)
        mu.reg_write(UC_X86_REG_IP, MEMORY_ADDRESS)

        # Setup stack segment (SS) and stack pointer (SP)
        # Assuming SS also points to the start of our flat memory model for now
        mu.reg_write(UC_X86_REG_SS, 0x0000)
        mu.reg_write(UC_X86_REG_SP, INITIAL_SP)

        # Initialize other general purpose registers to 0
        mu.reg_write(UC_X86_REG_AX, 0x0000)
        mu.reg_write(UC_X86_REG_BX, 0x0000)
        mu.reg_write(UC_X86_REG_CX, 0x0000)
        mu.reg_write(UC_X86_REG_DX, 0x0000)
        mu.reg_write(UC_X86_REG_SI, 0x0000)
        mu.reg_write(UC_X86_REG_DI, 0x0000)
        mu.reg_write(UC_X86_REG_BP, 0x0000)
        mu.reg_write(UC_X86_REG_ES, 0x0000) # Extra segment
        mu.reg_write(UC_X86_REG_DS, 0x0000) # Data segment

        print(f"Initial Registers: CS=0x{mu.reg_read(UC_X86_REG_CS):04x} IP=0x{mu.reg_read(UC_X86_REG_IP):04x} SS=0x{mu.reg_read(UC_X86_REG_SS):04x} SP=0x{mu.reg_read(UC_X86_REG_SP):04x}")

        # Add hooks
        mu.hook_add(UC_HOOK_CODE, hook_code)
        # Hooking specific IN/OUT instructions is more complex.
        # UC_HOOK_INSN can be used with a check for instruction ID.
        # For simplicity, let's use the generic I/O hooks if available for the API version.
        # uc.hook_add(UC_HOOK_IN, hook_io_in) # For specific IN port access
        # uc.hook_add(UC_HOOK_OUT, hook_io_out) # For specific OUT port access
        # Simpler I/O hooks for any IN/OUT instruction:
        mu.hook_add(UC_HOOK_INSN, hook_io_in, None, 1, 0, UC_X86_INS_IN)
        mu.hook_add(UC_HOOK_INSN, hook_io_out, None, 1, 0, UC_X86_INS_OUT)


        # Start emulation
        code_start = MEMORY_ADDRESS
        # code_end = MEMORY_ADDRESS + len(code_bytes) # Emulate only the loaded code
        # Emulate for a fixed number of instructions or until HLT
        emulation_instruction_count = 100
        print(f"\nStarting emulation from 0x{code_start:04x} for {emulation_instruction_count} instructions or until end/HLT...")

        mu.emu_start(code_start, -1, timeout=0, count=emulation_instruction_count)

    except UcError as e:
        print(f"Unicorn Error: {e}")
    except Exception as e:
        print(f"Unexpected Error during emulation setup or run: {e}")
    finally:
        print("\n--- Emulation finished ---")
        if 'mu' in locals():
            print("Final Register States:")
            regs_to_print = {
                "CS": UC_X86_REG_CS, "IP": UC_X86_REG_IP,
                "SS": UC_X86_REG_SS, "SP": UC_X86_REG_SP,
                "AX": UC_X86_REG_AX, "BX": UC_X86_REG_BX,
                "CX": UC_X86_REG_CX, "DX": UC_X86_REG_DX,
                "SI": UC_X86_REG_SI, "DI": UC_X86_REG_DI,
                "BP": UC_X86_REG_BP,
                "DS": UC_X86_REG_DS, "ES": UC_X86_REG_ES,
                "FLAGS": UC_X86_REG_EFLAGS
            }
            for name, const in regs_to_print.items():
                try:
                    print(f"  {name}: 0x{mu.reg_read(const):04x}")
                except UcError:
                     print(f"  {name}: <Error reading register>")


if __name__ == "__main__":
    app_config = load_app_config()
    binary_file_rel_path = app_config.get("paths", {}).get("binary_file", DEFAULT_BINARY_FILE_PATH)

    # The binary_file_rel_path from config.toml is like "../forth46bytes.bin"
    # This script (execute_unicorn_8086.py) is in python/
    # So, the path is already correct relative to the script's execution directory if run from python/
    # If make.py runs this, it ensures CWD is python/
    binary_file_abs_path = os.path.abspath(binary_file_rel_path) # Not strictly needed if CWD is python/

    print(f"Attempting to load binary from: {binary_file_rel_path} (resolved to {binary_file_abs_path})")

    if not os.path.exists(binary_file_rel_path):
        # Fallback if the relative path from script location is wrong, try from repo root perspective
        # This happens if binary_file is "forth46bytes.bin" and script is in "python/"
        alt_path = os.path.join("..", binary_file_rel_path) # This logic might be redundant now
        if os.path.exists(alt_path):
            binary_file_rel_path = alt_path
        else:
             print(f"Error: Binary file not found at '{binary_file_rel_path}' or '{alt_path}'")
             exit(1)

    try:
        with open(binary_file_rel_path, "rb") as f:
            code = f.read()
        emulate_code(code)
    except FileNotFoundError:
         print(f"Final Error: Binary file not found at '{binary_file_rel_path}'. Please check config.toml path.")
    except Exception as e:
        print(f"Error loading or starting emulation: {e}")
