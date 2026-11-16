class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.0/omega_0.28.0_darwin_arm64.tar.gz"
      sha256 "534ac13b0f0f54313923a19f23d5af0f2d80691fc011f7680ab2653064278f99"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.0/omega_0.28.0_darwin_amd64.tar.gz"
      sha256 "e646c78dace5cc7d4d2b079e37d3746a52bac45e0586dcc13ec85b391f03e881"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.0/omega_0.28.0_linux_arm64.tar.gz"
      sha256 "04bfaf64569b7402165ba8be3844353cb9d8d38e3c70d65c9934e35ae31cc654"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.28.0/omega_0.28.0_linux_amd64.tar.gz"
      sha256 "75e2bce68d282d6408d65ca121c08631a53dfb806010741c7d74340f4c890d2e"
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
