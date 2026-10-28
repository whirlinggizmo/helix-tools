#!/usr/bin/env python3
"""Builds one pinned tool for one platform, checks it, and packs it as a release zip.

    python3 build.py TOOL VERSION PLATFORM OUT

TOOL and VERSION name a pin in pins.json (its source's URL and SHA-256, and the platforms it's built for). PLATFORM is one of
linux-x86_64, linux-arm64, macos-universal, windows-x86_64, and must be the machine's own (macos-universal builds both of a Mac's
architectures). The source is fetched and checked against its hash, built with CMake in Release, its C++ runtime linked statically, then
run on smoke/: glslang compiles smoke.frag to SPIR-V, which must be smoke.frag.spv byte for byte (made by glslang's own release of the same
version); SPIRV-Cross translates smoke.frag.spv to GLSL ES 300, MSL and HLSL, which must be the files beside it. The zip, OUT/TOOL-VERSION-
PLATFORM.zip, holds bin/<program> and the source's license, as glslang's own releases are laid out. Standard library, CMake and a C++
compiler only."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
SMOKE = HERE / 'smoke'


def configure_flags(tool, platform):
    """CMake's flags for tool on platform: the program alone, Release, its C++ runtime static."""
    flags = ['-DCMAKE_BUILD_TYPE=Release']
    if tool == 'spirv-cross':
        flags += ['-DSPIRV_CROSS_CLI=ON', '-DSPIRV_CROSS_ENABLE_TESTS=OFF', '-DSPIRV_CROSS_SHARED=OFF', '-DSPIRV_CROSS_STATIC=ON']
    else:
        # The optimizer (SPIRV-Tools) left out: the compiler that runs it never optimizes.
        flags += ['-DENABLE_OPT=OFF', '-DGLSLANG_TESTS=OFF', '-DBUILD_SHARED_LIBS=OFF', '-DENABLE_GLSLANG_BINARIES=ON']
    if platform.startswith('linux'):
        flags.append('-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc')
    elif platform == 'macos-universal':
        flags += ['-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0']
    else:
        flags += ['-DCMAKE_POLICY_DEFAULT_CMP0091=NEW', '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded']
    return flags


def fetch(url, sha256):
    """The bytes at url, refused unless their SHA-256 is sha256."""
    with urllib.request.urlopen(url) as response:
        data = response.read()
    found = hashlib.sha256(data).hexdigest()
    if found != sha256:
        sys.exit(f'{url}: SHA-256 {found}, pinned {sha256}')
    return data


def program_in(build, name):
    """The built program named name somewhere under build."""
    exe = name + ('.exe' if os.name == 'nt' else '')
    found = [p for p in build.rglob(exe) if p.is_file()]
    if not found:
        sys.exit(f'{exe} not found under {build}')
    return found[0]


def same_text(path, expected):
    """Whether two text files hold the same lines, whatever their line endings."""
    return path.read_bytes().replace(b'\r\n', b'\n') == expected.read_bytes().replace(b'\r\n', b'\n')


def smoke(tool, program, scratch):
    """Runs the built program on smoke/ and exits unless its output is what's committed there."""
    if tool == 'glslang':
        spv = scratch / 'smoke.frag.spv'
        subprocess.run([str(program), '-V', '--target-env', 'vulkan1.0', '--auto-map-locations', str(SMOKE / 'smoke.frag'), '-o', str(spv)],
                       check=True, stdout=subprocess.DEVNULL)
        if spv.read_bytes() != (SMOKE / 'smoke.frag.spv').read_bytes():
            sys.exit('glslang: smoke.frag compiles to other SPIR-V than glslang\'s own release does')
        return
    for args, expected in ((['--version', '300', '--es'], 'smoke.es300.glsl'), (['--msl', '--msl-version', '20100'], 'smoke.msl'),
                           (['--hlsl', '--shader-model', '51'], 'smoke.hlsl')):
        out = scratch / expected
        subprocess.run([str(program), str(SMOKE / 'smoke.frag.spv'), *args, '--output', str(out)], check=True)
        if not same_text(out, SMOKE / expected):
            sys.exit(f'spirv-cross: smoke.frag.spv translates to another {expected}')


def main():
    if len(sys.argv) != 5 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 2)
    tool, version, platform, out = sys.argv[1:]
    pin = json.loads((HERE / 'pins.json').read_text(encoding='utf-8')).get(tool, {}).get(version)
    if pin is None:
        sys.exit(f'{tool} {version} is not pinned in pins.json')
    if platform not in pin['platforms']:
        sys.exit(f'{tool} {version} is not built for {platform} (pins.json: {", ".join(pin["platforms"])})')
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        with tarfile.open(fileobj=io.BytesIO(fetch(pin['url'], pin['sha256']))) as archive:
            archive.extractall(scratch / 'source', filter='data')
        source, = (scratch / 'source').iterdir()
        build = scratch / 'build'
        subprocess.run(['cmake', '-S', str(source), '-B', str(build), *configure_flags(tool, platform)], check=True)
        target = 'spirv-cross' if tool == 'spirv-cross' else 'glslang-standalone'
        subprocess.run(['cmake', '--build', str(build), '--config', 'Release', '--target', target, '--parallel'], check=True)
        program = program_in(build, 'spirv-cross' if tool == 'spirv-cross' else 'glslang')
        smoke(tool, program, scratch)
        license_file = next(source / n for n in ('LICENSE', 'LICENSE.txt') if (source / n).is_file())
        Path(out).mkdir(parents=True, exist_ok=True)
        zip_path = Path(out) / f'{tool}-{version}-{platform}.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            info = zipfile.ZipInfo(f'bin/{program.name}')
            info.external_attr = 0o755 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, program.read_bytes())
            z.write(license_file, license_file.name)
        print(f'{zip_path.name} {hashlib.sha256(zip_path.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
