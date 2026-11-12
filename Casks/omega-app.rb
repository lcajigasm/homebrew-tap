# The desktop app, for macOS. This file is written by script/update_tap.py
# from omega's latest release: its version and the sha256 of the disk image.
cask "omega-app" do
  version "0.22.1"
  sha256 "3a75859c91144975b192fd97ffda81fa29622e389eafbacf06e1a65648de133d"

  url "https://github.com/lcajigasm/omega/releases/download/v#{version}/omega-macos-universal.dmg"
  name "omega"
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole, in a window"
  homepage "https://github.com/lcajigasm/omega"

  livecheck do
    url :url
    strategy :github_releases do |json, regex|
      json.map do |release|
        next if release["draft"] || release["prerelease"]

        assets = release.fetch("assets", []).map { |asset| asset["name"] }
        next unless assets.include?("omega-macos-universal.dmg")

        match = release["tag_name"]&.match(regex)
        next unless match

        match[1]
      end
    end
  end

  depends_on macos: :ventura

  app "Omega.app"

  # No zap: ~/.config/omega and ~/.local/state/omega belong to the omega
  # command too (brew install lcajigasm/tap/omega), which shares them.

  caveats <<~EOS
    Omega.app is ad-hoc signed and is not notarized, so Gatekeeper
    quarantines it. Clear the quarantine attribute after install:

      xattr -dr com.apple.quarantine /Applications/Omega.app

    The app and the omega command share their configuration and API keys.
    The command is a separate formula:

      brew install lcajigasm/tap/omega
  EOS
end
