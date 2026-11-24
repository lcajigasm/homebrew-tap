class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.1/omega_0.32.1_darwin_arm64.tar.gz"
      sha256 "cfbb877b11d031be212a9836dcac30f8ff1d7fcf8c84007d21c43af0aeb26123"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.1/omega_0.32.1_darwin_amd64.tar.gz"
      sha256 "1e7c3a51ae73a15899715ee98f6e74a262b10eb5e8bff1b22880c06fcda82483"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.1/omega_0.32.1_linux_arm64.tar.gz"
      sha256 "c4ad0feb14649986394bcaf34acfa38088fc3fd37ac89df9b56429678a36ae7b"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.32.1/omega_0.32.1_linux_amd64.tar.gz"
      sha256 "763acb80e8b2ff0a2901b9978b80be4734f9934aadc23f312cda68736039b22f"
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
