# homebrew-tap

Homebrew tap for [lux](https://github.com/lcajigasm/lux), [ownterm](https://github.com/lcajigasm/ownterm) and [omega](https://github.com/lcajigasm/omega).

```bash
brew tap lcajigasm/tap
```

Homebrew asks before it installs from a third-party tap. In a non-interactive shell, trust it first:

```bash
brew trust lcajigasm/tap
```

Install one formula or cask without a separate tap:

```bash
brew install lcajigasm/tap/omega
brew install lcajigasm/tap/ownterm
brew install --cask lcajigasm/tap/lux
```

## What is in the tap

| Name | Kind | Source |
| --- | --- | --- |
| `omega` | formula | `omega_<version>_{darwin,linux}_{arm64,amd64}.tar.gz` |
| `ownterm` | formula | `ownterm-macos-arm64.tar.gz` and `ownterm-macos-x86_64.tar.gz` |
| `lux` | cask | `lux-macos-universal.dmg` (`Lux.app`) |

`lcajigasm/homebrew-omega` is an older tap and still points at omega 0.5.0. It is not updated from this repository. Install omega from `lcajigasm/tap`.

## lux and quarantine

`Lux.app` inside `lux-macos-universal.dmg` is a universal binary (Apple Silicon and Intel). The signature is ad-hoc. There is no Apple Developer ID and the app is not notarized, so Gatekeeper quarantines it.

After install:

```bash
xattr -dr com.apple.quarantine /Applications/Lux.app
```

Or skip quarantine at install time:

```bash
brew install --cask --no-quarantine lcajigasm/tap/lux
```

`brew uninstall --cask lux` leaves `~/.config/lux`. `brew uninstall --zap --cask lux` removes it.

## ownterm

The formula installs the `ownterm` and `ownterm-tui` binaries from the macOS tarballs (`on_arm` / `on_intel`). Those binaries are not code-signed. Configuration stays in `~/.ownterm`.

Current releases do not publish a disk image. When a release of [lcajigasm/ownterm](https://github.com/lcajigasm/ownterm) includes one, `script/update_tap.py` deletes `Formula/ownterm.rb` and writes `Casks/ownterm.rb`. The asset is chosen in this order:

1. `ownterm-macos-universal.dmg`
2. `OwnTerm.dmg`
3. `ownterm.dmg`
4. the only `*.dmg` attached to that release

The cask `app` stanza is the top-level `.app` inside that image. Install then becomes:

```bash
brew install --cask lcajigasm/tap/ownterm
```

The same quarantine commands apply, with `OwnTerm.app` or whichever app the image contains. Several disk images and none of the three names above make the updater fail instead of guessing.

## Updates

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs every 6 hours and can be started with `workflow_dispatch`. It reads the public releases API of the three repositories (no personal access token and no repository secrets). For each new release it rewrites the version, URL and sha256. Checksums come from that release's `SHA256SUMS`, or from a download when an asset is missing there.

The job commits to `main` with this repository's `GITHUB_TOKEN` (`permissions: contents: write`) only when a file changed. An unchanged tap produces no commit.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests and on pushes to `main`, on the standard `macos-14` runner. It runs `brew style`, `brew audit --online`, then `brew install` for `omega` and `ownterm` and `brew install --cask` for `lux`.
