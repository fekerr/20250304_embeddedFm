# execute_unicorn_8086.py
"""
Uses the Unicorn emulation framework to load and run a 16-bit x86 binary,
specifically targeting 10biForthOS (forth46bytes.bin).
"""

import os
import toml
import argparse # Added
import sys # Added
from unicorn import *
from unicorn.x86_const import *

# Configuration
DEFAULT_CONFIG_PATH = "config.toml" # Relative to this script's location (python/)
DEFAULT_FORTH_BINARY_PATH = "../forth46bytes.bin"

# Memory setup
CODE_LOAD_ADDRESS = 0x7C00
MEMORY_BASE = 0x00000
MEMORY_SIZE = 2 * 1024 * 1024
INITIAL_CS = CODE_LOAD_ADDRESS // 0x10
INITIAL_IP = CODE_LOAD_ADDRESS % 0x10
INITIAL_SS = INITIAL_CS
INITIAL_SP = 0xFFFE

# Buffer for simulated serial input - global, populated in main
SERIAL_INPUT_BUFFER = []

def load_app_config(config_path=DEFAULT_CONFIG_PATH):
    """Loads configuration from the TOML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = toml.load(f) # 'config' here is local to the function
        return config
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_path}' not found. Using defaults.")
    except toml.TomlDecodeError as e:
        print(f"Warning: Could not decode TOML from '{config_path}': {e}")
    return {}

# --- Unicorn Hooks ---
def hook_code(uc, address, size, user_data):
    cs = uc.reg_read(UC_X86_REG_CS)
    ip = uc.reg_read(UC_X86_REG_IP)
    print(f"TRACE: CS:0x{cs:04x} IP:0x{ip:04x} (Linear: 0x{address:05x}) Size: {size}")

def hook_intr(uc, intno, user_data):
    ah = uc.reg_read(UC_X86_REG_AH)
    global SERIAL_INPUT_BUFFER # Declare intent to modify global

    if intno == 0x14:
        if ah == 0x02:
            dx = uc.reg_read(UC_X86_REG_DX)
            if dx == 0:
                if SERIAL_INPUT_BUFFER:
                    char_to_send = SERIAL_INPUT_BUFFER.pop(0)
                    uc.reg_write(UC_X86_REG_AL, char_to_send)
                    uc.reg_write(UC_X86_REG_AH, 0x00)
                    print(f"[INT 0x14:AH=02,DX=0] Sent byte: {char_to_send:#02x} ({chr(char_to_send) if 32 <= char_to_send <= 126 else '.'}) to AL. "
                          f"Input buffer now {len(SERIAL_INPUT_BUFFER)} items.")
                else:
                    uc.reg_write(UC_X86_REG_AH, 0x80)
                    print(f"[INT 0x14:AH=02,DX=0] Input buffer empty. Signaling timeout (AH=0x80).")
            else:
                print(f"[INT 0x14:AH=02] Read from unhandled serial port DX={dx:#04x}.")
                uc.reg_write(UC_X86_REG_AH, 0x80)
        elif ah == 0x03:
            dx = uc.reg_read(UC_X86_REG_DX)
            al = uc.reg_read(UC_X86_REG_AL)
            if dx == 0:
                char_received = chr(al) if 32 <= al <= 126 else '.'
                print(f"[INT 0x14:AH=03,DX=0] Received byte: {al:#02x} ('{char_received}') from AL for serial output.")
                sys.stdout.write(chr(al))
                sys.stdout.flush()
                uc.reg_write(UC_X86_REG_AH, 0x00)
            else:
                print(f"[INT 0x14:AH=03] Write to unhandled serial port DX={dx:#04x}.")
        else:
            print(f"[INT 0x14:AH={ah:#02x}] Unhandled serial function.")
    elif intno == 0x10:
        if ah == 0x0E:
            al = uc.reg_read(UC_X86_REG_AL)
            char_to_print = chr(al)
            print(f"[INT 0x10:AH=0E] Teletype: '{char_to_print}' (char code: {al:#02x})")
        else:
            print(f"[INT 0x10:AH={ah:#02x}] Video interrupt called. (Not fully emulated)")
    else:
        print(f"[INT {intno:#02x}] Unhandled interrupt at CS:0x{uc.reg_read(UC_X86_REG_CS):04x}:IP:0x{uc.reg_read(UC_X86_REG_IP):04x}. Stopping.")
        uc.emu_stop()

def emulate_code(code_bytes, binary_file_path):
    mu = None
    try:
        mu = Uc(UC_ARCH_X86, UC_MODE_16)
        mu.mem_map(MEMORY_BASE, MEMORY_SIZE)
        print(f"Mapped {MEMORY_SIZE // (1024*1024)}MB memory from 0x{MEMORY_BASE:08x}")
        mu.mem_write(CODE_LOAD_ADDRESS, code_bytes)
        print(f"Loaded {len(code_bytes)} bytes from '{binary_file_path}' at 0x{CODE_LOAD_ADDRESS:04x}")

        mu.reg_write(UC_X86_REG_CS, INITIAL_CS)
        mu.reg_write(UC_X86_REG_IP, INITIAL_IP)
        mu.reg_write(UC_X86_REG_SS, INITIAL_SS)
        mu.reg_write(UC_X86_REG_SP, INITIAL_SP)
        mu.reg_write(UC_X86_REG_DS, INITIAL_CS)
        mu.reg_write(UC_X86_REG_ES, 0x0000)
        for reg_const in [UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
                           UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_BP]:
            mu.reg_write(reg_const, 0x0000)

        print(f"Initial Registers: CS=0x{mu.reg_read(UC_X86_REG_CS):04x} IP=0x{mu.reg_read(UC_X86_REG_IP):04x} "
              f"SS=0x{mu.reg_read(UC_X86_REG_SS):04x} SP=0x{mu.reg_read(UC_X86_REG_SP):04x} "
              f"DS=0x{mu.reg_read(UC_X86_REG_DS):04x} ES=0x{mu.reg_read(UC_X86_REG_ES):04x}")

        mu.hook_add(UC_HOOK_CODE, hook_code)
        mu.hook_add(UC_HOOK_INTR, hook_intr)

        CODE_START_LINEAR = (INITIAL_CS * 0x10) + INITIAL_IP
        EMULATION_END_ADDRESS = MEMORY_BASE + MEMORY_SIZE
        INSTRUCTION_COUNT_LIMIT = 500

        print(f"\nStarting emulation from CS:IP 0x{INITIAL_CS:04x}:0x{INITIAL_IP:04x} "
              f"(Linear: 0x{CODE_START_LINEAR:05x})")
        print(f"Max instructions: {INSTRUCTION_COUNT_LIMIT if INSTRUCTION_COUNT_LIMIT > 0 else 'unlimited (relies on HLT/error)'}")

        if SERIAL_INPUT_BUFFER:
            print(f"Using SERIAL_INPUT_BUFFER loaded from file: {SERIAL_INPUT_BUFFER[:20]}{'...' if len(SERIAL_INPUT_BUFFER) > 20 else ''}")
        else:
            print("Warning: SERIAL_INPUT_BUFFER is empty. Emulation might stall on input.")

        mu.emu_start(CODE_START_LINEAR, EMULATION_END_ADDRESS, timeout=0, count=INSTRUCTION_COUNT_LIMIT)

    except UcError as e:
        print(f"Unicorn Error: {e}")
        if mu:
            current_ip_err = mu.reg_read(UC_X86_REG_IP)
            current_cs_err = mu.reg_read(UC_X86_REG_CS)
            print(f"Error occurred at CS:0x{current_cs_err:04x} IP:0x{current_ip_err:04x}")
    except Exception as e:
        print(f"Unexpected Python Error during emulation setup or run: {e}")
    finally:
        print("\n--- Emulation finished ---")
        if mu:
            print("Final Register States:")
            regs_to_print = {
                "CS": UC_X86_REG_CS, "IP": UC_X86_REG_IP, "SS": UC_X86_REG_SS, "SP": UC_X86_REG_SP,
                "AX": UC_X86_REG_AX, "BX": UC_X86_REG_BX, "CX": UC_X86_REG_CX, "DX": UC_X86_REG_DX,
                "SI": UC_X86_REG_SI, "DI": UC_X86_REG_DI, "BP": UC_X86_REG_BP,
                "DS": UC_X86_REG_DS, "ES": UC_X86_REG_ES, "FLAGS": UC_X86_REG_EFLAGS
            }
            for name, const in regs_to_print.items():
                try:
                    print(f"  {name}: 0x{mu.reg_read(const):04x}")
                except UcError:
                     print(f"  {name}: <Error reading register>")
        else:
            print("Emulator was not initialized.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emulate 10biForthOS with serial input from a file.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the file containing serial input bytes (space or newline separated numbers)."
    )
    cli_args = parser.parse_args()
    input_filepath = cli_args.input

    # Populate global SERIAL_INPUT_BUFFER from the specified file
    try:
        with open(input_filepath, "r", encoding="utf-8") as f:
            for line_content in f:
                tokens = line_content.strip().split()
                for token in tokens:
                    if token:
                        SERIAL_INPUT_BUFFER.append(int(token))
        print(f"Loaded {len(SERIAL_INPUT_BUFFER)} bytes from '{input_filepath}' for serial input.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
        sys.exit(1)
    except ValueError:
        print(f"Error: Invalid content in input file '{input_filepath}'. All tokens must be integers.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file '{input_filepath}': {e}")
        sys.exit(1)

    if not SERIAL_INPUT_BUFFER and not os.path.exists(input_filepath): # Only warn if file existed but was empty
        pass # Allow empty buffer if file was empty, script will warn in emulate_code
    elif not SERIAL_INPUT_BUFFER:
         print(f"Warning: Input file '{input_filepath}' was empty or contained no valid numbers. Serial input buffer is empty.")


    app_config_main = load_app_config()
    binary_file_config_path = app_config_main.get("paths", {}).get("binary_file", DEFAULT_FORTH_BINARY_PATH)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
    binary_file_path = os.path.abspath(os.path.join(script_dir, binary_file_config_path))

    print(f"Attempting to load binary: '{binary_file_path}' (Original config path from TOML: '{binary_file_config_path}')")

    try:
        with open(binary_file_path, "rb") as f:
            code_content = f.read()
        if not code_content:
            print(f"Error: File '{binary_file_path}' is empty.")
            sys.exit(1)
        emulate_code(code_content, binary_file_path)
    except FileNotFoundError:
         print(f"Final Error: Binary file not found at '{binary_file_path}'. Please check config.toml path and CWD.")
         sys.exit(1)
    except Exception as e:
        print(f"Error loading or starting emulation: {e}")
        sys.exit(1)
