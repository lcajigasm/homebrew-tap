cask "lux" do
  version "1.5.7"
  sha256 "9d38b02605b2dd30b2609e2813c527cbfcc74248240e5533b79a3db1b31939e2"

  url "https://github.com/lcajigasm/lux/releases/download/v#{version}/lux-macos-universal.dmg"
  name "Lux"
  desc "Ultra-fast native code editor"
  homepage "https://github.com/lcajigasm/lux"

  livecheck do
    url :url
    strategy :github_releases do |json, regex|
      json.map do |release|
        next if release["draft"] || release["prerelease"]

        assets = release.fetch("assets", []).map { |asset| asset["name"] }
        next unless assets.include?("lux-macos-universal.dmg")

        match = release["tag_name"]&.match(regex)
        next unless match

        match[1]
      end
    end
  end

  depends_on :macos

  # Bundle id dev.lux.editor. Settings live in ~/.config/lux (settings.json).
  app "Lux.app"

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
