class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.2/omega_0.28.2_darwin_arm64.tar.gz"
      sha256 "5dea012b0e4eae3c3367de1ac8454c1f971165a75cebebf4ff2063f4bbef0ab1"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.2/omega_0.28.2_darwin_amd64.tar.gz"
      sha256 "2ca1afe1067a84b350b9fa4ce2d7b17b2870182ce8675b451de52f0b414803a9"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.2/omega_0.28.2_linux_arm64.tar.gz"
      sha256 "945836986ebdcfd21ee19238a3a96a6be78bbe37ed5e47b64afb857f9fe76a7f"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.2/omega_0.28.2_linux_amd64.tar.gz"
      sha256 "35dd5f6f283340e9377d2283a83ae624d1acbf4d7c5d1aa07d54cc1a34efe4fd"
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
