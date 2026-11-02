#!/usr/bin/env python3
"""Refresh this tap from the public GitHub release API.

Each repository is updated from its latest published release
(``/releases/latest``). That endpoint skips drafts and prereleases. A
newer git tag with no release is ignored, so one repository cannot block
the others.

Programs are independent. A failure restores only that program's files.
The others keep their rewrite. The process then exits 1 and prints a
summary naming each failure and its reason. The workflow commits the
successful rewrites and still fails the job. It does not commit when
every program failed or nothing changed.

Checksums come from the release asset SHA256SUMS. If that file omits an
asset, the script downloads the asset and hashes it. A digest published on
the asset itself must match.

No personal access token is required. When GITHUB_TOKEN is set (the token
GitHub Actions injects into this repository), it is sent only to raise the
public API rate limit. Unauthenticated requests work the same way.

ownterm packaging:

* Today the release ships ownterm-macos-arm64.tar.gz and
  ownterm-macos-x86_64.tar.gz, and this script writes Formula/ownterm.rb.
* When a release includes a disk image, this script removes that formula and
  writes Casks/ownterm.rb. Preferred asset names, in order:
  ownterm-macos-universal.dmg, OwnTerm.dmg, ownterm.dmg. Otherwise the only
  *.dmg on the release is used. The app stanza is the top-level .app inside
  the image (listed with 7z). An existing cask whose version, url and sha256
  already match is left as-is, so an unchanged release does not re-download
  the image.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "lcajigasm-homebrew-tap"
SEMVER = re.compile(r"^v(\d+\.\d+\.\d+)$")
SHA_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?\.?/?(\S+)$")

OWNTERM_DMG_PREFERENCE = (
    "ownterm-macos-universal.dmg",
    "OwnTerm.dmg",
    "ownterm.dmg",
)
LUX_DMG = "lux-macos-universal.dmg"
LUX_APP = "Lux.app"


class UpdateError(RuntimeError):
    pass


def token() -> str | None:
    value = os.environ.get("GITHUB_TOKEN", "").strip()
    return value or None


def request(url: str, auth: bool) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if auth:
        tok = token()
        if not tok:
            raise UpdateError("GITHUB_TOKEN is not set")
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        raise UpdateError(f"HTTP {exc.code} for {url}: {body}") from exc


def fetch(url: str) -> bytes:
    """Public API fetch. Falls back to GITHUB_TOKEN only after a rate limit."""
    try:
        return request(url, auth=False)
    except UpdateError as exc:
        if token() and ("HTTP 403" in str(exc) or "HTTP 429" in str(exc)):
            print("Public API rate limit; retrying with the workflow GITHUB_TOKEN.", file=sys.stderr)
            return request(url, auth=True)
        raise


def latest_release(repo: str) -> dict:
    """Latest published release. Drafts and prereleases are not used.

    GitHub's ``/releases/latest`` is the published release, not the newest
    git tag. A tag that has no release yet does not count.
    """
    url = f"https://api.github.com/repos/lcajigasm/{repo}/releases/latest"
    try:
        payload = json.loads(fetch(url).decode())
    except UpdateError as exc:
        if "HTTP 404" in str(exc):
            raise UpdateError(f"{repo} has no published release") from exc
        raise
    if not isinstance(payload, dict):
        raise UpdateError(f"{repo} latest release response is not an object")
    if payload.get("draft"):
        raise UpdateError(f"{repo} latest release is a draft")
    if payload.get("prerelease"):
        raise UpdateError(f"{repo} latest release is a prerelease")
    tag = payload.get("tag_name", "")
    if not SEMVER.fullmatch(tag):
        raise UpdateError(f"{repo} release tag {tag!r} is not vX.Y.Z")
    return payload


def version_of(release: dict) -> str:
    return SEMVER.fullmatch(release["tag_name"]).group(1)


def assets_by_name(release: dict) -> dict[str, dict]:
    return {asset["name"]: asset for asset in release.get("assets", [])}


def parse_sums(text: str) -> dict[str, str]:
    sums: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        match = SHA_LINE.match(line)
        if not match:
            raise UpdateError(f"bad SHA256SUMS line: {raw!r}")
        digest, name = match.group(1).lower(), match.group(2)
        name = name.removeprefix("./")
        sums[name] = digest
    return sums


def release_sums(release: dict) -> dict[str, str]:
    asset = assets_by_name(release).get("SHA256SUMS")
    if asset is None:
        return {}
    return parse_sums(fetch(asset["browser_download_url"]).decode())


def api_digest(asset: dict) -> str | None:
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        return digest.split(":", 1)[1].lower()
    return None


def sha256_of(release: dict, name: str, sums: dict[str, str]) -> str:
    named = assets_by_name(release)
    if name not in named:
        raise UpdateError(f"release {release['tag_name']} has no asset {name}")
    asset = named[name]
    published = api_digest(asset)
    if name in sums:
        digest = sums[name]
        if published and published != digest:
            raise UpdateError(
                f"SHA256SUMS and the asset digest disagree for {name}: {digest} vs {published}"
            )
        return digest
    print(f"SHA256SUMS has no {name}; downloading it to hash.", file=sys.stderr)
    blob = fetch(asset["browser_download_url"])
    digest = hashlib.sha256(blob).hexdigest()
    if published and published != digest:
        raise UpdateError(f"downloaded {name} does not match the asset digest")
    return digest


def download_asset(release: dict, name: str, dest: Path) -> None:
    asset = assets_by_name(release)[name]
    dest.write_bytes(fetch(asset["browser_download_url"]))


def ruby_url(repo: str, filename: str, version: str, *, interpolate: bool) -> str:
    """URL stanza.

    Casks interpolate ``#{version}`` because a cask must declare ``version``.
    Formulae embed the literal version: Homebrew treats an extra ``version``
    line as redundant when it can already read the version from the URL.
    """
    if interpolate:
        file_expr = filename.replace(version, "#{version}")
        tag = "v#{version}"
    else:
        file_expr = filename
        tag = "v" + version
    return (
        'url "https://github.com/lcajigasm/'
        + repo
        + "/releases/download/"
        + tag
        + "/"
        + file_expr
        + '"'
    )


def app_names_from_7z(listing: str) -> list[str]:
    """App bundles in a ``7z l -slt`` listing.

    7z prefixes an HFS volume (``Lux/Lux.app``) and leaves an APFS image at
    the root (``OwnTerm.app``). A bundle inside another bundle is not the
    app Homebrew copies to ``/Applications``.
    """
    apps: list[str] = []
    for line in listing.splitlines():
        if not line.startswith("Path = "):
            continue
        parts = [part for part in line[len("Path = ") :].strip().split("/") if part]
        for index, part in enumerate(parts):
            if not part.endswith(".app"):
                continue
            if any(previous.endswith(".app") for previous in parts[:index]):
                continue
            if part not in apps:
                apps.append(part)
            break
    return apps


def top_level_apps(dmg: Path) -> list[str]:
    if shutil.which("7z") is None:
        raise UpdateError("7z is required to read the .app name inside a disk image")
    output = subprocess.run(
        ["7z", "l", "-slt", str(dmg)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    apps = app_names_from_7z(output)
    if not apps:
        raise UpdateError(f"no .app found in {dmg.name}")
    return apps


def write_if_changed(path: Path, content: str) -> bool:
    if not content.endswith("\n"):
        content += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def remove_if_present(path: Path) -> bool:
    if path.is_file():
        path.unlink()
        return True
    return False


def cask_field(text: str, name: str) -> str | None:
    match = re.search(rf'^\s*{name}\s+"([^"]+)"', text, re.M)
    return match.group(1) if match else None


def cask_livecheck(asset: str) -> str:
    """Newest stable release that actually publishes this asset.

    ``:github_releases`` goes through Homebrew's authenticated GitHub client.
    A raw ``api.github.com`` livecheck URL does not, and the runner IP then
    receives HTTP 403 once the unauthenticated budget is spent. A tag can
    exist before its disk image is attached. Livecheck follows the asset so
    ``brew audit`` checks the installable release. The updater still fails
    when the highest tag is newer than that release.
    """
    return f"""livecheck do
    url :url
    strategy :github_releases do |json, regex|
      json.map do |release|
        next if release["draft"] || release["prerelease"]

        assets = release.fetch("assets", []).map {{ |asset| asset["name"] }}
        next unless assets.include?("{asset}")

        match = release["tag_name"]&.match(regex)
        next unless match

        match[1]
      end
    end
  end"""


def render_lux(version: str, sha: str) -> str:
    return f"""cask "lux" do
  version "{version}"
  sha256 "{sha}"

  {ruby_url("lux", LUX_DMG, version, interpolate=True)}
  name "Lux"
  desc "Ultra-fast native code editor"
  homepage "https://github.com/lcajigasm/lux"

  {cask_livecheck(LUX_DMG)}

  depends_on :macos

  # Bundle id dev.lux.editor. Settings live in ~/.config/lux (settings.json).
  app "{LUX_APP}"

  zap trash: [
    "~/.config/lux",
    "~/Library/Saved Application State/dev.lux.editor.savedState",
  ]

  caveats <<~EOS
    Lux is ad-hoc signed and is not notarized, so Gatekeeper quarantines the app.
    Clear the quarantine attribute after install:

      xattr -dr com.apple.quarantine /Applications/Lux.app

    Or install without quarantine:

      brew install --cask --no-quarantine lcajigasm/tap/lux
  EOS
