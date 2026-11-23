class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.31.0/omega_0.31.0_darwin_arm64.tar.gz"
      sha256 "0f07a83530d4ef89dd0fcdb2e51c7ec9c3f15c27f2ecb30e84a0472938d25337"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.31.0/omega_0.31.0_darwin_amd64.tar.gz"
      sha256 "73b26b265e530b3e7bb4e573583dba72a3c7c69a1a62c4db9732b6c0e7ce2d53"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.31.0/omega_0.31.0_linux_arm64.tar.gz"
      sha256 "415302e260876a9f285d84718366bd1976cd3fff80d8a9b0067d9910673eaa33"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.31.0/omega_0.31.0_linux_amd64.tar.gz"
      sha256 "54c64c6d3e286e454585eb8ddbcf5a4876c0613c0f5cbc2f7cb85e897196f7bd"
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
