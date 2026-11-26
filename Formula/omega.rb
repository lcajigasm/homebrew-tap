class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.36.0/omega_0.36.0_darwin_arm64.tar.gz"
      sha256 "55a2109894bf60167667354a105317cf29029a4f9727b551341e473a20a7592b"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.36.0/omega_0.36.0_darwin_amd64.tar.gz"
      sha256 "56090828329c7ffc4732acea674910e146dcd4c263fc66a4a2cc976e86382ea4"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.36.0/omega_0.36.0_linux_arm64.tar.gz"
      sha256 "44f3824fd61fc936cd221ebe0c91242dec9dd1976dffcf3f6d4716a00c5d8154"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.36.0/omega_0.36.0_linux_amd64.tar.gz"
      sha256 "cff9238401cada2fdba6b29687d517dc8edc6e69fc7d6a3bd06a5e607d241900"
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
