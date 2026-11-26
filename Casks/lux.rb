cask "lux" do
  version "1.5.12"
  sha256 "2745ab5317814286c3fdb3962d83ffc00194f35eed0101351437d6f16266ec53"

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
