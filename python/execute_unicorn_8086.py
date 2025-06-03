# execute_unicorn_8086.py
"""
Uses the Unicorn emulation framework to load and run a 16-bit x86 binary,
specifically targeting 10biForthOS (forth46bytes.bin).
"""

import os
import toml
from unicorn import *
from unicorn.x86_const import *

# Configuration
DEFAULT_CONFIG_PATH = "config.toml" # Relative to this script's location (python/)
# Fallback binary path if config fails or key is missing
DEFAULT_FORTH_BINARY_PATH = "../forth46bytes.bin"

# Memory setup for 10biForthOS
# According to typical .com file loading and common practice for small OSes.
# The documentation from sr.ht confirms loading at 0x7C00.
CODE_LOAD_ADDRESS = 0x7C00
MEMORY_BASE = 0x00000 # Start mapping from 0 for simplicity to include IVT, BDA
MEMORY_SIZE = 2 * 1024 * 1024  # 2MB, ample space

# Stack: Typically placed below the code or at the top of a segment.
# For 10biForthOS, the initial SP is low, suggesting the stack is in the same segment as code.
# The documentation implies SS will be set to CS by the OS itself (mov ss, cs).
# We will initialize SS = CS and SP = 0xFFFE (top of 64k segment, word aligned)
INITIAL_CS = CODE_LOAD_ADDRESS // 0x10
INITIAL_IP = CODE_LOAD_ADDRESS % 0x10 # Should be 0x0000 for .com files
INITIAL_SS = INITIAL_CS
INITIAL_SP = 0xFFFE

# Buffer for simulated serial input
SERIAL_INPUT_BUFFER = []

