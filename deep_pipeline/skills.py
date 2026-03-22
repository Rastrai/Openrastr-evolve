from __future__ import annotations

import json
import re
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GREEN = "\033[38;5;46m"
RESET = "\033[0m"


@dataclass
class ParsedSkill:
    name: str
    description: str
    inputs: list[str]
    outputs: list[str]
    execution_logic: str
    references: list[str]
    tags: list[str]
    source_type: str
    backend: str
    extracted_dir: Path | None = None
    original_path: Path | None = None


class SkillRegistryManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.registry_dir = project_root / "skills_registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.skills_db_path = self.registry_dir / "skills.json"
        self.upload_log_path = self.registry_dir / "upload.log"
        self.packages_dir = self.registry_dir / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.skills_db_path.exists():
            self.skills_db_path.write_text("[]", encoding="utf-8")
        if not self.upload_log_path.exists():
            self.upload_log_path.write_text("", encoding="utf-8")

    def list_skills(self) -> list[dict[str, Any]]:
        return json.loads(self.skills_db_path.read_text(encoding="utf-8"))

    def register_skill(self, upload_path: str | Path) -> dict[str, Any] | None:
        upload_path = Path(upload_path).expanduser().resolve()
        parsed_skill = self.parse_skill(upload_path)
        self._log("upload_received", {"path": str(upload_path), "name": parsed_skill.name})

        if input(
            f"{GREEN}Are you sure you want to upload and register this skill? (yes/no){RESET}\n> "
        ).strip().lower() != "yes":
            self._log("upload_aborted", {"path": str(upload_path), "name": parsed_skill.name})
            self._cleanup_temp(parsed_skill)
            return None

        existing = self.find_by_name(parsed_skill.name)
        version = 1
        skill_id = f"skill_{uuid.uuid4().hex[:10]}"
        if existing:
            answer = input(
                f"{GREEN}A skill named '{parsed_skill.name}' already exists. Overwrite and create a new version? (yes/no){RESET}\n> "
            ).strip().lower()
            if answer != "yes":
                self._log("overwrite_aborted", {"name": parsed_skill.name})
                self._cleanup_temp(parsed_skill)
                return None
            version = int(existing["version"]) + 1
            skill_id = existing["skill_id"]

        package_dir = self.packages_dir / skill_id / f"v{version}"
        package_dir.mkdir(parents=True, exist_ok=True)
        stored_reference = self._store_skill_assets(parsed_skill, package_dir)

        record = {
            "skill_id": skill_id,
            "version": version,
            "name": parsed_skill.name,
            "description": parsed_skill.description,
            "inputs": parsed_skill.inputs,
            "outputs": parsed_skill.outputs,
            "execution_logic": parsed_skill.execution_logic,
            "references": parsed_skill.references,
            "tags": parsed_skill.tags,
            "source_type": parsed_skill.source_type,
            "backend": parsed_skill.backend,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "package_path": str(package_dir),
            "stored_reference": stored_reference,
            "historical_usage": existing.get("historical_usage", 0) if existing else 0,
            "execution_compatible": self._validate_execution_compatibility(parsed_skill),
        }

        records = [item for item in self.list_skills() if item["name"].lower() != parsed_skill.name.lower()]
        records.append(record)
        self.skills_db_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        self._log("registration_complete", {"name": parsed_skill.name, "skill_id": skill_id, "version": version})
        self._cleanup_temp(parsed_skill)
        return record

    def parse_skill(self, upload_path: Path) -> ParsedSkill:
        if upload_path.suffix.lower() == ".md":
            return self._parse_markdown_skill(upload_path)
        if upload_path.suffix.lower() == ".zip":
            return self._parse_zip_skill(upload_path)
        raise ValueError("Only .md and .zip skill uploads are supported.")

    def find_by_name(self, name: str) -> dict[str, Any] | None:
        for item in self.list_skills():
            if item["name"].lower() == name.lower():
                return item
        return None

    def increment_usage(self, skill_or_capability_names: list[str]) -> None:
        lowered = {name.lower() for name in skill_or_capability_names}
        records = self.list_skills()
        changed = False
        for item in records:
            aliases = {item["name"].lower()}
            aliases.update(tag.lower() for tag in item.get("tags", []))
            if aliases & lowered:
                item["historical_usage"] = int(item.get("historical_usage", 0)) + 1
                changed = True
        if changed:
            self.skills_db_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def _parse_markdown_skill(self, path: Path) -> ParsedSkill:
        text = path.read_text(encoding="utf-8")
        sections = self._extract_markdown_sections(text)
        first_heading = next(iter(sections.keys()), "")
        name_match = re.search(r"^\#\s*Skill:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        name = (
            sections.get("skill name")
            or sections.get("name")
            or (name_match.group(1).strip() if name_match else "")
            or (first_heading.split(":", 1)[1].strip() if first_heading.startswith("skill:") else "")
            or path.stem
        )
        description = (
            sections.get("description")
            or sections.get("intent", "")
        )
        inputs = self._split_lines(self._section_block(text, "inputs"))
        outputs = self._split_lines(self._section_block(text, "output") or self._section_block(text, "outputs"))
        execution_logic = (
            self._section_block(text, "executable workflow")
            or sections.get("execution logic")
            or self._section_block(text, "prompt template")
            or sections.get("references")
            or ""
        )
        references = self._split_lines(self._section_block(text, "reference knowledge"))
        tags = self._split_csv_or_lines(
            sections.get("tags", "")
            or sections.get("categories", "")
            or sections.get("category", "")
        )
        backend = sections.get("llm backend") or sections.get("backend") or "mistral:latest"
        return ParsedSkill(
            name=name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            execution_logic=execution_logic,
            references=references,
            tags=tags,
            source_type="markdown",
            backend=backend,
            original_path=path,
        )

    def _parse_zip_skill(self, path: Path) -> ParsedSkill:
        temp_dir = Path(tempfile.mkdtemp(prefix="skill_upload_"))
        with zipfile.ZipFile(path, "r") as archive:
            archive.extractall(temp_dir)

        metadata_path = next(iter(sorted(temp_dir.rglob("metadata.json"))), None)
        if metadata_path and metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            return ParsedSkill(
                name=metadata.get("name", path.stem),
                description=metadata.get("description", ""),
                inputs=metadata.get("inputs", []),
                outputs=metadata.get("outputs", []),
                execution_logic=metadata.get("execution_logic", ""),
                references=metadata.get("references", []),
                tags=metadata.get("tags", []),
                source_type="zip",
                backend=metadata.get("backend", "mistral:latest"),
                extracted_dir=temp_dir,
                original_path=path,
            )

        markdown_path = next(iter(sorted(temp_dir.rglob("*.md"))), None)
        if markdown_path:
            parsed = self._parse_markdown_skill(markdown_path)
            parsed.source_type = "zip"
            parsed.extracted_dir = temp_dir
            parsed.original_path = path
            return parsed

        python_files = [str(item.relative_to(temp_dir)) for item in sorted(temp_dir.rglob("*.py"))]
        return ParsedSkill(
            name=path.stem,
            description=f"Imported zip skill package containing {len(python_files)} Python files.",
            inputs=[],
            outputs=[],
            execution_logic="Referenced package contents from uploaded zip archive.",
            references=python_files,
            tags=[],
            source_type="zip",
            backend="mistral:latest",
            extracted_dir=temp_dir,
            original_path=path,
        )

    def _store_skill_assets(self, parsed_skill: ParsedSkill, package_dir: Path) -> str:
        if parsed_skill.source_type == "markdown" and parsed_skill.original_path is not None:
            target = package_dir / parsed_skill.original_path.name
            shutil.copy2(parsed_skill.original_path, target)
            return str(target)
        if parsed_skill.extracted_dir is not None:
            target = package_dir / "contents"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(parsed_skill.extracted_dir, target)
            return str(target)
        return ""

    def _validate_execution_compatibility(self, parsed_skill: ParsedSkill) -> bool:
        if parsed_skill.execution_logic.strip():
            return True
        if parsed_skill.references:
            return True
        if parsed_skill.extracted_dir and list(parsed_skill.extracted_dir.rglob("*.py")):
            return True
        return False

    def _cleanup_temp(self, parsed_skill: ParsedSkill) -> None:
        if parsed_skill.extracted_dir and parsed_skill.extracted_dir.exists():
            shutil.rmtree(parsed_skill.extracted_dir, ignore_errors=True)

    def _log(self, event: str, payload: dict[str, Any]) -> None:
        line = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self.upload_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line) + "\n")

    @staticmethod
    def _extract_markdown_sections(text: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        current_key: str | None = None
        buffer: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                if current_key is not None:
                    sections[current_key] = "\n".join(buffer).strip()
                current_key = stripped.lstrip("#").strip().lower()
                buffer = []
                continue
            if current_key is not None:
                buffer.append(line)
        if current_key is not None:
            sections[current_key] = "\n".join(buffer).strip()
        return sections

    @staticmethod
    def _section_block(text: str, heading: str) -> str:
        pattern = re.compile(
            rf"^\#{{1,6}}\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^\#{{1,6}}\s+|\Z)",
            re.IGNORECASE | re.MULTILINE,
        )
        match = pattern.search(text)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _split_lines(value: str) -> list[str]:
        items: list[str] = []
        for line in value.splitlines():
            line = line.strip().lstrip("-").strip()
            if line:
                items.append(line)
        return items

    @classmethod
    def _split_csv_or_lines(cls, value: str) -> list[str]:
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return cls._split_lines(value)
