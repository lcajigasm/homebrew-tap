class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.25.0/omega_0.25.0_darwin_arm64.tar.gz"
      sha256 "267631e4c8eb1281fff5af3329cc2cf5773b87a3cfb91867430f0a765883e3b7"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.25.0/omega_0.25.0_darwin_amd64.tar.gz"
      sha256 "d1baa4f429b5f6988d0151afadecdb69d76d6bee1e4598ec86bd8be04e0df43e"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.25.0/omega_0.25.0_linux_arm64.tar.gz"
      sha256 "8f5d6d7db88a15d56b9daefc16c75556ddd60644753c63eefbd7e8a3a4e9afca"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.25.0/omega_0.25.0_linux_amd64.tar.gz"
      sha256 "f85a3790b22019ac9daf282610e77bb26f6fe37992baa4d08c4db4c41d378e0a"
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
