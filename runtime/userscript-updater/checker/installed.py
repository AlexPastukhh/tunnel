"""Independently installed Windows context. No development profile enables it.

The protected elevated-owner receipt binds the complete installed file closure,
native QA and the owner's inventory of agent write routes. Runtime repeats native
path/ACL/hash checks. This does not discover unreported external write services.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
from dataclasses import fields
from pathlib import Path

from .inventory import digest, read_stable_file, under
from .model import ContractError, relative_target
from .promotion_state import load_json, token
from .settings import DevelopmentSettings
from .windows_io import native_io

SYSTEM = "S-1-5-18"
ADMINS = "S-1-5-32-544"
INSTALLER = "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464"
IMMUTABLE_OWNERS = {SYSTEM, ADMINS, INSTALLER}
WRITE_RIGHTS = 0x10000000 | 0x40000000 | 0x10000 | 0x40000 | 0x80000 | 2 | 4 | 16 | 256 | 64
ANCESTOR_RIGHTS = 0x10000000 | 0x10000 | 0x40000 | 0x80000 | 64
REQUIRED_NATIVE = {"handles", "reparse", "hardlink", "ads", "sharing", "metadata",
                   "transaction", "interrupted-recovery", "child-containment", "real-analyzers", "isolation-canaries"}


def current_sid():
    import win32api
    import win32con
    import win32security as security
    token_handle = security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        return security.ConvertSidToStringSid(security.GetTokenInformation(token_handle, security.TokenUser)[0])
    finally:
        token_handle.Close()


def check_acl(path, owner_sid, *, immutable=False, ancestor=False):
    import win32security as security
    descriptor = security.GetFileSecurity(str(path),
        security.OWNER_SECURITY_INFORMATION | security.DACL_SECURITY_INFORMATION)
    owner = security.ConvertSidToStringSid(descriptor.GetSecurityDescriptorOwner())
    allowed = IMMUTABLE_OWNERS if immutable and not ancestor else IMMUTABLE_OWNERS | {owner_sid}
    if owner not in allowed:
        raise ContractError(f"Untrusted owner on protected path: {path}: {owner}")
    dacl = descriptor.GetSecurityDescriptorDacl()
    if dacl is None:
        raise ContractError(f"Unrestricted DACL: {path}")
    rights = ANCESTOR_RIGHTS if ancestor else WRITE_RIGHTS
    for index in range(dacl.GetAceCount()):
        ace = dacl.GetAce(index)
        kind, flags = ace[0]
        if flags & 8:  # INHERIT_ONLY_ACE does not apply to this object
            continue
        if kind == security.ACCESS_DENIED_ACE_TYPE:
            continue
        if kind != security.ACCESS_ALLOWED_ACE_TYPE:
            raise ContractError(f"Unsupported conditional/object ACL entry: {path}")
        mask, trustee = ace[1], security.ConvertSidToStringSid(ace[2])
        if mask & rights and trustee not in allowed:
            raise ContractError(f"Additional writable principal: {path}: {trustee}")


def protected_tree(root, owner_sid, *, immutable):
    io = native_io()
    io.validate(root)
    if not root.is_dir():
        raise ContractError("Protected installation/storage/approved root must be a directory")
    for parent in root.parents:
        io.validate(parent)
        check_acl(parent, owner_sid, immutable=immutable, ancestor=True)
    check_acl(root, owner_sid, immutable=immutable)
    for base, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(base) / name
            io.validate(path)
            check_acl(path, owner_sid, immutable=immutable)


def closure(root):
    result = []
    for base, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            native_io().validate(Path(base) / name)
        for name in files:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            if relative in ("installed-manifest.json", "security/acceptance.json"):
                continue
            sha256, size = native_io().hash(path)
            result.append(dict(path=relative, sha256=sha256, size=size))
    return sorted(result, key=lambda r: r["path"])


def verify_closure(root):
    manifest = load_json(root / "installed-manifest.json")
    if (not isinstance(manifest, dict) or set(manifest) != {"schema_version", "files"}
            or manifest["schema_version"] != 1 or not isinstance(manifest["files"], list)):
        raise ContractError("Invalid complete installed manifest")
    for row in manifest["files"]:
        if set(row) != {"path", "sha256", "size"}:
            raise ContractError("Invalid installed manifest entry")
        relative_target(row["path"])
    if closure(root) != manifest["files"]:
        raise ContractError("Installed closure changed, contains extra files or is incomplete")
    return digest(read_stable_file(root / "installed-manifest.json"))


def validate_routes(document, protected):
    if (not isinstance(document, dict) or set(document) != {"schema_version", "routes", "evidence"}
            or document["schema_version"] != 1 or not document["routes"] or not document["evidence"]):
        raise ContractError("Complete owner-reviewed agent-route inventory and probe evidence required")
    for route in document["routes"]:
        if (set(route) != {"name", "kind", "writable_windows_roots"}
                or route["kind"] not in ("docker-mount", "api-allowlist", "native-principal")
                or not route["name"] or not isinstance(route["writable_windows_roots"], list)):
            raise ContractError("Invalid agent-route inventory")
        for raw in route["writable_windows_roots"]:
            path = Path(raw)
            native_io().validate(path)
            windows = ctypes.create_unicode_buffer(32768)
            if not ctypes.windll.kernel32.GetWindowsDirectoryW(windows, len(windows)):
                raise ContractError("Cannot locate trusted Windows system dependencies")
            system_root = Path(windows.value)
            if under(system_root, path) or under(path, system_root):
                raise ContractError("An agent write route overlaps Windows system dependencies")
            if any(under(p, path) or under(path, p) for p in protected):
                raise ContractError("Protected installation overlaps a declared agent write route")
    seen = set()
    for row in document["evidence"]:
        if (set(row) != {"route", "marker", "challenge", "result", "receipt_sha256"}
                or row["route"] not in {r["name"] for r in document["routes"]}
                or row["result"] != "DENIED" or len(row["challenge"]) < 32
                or len(row["receipt_sha256"]) != 64):
            raise ContractError("Incomplete negative marker-probe evidence")
        marker = Path(row["marker"])
        native_io().validate(marker)
        matches = [p for p in protected if under(marker, p)]
        if not matches or read_stable_file(marker).decode("ascii") != row["challenge"]:
            raise ContractError("Probe marker moved/changed or is outside protected roots")
        seen.update((row["route"], str(p).casefold()) for p in matches)
    required = {(r["name"], str(p).casefold()) for r in document["routes"] for p in protected}
    if required - seen:
        raise ContractError("Each agent route needs an unchanged negative marker probe for every protected root")
    # These are explicit owner attestations of observed external routes, not automatic discovery.


class InstalledAuthority:
    def __init__(self, root):
        if os.name != "nt" or not sys.flags.isolated or not sys.flags.no_site:
            raise ContractError("Use the isolated installed Windows launcher")
        if ctypes.windll.shell32.IsUserAnAdmin():
            raise ContractError("Run the app as the normal owner, not elevated")
        self.root = Path(root)
        self.ready = False
        self.certificate = load_json(self.root / "security/acceptance.json")
        cert = self.certificate
        expected = {"schema_version", "owner_sid", "manifest_sha256", "profile_sha256",
                    "native_qa_sha256", "routes_sha256", "approved_roots", "manual_gui_receipt"}
        if not isinstance(cert, dict) or set(cert) != expected or cert["schema_version"] != 1:
            raise ContractError("Invalid protected installation acceptance receipt")
        self.owner_sid = current_sid()
        if cert["owner_sid"] != self.owner_sid or not cert["manual_gui_receipt"]:
            raise ContractError("Owner identity/manual GUI acceptance is missing")
        if Path(sys.executable) != self.root / "python/python.exe":
            raise ContractError("Unexpected Python interpreter")
        self.profile_path = self.root / "installation.json"
        self.profile = DevelopmentSettings.load(self.profile_path)
        self.approved_roots = tuple(Path(p) for p in cert["approved_roots"])
        if not self.approved_roots:
            raise ContractError("No owner-approved external target roots")
        self.verify(self.profile)
        self.ready = True

    def verify(self, settings, target=None):
        protected_tree(self.root, self.owner_sid, immutable=True)
        if digest(read_stable_file(self.profile_path)) != self.certificate["profile_sha256"]:
            raise ContractError("Installation profile changed")
        if verify_closure(self.root) != self.certificate["manifest_sha256"]:
            raise ContractError("Installation manifest changed")
        qa_raw = read_stable_file(self.root / "security/native-qa.json")
        routes_raw = read_stable_file(self.root / "security/routes.json")
        if (digest(qa_raw) != self.certificate["native_qa_sha256"]
                or digest(routes_raw) != self.certificate["routes_sha256"]):
            raise ContractError("Native QA/route evidence changed")
        gui_raw = read_stable_file(self.root / "security/gui-qa.json")
        if digest(gui_raw) != self.certificate["manual_gui_receipt"]:
            raise ContractError("Native GUI receipt changed")
        qa = json.loads(qa_raw)
        if (qa.get("platform") != "Windows" or qa.get("failures") != []
                or not REQUIRED_NATIVE <= set(qa.get("passed", []))):
            raise ContractError("Required native QA did not pass")
        roots = (settings.state_root.parent, settings.state_root, settings.policy_root, *self.approved_roots)
        validate_routes(json.loads(routes_raw), (self.root, *roots))
        for root in roots:
            protected_tree(root, self.owner_sid, immutable=False)
        for tool in settings.tools:
            for path in (tool.executable, tool.config, *([tool.node] if tool.node else [])):
                if not under(path, self.root):
                    raise ContractError("Analyzer/dependency/config outside installed closure")
        if target is not None:
            self.assert_target(target)

    def assert_target(self, target):
        target = Path(target)
        if not any(under(target, root) for root in self.approved_roots):
            raise ContractError("Destination is outside owner-approved roots")
        ancestor = target
        while not ancestor.exists():
            ancestor = ancestor.parent
        native_io().validate(ancestor)
        check_acl(ancestor, self.owner_sid)


class InstalledSettings(DevelopmentSettings):
    def __init__(self, authority):
        values = {f.name: getattr(authority.profile, f.name) for f in fields(DevelopmentSettings)}
        super().__init__(**values)
        object.__setattr__(self, "_authority", authority)

    def check_storage_paths(self):
        super().check_storage_paths()
        self._authority.verify(self)


class WindowsTarget:
    scope = "OWNER_INSTALLED_WINDOWS"

    def __init__(self, authority):
        if type(authority) is not InstalledAuthority or not authority.ready:
            raise ContractError("Only an independently validated installation can construct the writer")
        self.authority, self.io = authority, native_io()

    @property
    def available(self):
        return self.authority.ready

    def authorize(self, target, settings):
        self.authority.verify(settings, target)

    def path(self, root, relative):
        self.authority.assert_target(root)
        return root / relative_target(relative) if relative else root

    def read(self, root, relative):
        try:
            return self.io.read(self.path(root, relative))
        except OSError as exc:
            if exc.errno in (2, 3):
                return None
            raise

    def metadata(self, root, relative):
        import base64
        import win32security as security
        value = self.io.metadata(self.path(root, relative))
        descriptor = security.SECURITY_DESCRIPTOR(base64.b64decode(value["security"]))
        if security.ConvertSidToStringSid(descriptor.GetSecurityDescriptorOwner()) != self.authority.owner_sid:
            raise ContractError("Target file owner cannot be restored by the normal owner; explicit migration required")
        return value

    def replace(self, root, relative, data, metadata, *, expected_sha256):
        self.io.write(self.path(root, relative), data, metadata, expected_sha256)

    def remove(self, root, relative, *, expected_sha256, expected_metadata=None):
        self.io.remove(self.path(root, relative), expected_sha256, expected_metadata)

    def mkdir(self, root, relative):
        return self.io.mkdir(self.path(root, relative))

    def rmdir_if_owned_empty(self, root, relative, identity):
        self.io.rmdir_if_owned_empty(self.path(root, relative), identity)
