# OpenRastr Evolve

<img width="1024" height="1024" alt="OpenRastr Evolve logo" src="https://github.com/user-attachments/assets/b9beb81a-e810-4d12-ab2d-118adc426dee" />

OpenRastr Evolve is a Python-based AI workflow runtime built around three core modules:

1. Goal Interpretation
2. Capability Registration
3. Agent Spawning

It is designed to work with Ollama-served LLMs and SLMs, and to be easy to clone, install, configure, and run from GitHub.

## What It Does

OpenRastr Evolve helps turn a natural-language goal into an executable AI workflow by:

- interpreting the goal into a structured schema
- matching or generating the capabilities needed to fulfill it
- spawning agents to carry out the work

## Prerequisites

Before you start, make sure you have:

- Python 3.10 or newer
- `pip`
- Ollama installed and running
- at least one Ollama model available locally

## Quick Start

```bash
git clone <your-repo-url>
cd openrastr-evolve
./scripts/bootstrap.sh
```

The bootstrap script will:

- create a local virtual environment in `.venv`
- install required packaging tools
- install the project in editable mode
- launch the OpenRastr Evolve onboarding wizard

## Manual Setup

If you prefer to install manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install setuptools wheel
pip install --no-build-isolation -e .
openrastr-evolve onboard
openrastr-evolve doctor
```

## CLI Commands

```bash
openrastr-evolve onboard
openrastr-evolve doctor
openrastr-evolve run --goal-file path/to/goal.txt
openrastr-evolve register-skill path/to/skill.md
```

## Configuration

The onboarding wizard writes configuration to:

```text
~/.openrastr_evolve/config.json
```

Supported settings include:

- `workspace_root`
- `ollama_base_url`
- `goal_interpreter_model`
- `goal_interpreter_fallback_model`
- `pipeline_capability_model`
- `pipeline_agent_model`

## Recommended Install Mode

For a GitHub source checkout, the recommended installation method is:

```bash
pip install --no-build-isolation -e .
```

This keeps the repository editable while exposing the `openrastr-evolve` CLI command.

If you want the fastest setup path, use:

```bash
./scripts/bootstrap.sh
```

## First Run

After installation, the usual first-run flow is:

```bash
openrastr-evolve onboard
openrastr-evolve doctor
openrastr-evolve run --help
```

## License

This project is licensed under the GNU General Public License v3.0.

This product includes software developed by RastrAI Pvt Ltd.
