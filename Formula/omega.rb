class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.30.0/omega_0.30.0_darwin_arm64.tar.gz"
      sha256 "d4e4268328f521a39be69a3362de509c09dd8e9d72521f0946d12d254203029e"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.30.0/omega_0.30.0_darwin_amd64.tar.gz"
      sha256 "d7a9de1dd60c7f8e90256b9518f67bc168f051a5e1b133f42a35b99681dcff94"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.30.0/omega_0.30.0_linux_arm64.tar.gz"
      sha256 "d0925aa89c8705f2e55852069b88f9d084264a4ba7a342835c34480481ce43bd"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.30.0/omega_0.30.0_linux_amd64.tar.gz"
      sha256 "dfd4e0648262864ed697469317758a23c4a0b141e2a7d4da7353163f8b202086"
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
