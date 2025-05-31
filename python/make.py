# make.py
"""
A simple build/task automation script.
Reads tasks from make.yaml and configuration from config.toml.
"""

import argparse
import subprocess
import sys
import toml
import yaml

DEFAULT_CONFIG_PATH = "config.toml"
DEFAULT_MAKE_YAML_PATH = "make.yaml"


# --- Configuration Loading ---
def load_toml_config(config_path=DEFAULT_CONFIG_PATH):
    """Loads general configuration from the TOML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Error: Main configuration file '{config_path}' not found.")
    except toml.TomlDecodeError:
        print(f"Error: Could not decode TOML from '{config_path}'.")
    return None


def load_make_yaml(make_yaml_path=DEFAULT_MAKE_YAML_PATH):
    """Loads task definitions from the YAML file."""
    try:
        with open(make_yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Make definition file '{make_yaml_path}' not found.")
    except yaml.YAMLError as e:
        print(f"Error: Could not parse YAML from '{make_yaml_path}': {e}")
    return None


# --- Task Execution ---
def execute_shell_command(command, task_name):
    """Executes a shell command."""
    print(f"[{task_name}] Running shell command: {command}")
    try:
        process = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(process.stderr.strip(), file=sys.stderr)
        print(f"[{task_name}] Shell command completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command for task '{task_name}': {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout.strip(), file=sys.stderr)
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
        return False
    except (FileNotFoundError, PermissionError) as e: # More specific OS errors
        print(
            f"An OS error occurred for '{task_name}': {e}",
            file=sys.stderr,
        )
        return False
    except Exception as e:  # General fallback for other unexpected errors
        print(
            f"An unexpected error occurred running command for '{task_name}': {e}",
            file=sys.stderr,
        )
        return False


def execute_script_call(
    script_name, script_args, task_name, main_config
):  # Renamed 'args' to 'script_args'
    """
    Executes a Python script.
    For now, this is simplified: it assumes dumpit.py and its specific config needs.
    A more generic approach would use importlib or manage arguments better.
    """
    # script_args currently unused, placeholder for future script argument passing
    # main_config currently unused, placeholder for future script needs if scripts need main config access
    print(f"[{task_name}] Calling script: {script_name}")
    try:
        # This is a direct call, assuming the script is in the same directory
        # and handles its own config loading if necessary.
        # For future: Pass script_args and main_config to the script if a convention is established.
        process = subprocess.run(
            [sys.executable, script_name],  # Use sys.executable for portability
            check=True,
            text=True,
            capture_output=True,
        )
        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(process.stderr.strip(), file=sys.stderr)
        print(f"[{task_name}] Script '{script_name}' completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(
            f"Error executing script '{script_name}' for task '{task_name}': {e}",
            file=sys.stderr,
        )
        if e.stdout:
            print(e.stdout.strip(), file=sys.stderr)
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            f"Error: Script '{script_name}' not found for task '{task_name}'.",
            file=sys.stderr,
        )
        return False
    except Exception as e:  # General fallback for other unexpected errors
        print(
            f"An unexpected error occurred running script '{script_name}' for '{task_name}': {e}",
            file=sys.stderr,
        )
        return False


def run_task(task_name, make_config, main_config, executed_tasks=None):
    """Runs a specific task and its dependencies."""
    if executed_tasks is None:
        executed_tasks = set()

    if task_name in executed_tasks:
        print(f"Skipping already executed task: {task_name}")
        return True

    task = make_config.get("tasks", {}).get(task_name)
    if not task:
        print(
            f"Error: Task '{task_name}' not defined in '{DEFAULT_MAKE_YAML_PATH}'.",
            file=sys.stderr,
        )
        return False

    print(f"Starting task: {task_name} - {task.get('description', '')}")

    # Execute dependencies first
    for dep_name in task.get("dependencies", []):
        if (
            dep_name not in executed_tasks
        ):  # Check to avoid re-running dependencies if shared
            if not run_task(dep_name, make_config, main_config, executed_tasks):
                print(
                    f"Dependency task '{dep_name}' for '{task_name}' failed. Aborting.",
                    file=sys.stderr,
                )
                return False

    # Execute actions for the current task
    for action in task.get("actions", []):
        action_type = action.get("type")
        success = False
        if action_type == "shell_command":
            success = execute_shell_command(action.get("command"), task_name)
        elif action_type == "script_call":
            success = execute_script_call(
                action.get("script"),
                action.get("args"),  # These are args from make.yaml for the script
                task_name,
                main_config,
            )
        else:
            print(
                f"Error: Unknown action type '{action_type}' in task '{task_name}'.",
                file=sys.stderr,
            )
            return False  # Unknown action type

        if not success:
            print(
                f"Action type '{action_type}' for task '{task_name}' failed. Aborting.",
                file=sys.stderr,
            )
            return False  # Action failed

    executed_tasks.add(task_name)
    print(f"Finished task: {task_name}")
    return True


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python-based build/task runner.")
    parser.add_argument(
        "task",
        nargs="?",
        help="The task to run (as defined in make.yaml). Runs default if not specified.",
    )
    parser.add_argument(
        "--list-tasks", action="store_true", help="List all available tasks."
    )

    args = parser.parse_args()

    main_app_config = load_toml_config()
    make_definitions = load_make_yaml()

    if not make_definitions:
        print("Could not load make definitions. Exiting.")
        sys.exit(1)

    # settings = make_definitions.get("settings", {}) # For future use, e.g. default_task

    if args.list_tasks:
        print("Available tasks:")
        tasks_data = make_definitions.get("tasks", {})
        if not tasks_data:
            print("  No tasks defined.")
        else:
            for name, details in tasks_data.items():
                print(f"  - {name}: {details.get('description', 'No description')}")
        sys.exit(0)

    task_to_run = args.task
    TASK_TO_RUN = args.task  # Renamed to uppercase
    if not TASK_TO_RUN:
        # DEFAULT_TASK_NAME = settings.get("default_task") # Future: get from make.yaml settings
        DEFAULT_TASK_NAME = "dump_binary"  # Hardcoded for now, renamed
        if not DEFAULT_TASK_NAME:
            print(
                "No task specified and no default task defined. Use --list-tasks to see options."
            )
            sys.exit(1)
        print(f"No task specified, running default task: '{DEFAULT_TASK_NAME}'")
        TASK_TO_RUN = DEFAULT_TASK_NAME

    if not run_task(TASK_TO_RUN, make_definitions, main_app_config):
        print(
            f"Task '{TASK_TO_RUN}' or one of its dependencies failed.", file=sys.stderr
        )
        sys.exit(1)
    else:
        print(f"Task '{TASK_TO_RUN}' and its dependencies completed successfully.")
        sys.exit(0)
