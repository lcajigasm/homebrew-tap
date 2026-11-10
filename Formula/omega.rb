class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.17.0/omega_0.17.0_darwin_arm64.tar.gz"
      sha256 "2286af2c5278057831f1db58eb89b2facf1d96e4c0f1ec21bec550d803f7887f"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.17.0/omega_0.17.0_darwin_amd64.tar.gz"
      sha256 "ec361b215b2082b2691b61aa75bb94197420376df1cf98b76c2d49e3ba7d290a"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.17.0/omega_0.17.0_linux_arm64.tar.gz"
      sha256 "f7dba10643177b11fd53fdd560f80843db4cf731066708ef37c163523e0c94c7"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.17.0/omega_0.17.0_linux_amd64.tar.gz"
      sha256 "93ec7e33d6a9ff8cdc83d59b129a3b2beec20950c0d68395f752a809ff0f7975"
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
