"""Restore an isolated Neovim profile without modifying system packages or defaults."""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

REPO = Path(__file__).resolve().parent
PROFILE = "nvim-sam"
FEDORA_PACKAGES = (
    "sudo dnf install python3 git gcc gcc-c++ make nodejs nodejs-npm "
    "java-21-openjdk-devel ripgrep fd-find curl tar gzip xz unzip wl-clipboard libatomic"
)
MAC_PACKAGES = "brew install python git node openjdk ripgrep fd"


def host_platform() -> str:
    """Identify a supported host; reject Atomic hosts before producing write actions."""
    system, machine = platform.system(), platform.machine()
    if system == "Darwin" and machine == "arm64":
        return "macos-arm64"
    if system == "Linux":
        release = platform.freedesktop_os_release()
        atomic = Path("/run/ostree-booted").exists() or Path("/sysroot/ostree").exists()
        if atomic or release.get("VARIANT_ID") in {"silverblue", "kinoite", "sericea", "onyx"}:
            raise ValueError("Fedora Atomic is not supported; no rpm-ostree changes will be made")
        if (
            release.get("ID") == "fedora"
            and release.get("VERSION_ID") == "43"
            and machine == "x86_64"
        ):
            return "linux-x86_64"
    raise ValueError(
        f"Unsupported host: {system} {machine}; supported: Fedora 43 x86-64, macOS ARM64"
    )


def profile_paths() -> dict[str, Path]:
    """Resolve absolute XDG roots and reject overlapping profile directories."""
    home = Path.home()
    paths = {}
    for kind, default in {
        "config": ".config",
        "data": ".local/share",
        "state": ".local/state",
        "cache": ".cache",
    }.items():
        base = Path(os.environ.get(f"XDG_{kind.upper()}_HOME") or home / default)
        if not base.is_absolute():
            raise ValueError(f"XDG_{kind.upper()}_HOME must be absolute")
        paths[kind] = base / PROFILE
    paths["launcher"] = home / ".local/bin/nv"
    roots = [paths[k] for k in ("config", "data", "state", "cache")]
    for index, root in enumerate(roots):
        for other in roots[index + 1 :]:
            if root == other or root.is_relative_to(other) or other.is_relative_to(root):
                raise ValueError("XDG profile directories must not overlap")
    return paths


def matches_link(path: Path, target: Path) -> bool:
    """Check the destination of a link without treating a directory as managed."""
    return path.is_symlink() and path.resolve() == target.resolve()


def expected_links(paths: dict[str, Path]) -> dict[Path, Path]:
    """Return the only two user-visible links owned by this configuration."""
    return {paths["config"]: REPO, paths["launcher"]: REPO / "bin/nv"}


def guard_roots(paths: dict[str, Path]) -> None:
    """Reject redirected runtime roots and paths that could erase source or home."""
    roots = [paths[k] for k in ("data", "state", "cache")]
    for root in roots:
        resolved = root.resolve()
        if root.is_symlink() or (root.exists() and not root.is_dir()):
            raise ValueError(f"Runtime root must be a real directory: {root}")
        if Path.home().resolve().is_relative_to(resolved) or REPO.is_relative_to(resolved):
            raise ValueError(f"Runtime root contains home or repository: {root}")
    for index, root in enumerate(roots):
        for other in roots[index + 1 :]:
            if root.resolve().is_relative_to(other.resolve()) or other.resolve().is_relative_to(
                root.resolve()
            ):
                raise ValueError("Resolved runtime roots must not overlap")
    for path in (paths["data"] / "tools", paths["data"] / "tools/bin"):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"Managed tools directory is redirected: {path}")


