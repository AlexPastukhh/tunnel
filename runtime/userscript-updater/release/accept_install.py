"""Elevated owner action: bind native evidence to an immutable installation."""
import argparse
import ctypes
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
handles = []
if os.name == "nt":
    for directory in (ROOT / "python/DLLs", ROOT / "pydeps/pywin32_system32"):
        if directory.is_dir():
            handles.append(os.add_dll_directory(str(directory)))

from checker.installed import REQUIRED_NATIVE, closure, protected_tree, validate_routes, verify_closure
from checker.inventory import digest, read_stable_file
from checker.model import ContractError
from checker.promotion_state import encoded, load_json
from checker.settings import DevelopmentSettings


def immutable_file(path):
    import win32security as security
    administrators = security.ConvertStringSidToSid("S-1-5-32-544")
    security.SetNamedSecurityInfo(str(path), security.SE_FILE_OBJECT,
                                 security.OWNER_SECURITY_INFORMATION, administrators, None, None, None)


def accept(root, native_report, route_inventory, gui_report):
    if os.name != "nt" or not sys.flags.isolated or not sys.flags.no_site:
        raise ContractError("Use the installed isolated Windows interpreter")
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise ContractError("The reviewed acceptance action requires elevated owner PowerShell")
    settings = DevelopmentSettings.load(root / "installation.json")
    owner = load_json(root / "installation-owner.json")
    roots = tuple(Path(p) for p in owner["approved_roots"])
    qa, routes, gui = map(load_json, (native_report, route_inventory, gui_report))
    profile_hash = digest(read_stable_file(root / "installation.json"))
    if (qa.get("platform") != "Windows" or qa.get("failures") != []
            or not REQUIRED_NATIVE <= set(qa.get("passed", []))
            or qa.get("installation_profile_sha256") != profile_hash):
        raise ContractError("Native acceptance is incomplete or refers to another profile")
    observed = gui.get("observed", {})
    for phase in ("COMPLETE_DEVELOPMENT", "REVIEW_READY", "COMPLETED", "ROLLED_BACK", "POLICY_SAVED", "CANCELLED"):
        if type(observed.get(phase)) is not int or observed[phase] < 1:
            raise ContractError("Missing native GUI observation: " + phase)
    if (gui.get("platform") != "Windows" or gui.get("fixture_only") is not True
            or gui.get("installation_profile_sha256") != profile_hash
            or gui.get("owner_sid") != owner["owner_sid"]
            or gui.get("manual_picker_visual") is not True):
        raise ContractError("Native GUI report/owner picker and visual receipt is incomplete")
    validate_routes(routes, (root, settings.state_root.parent, settings.state_root, settings.policy_root, *roots))
    protected_tree(root, owner["owner_sid"], immutable=True)
    for path in (settings.state_root, settings.policy_root, *roots):
        protected_tree(path, owner["owner_sid"], immutable=False)
    security_dir = root / "security"
    security_dir.mkdir(exist_ok=True)
    for name, document in (("native-qa.json", qa), ("routes.json", routes), ("gui-qa.json", gui)):
        path = security_dir / name
        path.write_bytes(encoded(document))
        immutable_file(path)
    manifest_path = root / "installed-manifest.json"
    manifest_path.write_bytes(encoded(dict(schema_version=1, files=closure(root))))
    immutable_file(manifest_path)
    manifest_hash = verify_closure(root)
    certificate = dict(schema_version=1, owner_sid=owner["owner_sid"], manifest_sha256=manifest_hash,
                       profile_sha256=profile_hash, native_qa_sha256=digest(read_stable_file(security_dir / "native-qa.json")),
                       routes_sha256=digest(read_stable_file(security_dir / "routes.json")),
                       approved_roots=[str(p) for p in roots], manual_gui_receipt=digest(read_stable_file(security_dir / "gui-qa.json")))
    path = security_dir / "acceptance.json"
    if path.exists():
        raise ContractError("Existing receipt is preserved; use a new side-by-side installation")
    path.write_bytes(encoded(certificate))
    immutable_file(path)
    protected_tree(root, owner["owner_sid"], immutable=True)
    print("Installation receipt created. Run the normal owner launcher and verify a safe external fixture before real projects.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--gui-report", type=Path, required=True)
    arguments = parser.parse_args()
    accept(ROOT, arguments.native_report, arguments.routes, arguments.gui_report)
