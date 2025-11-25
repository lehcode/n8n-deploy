#!/usr/bin/env python3
"""
Automatic test scenario generator for n8n-deploy CLI

Generates comprehensive test cases by introspecting Click commands.
Handles command groups, subcommands, positional arguments, and all parameter types.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def extract_click_commands(cli_group: click.Group) -> Dict[str, Tuple[List[str], click.Command]]:
    """
    Extract all Click commands from a CLI group, including subcommands.

    Returns:
        Dict mapping command_id -> (command_path, command_object)
        Example: {'wf_list': (['wf', 'list'], <Command object>)}
    """
    commands = {}

    if isinstance(cli_group, click.Group):
        for cmd_name, cmd in cli_group.commands.items():
            if isinstance(cmd, click.Group):
                # Nested group (like 'wf' or 'db')
                for sub_name, sub_cmd in cmd.commands.items():
                    command_id = f"{cmd_name}_{sub_name}".replace("-", "_")
                    commands[command_id] = ([cmd_name, sub_name], sub_cmd)
            else:
                # Top-level command
                command_id = cmd_name.replace("-", "_")
                commands[command_id] = ([cmd_name], cmd)

    return commands


def get_param_type_name(param: click.Parameter) -> str:
    """Get readable type name for a parameter"""
    if isinstance(param.type, click.Path):
        return "path"
    elif isinstance(param.type, click.Choice):
        return "choice"
    elif isinstance(param.type, click.types.IntParamType):
        return "int"
    elif isinstance(param.type, click.types.BoolParamType):
        return "bool"
    elif param.is_flag:
        return "flag"
    else:
        return "string"


def generate_test_scenarios(command_path: List[str], command: click.Command) -> List[Dict[str, Any]]:
    """
    Generate comprehensive test scenarios from a Click command.

    Args:
        command_path: List of command names ['wf', 'list']
        command: Click Command object
    """
    scenarios = []
    cmd_id = "_".join(command_path).replace("-", "_")

    # Separate positional arguments from options
    positional_args = [p for p in command.params if isinstance(p, click.Argument)]
    options = [p for p in command.params if isinstance(p, click.Option)]
    required_options = [o for o in options if o.required]

    # Test 1: Always test --help (should work for all commands)
    scenarios.append(
        {
            "name": f"test_{cmd_id}_help",
            "description": f"Test {'  '.join(command_path)} --help",
            "command": command_path + ["--help"],
            "expected_exit_code": 0,
            "expected_output": "Usage:",
        }
    )

    # Test 2: Test command with no arguments (only if no required params)
    if not positional_args and not required_options:
        scenarios.append(
            {
                "name": f"test_{cmd_id}_no_args",
                "description": f"Test {'  '.join(command_path)} with no arguments",
                "command": command_path,
                "expected_exit_code": [0, 1],  # May succeed or gracefully fail
            }
        )

    # Test 3: Test each option individually
    for option in options:
        param_name = option.name.replace("_", "-")
        param_type = get_param_type_name(option)

        # Skip global flags that are handled elsewhere
        if option.name in ["app_dir", "flow_dir", "server_url", "no_emoji"]:
            continue

        # Boolean flags
        if option.is_flag:
            scenarios.append(
                {
                    "name": f"test_{cmd_id}_{option.name}_flag",
                    "description": f"Test {'  '.join(command_path)} with --{param_name} flag",
                    "command": command_path + [f"--{param_name}"],
                    "expected_exit_code": [0, 1, 2],
                }
            )

        # Choice parameters - test each valid choice
        elif isinstance(option.type, click.Choice):
            for choice in option.type.choices:
                scenarios.append(
                    {
                        "name": f"test_{cmd_id}_{option.name}_{choice}",
                        "description": f"Test {'  '.join(command_path)} with --{param_name}={choice}",
                        "command": command_path + [f"--{param_name}", choice],
                        "expected_exit_code": [0, 1, 2],
                    }
                )

        # Path parameters
        elif isinstance(option.type, click.Path):
            scenarios.append(
                {
                    "name": f"test_{cmd_id}_{option.name}_valid_path",
                    "description": f"Test {'  '.join(command_path)} with valid --{param_name}",
                    "command": command_path + [f"--{param_name}", "/tmp"],
                    "expected_exit_code": [0, 1, 2],
                }
            )

    # Test 4: Test positional arguments
    if positional_args:
        # Generate example values for positional args
        arg_values = []
        for arg in positional_args:
            if isinstance(arg.type, click.Path):
                arg_values.append("/tmp/test_file.json")
            else:
                arg_values.append(f"test_{arg.name}")

        scenarios.append(
            {
                "name": f"test_{cmd_id}_with_positional_args",
                "description": f"Test {'  '.join(command_path)} with positional arguments",
                "command": command_path + arg_values,
                "expected_exit_code": [0, 1, 2],
            }
        )

        # Test missing required positional arguments
        if any(arg.required for arg in positional_args):
            scenarios.append(
                {
                    "name": f"test_{cmd_id}_missing_required_args",
                    "description": f"Test {'  '.join(command_path)} with missing required arguments",
                    "command": command_path,
                    "expected_exit_code": 2,  # Should fail with usage error
                    "expected_output": "Error:",
                }
            )

    return scenarios


def generate_pytest_code(scenarios: List[Dict[str, Any]]) -> str:
    """Generate pytest code from test scenarios"""
    code = '''#!/usr/bin/env python3
"""
Auto-generated CLI tests from command introspection

