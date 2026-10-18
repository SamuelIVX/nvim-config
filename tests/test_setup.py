"""Installer contracts using disposable homes, fake tools, and controlled downloads."""

import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("nvim_setup", Path(__file__).parents[1] / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class InstallerTest(unittest.TestCase):
    """Exercise the installer without changing the user's home or contacting services."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nvim setup test ")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / "checkout"
        (self.repo / "bin").mkdir(parents=True)
        self.environment = patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "XDG_CONFIG_HOME": "",
                "XDG_DATA_HOME": "",
                "XDG_STATE_HOME": "",
                "XDG_CACHE_HOME": "",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.repo_patch = patch.object(setup, "REPO", self.repo)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)
        self.paths = setup.profile_paths()
        self.tool = {
            "version": "0.12.5",
            "minimum": "0.12.0",
            "platforms": {
                "macos-arm64": {
                    "url": "https://example.invalid/nvim.gz",
                    "format": "gzip",
                    "executable": "nvim",
                    "sha256": "",
                }
            },
        }
        self.manifest = {"nvim": self.tool}
        self.download = patch.object(
            setup.urllib.request, "urlopen", side_effect=AssertionError("Unexpected network access")
        )
        self.download.start()
        self.addCleanup(self.download.stop)

    def prepare_receipt(self):
        for link, target in setup.expected_links(self.paths).items():
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
        setup.write_receipt(self.paths, [])

    def fake_archive(self):
        payload = gzip.compress(b"#!/bin/sh\nprintf 'NVIM v0.12.5\\n'\n")
        self.tool["platforms"]["macos-arm64"]["sha256"] = hashlib.sha256(payload).hexdigest()
        return payload

    def test_preview_does_not_write_or_download(self):
        before = sorted(str(p) for p in self.home.rglob("*"))
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value=None),
        ):
            plan = setup.make_plan(self.paths, "macos-arm64", self.manifest, True)
        self.assertEqual(plan["errors"], [])
        self.assertTrue(plan["tools"][0]["install"])
        self.assertEqual(before, sorted(str(p) for p in self.home.rglob("*")))

    def test_existing_compatible_tool_is_preserved(self):
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value="/existing/nvim"),
            patch.object(setup, "version_of", return_value=(0, 13, 0)),
        ):
            plan = setup.make_plan(self.paths, "macos-arm64", self.manifest, True)
        self.assertFalse(plan["tools"][0]["install"])
        self.assertEqual(plan["tools"][0]["path"], "/existing/nvim")

    def test_old_tool_needs_explicit_install_flag(self):
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value="/existing/nvim"),
            patch.object(setup, "version_of", return_value=(0, 11, 6)),
        ):
            self.assertTrue(
                setup.make_plan(self.paths, "macos-arm64", self.manifest, False)["errors"]
            )
            self.assertTrue(
                setup.make_plan(self.paths, "macos-arm64", self.manifest, True)["tools"][0][
                    "install"
                ]
            )

    def test_platform_detection_rejects_atomic_and_other_releases(self):
        with (
            patch.object(setup.platform, "system", return_value="Linux"),
            patch.object(setup.platform, "machine", return_value="x86_64"),
            patch.object(
                setup.platform,
                "freedesktop_os_release",
                return_value={"ID": "fedora", "VERSION_ID": "43"},
            ),
            patch.object(Path, "exists", return_value=False),
        ):
            self.assertEqual(setup.host_platform(), "linux-x86_64")
            with patch.object(
                setup.platform,
                "freedesktop_os_release",
                return_value={"ID": "fedora", "VERSION_ID": "43", "VARIANT_ID": "kinoite"},
            ):
                self.assertRaisesRegex(ValueError, "Atomic", setup.host_platform)
            with patch.object(
                setup.platform,
                "freedesktop_os_release",
                return_value={"ID": "fedora", "VERSION_ID": "44"},
            ):
                self.assertRaisesRegex(ValueError, "Unsupported", setup.host_platform)

    def test_mac_architecture_detection(self):
        with (
            patch.object(setup.platform, "system", return_value="Darwin"),
            patch.object(setup.platform, "machine", return_value="arm64"),
        ):
            self.assertEqual(setup.host_platform(), "macos-arm64")
        with (
            patch.object(setup.platform, "system", return_value="Darwin"),
            patch.object(setup.platform, "machine", return_value="x86_64"),
        ):
            self.assertRaises(ValueError, setup.host_platform)

    def test_relative_and_overlapping_xdg_roots_rejected(self):
        with patch.dict(os.environ, {"XDG_DATA_HOME": "relative"}):
            self.assertRaises(ValueError, setup.profile_paths)
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.home / ".config")}):
            self.assertRaises(ValueError, setup.profile_paths)

    def test_custom_xdg_paths_with_spaces(self):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.home / "custom data")}):
            self.assertEqual(setup.profile_paths()["data"], self.home / "custom data/nvim-sam")

    def test_link_conflict_prevents_any_apply_changes(self):
        self.paths["config"].mkdir(parents=True)
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value="/existing/nvim"),
            patch.object(setup, "version_of", return_value=(0, 12, 5)),
        ):
            self.assertRaises(
                ValueError, setup.apply, self.paths, "macos-arm64", self.manifest, True
            )
        self.assertFalse(self.paths["launcher"].exists())
        self.assertFalse(self.paths["state"].exists())

    def test_matching_links_and_repeat_apply_keep_receipt_stable(self):
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value="/existing/nvim"),
            patch.object(setup, "version_of", return_value=(0, 12, 5)),
            patch.object(setup, "run_editor"),
        ):
            setup.apply(self.paths, "macos-arm64", self.manifest, False)
            receipt = self.paths["state"] / "setup.json"
            before = receipt.stat().st_mtime_ns
            setup.apply(self.paths, "macos-arm64", self.manifest, False)
            self.assertEqual(before, receipt.stat().st_mtime_ns)
        for link, target in setup.expected_links(self.paths).items():
            self.assertTrue(setup.matches_link(link, target))

    def test_verified_download_is_published_and_reused(self):
        payload = self.fake_archive()
        with patch.object(
            setup.urllib.request, "urlopen", return_value=io.BytesIO(payload)
        ) as network:
            setup.install_tool(self.paths, "nvim", self.tool, "macos-arm64")
            self.assertEqual(network.call_count, 1)
        alias = self.paths["data"] / "tools/bin/nvim"
        self.assertEqual(setup.version_of(str(alias)), (0, 12, 5))
        setup.install_tool(self.paths, "nvim", self.tool, "macos-arm64")
        self.assertTrue(alias.is_symlink())

    def test_bad_checksum_does_not_publish_executable(self):
        self.fake_archive()
        with patch.object(setup.urllib.request, "urlopen", return_value=io.BytesIO(b"bad bytes")):
            self.assertRaisesRegex(
                ValueError,
                "Checksum",
                setup.install_tool,
                self.paths,
                "nvim",
                self.tool,
                "macos-arm64",
            )
        self.assertFalse((self.paths["data"] / "tools/bin/nvim").exists())

    def test_interrupted_download_can_retry(self):
        payload = self.fake_archive()
        with patch.object(setup.urllib.request, "urlopen", side_effect=OSError("interrupted")):
            self.assertRaises(
                OSError, setup.install_tool, self.paths, "nvim", self.tool, "macos-arm64"
            )
        self.assertEqual(list((self.paths["cache"] / "downloads").iterdir()), [])
        with patch.object(setup.urllib.request, "urlopen", return_value=io.BytesIO(payload)):
            setup.install_tool(self.paths, "nvim", self.tool, "macos-arm64")

    def test_incomplete_tool_directory_is_not_overwritten(self):
        package = self.paths["data"] / "tools/nvim/0.12.5"
        package.mkdir(parents=True)
        (package / "personal").write_text("keep")
        self.assertRaisesRegex(
            ValueError,
            "incomplete",
            setup.install_tool,
            self.paths,
            "nvim",
            self.tool,
            "macos-arm64",
        )
        self.assertEqual((package / "personal").read_text(), "keep")

    def test_tar_traversal_links_and_special_files_are_rejected(self):
        for name, kind in [
            ("../escape", tarfile.REGTYPE),
            ("/absolute", tarfile.REGTYPE),
            ("link", tarfile.SYMTYPE),
            ("hard", tarfile.LNKTYPE),
            ("fifo", tarfile.FIFOTYPE),
        ]:
            with self.subTest(name=name):
                source = self.home / "malicious.tar"
                with tarfile.open(source, "w") as archive:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.linkname = "../../escape"
                    archive.addfile(member)
                self.assertRaises(
                    ValueError, setup.extract_archive, source, self.repo, "tar", "nvim"
                )
        self.assertFalse((self.home / "escape").exists())

    def test_zip_traversal_and_symlink_rejected(self):
        for name, mode in [("../escape", 0), ("/absolute", 0), ("link", 0o120777 << 16)]:
            source = self.home / "malicious.zip"
            with zipfile.ZipFile(source, "w") as archive:
                info = zipfile.ZipInfo(name)
                info.external_attr = mode
                archive.writestr(info, "../../escape")
            self.assertRaises(ValueError, setup.extract_archive, source, self.repo, "zip", "nvim")

    def test_unknown_managed_alias_is_a_conflict(self):
        alias = self.paths["data"] / "tools/bin/nvim"
        alias.parent.mkdir(parents=True)
        alias.symlink_to(self.home / "someone-elses-binary")
        with patch.object(setup, "prerequisites", return_value=[]):
            self.assertTrue(
                setup.make_plan(self.paths, "macos-arm64", self.manifest, True)["errors"]
            )

    def test_remove_preserves_repository_and_downloads(self):
        self.prepare_receipt()
        self.paths["data"].mkdir(parents=True)
        (self.paths["data"] / "keep").write_text("runtime")
        setup.remove(self.paths, False)
        self.assertTrue(self.repo.is_dir())
        self.assertTrue((self.paths["data"] / "keep").is_file())
        self.assertFalse(os.path.lexists(self.paths["config"]))

    def test_purge_does_not_follow_nested_symlinks(self):
        self.prepare_receipt()
        external = self.home / "external"
        external.mkdir()
        (external / "keep").write_text("user data")
        self.paths["data"].mkdir(parents=True)
        (self.paths["data"] / "link").symlink_to(external)
        default = self.home / ".local/share/nvim"
        default.mkdir(parents=True)
        setup.remove(self.paths, True)
        self.assertTrue((external / "keep").is_file())
        self.assertTrue(default.is_dir())
        self.assertTrue(self.repo.is_dir())
        self.assertFalse(self.paths["state"].exists())

    def test_purge_rejects_redirected_root_before_unlinking(self):
        self.prepare_receipt()
        self.paths["data"].parent.mkdir(parents=True, exist_ok=True)
        self.paths["data"].symlink_to(self.repo)
        self.assertRaises(ValueError, setup.remove, self.paths, True)
        self.assertTrue(self.paths["config"].is_symlink())

    def test_remove_rejects_changed_destination_and_forged_receipt(self):
        self.prepare_receipt()
        self.paths["launcher"].unlink()
        self.paths["launcher"].write_text("new user script")
        self.assertRaises(ValueError, setup.remove, self.paths, True)
        self.assertTrue(self.paths["config"].is_symlink())
        file = self.paths["state"] / "setup.json"
        receipt = json.loads(file.read_text())
        receipt["paths"]["data"] = str(self.repo)
        file.write_text(json.dumps(receipt))
        self.assertRaises(ValueError, setup.read_receipt, self.paths)

    def test_jdtls_java_home_takes_precedence(self):
        jdk = self.home / "jdk/bin"
        jdk.mkdir(parents=True)
        (jdk / "java").touch()

        def probe(argv):
            return 'openjdk version "17.0.0"' if argv[0] == str(jdk / "java") else ""

        with (
            patch.dict(os.environ, {"JAVA_HOME": str(jdk.parent)}),
            patch.object(setup.shutil, "which", return_value="/usr/bin/tool"),
            patch.object(setup, "version_of", return_value=(25, 0, 0)),
            patch.object(setup, "command_output", side_effect=probe),
        ):
            self.assertIn("Java >=21 (check JAVA_HOME)", setup.prerequisites("macos-arm64"))

    def test_mac_compiler_stubs_do_not_prove_command_line_tools_are_installed(self):
        def probe(argv):
            return 'openjdk version "21.0.1"' if argv[-1] == "-version" else ""

        with (
            patch.object(setup.shutil, "which", return_value="/usr/bin/tool"),
            patch.object(setup, "version_of", return_value=(25, 0, 0)),
            patch.object(setup, "command_output", side_effect=probe),
        ):
            self.assertIn(
                "Command Line Tools (run xcode-select --install)",
                setup.prerequisites("macos-arm64"),
            )

    def test_launcher_scopes_managed_path_and_forwards_arguments(self):
        launcher = Path(__file__).parents[1] / "bin/nv"
        binary = self.paths["data"] / "tools/bin/nvim"
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nprintf "%s\\n" "$NVIM_APPNAME" "$1"\n')
        binary.chmod(0o755)
        result = subprocess.run(
            [str(launcher), "file with spaces"], capture_output=True, text=True, check=True
        )
        self.assertEqual(result.stdout.splitlines(), ["nvim-sam", "file with spaces"])
        self.assertNotIn(str(binary.parent), os.environ["PATH"].split(os.pathsep))

    def test_operation_lock_blocks_a_second_process(self):
        with setup.operation_lock(self.paths):
            code = "import os,fcntl,sys; fd=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY); fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)"
            result = subprocess.run(
                [sys.executable, "-c", code, str(self.paths["state"].parent)], capture_output=True
            )
            self.assertNotEqual(result.returncode, 0)
        with setup.operation_lock(self.paths):
            pass

    def test_verify_missing_plugin_fails_without_starting_editor(self):
        self.prepare_receipt()
        (self.repo / "lazy-lock.json").write_text('{"lazy.nvim":{"commit":"expected"}}')
        with (
            patch.object(setup, "prerequisites", return_value=[]),
            patch.object(setup.shutil, "which", return_value="/existing/nvim"),
            patch.object(setup, "version_of", return_value=(2, 0, 0)),
            patch.object(setup, "command_output", return_value=""),
            patch.object(setup, "run_editor") as editor,
        ):
            self.assertRaisesRegex(
                ValueError, "Plugin", setup.verify, self.paths, "macos-arm64", self.manifest, False
            )
            editor.assert_not_called()

    def test_cached_download_symlink_is_rejected(self):
        self.fake_archive()
        cache = self.paths["cache"] / "downloads"
        cache.mkdir(parents=True)
        digest = self.tool["platforms"]["macos-arm64"]["sha256"]
        (cache / digest).symlink_to(self.home / "missing")
        self.assertRaisesRegex(
            ValueError,
            "Invalid download cache",
            setup.install_tool,
            self.paths,
            "nvim",
            self.tool,
            "macos-arm64",
        )
        self.assertTrue((cache / digest).is_symlink())

    def test_runtime_roots_cannot_contain_source(self):
        with patch.object(setup, "REPO", (self.paths["data"] / "checkout").resolve()):
            self.assertRaisesRegex(ValueError, "repository", setup.guard_roots, self.paths)

    def test_manifest_has_complete_pins_for_both_targets(self):
        source = Path(__file__).parents[1] / "manifests/tools.json"
        manifest = json.loads(source.read_text())
        self.assertEqual(set(manifest), {"nvim", "tree-sitter", "stylua"})
        for tool in manifest.values():
            self.assertEqual(set(tool["platforms"]), {"linux-x86_64", "macos-arm64"})
            for artifact in tool["platforms"].values():
                self.assertRegex(artifact["sha256"], r"^[a-f0-9]{64}$")
                self.assertTrue(artifact["url"].startswith("https://github.com/"))
                self.assertNotIn("latest", artifact["url"])


if __name__ == "__main__":
    unittest.main()
