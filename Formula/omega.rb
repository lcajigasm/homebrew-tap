class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.34.0/omega_0.34.0_darwin_arm64.tar.gz"
      sha256 "d6e5aa335ad68fd00bd8d0574a3c953a39ac17f32d3bcb1829eadb6e814705bc"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.34.0/omega_0.34.0_darwin_amd64.tar.gz"
      sha256 "f240ab154e087e6983556833160f8b4a8f38181643865c4557d77ad5989afa2d"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.34.0/omega_0.34.0_linux_arm64.tar.gz"
      sha256 "ac4abe9dd0081c553331b0c07a283d326066dcb6a2ec2ca46a310cc7a1a9e271"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.34.0/omega_0.34.0_linux_amd64.tar.gz"
      sha256 "f88aa78d46c33ab0e355a3bffcf8642071fc172bb2373316a831872a12577a3e"
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