end
"""


def render_omega(version: str, shas: dict[str, str]) -> str:
    def block(os_name: str, arch: str, goarch: str) -> str:
        filename = f"omega_{version}_{os_name}_{goarch}.tar.gz"
        return (
            f"    {arch} do\n"
            f"      {ruby_url('omega', filename, version, interpolate=False)}\n"
            f'      sha256 "{shas[filename]}"\n'
            f"    end"
        )

    return f"""class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
{block("darwin", "on_arm", "arm64")}

{block("darwin", "on_intel", "amd64")}
  end

  on_linux do
{block("linux", "on_arm", "arm64")}

{block("linux", "on_intel", "amd64")}
  end

  def install
    bin.install "omega"
    generate_completions_from_executable(bin/"omega", "completion", shell_parameter_format: :cobra)
  end

  def caveats
    <<~EOS
      Configure a provider and API key with:
        omega setup
      topgrade and Mole are optional backends:
        brew install topgrade mole
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/omega --version")
    assert_match "brew", shell_output("#{{bin}}/omega steps")
  end
end
"""


def render_ownterm_formula(version: str, arm_name: str, arm_sha: str, intel_name: str, intel_sha: str) -> str:
    return f"""class Ownterm < Formula
  desc "Local-first terminal with a native AI agent"
  homepage "https://github.com/lcajigasm/ownterm"
  license "AGPL-3.0-only"

  # Tarballs until a release ships a .dmg. script/update_tap.py then deletes
  # this formula and writes Casks/ownterm.rb instead.
  depends_on :macos

  on_macos do
    on_arm do
      {ruby_url("ownterm", arm_name, version, interpolate=False)}
      sha256 "{arm_sha}"
    end

    on_intel do
      {ruby_url("ownterm", intel_name, version, interpolate=False)}
      sha256 "{intel_sha}"
    end
  end

  def install
    bin.install "ownterm", "ownterm-tui"
  end

  def caveats
    <<~EOS
      The macOS binaries are not code-signed. macOS may ask for approval in
      Privacy & Security the first time ownterm launches.

      Configuration stays outside Homebrew, under ~/.ownterm.
    EOS
  end

  test do
    output = shell_output("#{{bin}}/ownterm-tui --version")
    assert_match(/\\d/, output)
    assert_predicate bin/"ownterm", :executable?
  end
