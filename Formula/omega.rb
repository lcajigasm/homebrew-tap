class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.22.1/omega_0.22.1_darwin_arm64.tar.gz"
      sha256 "508506fd13e2bce9d9a081945d94a6bce30eec8fc283b81e2c12a687b2605333"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.22.1/omega_0.22.1_darwin_amd64.tar.gz"
      sha256 "289cb98f0cd9dea7ca7282698fd9ec9bd4014edabe4ef4d0f15faaef7d50c4c3"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.22.1/omega_0.22.1_linux_arm64.tar.gz"
      sha256 "7fb79cda1cfb26f532de5f338a5f4e6c5bffb4f6f4c0870209d84b303ac56d77"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.22.1/omega_0.22.1_linux_amd64.tar.gz"
      sha256 "a36dbba9008732a8be84a9b73915dd764cbc3708751cddfd2c094a54d9b9b264"
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
