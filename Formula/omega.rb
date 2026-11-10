class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.18.0/omega_0.18.0_darwin_arm64.tar.gz"
      sha256 "583f4e0d142493b82472c6541593860c03adb57b368087b3092bdba30522cc32"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.18.0/omega_0.18.0_darwin_amd64.tar.gz"
      sha256 "1526ade4a9624a1552a12c6e0847702a15fce7787e546425313c2d44dff81894"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.18.0/omega_0.18.0_linux_arm64.tar.gz"
      sha256 "de0ca9d0083260de228db7edc6ac9a8fab5c7e962f2fd5cc6d0953bc95dbcfbd"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.18.0/omega_0.18.0_linux_amd64.tar.gz"
      sha256 "e158c045b670ea3dec56d10ac88a07d6aed2e68be134e82f10d33226221376ac"
    end
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
    assert_match version.to_s, shell_output("#{bin}/omega --version")
    assert_match "brew", shell_output("#{bin}/omega steps")
  end
end