end
"""


def render_ownterm_cask(version: str, sha: str, filename: str, app: str) -> str:
    return f"""cask "ownterm" do
  version "{version}"
  sha256 "{sha}"

  {ruby_url("ownterm", filename, version, interpolate=True)}
  name "OwnTerm"
  desc "Local-first terminal with a native AI agent"
  homepage "https://github.com/lcajigasm/ownterm"

  {cask_livecheck(filename)}

  depends_on :macos

  app "{app}"

  zap trash: "~/.ownterm"

  caveats <<~EOS
    OwnTerm is not notarized, so Gatekeeper quarantines the app.
    Clear the quarantine attribute after install:

      xattr -dr com.apple.quarantine "/Applications/{app}"

    Or install without quarantine:

      brew install --cask --no-quarantine lcajigasm/tap/ownterm
  EOS
end
"""


def choose_ownterm_dmg(names: list[str]) -> str | None:
    dmgs = [name for name in names if name.lower().endswith(".dmg")]
    for preferred in OWNTERM_DMG_PREFERENCE:
        if preferred in dmgs:
            return preferred
    if not dmgs:
        return None
    if len(dmgs) == 1:
        return dmgs[0]
    raise UpdateError(
        "ownterm release has several disk images and none of "
        + ", ".join(OWNTERM_DMG_PREFERENCE)
        + f": {dmgs}"
    )


def choose_tarball(names: list[str], exact: str, markers: tuple[str, ...]) -> str:
    if exact in names:
        return exact
    matches = [
        name
        for name in names
        if name.endswith(".tar.gz")
        and ("macos" in name.lower() or "darwin" in name.lower())
        and any(marker in name.lower() for marker in markers)
    ]
    if len(matches) == 1:
        return matches[0]
    raise UpdateError(f"expected one ownterm tarball like {exact}, found {matches or names}")


def verify_lux_app(release: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dmg = Path(tmp) / LUX_DMG
        download_asset(release, LUX_DMG, dmg)
        apps = top_level_apps(dmg)
    if LUX_APP not in apps:
        raise UpdateError(f"{LUX_DMG} does not contain {LUX_APP} (found {apps})")


def update_lux(release: dict, sums: dict[str, str]) -> bool:
    version = version_of(release)
    sha = sha256_of(release, LUX_DMG, sums)
    path = ROOT / "Casks" / "lux.rb"
    current = path.read_text() if path.is_file() else ""
    same = (
        cask_field(current, "version") == version
        and cask_field(current, "sha256") == sha
        and LUX_DMG.replace(version, "#{version}") in current
    )
    if not same:
        verify_lux_app(release)
    return write_if_changed(path, render_lux(version, sha))


def update_omega(release: dict, sums: dict[str, str]) -> bool:
    version = version_of(release)
    filenames = [
        f"omega_{version}_darwin_arm64.tar.gz",
        f"omega_{version}_darwin_amd64.tar.gz",
        f"omega_{version}_linux_arm64.tar.gz",
        f"omega_{version}_linux_amd64.tar.gz",
    ]
    shas = {name: sha256_of(release, name, sums) for name in filenames}
    return write_if_changed(ROOT / "Formula" / "omega.rb", render_omega(version, shas))


def ownterm_cask_is_current(version: str, sha: str, filename: str) -> str | None:
    path = ROOT / "Casks" / "ownterm.rb"
    if not path.is_file():
        return None
    text = path.read_text()
    file_expr = filename.replace(version, "#{version}")
    if (
        cask_field(text, "version") == version
        and cask_field(text, "sha256") == sha
        and file_expr in text
    ):
        return cask_field(text, "app")
    return None


def update_ownterm(release: dict, sums: dict[str, str]) -> bool:
    version = version_of(release)
    names = list(assets_by_name(release))
    formula = ROOT / "Formula" / "ownterm.rb"
    cask = ROOT / "Casks" / "ownterm.rb"
    dmg_name = choose_ownterm_dmg(names)
    changed = False
    if dmg_name:
        sha = sha256_of(release, dmg_name, sums)
        app = ownterm_cask_is_current(version, sha, dmg_name)
        if app is None:
            with tempfile.TemporaryDirectory() as tmp:
                dmg = Path(tmp) / dmg_name
                download_asset(release, dmg_name, dmg)
                apps = top_level_apps(dmg)
            if len(apps) != 1:
                preferred = [item for item in apps if item.lower() in {"ownterm.app", "warp.app"}]
                if len(preferred) == 1:
                    apps = preferred
                else:
                    raise UpdateError(f"several apps in {dmg_name}: {apps}")
            app = apps[0]
        changed = write_if_changed(cask, render_ownterm_cask(version, sha, dmg_name, app)) or changed
        changed = remove_if_present(formula) or changed
        return changed

    arm = choose_tarball(names, "ownterm-macos-arm64.tar.gz", ("arm64", "aarch64"))
    intel = choose_tarball(names, "ownterm-macos-x86_64.tar.gz", ("x86_64", "amd64"))
    changed = write_if_changed(
        formula,
        render_ownterm_formula(
            version,
            arm,
            sha256_of(release, arm, sums),
            intel,
            sha256_of(release, intel, sums),
        ),
    )
    changed = remove_if_present(cask) or changed
    return changed


VERSION_STANZA = re.compile(r'^\s*version "(\d+\.\d+\.\d+)"\s*$', re.M)
URL_VERSION = re.compile(r"/releases/download/v(\d+\.\d+\.\d+)/")


def declared_version(path: Path) -> str:
    if not path.is_file():
        raise UpdateError(f"missing {path.relative_to(ROOT)}")
    text = path.read_text()
    found = set(VERSION_STANZA.findall(text)) | set(URL_VERSION.findall(text))
    if len(found) != 1:
        raise UpdateError(f"{path.relative_to(ROOT)} does not record a single version ({sorted(found)})")
    return found.pop()


def ownterm_path() -> Path:
    formula = ROOT / "Formula" / "ownterm.rb"
    cask = ROOT / "Casks" / "ownterm.rb"
    if formula.is_file() and not cask.is_file():
        return formula
    if cask.is_file() and not formula.is_file():
        return cask
    raise UpdateError("ownterm must be exactly one of Formula/ownterm.rb or Casks/ownterm.rb")


def packaged_path(repo: str) -> Path:
    if repo == "lux":
        return ROOT / "Casks" / "lux.rb"
    if repo == "omega":
        return ROOT / "Formula" / "omega.rb"
    if repo == "ownterm":
        return ownterm_path()
    raise UpdateError(f"unknown program {repo}")


def owned_paths(repo: str) -> list[Path]:
    if repo == "ownterm":
        return [ROOT / "Formula" / "ownterm.rb", ROOT / "Casks" / "ownterm.rb"]
    return [packaged_path(repo)]


def snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def restore(saved: dict[Path, bytes | None]) -> None:
    for path, data in saved.items():
        if data is None:
            if path.is_file():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def execute(jobs: list[tuple[str, Callable[[], str], list[Path]]]) -> int:
    """Run each program on its own.

    ``jobs`` is ``(name, work, paths)``. ``work`` returns a short success
    detail. On failure, only ``paths`` are restored. The return code is 1
    when any program failed. The summary lists every program.
    """
    results: list[str] = []
    failed = 0
    for name, work, paths in jobs:
        saved = snapshot(paths)
        try:
            detail = work()
        except (UpdateError, subprocess.CalledProcessError, urllib.error.URLError, OSError) as exc:
            restore(saved)
            failed += 1
            line = f"{name}: failed: {exc}"
            print(line, file=sys.stderr)
        else:
            line = f"{name}: ok: {detail}"
            print(line)
        results.append(line)
    print("summary:")
    for line in results:
        print(f"  {line}")
    if failed:
        noun = "program" if failed == 1 else "programs"
        print(f"{failed} {noun} failed")
        return 1
    print("all ok")
    return 0


def live_work(repo: str, updater) -> str:
    release = latest_release(repo)
    sums = release_sums(release)
    changed = updater(release, sums)
    path = packaged_path(repo)
    got = declared_version(path)
    want = version_of(release)
    rel = path.relative_to(ROOT)
    if got != want:
        raise UpdateError(f"{rel} is {got}, {repo} latest release is v{want}")
    state = "updated" if changed else "unchanged"
    return f"v{want} {state} ({rel})"


def dry_work(repo: str) -> str:
    """Compare the packaged version with the latest release. Do not write."""
    release = latest_release(repo)
    want = version_of(release)
    path = packaged_path(repo)
    got = declared_version(path)
    rel = path.relative_to(ROOT)
    if got != want:
        raise UpdateError(f"{rel} is {got}, {repo} latest release is v{want}")
    return f"v{want} matches {rel}"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = False
    if args == ["--dry-run"]:
        dry_run = True
    elif args:
        raise UpdateError(f"unknown arguments: {' '.join(args)}")
    programs = (
        ("lux", update_lux),
        ("ownterm", update_ownterm),
        ("omega", update_omega),
    )
    if dry_run:
        jobs = [(repo, (lambda repo=repo: dry_work(repo)), []) for repo, _updater in programs]
    else:
        jobs = [
            (repo, (lambda repo=repo, updater=updater: live_work(repo, updater)), owned_paths(repo))
            for repo, updater in programs
        ]
    return execute(jobs)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (UpdateError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
