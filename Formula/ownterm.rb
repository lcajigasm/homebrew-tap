class Ownterm < Formula
  desc "Local-first terminal with a native AI agent"
  homepage "https://github.com/lcajigasm/ownterm"
  license "AGPL-3.0-only"

  # Tarballs until a release ships a .dmg. script/update_tap.py then deletes
  # this formula and writes Casks/ownterm.rb instead.
  depends_on :macos

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/ownterm/releases/download/v0.5.0/ownterm-macos-arm64.tar.gz"
      sha256 "746ee278e1ea1d83da51877a8bf1af40e43b2af0213fb297c4723145f2c79752"
    end

    on_intel do
      url "https://github.com/lcajigasm/ownterm/releases/download/v0.5.0/ownterm-macos-x86_64.tar.gz"
      sha256 "577cb3446c4eb9ed5ae0f089ddd268b91d1c91bfe431a7b4eb1774862a81be99"
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
    output = shell_output("#{bin}/ownterm-tui --version")
    assert_match(/\d/, output)
    assert_predicate bin/"ownterm", :executable?
  end
end