def load_app_config(config_path=DEFAULT_CONFIG_PATH):
    """Loads configuration from the TOML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = toml.load(f)
        return config
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_path}' not found. Using defaults.")
    except toml.TomlDecodeError as e:
        print(f"Warning: Could not decode TOML from '{config_path}': {e}")
    return {}

# --- Unicorn Hooks ---
def hook_code(uc, address, size, user_data):
    """
    Hook called for each instruction executed.
    Prints current CS:IP and the instruction's address.
    """
    cs = uc.reg_read(UC_X86_REG_CS)
    ip = uc.reg_read(UC_X86_REG_IP) # This is IP at the *start* of the instruction

    # The 'address' param is the linear address of the current instruction.
    print(f"TRACE: CS:0x{cs:04x} IP:0x{ip:04x} (Linear: 0x{address:05x}) Size: {size}")

def hook_intr(uc, intno, user_data):
    """ Hook for software interrupts (INT instruction). """
    ah = uc.reg_read(UC_X86_REG_AH)

    if intno == 0x14: # Serial I/O
        if ah == 0x02: # Read char from serial port (DX=0 specified by 10biForthOS for COM1)
            dx = uc.reg_read(UC_X86_REG_DX)
            if dx == 0: # Check if it's for COM1 as per 10biForthOS
                if SERIAL_INPUT_BUFFER:
                    char_to_send = SERIAL_INPUT_BUFFER.pop(0)
                    uc.reg_write(UC_X86_REG_AL, char_to_send)
                    uc.reg_write(UC_X86_REG_AH, 0x00) # Success
                    print(f"[INT 0x14:AH=02,DX=0] Sent byte: {char_to_send:#02x} ({chr(char_to_send) if 32 <= char_to_send <= 126 else '.'}) to AL. "
                          f"Input buffer now {len(SERIAL_INPUT_BUFFER)} items.")
                else:
                    uc.reg_write(UC_X86_REG_AH, 0x80) # Timeout/Failure
                    print(f"[INT 0x14:AH=02,DX=0] Input buffer empty. Signaling timeout (AH=0x80).")
            else:
                print(f"[INT 0x14:AH=02] Read from unhandled serial port DX={dx:#04x}.")
                uc.reg_write(UC_X86_REG_AH, 0x80) # Failure
        elif ah == 0x03: # Write char to serial port (DX=0 specified by 10biForthOS for COM1)
            dx = uc.reg_read(UC_X86_REG_DX)
            al = uc.reg_read(UC_X86_REG_AL)
            if dx == 0:
                char_received = chr(al) if 32 <= al <= 126 else '.'
                print(f"[INT 0x14:AH=03,DX=0] Received byte: {al:#02x} ('{char_received}') from AL for serial output.")
                # Here, one might append to a SERIAL_OUTPUT_BUFFER or print to console directly
                # For now, just printing to console.
                sys.stdout.write(chr(al)) # Try to write char directly
                sys.stdout.flush()
                uc.reg_write(UC_X86_REG_AH, 0x00) # Success (assuming char sent)
            else:
                print(f"[INT 0x14:AH=03] Write to unhandled serial port DX={dx:#04x}.")
        else:
            print(f"[INT 0x14:AH={ah:#02x}] Unhandled serial function.")

    elif intno == 0x10: # Video
        if ah == 0x0E: # Teletype output
            al = uc.reg_read(UC_X86_REG_AL)
            char_to_print = chr(al)
            # Print to console, simulating teletype
            # sys.stdout.write(char_to_print)
            # sys.stdout.flush()
            print(f"[INT 0x10:AH=0E] Teletype: '{char_to_print}' (char code: {al:#02x})")
        else:
            print(f"[INT 0x10:AH={ah:#02x}] Video interrupt called. (Not fully emulated)")
    else:
        print(f"[INT {intno:#02x}] Unhandled interrupt at CS:0x{uc.reg_read(UC_X86_REG_CS):04x}:IP:0x{uc.reg_read(UC_X86_REG_IP):04x}. Stopping.")
        uc.emu_stop() # Stop on unhandled interrupts for safety


def emulate_code(code_bytes, binary_file_path):
    """
    Initializes Unicorn, loads code, sets up hooks, and runs emulation.
    """
    mu = None
    try:
        mu = Uc(UC_ARCH_X86, UC_MODE_16)

        # Map memory. Ensure it covers code, stack, and data areas (for compiled code).
        # 0x7C00 (code) up to at least 0x7E000 + space (e.g. 4KB = 0x1000) = ~0x7F000
        # So, mapping MEMORY_BASE to MEMORY_SIZE should be sufficient if MEMORY_BASE is 0.
        mu.mem_map(MEMORY_BASE, MEMORY_SIZE)
        print(f"Mapped {MEMORY_SIZE // (1024*1024)}MB memory from 0x{MEMORY_BASE:08x}")

        mu.mem_write(CODE_LOAD_ADDRESS, code_bytes)
        print(f"Loaded {len(code_bytes)} bytes from '{binary_file_path}' at 0x{CODE_LOAD_ADDRESS:04x}")

        # Initialize Registers
        mu.reg_write(UC_X86_REG_CS, INITIAL_CS)
        mu.reg_write(UC_X86_REG_IP, INITIAL_IP)
        mu.reg_write(UC_X86_REG_SS, INITIAL_SS)
        mu.reg_write(UC_X86_REG_SP, INITIAL_SP)

        # DS will be set by the OS to 0x07E0 for data. Initialize to CS for now.
        mu.reg_write(UC_X86_REG_DS, INITIAL_CS)
        mu.reg_write(UC_X86_REG_ES, 0x0000) # Often 0 or set by program

        for reg in [UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
                    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_BP]:
            mu.reg_write(reg, 0x0000)

        print(f"Initial Registers: CS=0x{mu.reg_read(UC_X86_REG_CS):04x} IP=0x{mu.reg_read(UC_X86_REG_IP):04x} "
              f"SS=0x{mu.reg_read(UC_X86_REG_SS):04x} SP=0x{mu.reg_read(UC_X86_REG_SP):04x} "
              f"DS=0x{mu.reg_read(UC_X86_REG_DS):04x} ES=0x{mu.reg_read(UC_X86_REG_ES):04x}")

        mu.hook_add(UC_HOOK_CODE, hook_code)
        mu.hook_add(UC_HOOK_INTR, hook_intr)

        CODE_START_LINEAR = (INITIAL_CS * 0x10) + INITIAL_IP
        EMULATION_END_ADDRESS = MEMORY_BASE + MEMORY_SIZE
        INSTRUCTION_COUNT_LIMIT = 500 # Increased instruction count

        print(f"\nStarting emulation from CS:IP 0x{INITIAL_CS:04x}:0x{INITIAL_IP:04x} "
              f"(Linear: 0x{CODE_START_LINEAR:05x})")
        print(f"Max instructions: {INSTRUCTION_COUNT_LIMIT if INSTRUCTION_COUNT_LIMIT > 0 else 'unlimited (relies on HLT/error)'}")

        # Pre-fill serial buffer for testing
        # Example: 1 (compile mode), B8 0100 (MOV AX, 0001), F4 (HLT), 0 (execute mode)
        global SERIAL_INPUT_BUFFER
        SERIAL_INPUT_BUFFER = [
            ord('1'), # Compile mode
            0xB8,     # MOV AX, imm16
            0x01,     # Low byte of 0x0001
            0x00,     # High byte of 0x0001
            0xF4,     # HLT
            ord('0')  # Execute mode
        ]
        print(f"Pre-filled SERIAL_INPUT_BUFFER with: {SERIAL_INPUT_BUFFER}")


        mu.emu_start(CODE_START_LINEAR, EMULATION_END_ADDRESS, timeout=0, count=INSTRUCTION_COUNT_LIMIT)

    except UcError as e:
        print(f"Unicorn Error: {e}")
        if mu: # Check if mu exists before trying to read registers
            current_ip = mu.reg_read(UC_X86_REG_IP)
            current_cs = mu.reg_read(UC_X86_REG_CS)
            print(f"Error occurred at CS:0x{current_cs:04x} IP:0x{current_ip:04x}")
    except Exception as e:
        print(f"Unexpected Python Error during emulation setup or run: {e}")
    finally:
        print("\n--- Emulation finished ---")
        if mu:
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
        else:
            print("Emulator was not initialized.")

if __name__ == "__main__":
    config = load_app_config()
    binary_file_config_path = config.get("paths", {}).get("binary_file", DEFAULT_FORTH_BINARY_PATH)

    # Determine script's directory to correctly resolve relative paths
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
    # Path in config.toml is relative to python/ dir. If script is in python/, this works.
    # If script is run from repo root, config path might be "python/config.toml"
    # For binary_file_path, it's specified as "../forth46bytes.bin" in config.toml,
    # meaning it's in the repo root, one level above the python/ directory.
    binary_file_path = os.path.join(script_dir, binary_file_config_path)
    binary_file_path = os.path.abspath(binary_file_path)

    print(f"Attempting to load binary: '{binary_file_path}' (Original config path: '{binary_file_config_path}')")

    try:
        with open(binary_file_path, "rb") as f:
            code_content = f.read()
        if not code_content:
            print(f"Error: File '{binary_file_path}' is empty.")
            exit(1)
        emulate_code(code_content, binary_file_path)
    except FileNotFoundError:
         print(f"Final Error: Binary file not found at '{binary_file_path}'. Please check path.")
    except Exception as e:
        print(f"Error loading or starting emulation: {e}")
