class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.0/omega_0.32.0_darwin_arm64.tar.gz"
      sha256 "c4dc1b7d2e10805af92de5813a465823bca9661d9f99913b07d9eedcd62506fa"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.0/omega_0.32.0_darwin_amd64.tar.gz"
      sha256 "4ccfd27bee2615df8943da45e42a365823b955f3bdeffefbdacef57d499eb180"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.0/omega_0.32.0_linux_arm64.tar.gz"
      sha256 "0de8b00f50ad2f027f29dca9f2281a38005cd1e90328c5dc87ae49e71878f88c"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.0/omega_0.32.0_linux_amd64.tar.gz"
      sha256 "e62079e98537c02f225b3896f24275b56474d9391a36416528b88cd5ee7114e1"
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
