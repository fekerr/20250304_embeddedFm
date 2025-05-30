# dumpit.py
"""
Performs a hexadecimal dump of a binary file.
Reads configuration from config.toml.
"""

import toml

DEFAULT_CONFIG_PATH = "config.toml"


def load_config(config_path=DEFAULT_CONFIG_PATH):
    """Loads configuration from the TOML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = toml.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        return None
    except toml.TomlDecodeError:
        print(f"Error: Could not decode TOML from '{config_path}'.")
        return None


def hexdump(filepath, bytes_per_line=16):
    """
    Prints a hex dump of the given file.

    Args:
        filepath (str): Path to the binary file.
        bytes_per_line (int): Number of bytes to display per line.
    """
    try:
        with open(filepath, "rb") as f:
            offset = 0
            while True:
                chunk = f.read(bytes_per_line)
                if not chunk:
                    break

                # Offset
                print(f"{offset:08x}  ", end="")

                # Hex bytes
                hex_bytes = " ".join(f"{b:02x}" for b in chunk)
                print(f"{hex_bytes:<{bytes_per_line * 3}}", end="")

                # ASCII representation
                ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
                print(f"|{ascii_repr}|")

                offset += len(chunk)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except IOError as e: # More specific exception for file operations
        print(f"An I/O error occurred: {e}")
    except Exception as e: # Fallback for truly unexpected errors
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main_config = load_config() # Renamed to avoid W0621 in this scope

    if main_config:
        binary_file_path = main_config.get("paths", {}).get("binary_file")
        # # Adjust path to be relative to repository root if dumpit.py is in python/
        # if binary_file_path and not binary_file_path.startswith("/"):
        #     binary_file_path = f"../{binary_file_path}" # Assuming config.toml path is relative to repo root

        # Renamed to avoid W0621 with hexdump's parameter
        dump_bytes_per_line = main_config.get("dump_settings", {}).get(
            "bytes_per_line", 16
        )

        if binary_file_path:
            print(
                f"Dumping '{binary_file_path}' with {dump_bytes_per_line} bytes per line:"
            )
            hexdump(binary_file_path, dump_bytes_per_line)
        else:
            print("Error: 'paths.binary_file' not specified in config.toml")

    else:
        print("Could not proceed without configuration.")
