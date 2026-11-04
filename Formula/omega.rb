class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.13.0/omega_0.13.0_darwin_arm64.tar.gz"
      sha256 "732cf4caabecd68adf0c0d6a1186be2ec648a53880eb6afa09f326b062931693"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.13.0/omega_0.13.0_darwin_amd64.tar.gz"
      sha256 "20faad80ac62cd3ca61e4d8aec8387079bbcb96b9a0f66900b5eb9d6b08eadee"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.13.0/omega_0.13.0_linux_arm64.tar.gz"
      sha256 "f6d8c26ecadff497c3cd1739e8516a30077dbdae0f70a11f67d0eeef7e146488"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.13.0/omega_0.13.0_linux_amd64.tar.gz"
      sha256 "849782ea95ac5c874d4d7997c06ae78f894b7738ac4bedb546b6834b24bc910b"
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
