#!/usr/bin/env python3
"""Refresh this tap from the public GitHub release API.

Reads the latest non-draft, non-prerelease release of lcajigasm/lux,
lcajigasm/ownterm and lcajigasm/omega. Rewrites version, url and sha256 in
the cask or formula. Does not commit. The workflow commits only when this
script changes a file.

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
    url = f"https://api.github.com/repos/lcajigasm/{repo}/releases/latest"
    payload = json.loads(fetch(url).decode())
    if payload.get("draft") or payload.get("prerelease"):
        raise UpdateError(f"{repo} latest release is draft or prerelease")
    tag = payload.get("tag_name", "")
    if not SEMVER.fullmatch(tag):
        raise UpdateError(f"{repo} tag {tag!r} is not vX.Y.Z")
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


def top_level_apps(dmg: Path) -> list[str]:
    if shutil.which("7z") is None:
        raise UpdateError("7z is required to read the .app name inside a disk image")
    output = subprocess.run(
        ["7z", "l", "-slt", str(dmg)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    apps: list[str] = []
    for line in output.splitlines():
        if not line.startswith("Path = "):
            continue
        top = line[len("Path = ") :].strip().split("/")[0]
        if top.endswith(".app") and top not in apps:
            apps.append(top)
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


def render_lux(version: str, sha: str) -> str:
    return f"""cask "lux" do
  version "{version}"
  sha256 "{sha}"

  {ruby_url("lux", LUX_DMG, version, interpolate=True)}
  name "Lux"
  desc "Ultra-fast native code editor"
  homepage "https://github.com/lcajigasm/lux"

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


def main() -> int:
    changed = False
    for repo, updater in (
        ("lux", update_lux),
        ("ownterm", update_ownterm),
        ("omega", update_omega),
    ):
        release = latest_release(repo)
        sums = release_sums(release)
        print(f"{repo} {release['tag_name']}")
        changed = updater(release, sums) or changed
    if changed:
        print("updated")
    else:
        print("unchanged")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (UpdateError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
