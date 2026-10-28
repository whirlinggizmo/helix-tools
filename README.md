# helix-tools

Prebuilt programs that [helix-platform](https://github.com/whirlinggizmo/helix)'s shader compiler runs, for the systems their own
projects don't publish for, so a shader author needs nothing but Haxe. The compiler fetches a release's zip the first time it compiles a
shader, checks its SHA-256 against the one it pins, and unpacks it into the user's cache.

| Tool | Version | Platforms | Why |
|---|---|---|---|
| [SPIRV-Cross](https://github.com/KhronosGroup/SPIRV-Cross) | `vulkan-sdk-1.4.363.0` | Linux x86_64 and ARM64, macOS (universal), Windows x86_64 | It publishes source only. |
| [glslang](https://github.com/KhronosGroup/glslang) | `16.6.0` | Linux ARM64 | Its releases cover Linux x86_64, macOS and Windows; the compiler uses those. |

Each is built from its project's source, unchanged, at the pin in `pins.json` (the source archive's URL and SHA-256). A release is one
tool at one version, tagged `<tool>-<version>`: each zip, `<tool>-<version>-<platform>.zip`, holds `bin/<program>` and the project's
license, as glslang's own releases are laid out, and the release lists the zips' SHA-256s in `SHA256SUMS`.

## How a release is made

`build.py` builds one tool for one platform: it fetches the source and checks its hash, builds the program with CMake in Release (its C++
runtime linked statically, macOS for both architectures from 11.0), checks it on `smoke/`, and zips it. The check compiles
`smoke/smoke.frag` with glslang and compares the SPIR-V with `smoke.frag.spv`, which glslang's own release of the same version made, byte
for byte; SPIRV-Cross translates that SPIR-V to GLSL ES 300, MSL and HLSL and compares each with the file beside it.

`.github/workflows/release.yml` runs it on GitHub's runners for every platform a pin lists. Pushing a tag `<tool>-<version>` builds that
pin and publishes the release; a pull request builds every pin and publishes nothing. Linux builds run on Ubuntu 22.04, so they need
glibc 2.35 or later.

To add a version: add its pin to `pins.json` (`sha256sum` of the source archive), update `smoke/` if the outputs change on purpose, open
a pull request, then tag the merge.

## Licenses

The programs are their projects' own: SPIRV-Cross under Apache-2.0, glslang under BSD-3-Clause and the others its `LICENSE.txt` lists.
Each zip carries the license. This repository's own files are MIT (`LICENSE`).
