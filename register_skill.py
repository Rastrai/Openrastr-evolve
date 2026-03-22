from __future__ import annotations

import argparse
from pathlib import Path

from deep_pipeline.registry import ExtendedCapabilityRegistry
from deep_pipeline.skills import SkillRegistryManager
from openrastr_evolve.config import apply_environment, load_config, resolve_workspace

GREEN = "\033[38;5;46m"
RESET = "\033[0m"


def print_startup_banner() -> None:
    banner = r"""
 ██████╗ ██████╗ ███████╗███╗   ██╗██████╗  █████╗ ███████╗████████╗██████╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔══██╗
██║   ██║██████╔╝█████╗  ██╔██╗ ██║██████╔╝███████║███████╗   ██║   ██████╔╝
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██╗██╔══██║╚════██║   ██║   ██╔══██╗
╚██████╔╝██║     ███████╗██║ ╚████║██║  ██║██║  ██║███████║   ██║   ██║  ██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝

███████╗██╗   ██╗ ██████╗ ██╗    ██╗   ██╗███████╗
██╔════╝██║   ██║██╔═══██╗██║    ██║   ██║██╔════╝
█████╗  ██║   ██║██║   ██║██║    ██║   ██║█████╗
██╔══╝  ╚██╗ ██╔╝██║   ██║██║    ╚██╗ ██╔╝██╔══╝
███████╗ ╚████╔╝ ╚██████╔╝███████╗╚████╔╝ ███████╗
╚══════╝  ╚═══╝   ╚═════╝ ╚══════╝ ╚═══╝  ╚══════╝
"""
    print(f"{GREEN}{banner}{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload and register a skill as a capability.")
    parser.add_argument("skill_path", help="Path to a .md or .zip skill package.")
    args = parser.parse_args()
    config = load_config()
    apply_environment(config)

    print_startup_banner()
    print(f"{GREEN}[...] Skill upload requested for {args.skill_path}{RESET}")

    project_root = resolve_workspace(config)
    manager = SkillRegistryManager(project_root)
    registry = ExtendedCapabilityRegistry(project_root)
    skills_before = manager.list_skills()
    old_skill_names = [item["name"] for item in skills_before]

    record = manager.register_skill(args.skill_path)
    if record is None:
        print(f"{GREEN}Skill upload aborted.{RESET}")
        return

    registry.sync_skill_records()
    print(f"{GREEN}Skill successfully registered and available for capability matching{RESET}")
    answer = input(f"{GREEN}Would you like to list the old and new skills? (yes/no){RESET}\n> ").strip().lower()
    if answer == "yes":
        skills_after = manager.list_skills()
        new_skill_names = [item["name"] for item in skills_after]
        print(f"{GREEN}Old skills:{RESET}")
        for name in old_skill_names:
            print(f"{GREEN}- {name}{RESET}")
        print(f"{GREEN}New skills:{RESET}")
        for name in new_skill_names:
            print(f"{GREEN}- {name}{RESET}")


if __name__ == "__main__":
    main()
