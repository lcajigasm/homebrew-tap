cask "ownterm" do
  version "0.7.0"
  sha256 "f429d475af3f849df748c1093849c23a74a8fd0b089479cb26e2fdaa01e4fb6f"

  url "https://github.com/lcajigasm/ownterm/releases/download/v#{version}/ownterm-macos-universal.dmg"
  name "OwnTerm"
  desc "Local-first terminal with a native AI agent"
  homepage "https://github.com/lcajigasm/ownterm"

  livecheck do
    url :url
    strategy :github_releases do |json, regex|
      json.map do |release|
        next if release["draft"] || release["prerelease"]

        assets = release.fetch("assets", []).map { |asset| asset["name"] }
        next unless assets.include?("ownterm-macos-universal.dmg")

        match = release["tag_name"]&.match(regex)
        next unless match

        match[1]
      end
    end
  end

  depends_on :macos

  app "OwnTerm.app"

  zap trash: "~/.ownterm"

  caveats <<~EOS
    OwnTerm is not notarized, so Gatekeeper quarantines the app.
    Clear the quarantine attribute after install:

      xattr -dr com.apple.quarantine "/Applications/OwnTerm.app"

    Or install without quarantine:

      brew install --cask --no-quarantine lcajigasm/tap/ownterm
  EOS
end
