#!/usr/bin/env python3
"""Offline checks for independent release updates.

These tests do not call the GitHub API. CI runs this file so a failure in
one program cannot silently block the others again.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import update_tap


class ExecuteTests(unittest.TestCase):
    def test_one_failure_keeps_the_other_updates_and_names_the_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lux = root / "lux.rb"
            ownterm = root / "ownterm.rb"
            omega = root / "omega.rb"
            lux.write_text("old-lux")
            ownterm.write_text("old-ownterm")
            omega.write_text("old-omega")

            def ok_lux() -> str:
                lux.write_text("new-lux")
                return "v1.3.1 unchanged (Casks/lux.rb)"

            def bad_ownterm() -> str:
                ownterm.write_text("partial-ownterm")
                raise update_tap.UpdateError("ownterm has no published release")

            def ok_omega() -> str:
                omega.write_text("new-omega")
                return "v0.11.0 updated (Formula/omega.rb)"

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = update_tap.execute(
                    [
                        ("lux", ok_lux, [lux]),
                        ("ownterm", bad_ownterm, [ownterm]),
                        ("omega", ok_omega, [omega]),
                    ]
                )

            self.assertEqual(code, 1)
            self.assertEqual(lux.read_text(), "new-lux")
            self.assertEqual(ownterm.read_text(), "old-ownterm")
            self.assertEqual(omega.read_text(), "new-omega")
        summary = stdout.getvalue()
        self.assertIn("summary:", summary)
        self.assertIn("lux: ok: v1.3.1 unchanged (Casks/lux.rb)", summary)
        self.assertIn("ownterm: failed: ownterm has no published release", summary)
        self.assertIn("omega: ok: v0.11.0 updated (Formula/omega.rb)", summary)
        self.assertIn("1 program failed", summary)
        self.assertIn("ownterm: failed: ownterm has no published release", stderr.getvalue())

    def test_created_file_is_removed_when_that_program_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = Path(tmp) / "Casks" / "ownterm.rb"

            def fail() -> str:
                created.parent.mkdir()
                created.write_text("new cask")
                raise update_tap.UpdateError("missing asset ownterm-macos-universal.dmg")

            code = update_tap.execute([("ownterm", fail, [created])])
            self.assertEqual(code, 1)
            self.assertFalse(created.exists())

    def test_all_ok(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = update_tap.execute(
                [
                    ("lux", lambda: "v1.3.1 unchanged", []),
                    ("omega", lambda: "v0.11.0 unchanged", []),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn("all ok", stdout.getvalue())
        self.assertNotIn("failed", stdout.getvalue())


class LatestReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_fetch = update_tap.fetch

    def tearDown(self) -> None:
        update_tap.fetch = self.original_fetch

    def test_reads_releases_latest_not_the_newest_tag(self) -> None:
        seen: list[str] = []

        def fake_fetch(url: str) -> bytes:
            seen.append(url)
            self.assertNotIn("/tags", url)
            body = {
                "tag_name": "v0.11.0",
                "draft": False,
                "prerelease": False,
                "assets": [],
            }
            return json.dumps(body).encode()

        update_tap.fetch = fake_fetch
        release = update_tap.latest_release("omega")
        self.assertEqual(release["tag_name"], "v0.11.0")
        self.assertEqual(
            seen,
            ["https://api.github.com/repos/lcajigasm/omega/releases/latest"],
        )

    def test_draft_is_rejected(self) -> None:
        def fake_fetch(url: str) -> bytes:
            return json.dumps(
                {"tag_name": "v0.6.0", "draft": True, "prerelease": False}
            ).encode()

        update_tap.fetch = fake_fetch
        with self.assertRaises(update_tap.UpdateError) as caught:
            update_tap.latest_release("ownterm")
        self.assertIn("draft", str(caught.exception))

    def test_missing_release_is_a_program_error(self) -> None:
        def fake_fetch(url: str) -> bytes:
            raise update_tap.UpdateError(f"HTTP 404 for {url}: missing")

        update_tap.fetch = fake_fetch
        with self.assertRaises(update_tap.UpdateError) as caught:
            update_tap.latest_release("ownterm")
        self.assertIn("ownterm has no published release", str(caught.exception))


class DryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved = {
            name: getattr(update_tap, name)
            for name in ("latest_release", "update_lux", "update_ownterm", "update_omega", "declared_version", "packaged_path")
        }

    def tearDown(self) -> None:
        for name, value in self.saved.items():
            setattr(update_tap, name, value)

    def test_dry_run_does_not_rewrite_and_isolates_a_mismatch(self) -> None:
        calls: list[str] = []

        def updater(release: dict, sums: dict) -> bool:
            calls.append("rewrite")
            return True

        def release(repo: str) -> dict:
            tag = "v9.9.9" if repo == "omega" else "v1.0.0"
            return {"tag_name": tag, "draft": False, "prerelease": False, "assets": []}

        update_tap.latest_release = release
        update_tap.update_lux = updater
        update_tap.update_ownterm = updater
        update_tap.update_omega = updater
        update_tap.packaged_path = lambda repo: update_tap.ROOT / f"{repo}.rb"
        update_tap.declared_version = lambda path: "1.0.0"

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = update_tap.main(["--dry-run"])

        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        text = stdout.getvalue()
        self.assertIn("lux: ok:", text)
        self.assertIn("ownterm: ok:", text)
        self.assertIn("omega: failed: omega.rb is 1.0.0, omega latest release is v9.9.9", text)
        self.assertIn("1 program failed", text)


if __name__ == "__main__":
    unittest.main()
