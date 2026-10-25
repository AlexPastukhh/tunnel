"""Real local engine-config validation on safe fixtures, never an owner PASS.

Supported development profile: ESLint core JS/CJS/MJS and Semgrep CE JS/Python.
Compilation/loaded IDs do not prove semantic effectiveness or project coverage.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from .inventory import digest
from .model import ContractError
from .policies import CapturedPolicies, PolicyPack
from .reports import parse_semgrep
from .processes import execute, RunControl, Cancelled, DeadlineExceeded

if TYPE_CHECKING:
    from .engines import EngineConfig

# Absolute package import; no candidate require(), config lookup, inline directives or fix.
ESLINT_PROBE = r"""
const path = require('node:path');
const [pkg, config, cwd] = process.argv.slice(1);
const { ESLint } = require(path.join(pkg, 'lib/api.js'));
const { builtinRules } = require(path.join(pkg, 'lib/unsupported-api.js'));
(async () => {
  const eslint = new ESLint({ cwd, overrideConfigFile: config,
    allowInlineConfig: false, ignore: false });
  const rows = [];
  for (const suffix of ['js', 'cjs', 'mjs']) {
    const file = path.join(cwd, 'fixture.' + suffix);
    const effective = await eslint.calculateConfigForFile(file);
    const result = await eslint.lintFiles([file]);
    rows.push({ suffix, rules: effective?.rules ?? null,
      fatal: result.some(r => r.fatalErrorCount || r.messages.some(m => m.fatal)) });
  }
  console.log(JSON.stringify({ version: ESLint.version,
    builtin: [...builtinRules.keys()], rows }));
})().catch(e => { console.error(String(e)); process.exitCode = 2; });
"""


def _environment(root: Path) -> dict[str, str]:
    return {"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C.UTF-8",
            "NODE_OPTIONS": "", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(root), "SEMGREP_SEND_METRICS": "off",
            "SEMGREP_ENABLE_VERSION_CHECK": "false"}


def _yaml_rules(text: str) -> list[dict]:
    # Optional until installed: absence is ERROR, never a silent unvalidated config.
    try:
        import yaml
    except ImportError as exc:
        raise ContractError("Install pinned PyYAML dependency to validate Semgrep policies") from exc

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ContractError(f"Duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        value = yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise ContractError(f"Invalid Semgrep YAML: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"rules"} or not isinstance(value["rules"], list) or not value["rules"]:
        raise ContractError("Semgrep config must contain nonempty rules list")
    ids = []
    for rule in value["rules"]:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"]:
            raise ContractError("Semgrep rule ID required")
        ids.append(rule["id"])
    if len(ids) != len(set(ids)):
        raise ContractError("Duplicate Semgrep rule IDs")
    return value["rules"]


@dataclass(frozen=True)
class EnginePolicyValidation:
    engine: str
    status: str
    effective_rules: tuple[str, ...]
    tool_fingerprint: str
    detail: str


def validate_engine_config(config: EngineConfig, *, required_rules: tuple[str, ...] = (),
                           timeout: int = 30, control: RunControl | None = None) -> EnginePolicyValidation:
    """Load actual pinned config in real engine; all errors block development scan."""
    try:
        config.validate()
        identity = config.fingerprint()
        with tempfile.TemporaryDirectory(prefix="checker-policy-") as temporary:
            root = Path(temporary)
            env = _environment(root)
            if config.kind == "eslint":
                for suffix in ("js", "cjs", "mjs"):
                    (root / f"fixture.{suffix}").write_text("const answer = 42;\n", encoding="utf-8")
                process = execute([str(config.node), "-e", ESLINT_PROBE,
                    str(config.executable.parent.parent), str(config.config), str(root)],
                    cwd=root, env=env, shell=False, capture_output=True, text=True,
                    errors="replace", timeout=timeout, check=False, control=control)
                if process.returncode:
                    raise ContractError(f"ESLint config load failed: {process.stderr[-2000:]}")
                data = json.loads(process.stdout)
                builtins = set(data["builtin"])
                rule_sets = []
                for row in data["rows"]:
                    rules = row["rules"]
                    if not isinstance(rules, dict) or row["fatal"]:
                        raise ContractError("ESLint ignored/unconfigured/fatal validation fixture")
                    if set(rules) - builtins:
                        raise ContractError("Unknown or unsupported ESLint core rule IDs")
                    enabled = {name for name, setting in rules.items()
                               if setting and setting[0] in (1, 2, "warn", "error")}
                    if not enabled or set(required_rules) - enabled:
                        raise ContractError("Disabled/missing required ESLint rules or empty effective policy")
                    rule_sets.append(enabled)
                if len(rule_sets) != 3 or any(rules != rule_sets[0] for rules in rule_sets):
                    raise ContractError("Inconsistent ESLint rules across JS/CJS/MJS fixtures")
                active = tuple(sorted(rule_sets[0]))
                version = data["version"]
            else:
                from .engines import build_argv
                rules = _yaml_rules(config.config.read_text(encoding="utf-8"))
                configured = {rule["id"] for rule in rules}
                if set(required_rules) - configured:
                    raise ContractError("Missing required Semgrep rules")
                probes = {"javascript": ("js", "const answer = 42;\n"),
                          "js": ("js", "const answer = 42;\n"),
                          "python": ("py", "answer = 42\n")}
                suffixes = {}
                for rule in rules:
                    languages = rule.get("languages")
                    if not isinstance(languages, list) or not languages:
                        raise ContractError("Semgrep rule languages required")
                    for language in languages:
                        if language not in probes:
                            raise ContractError(f"No development validation fixture for language: {language}")
                        suffix, code = probes[language]
                        suffixes[suffix] = code
                files = []
                for suffix, code in sorted(suffixes.items()):
                    path = root / f"fixture.{suffix}"
                    path.write_text(code, encoding="utf-8")
                    files.append(path)
                argv = build_argv(config, tuple(files))
                argv[argv.index("--"):argv.index("--")] = ["--time", "--no-rewrite-rule-ids"]
                process = execute(argv, cwd=root, env=env, shell=False,
                    capture_output=True, text=True, errors="replace", timeout=timeout, check=False, control=control)
                report = parse_semgrep(process.stdout, process.returncode, tuple(files), root)
                if report.status not in ("STRUCTURAL_CLEAR", "FINDINGS"):
                    raise ContractError(f"Semgrep config compile/fixture coverage failed: {report.detail}; {process.stderr[-1500:]}")
                data = json.loads(process.stdout)
                loaded = data.get("time", {}).get("rules")
                if not isinstance(loaded, list) or len(loaded) != len(set(loaded)) or set(loaded) != configured:
                    raise ContractError("Semgrep skipped/missing/disabled effective rules")
                active = tuple(sorted(loaded))
                version = data["version"]
        # Changed executable/config/Node invalidates the result of the probe.
        if config.fingerprint() != identity:
            raise ContractError("Tool/config changed during policy validation")
        return EnginePolicyValidation(config.kind, "VALIDATED_DEVELOPMENT", active, identity,
            f"{version}; actual config loaded on safe fixtures; semantic effectiveness NOT proven")
    except (Cancelled, DeadlineExceeded):
        raise
    except Exception as exc:
        # Malformed YAML/JSON, missing dependency/tool, timeout, unsupported API/version.
        return EnginePolicyValidation(config.kind, "ERROR", (), "",
                                      f"{type(exc).__name__}: {exc}")


@dataclass(frozen=True)
class EffectivePolicy:
    policy_sha256: str
    configs: tuple[EngineConfig, ...]
    required_rules: tuple[tuple[str, tuple[str, ...]], ...]
    validations: tuple[EnginePolicyValidation, ...]

    @property
    def tool_fingerprints(self) -> tuple[tuple[str, str], ...]:
        return tuple((v.engine, v.tool_fingerprint) for v in self.validations)


def prepare_effective_policy(captured: CapturedPolicies, tools: tuple[EngineConfig, ...],
                             directory: Path, *,
                             required_rules: tuple[tuple[str, tuple[str, ...]], ...] = (),
                             timeout: int = 30, control: RunControl | None = None) -> EffectivePolicy:
    """Compose captured shared packs, reject conflicts, compile real configs or raise.

    directory must be new job-owned development storage, never a source directory.
    Generated configs are data-only. Tools/dependencies still need Windows installation.
    """
    eslint = {}
    semgrep = []
    ids = set()
    for pack_id, expected, raw in captured.packs:
        if digest(raw) != expected:
            raise ContractError("Captured policy bytes changed")
        pack = PolicyPack.parse(raw)
        if pack.pack_id != pack_id:
            raise ContractError("Captured policy identity mismatch")
        for name, level in pack.eslint_core_rules.items():
            if name in eslint and eslint[name] != level:
                raise ContractError(f"Conflicting ESLint rule: {name}")
            eslint[name] = level
        if pack.semgrep_rules_text.strip():
            for rule in _yaml_rules(pack.semgrep_rules_text):
                if rule["id"] in ids:
                    raise ContractError(f"Conflicting Semgrep rule ID: {rule['id']}")
                ids.add(rule["id"])
                semgrep.append(rule)
    tokens = [(i, token) for i, token, _ in captured.packs]
    if not tokens or digest(json.dumps(tokens, sort_keys=True).encode()) != captured.combined_sha256:
        raise ContractError("Captured effective policy hash mismatch")
    by_kind = {tool.kind: tool for tool in tools}
    if len(by_kind) != len(tools):
        raise ContractError("Duplicate engine configuration")
    requirements = dict(required_rules)
    if len(requirements) != len(required_rules) or set(requirements) - {"eslint", "semgrep"}:
        raise ContractError("Invalid required rule engine")
    needed = ({"eslint"} if eslint else set()) | ({"semgrep"} if semgrep else set()) | set(requirements)
    if not needed or needed - set(by_kind):
        raise ContractError("Missing required engine")
    # Validate original supplied pins before creating any generated config.
    for kind in needed:
        by_kind[kind].validate()
    directory.mkdir(parents=True, exist_ok=False)
    configs, validations, all_required = [], [], []
    for kind in sorted(needed):
        if kind == "eslint":
            path = directory / "eslint.config.cjs"
            value = [{"files": ["**/*.js", "**/*.cjs", "**/*.mjs"], "rules": eslint}]
            path.write_text("module.exports = " + json.dumps(value) + ";\n", encoding="utf-8")
            required = tuple(sorted(set(requirements.get(kind, ())) |
                                    {r for r, level in eslint.items() if level != "off"}))
        else:
            path = directory / "semgrep-rules.json"
            path.write_text(json.dumps({"rules": semgrep}, ensure_ascii=False), encoding="utf-8")
            required = tuple(sorted(set(requirements.get(kind, ())) | ids))
        config = replace(by_kind[kind], config=path, config_sha256=digest(path.read_bytes()))
        validation = validate_engine_config(config, required_rules=required, timeout=timeout, control=control)
        if validation.status != "VALIDATED_DEVELOPMENT":
            raise ContractError(f"{kind} effective policy invalid: {validation.detail}")
        configs.append(config)
        validations.append(validation)
        all_required.append((kind, required))
    return EffectivePolicy(captured.combined_sha256, tuple(configs), tuple(all_required), tuple(validations))
