from __future__ import annotations

import json
import re
from pathlib import Path

from rapidfuzz import process

from .models import CapabilityDefinition, CapabilityMatch
from .skills import SkillRegistryManager


class ExtendedCapabilityRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.registry_dir = project_root / "capability_registry"
        self.skill_md_path = self.registry_dir / "skill.md"
        self.generated_registry_path = self.registry_dir / "generated_capabilities.json"
        self.skill_capability_map_path = self.registry_dir / "skill_capability_map.json"
        self.skills = SkillRegistryManager(project_root)
        self.capabilities: dict[str, CapabilityDefinition] = {}
        self._last_goal_domain = ""
        self.reload()

    def reload(self) -> None:
        self.capabilities = {}
        self.capabilities.update(self._load_skill_registry())
        self.capabilities.update(self._load_generated_registry())
        self.capabilities.update(self._load_registered_skills())

    def _load_skill_registry(self) -> dict[str, CapabilityDefinition]:
        capabilities: dict[str, CapabilityDefinition] = {}
        current: dict[str, object] | None = None

        for raw_line in self.skill_md_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("## Capability:"):
                if current:
                    definition = self._build_definition(current, source="skill.md")
                    capabilities[definition.name] = definition
                current = {
                    "name": line.replace("## Capability:", "", 1).strip(),
                    "backend": "",
                    "description": "",
                    "dependencies": [],
                    "module_path": None,
                }
                continue

            if current is None:
                continue

            if line.startswith("llm_backend:"):
                current["backend"] = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                current["description"] = line.split(":", 1)[1].strip()
            elif line.startswith("tags:"):
                current["tags"] = [
                    item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()
                ]
            elif line.startswith("module_path:"):
                current["module_path"] = line.split(":", 1)[1].strip()
            elif line.startswith("-"):
                dependency = line.lstrip("-").strip()
                if dependency and dependency.lower() != "none":
                    current["dependencies"].append(dependency)

        if current:
            definition = self._build_definition(current, source="skill.md")
            capabilities[definition.name] = definition

        return capabilities

    def _load_generated_registry(self) -> dict[str, CapabilityDefinition]:
        if not self.generated_registry_path.exists():
            return {}

        raw_items = json.loads(self.generated_registry_path.read_text(encoding="utf-8"))
        generated: dict[str, CapabilityDefinition] = {}
        for item in raw_items:
            definition = CapabilityDefinition(
                name=item["name"],
                backend=item["backend"],
                description=item.get("description", ""),
                dependencies=item.get("dependencies", []),
                module_path=item.get("module_path"),
                source="generated",
            )
            generated[definition.name] = definition
        return generated

    def _load_registered_skills(self) -> dict[str, CapabilityDefinition]:
        skill_capabilities: dict[str, CapabilityDefinition] = {}
        for item in self.skills.list_skills():
            definition = CapabilityDefinition(
                name=item["name"],
                backend=item.get("backend", "mistral:latest"),
                description=item.get("description", ""),
                dependencies=[],
                module_path=None,
                source="registered_skill",
                tags=item.get("tags", []),
                inputs=item.get("inputs", []),
                outputs=item.get("outputs", []),
                skill_id=item.get("skill_id"),
                version=item.get("version"),
            )
            skill_capabilities[definition.name] = definition
        self._write_skill_capability_map(skill_capabilities)
        return skill_capabilities

    def _build_definition(self, payload: dict[str, object], source: str) -> CapabilityDefinition:
        return CapabilityDefinition(
            name=str(payload["name"]),
            backend=str(payload.get("backend", "")),
            description=str(payload.get("description", "")),
            dependencies=list(payload.get("dependencies", [])),
            module_path=payload.get("module_path") or None,
            source=source,
            tags=list(payload.get("tags", [])),
        )

    def list_capabilities(self) -> list[str]:
        return list(self.capabilities.keys())

    def get(self, capability_name: str) -> CapabilityDefinition | None:
        for name, definition in self.capabilities.items():
            if name.lower() == capability_name.lower():
                return definition
        return None

    def match_required_capabilities(self, required_capabilities: list[str], score_cutoff: int = 70) -> CapabilityMatch:
        matched: dict[str, CapabilityDefinition] = {}
        missing: list[str] = []
        fuzzy_aliases: dict[str, str] = {}

        registry_names = self.list_capabilities()
        lower_map = {name.lower(): name for name in registry_names}
        goal_domain = self._last_goal_domain or ""

        for capability in required_capabilities:
            exact_name = lower_map.get(capability.lower())
            if exact_name:
                matched[exact_name] = self.capabilities[exact_name]
                if exact_name != capability:
                    fuzzy_aliases[capability] = exact_name
                continue

            fuzzy_match = process.extractOne(capability, registry_names, score_cutoff=score_cutoff)
            if fuzzy_match:
                canonical_name = fuzzy_match[0]
                if not self._is_domain_compatible(
                    self.capabilities[canonical_name],
                    goal_domain,
                    capability,
                ):
                    missing.append(capability)
                    continue
                matched[canonical_name] = self.capabilities[canonical_name]
                fuzzy_aliases[capability] = canonical_name
                continue

            missing.append(capability)

        return CapabilityMatch(
            requested=required_capabilities,
            matched=matched,
            missing=missing,
            fuzzy_aliases=fuzzy_aliases,
        )

    def find_best_reusable_capability(
        self,
        requested_capability: str,
        goal_schema: dict | None = None,
        min_score: float = 95.0,
    ) -> CapabilityDefinition | None:
        goal_schema = goal_schema or {}
        goal_domain = goal_schema.get("domain", "")
        query_text = " ".join(
            [
                requested_capability,
                goal_schema.get("objective", ""),
                " ".join(goal_schema.get("data_inputs", [])),
                " ".join(goal_schema.get("expected_outputs", [])),
            ]
        )
        candidates: list[tuple[float, CapabilityDefinition]] = []
        for capability in self.capabilities.values():
            if not self._is_domain_compatible(capability, goal_domain, query_text):
                continue
            score = self._capability_reuse_score(requested_capability, capability, goal_schema)
            if score >= min_score:
                candidates.append((score, capability))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def match_goal_to_capabilities(self, goal_text: str, goal_schema: dict | None = None, limit: int = 3) -> list[str]:
        goal_schema = goal_schema or {}
        self._last_goal_domain = goal_schema.get("domain", "")
        query = " ".join(
            [
                goal_text,
                goal_schema.get("objective", ""),
                " ".join(goal_schema.get("required_capabilities", [])),
                " ".join(goal_schema.get("data_inputs", [])),
                " ".join(goal_schema.get("expected_outputs", [])),
            ]
        ).lower()
        query_tokens = {token for token in re.findall(r"[a-z0-9]+", query) if len(token) > 2}
        goal_domain = goal_schema.get("domain", "")

        scored: list[tuple[float, str]] = []
        for name, capability in self.capabilities.items():
            if not self._is_domain_compatible(capability, goal_domain, goal_text):
                continue
            capability_text = " ".join(
                [
                    name,
                    capability.description,
                    " ".join(capability.tags),
                    " ".join(capability.inputs),
                    " ".join(capability.outputs),
                ]
            ).lower()
            similarity = process.extractOne(query, [capability_text], score_cutoff=0)
            fuzzy_score = float(similarity[1]) if similarity else 0.0
            capability_tokens = {token for token in re.findall(r"[a-z0-9]+", capability_text) if len(token) > 2}
            overlap = len(query_tokens & capability_tokens) / max(len(capability_tokens) or 1, 1)
            usage_score = 0.0
            if capability.skill_id:
                skill = self.skills.find_by_name(name)
                usage_score = float(skill.get("historical_usage", 0)) if skill else 0.0
            source_bonus = self._source_priority_bonus(capability)
            score = fuzzy_score + (overlap * 100.0) + usage_score + source_bonus
            if score >= 110.0:
                scored.append((score, name))

        scored.sort(reverse=True)
        return [name for _, name in scored[:limit]]

    def increment_usage(self, capability_names: list[str]) -> None:
        self.skills.increment_usage(capability_names)

    def sync_skill_records(self) -> None:
        for item in self.skills.list_skills():
            self._upsert_skill_md_capability(
                name=item["name"],
                backend=item.get("backend", "mistral:latest"),
                description=item.get("description", ""),
                tags=item.get("tags", []),
                inputs=item.get("inputs", []),
                outputs=item.get("outputs", []),
            )
        self.reload()

    def _write_skill_capability_map(self, capabilities: dict[str, CapabilityDefinition]) -> None:
        skill_records = []
        for definition in capabilities.values():
            if definition.skill_id is None:
                continue
            skill_records.append(
                {
                    "skill_id": definition.skill_id,
                    "skill_name": definition.name,
                    "capability_name": definition.name,
                    "description": definition.description,
                    "tags": definition.tags,
                    "semantic_text": " ".join(
                        [definition.name, definition.description, " ".join(definition.tags)]
                    ).strip(),
                    "embedding": None,
                    "version": definition.version,
                }
            )
        self.skill_capability_map_path.write_text(
            json.dumps(skill_records, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}

    def _is_domain_compatible(
        self,
        capability: CapabilityDefinition,
        goal_domain: str,
        query_text: str,
    ) -> bool:
        goal_domain = (goal_domain or "").lower()
        capability_text = " ".join(
            [capability.name, capability.description, " ".join(capability.tags)]
        ).lower()

        healthcare_terms = {
            "healthcare", "clinical", "claims", "patient", "disease", "risk",
            "intervention", "oncology", "respiratory", "diabetes", "cardiovascular",
        }
        knowledge_terms = {
            "ontology", "rdf", "owl", "json", "jsonld", "json-ld", "markdown",
            "semantic", "knowledge", "graph", "entity", "relationship", "property",
        }

        goal_tokens = self._tokenize(f"{goal_domain} {query_text}")
        capability_tokens = self._tokenize(capability_text)

        goal_is_healthcare = bool(goal_tokens & healthcare_terms)
        cap_is_healthcare = bool(capability_tokens & healthcare_terms)
        goal_is_knowledge = bool(goal_tokens & knowledge_terms)
        cap_is_knowledge = bool(capability_tokens & knowledge_terms)

        if goal_is_knowledge and cap_is_healthcare and not cap_is_knowledge:
            return False
        if goal_is_healthcare and cap_is_knowledge and not cap_is_healthcare:
            return False

        overlap = goal_tokens & capability_tokens
        if cap_is_healthcare or cap_is_knowledge:
            return bool(overlap) or (goal_is_healthcare and cap_is_healthcare) or (goal_is_knowledge and cap_is_knowledge)

        return True

    def _capability_reuse_score(
        self,
        requested_capability: str,
        capability: CapabilityDefinition,
        goal_schema: dict,
    ) -> float:
        capability_text = " ".join(
            [
                capability.name,
                capability.description,
                " ".join(capability.tags),
                " ".join(capability.inputs),
                " ".join(capability.outputs),
            ]
        )
        query_text = " ".join(
            [
                requested_capability,
                goal_schema.get("objective", ""),
                " ".join(goal_schema.get("data_inputs", [])),
                " ".join(goal_schema.get("expected_outputs", [])),
            ]
        )
        similarity = process.extractOne(query_text, [capability_text], score_cutoff=0)
        fuzzy_score = float(similarity[1]) if similarity else 0.0
        requested_tokens = self._tokenize(requested_capability)
        capability_tokens = self._tokenize(capability_text)
        token_overlap = len(requested_tokens & capability_tokens)
        return fuzzy_score + (token_overlap * 15.0) + self._source_priority_bonus(capability)

    @staticmethod
    def _source_priority_bonus(capability: CapabilityDefinition) -> float:
        if capability.source == "registered_skill":
            return 40.0
        if capability.source == "skill.md":
            return 20.0
        if capability.source == "generated":
            return -15.0
        return 0.0

    def _upsert_skill_md_capability(
        self,
        name: str,
        backend: str,
        description: str,
        tags: list[str],
        inputs: list[str],
        outputs: list[str],
    ) -> None:
        content = self.skill_md_path.read_text(encoding="utf-8")
        block = (
            "\n\n---\n\n"
            f"## Capability: {name}\n"
            f"llm_backend: {backend}\n"
            f"description: {description}\n"
            "input_schema:\n"
            + "".join(f"  {item}: dynamic\n" for item in (inputs or ["dynamic_input"]))
            + "output_schema:\n"
            + "".join(f"  {item}: dynamic\n" for item in (outputs or ["dynamic_output"]))
            + "dependencies:\n"
            "  - None\n"
            + (f"tags: {', '.join(tags)}\n" if tags else "")
        )
        pattern = re.compile(
            rf"\n*---\n\n## Capability: {re.escape(name)}\n.*?(?=\n---\n\n## Capability:|\Z)",
            re.DOTALL,
        )
        if f"## Capability: {name}" in content:
            updated = pattern.sub(block, content)
            self.skill_md_path.write_text(updated, encoding="utf-8")
            return
        with self.skill_md_path.open("a", encoding="utf-8") as handle:
            handle.write(block)

    def register_generated_capability(
        self,
        name: str,
        backend: str,
        description: str,
        dependencies: list[str],
        module_path: str,
    ) -> CapabilityDefinition:
        record = {
            "name": name,
            "backend": backend,
            "description": description,
            "dependencies": dependencies,
            "module_path": module_path,
        }

        generated_records: list[dict[str, object]]
        if self.generated_registry_path.exists():
            generated_records = json.loads(self.generated_registry_path.read_text(encoding="utf-8"))
        else:
            generated_records = []

        existing_index = next(
            (index for index, item in enumerate(generated_records) if item["name"].lower() == name.lower()),
            None,
        )
        if existing_index is None:
            generated_records.append(record)
        else:
            generated_records[existing_index] = record

        self.generated_registry_path.write_text(
            json.dumps(generated_records, indent=2),
            encoding="utf-8",
        )

        if self.get(name) is None:
            self._append_to_skill_md(record)

        self.reload()
        definition = self.get(name)
        if definition is None:
            raise RuntimeError(f"Failed to register capability: {name}")
        return definition

    def _append_to_skill_md(self, record: dict[str, object]) -> None:
        dependency_lines = "\n".join(
            f"  - {dependency}" for dependency in record["dependencies"]
        ) or "  - None"
        block = (
            "\n\n---\n\n"
            f"## Capability: {record['name']}\n"
            f"llm_backend: {record['backend']}\n"
            f"description: {record['description']}\n"
            "input_schema:\n"
            "  generated_payload: object\n"
            "output_schema:\n"
            "  generated_result: object\n"
            "dependencies:\n"
            f"{dependency_lines}\n"
            f"module_path: {record['module_path']}\n"
        )
        with self.skill_md_path.open("a", encoding="utf-8") as handle:
            handle.write(block)

    @staticmethod
    def capability_to_module_name(capability_name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", capability_name.lower()).strip("_")
        return slug or "generated_capability"
