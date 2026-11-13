class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.24.0/omega_0.24.0_darwin_arm64.tar.gz"
      sha256 "5d1df768533eb1f5385bd00e65196613680bea2ed987b7fce987c45c990f360c"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.24.0/omega_0.24.0_darwin_amd64.tar.gz"
      sha256 "c80e34bcec6333e2e90ad479c1db1672f34254fc82f1a8eeb52f39f2a42cf25c"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.24.0/omega_0.24.0_linux_arm64.tar.gz"
      sha256 "7bd2e4e86b2a99fc8bd9c6030a5c52a5899b96e7ba20437289b7c667c70c4dcd"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.24.0/omega_0.24.0_linux_amd64.tar.gz"
      sha256 "322e79e8503e1fd4df735b900c813b59ff8335e3087a6179ff93263f8b71a4e6"
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
