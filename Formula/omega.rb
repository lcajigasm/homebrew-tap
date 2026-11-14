class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.27.0/omega_0.27.0_darwin_arm64.tar.gz"
      sha256 "21833819b2ecf8a6450fd325f5808119c21862674b149bcd0aed3f22cc86b441"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.27.0/omega_0.27.0_darwin_amd64.tar.gz"
      sha256 "b6e5f0bc079b23f57afca5ca1bdbb699e36b0ce8edb8e6d5f9d8e52c248bb743"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.27.0/omega_0.27.0_linux_arm64.tar.gz"
      sha256 "c0011850183bbb9d10f93b4574a002b55ad356defcb66f972227109dc85c67be"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.27.0/omega_0.27.0_linux_amd64.tar.gz"
      sha256 "cf98d29c0faa434e3099f53a3d1f8633eee482903773e9cbddef267c4e7702ef"
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
