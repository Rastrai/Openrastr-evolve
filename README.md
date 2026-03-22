# OpenRastr Evolve

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/b9beb81a-e810-4d12-ab2d-118adc426dee" />


OpenRastr Evolve is a Python-first AI workflow runtime built around three generic modules:

1. Goal Interpretation
2. Capability Registration
3. Agent Spawning

It is designed to work with Ollama-served LLMs or SLMs and to be easy to clone, install, onboard, and run from GitHub.

## Quick Start

```bash
git clone <your-repo-url>
cd Project_OS_S_mini.v01
./scripts/bootstrap.sh
```

The bootstrap script will:

- create `.venv`
- install the project in editable mode
- launch the OpenRastr Evolve onboarding wizard

## Manual Setup

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

The onboarding wizard writes config to:

```text
~/.openrastr_evolve/config.json
```

Supported settings:

- `workspace_root`
- `ollama_base_url`
- `goal_interpreter_model`
- `goal_interpreter_fallback_model`
- `pipeline_capability_model`
- `pipeline_agent_model`

## Recommended Install Mode

For a GitHub source checkout, the recommended path is:

```bash
pip install --no-build-isolation -e .
```

That keeps the repo editable while still exposing the `openrastr-evolve` command. The bash bootstrap script is there to automate the environment creation, packaging prerequisites, and first-run onboarding.
