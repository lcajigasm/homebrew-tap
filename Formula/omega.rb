class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.1/omega_0.28.1_darwin_arm64.tar.gz"
      sha256 "7aaa3d4a5b75023e0ffdd0ff5ce8fc8450577190a900cdccc480751250693bd7"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.1/omega_0.28.1_darwin_amd64.tar.gz"
      sha256 "66ba871b79e5c090f791ad68aea97b3086abbccde776f024e66581196376dab8"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.1/omega_0.28.1_linux_arm64.tar.gz"
      sha256 "5ccdf3b5f082503caf8fd7c646564af213e61098ff09899df4f8607e74b6e470"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.1/omega_0.28.1_linux_amd64.tar.gz"
      sha256 "04e54fbb3096aebb3bef9e204ed2ed6f57c838dbecf8daf7155e29967145ca15"
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
