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
- for example, `qwen2.5:7b`

## Quick Start: macOS and Linux

```bash
git clone https://github.com/Rastrai/Openrastr-evolve.git
cd Openrastr-evolve
./scripts/bootstrap.sh
openrastr-evolve doctor
```

The bootstrap script will:

- create a local virtual environment in `.venv`
- install required packaging tools
- install the project in editable mode
- launch the OpenRastr Evolve onboarding wizard

## Quick Start: Windows

Use PowerShell for the steps below.

```powershell
git clone https://github.com/Rastrai/Openrastr-evolve.git
cd Openrastr-evolve

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install setuptools wheel
python -m pip install --no-build-isolation -e .
python -m openrastr_evolve.cli onboard
python -m openrastr_evolve.cli doctor
python -m openrastr_evolve.cli run --help
```

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

If `openrastr-evolve` is not recognized on Windows, use:

```powershell
python -m openrastr_evolve.cli onboard
python -m openrastr_evolve.cli doctor
python -m openrastr_evolve.cli run --help
```

## Manual Setup

If you prefer to install manually on macOS or Linux:

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

On macOS and Linux:

```bash
openrastr-evolve onboard
openrastr-evolve doctor
openrastr-evolve run --goal-file path/to/goal.txt
openrastr-evolve register-skill path/to/skill.md
```

On Windows, if the CLI command is not available in `PATH`:

```powershell
python -m openrastr_evolve.cli onboard
python -m openrastr_evolve.cli doctor
python -m openrastr_evolve.cli run --goal-file path\to\goal.txt
python -m openrastr_evolve.cli register-skill path\to\skill.md
```

## Configuration

The onboarding wizard writes configuration to:

```text
~/.openrastr_evolve/config.json
```

On Windows, `~` refers to your user home directory.

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

If you want the fastest setup path on macOS or Linux, use:

```bash
./scripts/bootstrap.sh
```

## First Run

Typical first-run flow on macOS and Linux:

```bash
openrastr-evolve onboard
openrastr-evolve doctor
openrastr-evolve run --help
```

Typical first-run flow on Windows:

```powershell
python -m openrastr_evolve.cli onboard
python -m openrastr_evolve.cli doctor
python -m openrastr_evolve.cli run --help
```

## License

This project is licensed under the GNU General Public License v3.0.

This product includes software developed by RastrAI Pvt Ltd.
