class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.15.0/omega_0.15.0_darwin_arm64.tar.gz"
      sha256 "7145688db5944e3f3b7000856842a9c719c1b3889af85db822fc3274fde9a54e"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.15.0/omega_0.15.0_darwin_amd64.tar.gz"
      sha256 "c94a68037fd0d30b3365cd571ec0cf5f97830f6f38c4039e3842522370b447c7"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.15.0/omega_0.15.0_linux_arm64.tar.gz"
      sha256 "522a64d09a4ab16da34777aa36c2cc876b019e0b71750b3229304d9141d70883"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.15.0/omega_0.15.0_linux_amd64.tar.gz"
      sha256 "d7dc6e0ff2a6dc43e0b23e4044b7c200d1fd6d6b58ef46b7edaa7fe5a12a113e"
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
