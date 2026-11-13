class Omega < Formula
  desc "AI-driven maintenance: updates like topgrade, cleans like Mole"
  homepage "https://github.com/lcajigasm/omega"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.26.0/omega_0.26.0_darwin_arm64.tar.gz"
      sha256 "cff8773fccc9aebf699c2b372dedc5fc04840e6beff563bfd8075c599c67cf53"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.26.0/omega_0.26.0_darwin_amd64.tar.gz"
      sha256 "0c9772e0274fcb3d0944324c29878b068cf09ee2996af43b2fef07891112f740"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lcajigasm/omega/releases/download/v0.26.0/omega_0.26.0_linux_arm64.tar.gz"
      sha256 "2dfde83d87abd6209530d536bb0e6fa3b0a8917199eb1417ed7a204a87552ba8"
    end

    on_intel do
      url "https://github.com/lcajigasm/omega/releases/download/v0.26.0/omega_0.26.0_linux_amd64.tar.gz"
      sha256 "d7072744f0ea2ab8fe35e85d3b685d9e8a64a575f9df8ca0896b4e224b5eb3c4"
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