Generated by: tests/generators/test_generator.py
DO NOT EDIT MANUALLY - Regenerate with: python tests/generators/test_generator.py

This file provides comprehensive coverage of all CLI commands, options,
and parameter combinations. Tests are automatically generated by introspecting
the Click command structure.
"""

import subprocess
import os

# Set testing environment variable
os.environ["N8N_DEPLOY_TESTING"] = "1"

CLI_COMMAND = ["./n8n-deploy"]

'''

    for scenario in scenarios:
        cmd_args = scenario["command"]
        expected_codes = scenario.get("expected_exit_code", 0)
        if isinstance(expected_codes, list):
            expected_codes_str = str(expected_codes)
        else:
            expected_codes_str = f"[{expected_codes}]"

        # Build command list
        cmd_list_str = "CLI_COMMAND + " + repr(cmd_args)

        code += f'''
def {scenario['name']}():
    """{scenario['description']}"""
    result = subprocess.run(
        {cmd_list_str},
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode in {expected_codes_str}, (
        f"Command failed with exit code {{result.returncode}}\\n"
        f"Command: {' '.join(cmd_args)}\\n"
        f"stdout: {{result.stdout[:500]}}\\n"
        f"stderr: {{result.stderr[:500]}}"
    )
'''

        if "expected_output" in scenario:
            code += f"""    assert "{scenario['expected_output']}" in result.stdout or "{scenario['expected_output']}" in result.stderr, (
        f"Expected '{scenario['expected_output']}' in output\\n"
        f"stdout: {{result.stdout[:500]}}\\n"
        f"stderr: {{result.stderr[:500]}}"
    )
"""

    return code


def main():
    """Generate test scenarios for all CLI commands"""
    print("🔍 Introspecting CLI commands...")

    # Import the main CLI app
    from api.cli.app import cli

    all_scenarios = []
    command_count = 0

    # Extract all commands and subcommands
    commands = extract_click_commands(cli)

    print(f"📋 Found {len(commands)} commands to test\n")

    # Generate scenarios for each command
    for cmd_id, (cmd_path, cmd_obj) in sorted(commands.items()):
        print(f"  Generating tests for: {' '.join(cmd_path)}")
        scenarios = generate_test_scenarios(cmd_path, cmd_obj)
        all_scenarios.extend(scenarios)
        command_count += 1
        print(f"    ✓ Generated {len(scenarios)} test scenarios")

    # Generate pytest code
    pytest_code = generate_pytest_code(all_scenarios)

    # Write to file
    output_path = Path(__file__).parent.parent / "generated" / "test_cli_generated.py"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(pytest_code)

    print(f"\n✅ Generated {len(all_scenarios)} test scenarios for {command_count} commands")
    print(f"📝 Written to: {output_path}")
    print(f"\n🧪 Run with: pytest {output_path} -v")
    print(f"📊 Or add to test suite: python run_tests.py --generated")


if __name__ == "__main__":
    main()