def command_output(argv: list[str]) -> str:
    """Run a bounded version probe; return an empty result for unusable executables."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        return result.stdout + result.stderr if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


@contextmanager
def operation_lock(paths: dict[str, Path]) -> Iterator[None]:
    """Serialize operations on the state parent, which survives profile purge."""
    parent = paths["state"].parent
    parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(parent.resolve(), os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another profile setup operation is running") from error
        yield
    finally:
        os.close(descriptor)


def version_of(executable: str, flag: str = "--version") -> tuple[int, ...]:
    """Parse a numeric executable version, or return an empty tuple on failure."""
    found = re.search(r"\b(?:v)?(\d+)\.(\d+)(?:\.(\d+))?", command_output([executable, flag]))
    return tuple(int(part or 0) for part in found.groups()) if found else ()


def prerequisites(host: str) -> list[str]:
    """Check external prerequisites, including the JVM selected by the JDTLS wrapper."""
    missing = []
    for name in (
        "git",
        "cc",
        "c++",
        "make",
        "npm",
        "python3",
        "rg",
        "fd",
        "curl",
        "tar",
        "gzip",
        "unzip",
    ):
        if not shutil.which(name):
            missing.append(name)
    if host == "macos-arm64" and not command_output(["xcode-select", "-p"]).strip():
        missing.append("Command Line Tools (run xcode-select --install)")
    if version_of(shutil.which("node") or "node") < (22, 0, 0):
        missing.append("Node.js >=22")
    if version_of(shutil.which("python3") or "python3") < (3, 9, 0):
        missing.append("python3 >=3.9 for JDTLS")
    java_home = os.environ.get("JAVA_HOME")
    java = Path(java_home) / "bin/java" if java_home else None
    java_cmd = str(java) if java and java.is_file() else (shutil.which("java") or "java")
    output = command_output([java_cmd, "-version"])
    major = re.search(r'version\s+"(\d+)', output)
    if not major or int(major[1]) < 21:
        missing.append("Java >=21 (check JAVA_HOME)")
    if host == "linux-x86_64" and not all(shutil.which(name) for name in ("wl-copy", "wl-paste")):
        missing.append("wl-clipboard")
    return missing


def tool_executable(paths: dict[str, Path], name: str, spec: dict, host: str) -> Path:
    """Return the expected executable inside a versioned, profile-owned installation."""
    artifact = spec["platforms"][host]
    return paths["data"] / "tools" / name / spec["version"] / artifact["executable"]


def make_plan(paths: dict[str, Path], host: str, manifest: dict, install_tools: bool) -> dict:
    """Build a read-only installation plan, retaining every conflict and missing dependency."""
    guard_roots(paths)
    errors = []
    links = []
    for path, target in expected_links(paths).items():
        if os.path.lexists(path) and not matches_link(path, target):
            errors.append(f"Conflicting destination: {path}")
        else:
            links.append(
                {"path": str(path), "target": str(target), "create": not path.is_symlink()}
            )
    tools = []
    for name, spec in manifest.items():
        alias = paths["data"] / "tools/bin" / name
        managed = tool_executable(paths, name, spec, host)
        package = paths["data"] / "tools" / name / spec["version"]
        if package.parent.is_symlink() or package.is_symlink():
            errors.append(f"Redirected managed package directory: {package}")
            continue
        if os.path.lexists(alias) and not matches_link(alias, managed):
            # Being under tools/ is not proof an alias belongs to this manifest.
            errors.append(f"Conflicting managed executable link: {alias}")
            continue
        current = str(alias) if alias.is_symlink() else shutil.which(name)
        usable = current and version_of(current) >= tuple(map(int, spec["minimum"].split(".")))
        if usable:
            tools.append({"name": name, "path": current, "install": False})
        elif install_tools:
            tools.append({"name": name, "path": str(managed), "install": True})
        else:
            errors.append(f"{name} >= {spec['minimum']} is required; use --install-tools")
    missing = prerequisites(host)
    if missing:
        errors.append("Missing prerequisites: " + ", ".join(missing))
    return {
        "platform": host,
        "links": links,
        "tools": tools,
        "errors": errors,
        "prerequisite_command": FEDORA_PACKAGES if host == "linux-x86_64" else MAC_PACKAGES,
    }


def extract_archive(source: Path, destination: Path, kind: str, executable: str) -> None:
    """Extract release bytes without permitting links, special files, or path traversal."""

    def safe_name(name: str) -> None:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError(f"Unsafe archive path: {name}")

    if kind == "gzip":
        with gzip.open(source, "rb") as src, (destination / executable).open("wb") as dst:
            shutil.copyfileobj(src, dst)
    elif kind == "tar":
        with tarfile.open(source) as archive:
            for member in archive.getmembers():
                safe_name(member.name)
                if not (member.isdir() or member.isfile()):
                    raise ValueError(f"Unsupported archive link or special file: {member.name}")
            archive.extractall(destination, filter="data")
    elif kind == "zip":
        with zipfile.ZipFile(source) as archive:
            for member in archive.infolist():
                safe_name(member.filename)
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode) or (
                    stat.S_IFMT(mode) and not (stat.S_ISDIR(mode) or stat.S_ISREG(mode))
                ):
                    raise ValueError(f"Unsupported zip entry: {member.filename}")
            archive.extractall(destination)
    else:
        raise ValueError(f"Unknown archive format: {kind}")


def install_tool(paths: dict[str, Path], name: str, spec: dict, host: str) -> None:
    """Verify an official archive and atomically publish a complete managed tool."""
    artifact = spec["platforms"][host]
    executable = tool_executable(paths, name, spec, host)
    package = paths["data"] / "tools" / name / spec["version"]
    marker = package / ".archive-sha256"
    for parent in (package.parent, package):
        if parent.is_symlink():
            raise ValueError(f"Redirected installation directory: {parent}")
    if package.exists():
        if (
            not marker.is_file()
            or marker.read_text().strip() != artifact["sha256"]
            or version_of(str(executable)) != tuple(map(int, spec["version"].split(".")))
        ):
            raise ValueError(
                f"Unknown or incomplete installation: {package}; inspect it before retrying"
            )
    else:
        cache = paths["cache"] / "downloads"
        if cache.is_symlink():
            raise ValueError(f"Redirected download cache: {cache}")
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / artifact["sha256"]
        if not os.path.lexists(archive):
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as tmp:
                temporary = Path(tmp.name)
                try:
                    with urllib.request.urlopen(artifact["url"], timeout=60) as response:
                        shutil.copyfileobj(response, tmp)
                    tmp.flush()
                    if hashlib.sha256(temporary.read_bytes()).hexdigest() != artifact["sha256"]:
                        raise ValueError(f"Checksum mismatch for {name}")
                    os.replace(temporary, archive)
                finally:
                    temporary.unlink(missing_ok=True)
        if (
            archive.is_symlink()
            or hashlib.sha256(archive.read_bytes()).hexdigest() != artifact["sha256"]
        ):
            raise ValueError(f"Invalid download cache: {archive}")
        package.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=package.parent) as tmp:
            stage = Path(tmp) / "payload"
            stage.mkdir()
            extract_archive(archive, stage, artifact["format"], artifact["executable"])
            binary = stage / artifact["executable"]
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
            if version_of(str(binary)) != tuple(map(int, spec["version"].split("."))):
                raise ValueError(f"Downloaded {name} failed its version probe")
            (stage / ".archive-sha256").write_text(artifact["sha256"] + "\n")
            if os.path.lexists(package):
                raise ValueError(f"Installation destination appeared concurrently: {package}")
            stage.rename(package)
    alias = paths["data"] / "tools/bin" / name
    alias.parent.mkdir(parents=True, exist_ok=True)
    if not matches_link(alias, executable):
        alias.symlink_to(executable)


def read_receipt(paths: dict[str, Path]) -> dict | None:
    """Read installer ownership only if it matches the current repository and roots."""
    file = paths["state"] / "setup.json"
    if file.is_symlink():
        raise ValueError(f"Redirected setup receipt: {file}")
    if not file.exists():
        return None
    receipt = json.loads(file.read_text())
    if not isinstance(receipt, dict):
        raise ValueError("Invalid setup receipt; expected an ownership object")
    expected = {kind: str(path) for kind, path in paths.items()}
    if (
        receipt.get("schema") != 1
        or receipt.get("repository") != str(REPO)
        or receipt.get("paths") != expected
    ):
        raise ValueError("Setup receipt belongs to a different repository or profile roots")
    return receipt


def write_receipt(paths: dict[str, Path], tools: list[dict]) -> None:
    """Atomically persist ownership before the potentially partial plugin installation."""
    paths["state"].mkdir(parents=True, exist_ok=True)
    selected = [
        {
            "name": t["name"],
            "path": str(paths["data"] / "tools/bin" / t["name"]) if t["install"] else t["path"],
        }
        for t in tools
    ]
    payload = {
        "schema": 1,
        "repository": str(REPO),
        "paths": {k: str(v) for k, v in paths.items()},
        "tools": selected,
    }
    if read_receipt(paths) == payload:
        return
    with tempfile.NamedTemporaryFile(mode="w", dir=paths["state"], delete=False) as file:
        tmp = Path(file.name)
        try:
            json.dump(payload, file, indent=2)
            file.flush()
            os.replace(tmp, paths["state"] / "setup.json")
        finally:
            tmp.unlink(missing_ok=True)


def run_editor(lua: str, paths: dict[str, Path]) -> None:
    """Run an explicit headless operation and propagate failures to the caller."""
    env = os.environ.copy()
    env["NVIM_CONFIG_OPERATION"] = (
        "restore"
        if lua == "scripts/restore.lua"
        else "install"
        if lua == "scripts/install.lua"
        else "verify"
    )
    subprocess.run(
        [str(REPO / "bin/nv"), "--headless", "-i", "NONE", "+luafile " + lua],
        cwd=REPO,
        env=env,
        check=True,
        timeout=1200,
    )


def apply(paths: dict[str, Path], host: str, manifest: dict, install_tools: bool) -> None:
    """Apply a preflighted plan without replacing existing files or global executables."""
    plan = make_plan(paths, host, manifest, install_tools)
    print(json.dumps(plan, indent=2), flush=True)
    if plan["errors"]:
        raise ValueError("Resolve the reported prerequisites/conflicts before applying")
    read_receipt(paths)
    for tool in plan["tools"]:
        if tool["install"]:
            install_tool(paths, tool["name"], manifest[tool["name"]], host)
    guard_roots(paths)
    for path, target in expected_links(paths).items():
        if not matches_link(path, target):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target)
    write_receipt(paths, plan["tools"])
    run_editor("scripts/restore.lua", paths)
    run_editor("scripts/install.lua", paths)


def verify(paths: dict[str, Path], host: str, manifest: dict, lsp: bool) -> None:
    """Check existing installations before starting Neovim without download side effects."""
    plan = make_plan(paths, host, manifest, False)
    if plan["errors"]:
        raise ValueError("; ".join(plan["errors"]))
    if read_receipt(paths) is None:
        raise ValueError("No setup receipt; run apply to adopt this profile")
    for path, target in expected_links(paths).items():
        if not matches_link(path, target):
            raise ValueError(f"Missing managed link: {path}")
    lock = json.loads((REPO / "lazy-lock.json").read_text())
    for name, revision in lock.items():
        source = paths["data"] / "lazy" / name
        actual = command_output(["git", "-C", str(source), "rev-parse", "HEAD"]).strip()
        if actual != revision["commit"]:
            raise ValueError(f"Plugin {name} differs from lazy-lock.json; run apply")
    subprocess.run(
        [plan_tool["path"] for plan_tool in plan["tools"] if plan_tool["name"] == "stylua"]
        + ["--check", "."],
        cwd=REPO,
        check=True,
    )
    run_editor("scripts/verify.lua", paths)
    run_editor("tests/check.lua", paths)
    if lsp:
        print("Running LSP checks; Java imports may download build metadata", flush=True)
        run_editor("tests/lsp.lua", paths)
    if host == "linux-x86_64":
        print(
            "Wayland clipboard/font appearance requires a graphical session; not proven by headless checks"
        )
    print("Profile verification passed")


def remove(paths: dict[str, Path], purge: bool) -> None:
    """Disconnect recognized links; purge only validated, recorded runtime roots."""
    guard_roots(paths)
    if read_receipt(paths) is None:
        raise ValueError("No matching setup receipt; refusing removal")
    links = expected_links(paths)
    for path, target in links.items():
        if os.path.lexists(path) and not matches_link(path, target):
            raise ValueError(f"Changed destination; refusing removal: {path}")
    roots = [paths[k] for k in ("data", "cache", "state")] if purge else []
    identities = {
        root: (root.stat().st_dev, root.stat().st_ino) if root.exists() else None for root in roots
    }
    print(
        json.dumps({"unlink": [str(p) for p in links], "purge": [str(p) for p in roots]}, indent=2),
        flush=True,
    )
    for path, target in links.items():
        if os.path.lexists(path):
            if not matches_link(path, target):
                raise ValueError(f"Destination changed during removal: {path}")
            path.unlink()
    for root in roots:
        guard_roots(paths)
        if root.exists():
            if (root.stat().st_dev, root.stat().st_ino) != identities[root]:
                raise ValueError(f"Runtime directory changed during removal: {root}")
            shutil.rmtree(root)


def main() -> int:
    """Dispatch the documented CLI and turn actionable setup failures into exit code 1."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "apply"):
        commands.add_parser(name).add_argument("--install-tools", action="store_true")
    commands.add_parser("verify").add_argument("--lsp", action="store_true")
    commands.add_parser("remove").add_argument("--purge", action="store_true")
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 12):
            raise ValueError("Python 3.12+ is required")
        host = host_platform()
        paths = profile_paths()
        manifest = json.loads((REPO / "manifests/tools.json").read_text())
        if args.command == "plan":
            plan = make_plan(paths, host, manifest, args.install_tools)
            print(json.dumps(plan, indent=2))
            return int(bool(plan["errors"]))
        guard_roots(paths)
        if args.command == "apply":
            preflight = make_plan(paths, host, manifest, args.install_tools)
            if preflight["errors"]:
                print(json.dumps(preflight, indent=2))
                raise ValueError("Resolve the reported prerequisites/conflicts before applying")
        elif read_receipt(paths) is None:
            raise ValueError("No matching setup receipt; run apply first")
        with operation_lock(paths):
            if args.command == "apply":
                apply(paths, host, manifest, args.install_tools)
            elif args.command == "verify":
                verify(paths, host, manifest, args.lsp)
            else:
                remove(paths, args.purge)
        return 0
    except (
        ValueError,
        OSError,
        subprocess.SubprocessError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        print(
            "Completed downloads/links may remain; inspect plan before retry. No system packages were changed.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
