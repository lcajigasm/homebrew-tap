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
brew install --cask lcajigasm/tap/ownterm
brew install --cask lcajigasm/tap/lux
```

## What is in the tap

| Name | Kind | Source |
| --- | --- | --- |
| `omega` | formula | `omega_<version>_{darwin,linux}_{arm64,amd64}.tar.gz` |
| `ownterm` | cask | `ownterm-macos-universal.dmg` (`OwnTerm.app`) |
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

The current release publishes `ownterm-macos-universal.dmg`, so the tap ships `Casks/ownterm.rb` and installs `OwnTerm.app`. The app is not notarized. Configuration stays in `~/.ownterm`.

```bash
brew install --cask lcajigasm/tap/ownterm
xattr -dr com.apple.quarantine /Applications/OwnTerm.app
```

Or skip quarantine at install time:

```bash
brew install --cask --no-quarantine lcajigasm/tap/ownterm
```

If a release has no disk image, `script/update_tap.py` deletes the cask and writes `Formula/ownterm.rb` from the macOS tarballs. When a disk image is present, the asset is chosen in this order: `ownterm-macos-universal.dmg`, `OwnTerm.dmg`, `ownterm.dmg`, otherwise the only `*.dmg`. Several disk images and none of those three names make the ownterm update fail instead of guessing. That failure does not block lux or omega.

## Updates

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs every hour (`23 * * * *`) and can be started with `workflow_dispatch`. It reads the public releases API of the three repositories (no personal access token and no repository secrets). For each new release it rewrites the version, URL and sha256. Checksums come from that release's `SHA256SUMS`, or from a download when an asset is missing there.

Each program follows its latest published release (`/releases/latest`), not the newest git tag. Drafts and prereleases are skipped. A tag that has no release yet is ignored. Lux, ownterm and omega are updated independently: if one fails, the others are still rewritten and committed, and the job ends in failure. The log summary names the program and the reason. `brew audit` livecheck for a cask uses Homebrew's authenticated GitHub releases list and follows the newest release that contains its asset. The workflow commits to `main` with this repository's `GITHUB_TOKEN` (`permissions: contents: write`) only when a file changed. An unchanged tap produces no commit.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests and on pushes to `main`. An Ubuntu job runs `script/test_update_tap.py`, which checks that one program's failure does not undo the others and that the updater reads `/releases/latest`. The `macos-15` job runs `brew style`, `brew audit --online`, then `brew install` for `omega` and `brew install --cask` for `ownterm` and `lux`. Audit authenticates with the workflow `GITHUB_TOKEN` so it does not share the unauthenticated API limit of 60 requests per hour.
