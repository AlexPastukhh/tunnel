"""Explicit development tool profile; never confers installed Windows authority."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .engines import EngineConfig
from .inventory import digest, under, check_plain_chain
from .model import ContractError
from .registry import unique_object


@dataclass(frozen=True)
class DevelopmentSettings:
    state_root: Path
    policy_root: Path
    source_roots: tuple[Path, ...]
    tools: tuple[EngineConfig, ...]
    required_for_suffix: dict[str, tuple[str, ...]]
    timeout_seconds: float = 120

    def validate(self):
        paths = (self.state_root, self.policy_root, *self.source_roots)
        if not self.source_roots or any(not p.is_absolute() or ".." in p.parts for p in paths):
            raise ContractError("Absolute state/policy/source paths without traversal required")
        for source in self.source_roots:
            if any(under(root, source) or under(source, root) for root in (self.state_root, self.policy_root)):
                raise ContractError("State/policy storage must be separate from source roots")
            for tool in self.tools:
                if any(under(path, source) for path in (tool.executable, tool.config, *([tool.node] if tool.node else []))):
                    raise ContractError("Tools/config/Node must be outside candidate source roots")
        if not self.tools or len({t.kind for t in self.tools}) != len(self.tools):
            raise ContractError("Explicit nonduplicate engine tools required")
        if not 0 < self.timeout_seconds <= 900:
            raise ContractError("Job timeout must be within (0, 900] seconds")
        for suffix, engines in self.required_for_suffix.items():
            if (suffix not in (".js", ".cjs", ".mjs", ".py") or not engines
                    or len(set(engines)) != len(engines) or set(engines) - {"eslint", "semgrep"}):
                raise ContractError("Invalid explicit language/engine coverage profile")

    def check_target_isolation(self, target_root: str | None):
        if target_root is None:
            return
        target = Path(target_root)
        roots = {self.state_root, self.policy_root, Path(__file__).resolve().parent.parent}
        for tool in self.tools:
            roots.add(tool.executable.parent.parent)
            roots.add(tool.config.parent)
            if tool.node:
                roots.add(tool.node.parent)
        if any(under(root, target) or under(target, root) for root in roots):
            raise ContractError("Target must not overlap job state, policies or application/tools")
        ancestor = target
        while not ancestor.exists():
            ancestor = ancestor.parent
        check_plain_chain(ancestor)

    def check_storage_paths(self):
        for root in (self.state_root, self.policy_root):
            ancestor = root
            while not ancestor.exists():
                ancestor = ancestor.parent
            check_plain_chain(ancestor)

    @classmethod
    def load(cls, path: Path):
        try:
            if path.stat().st_size > 256 * 1024:
                raise ContractError("Development profile exceeds size limit")
            data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
            fields = {"schema_version", "state_root", "policy_root", "source_roots", "tools", "required_for_suffix", "timeout_seconds"}
            if (not isinstance(data, dict) or set(data) != fields
                    or type(data["schema_version"]) is not int or data["schema_version"] != 1
                    or not isinstance(data["tools"], list) or not isinstance(data["source_roots"], list)
                    or not isinstance(data["required_for_suffix"], dict)
                    or type(data["timeout_seconds"]) not in (int, float)):
                raise ContractError("Unsupported development settings schema/types")
            tools = []
            for item in data["tools"]:
                if (not isinstance(item, dict) or set(item) !=
                        {"kind", "executable", "executable_sha256", "config", "config_sha256", "node"}):
                    raise ContractError("Unexpected engine configuration schema")
                tools.append(EngineConfig(item["kind"], Path(item["executable"]), item["executable_sha256"],
                    Path(item["config"]), item["config_sha256"], Path(item["node"]) if item["node"] else None))
            if any(not isinstance(value, list) for value in data["required_for_suffix"].values()):
                raise ContractError("Language/engine coverage values must be lists")
            result = cls(Path(data["state_root"]), Path(data["policy_root"]),
                tuple(Path(p) for p in data["source_roots"]), tuple(tools),
                {key: tuple(value) for key, value in data["required_for_suffix"].items()}, data["timeout_seconds"])
            result.validate()
            return result
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise ContractError(f"Invalid development profile: {exc}") from exc

    def tool_identities(self):
        return tuple((t.kind, t.fingerprint()) for t in self.tools)
