#!/usr/bin/env python3
"""
Installation and setup script for n8n-deploy

Creates symlinks, checks for conflicts, and warns about existing environment variables.
"""

import os
import stat
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class N8nDeployInstaller(object):
    """Installer for n8n-deploy CLI tool"""

    # Environment variables used by n8n-deploy
    ENV_VARS = {
        "N8N_DEPLOY_DATA_DIR": "Application directory for database and app data",
        "N8N_DEPLOY_FLOWS_DIR": "User wf files directory path",
        "N8N_SERVER_URL": "n8n server URL for remote operations",
        "N8N_API_KEY": "Default API key for n8n server",
        "N8N_DEPLOY_TESTING": "Testing mode flag (internal use)",
    }

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.absolute()
        self.home_dir = Path.home()
        self.bin_dir = self.home_dir / ".local" / "bin"
        self.wrapper_script = self.project_root / "n8n-deploy"

    def check_environment_conflicts(self) -> Tuple[bool, List[str]]:
        """
        Check for existing n8n-deploy environment variables.

        Returns:
            Tuple of (has_conflicts, list of conflicting vars)
        """
        print("🔍 Checking for environment variable conflicts...")

        conflicts = []
        for env_var, description in self.ENV_VARS.items():
            if env_var in os.environ and env_var != "N8N_DEPLOY_TESTING":
                value = os.environ[env_var]
                conflicts.append(f"  • {env_var}={value}")
                print(f"  ⚠️  Found: {env_var}={value}")

        if conflicts:
            print("\n❌ Environment variable conflicts detected!")
            print("\nThe following n8n-deploy environment variables are already set:")
            for conflict in conflicts:
                print(conflict)

            print("\n⚠️  WARNING: These variables may interfere with n8n-deploy operation.")
            print("\nOptions:")
            print("  1. Unset these variables before running n8n-deploy")
            print("  2. Ensure they point to the correct directories")
            print("  3. Use CLI options (--data-dir, --flow-dir, --remote) to override")

            response = input("\nContinue installation anyway? [y/N]: ").strip().lower()
            if response not in ["y", "yes"]:
                print("\n❌ Installation aborted by user")
                return False, conflicts

            print("⚠️  Continuing installation despite conflicts...")

        else:
            print("  ✅ No environment variable conflicts found")

        return True, conflicts

    def check_wrapper_script(self) -> bool:
        """Check if wrapper script exists and is executable"""
        print("🔍 Checking wrapper script...")

        if not self.wrapper_script.exists():
            print(f"  ❌ Wrapper script not found: {self.wrapper_script}")
            print("  Run: chmod +x n8n-deploy")
            return False

        if not os.access(self.wrapper_script, os.X_OK):
            print("  ⚠️  Wrapper script not executable, fixing...")
            self.wrapper_script.chmod(self.wrapper_script.stat().st_mode | stat.S_IEXEC)
            print("  ✅ Made wrapper script executable")

        print(f"  ✅ Wrapper script ready: {self.wrapper_script}")
        return True

    def create_symlink(self) -> bool:
        """Create symlink in ~/.local/bin"""
        print("🔗 Creating symlink...")

        # Ensure .local/bin directory exists
        self.bin_dir.mkdir(parents=True, exist_ok=True)

        # Check if .local/bin is in PATH
        if str(self.bin_dir) not in os.environ.get("PATH", ""):
            print(f"  ⚠️  Warning: {self.bin_dir} is not in your PATH")
            print("  Add this line to your ~/.bashrc or ~/.zshrc:")
            print('  export PATH="$HOME/.local/bin:$PATH"')

        link_path = self.bin_dir / "n8n-deploy"

        try:
            # Remove existing symlink/file
            if link_path.exists() or link_path.is_symlink():
                old_target = link_path.resolve() if link_path.is_symlink() else link_path
                print(f"  ℹ️  Removing existing: {link_path} -> {old_target}")
                link_path.unlink()

            # Create symlink
            link_path.symlink_to(self.wrapper_script)
            print(f"  ✅ Created symlink: {link_path} -> {self.wrapper_script}")

            return True

        except Exception as e:
            print(f"  ❌ Failed to create symlink: {e}")
            return False

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("📦 Checking Python dependencies...")

        try:
            # Check if running in virtual environment
            in_venv = sys.prefix != sys.base_prefix
            if not in_venv:
                print("  ⚠️  Not in a virtual environment")
                print("  Recommended: Create a venv first")
                print("    python -m venv .venv")
                print("    source .venv/bin/activate  # or .venv/Scripts/activate on Windows")
                print("    python install.py")

                response = input("\n  Install globally anyway? [y/N]: ").strip().lower()
                if response not in ["y", "yes"]:
                    print("  ❌ Installation aborted - create venv and try again")
                    return False

            import subprocess

            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                print(f"  ❌ requirements.txt not found at {requirements_file}")
                return False

            print(f"  📥 Installing from {requirements_file}...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("  ✅ Dependencies installed successfully")
                return True
            else:
                print("  ❌ Failed to install dependencies:")
                print(f"  {result.stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Failed to install dependencies: {e}")
            return False

    def verify_installation(self) -> bool:
        """Verify the installation works"""
        print("🧪 Verifying installation...")

        try:
            import subprocess

            # Test help command
            result = subprocess.run(
                [str(self.wrapper_script), "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("  ✅ n8n-deploy command works")

                # Check for key help text
                if "n8n-deploy - a simple N8N Workflow Manager" in result.stdout:
                    print("  ✅ CLI help output correct")
                else:
                    print("  ⚠️  Help output may be incomplete")

                return True
            else:
                print(f"  ❌ Command failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Verification failed: {e}")
            return False

    def show_next_steps(self, has_conflicts: bool) -> None:
        """Show post-installation instructions"""
        print("\n" + "=" * 60)
        print("🎉 Installation completed!")
        print("=" * 60)

        print("\n📋 Next steps:")
        print("1. Test installation:")
        print("   n8n-deploy --help")
        print("   ./n8n-deploy --help  # Alternative if symlink not in PATH")

        print("\n2. Initialize database:")
        print("   n8n-deploy --data-dir /path/to/app/dir db init")
        print("   Or set N8N_DEPLOY_DATA_DIR environment variable")

        print("\n3. Configure wf directory:")
        print("   export N8N_DEPLOY_FLOWS_DIR=/path/to/your/workflows")
        print("   Or use --flow-dir option")

        if has_conflicts:
            print("\n⚠️  WARNING: Environment variable conflicts detected!")
            print("Review the conflicts shown above and adjust your environment.")

        print("\n📚 Documentation:")
        print(f"   README: {self.project_root / 'README.md'}")
        print(f"   Examples: {self.project_root / 'docs' / 'CLAUDE.md'}")

        print("\n🔧 Environment variables (optional):")
        for env_var, description in self.ENV_VARS.items():
            if env_var != "N8N_DEPLOY_TESTING":
                print(f"   • {env_var}: {description}")

    def run_installation(self) -> bool:
        """Run the complete installation process"""
        print("🎭 n8n-deploy Installation")
        print("=" * 60)

        # Check for environment conflicts first
        continue_install, conflicts = self.check_environment_conflicts()
        if not continue_install:
            return False

        # Run installation steps
        steps = [
            ("Checking wrapper script", self.check_wrapper_script),
            ("Installing dependencies", self.install_dependencies),
            ("Creating symlink", self.create_symlink),
            ("Verifying installation", self.verify_installation),
        ]

        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"\n❌ Installation failed at: {step_name}")
                return False

        # Show next steps
        self.show_next_steps(has_conflicts=bool(conflicts))
        return True

    def uninstall(self) -> None:
        """Remove n8n-deploy installation"""
        print("🗑️  Uninstalling n8n-deploy...")

        # Remove symlink
        link_path = self.bin_dir / "n8n-deploy"
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
            print(f"  ✅ Removed symlink: {link_path}")
        else:
            print(f"  ℹ️  No symlink found at {link_path}")

        print("\n✅ Uninstallation completed")
        print("\nNote: Dependencies and project files were not removed.")
        print("To fully remove:")
        print(f"  1. Delete project directory: {self.project_root}")
        print("  2. Optionally uninstall dependencies: pip uninstall -r requirements.txt")


def main() -> None:
    """Main installation script"""
    installer = N8nDeployInstaller()

    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        installer.uninstall()
    else:
        success = installer.run_installation()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
