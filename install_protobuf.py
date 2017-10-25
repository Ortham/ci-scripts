#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib

def get_archive_extension():
    if os.name == 'nt':
        return '.zip'
    else:
        return '.tar.gz'

def build(source_dir, output_dir):
    build_dir = os.path.join(source_dir, 'cmake')

    cmake_command = [
        'cmake',
        '.',
        '-DCMAKE_INSTALL_PREFIX={}'.format(output_dir),
        '-DCMAKE_CXX_STANDARD=14'
    ]

    subprocess.check_call(cmake_command, cwd = build_dir)

    build_command = [
        'cmake',
        '--build',
        '.',
        '--target',
        'install',
        '--config',
        'release',
    ]

    subprocess.check_call(build_command, cwd = build_dir)

def extract_archive(archive_path):
    print('Extracting {}...'.format(archive_path))

    output_path = os.path.dirname(archive_path)

    extracted_path = get_extracted_path(archive_path)
    if os.path.exists(extracted_path):
        shutil.rmtree(extracted_path)

    if os.name == 'nt':
        subprocess.check_call(['7z', 'x', archive_path, u'-o{}'.format(output_path)], cwd = output_path)
    else:
        subprocess.check_call(['tar', 'xf', archive_path], cwd = output_path)

    return extracted_path

def get_extracted_path(archive_path):
    extension_length = -1 * len(get_archive_extension())
    filename = 'protobuf-{}'.format(
        archive_path.split('-')[-1][:extension_length]
    )
    return os.path.join(
        os.path.dirname(archive_path),
        filename
    )

def get_archive_name(version):
    return 'protobuf-cpp-{}{}'.format(version, get_archive_extension())

def get_url(version):
    return 'https://github.com/google/protobuf/releases/download/v{}/{}'.format(
        version,
        get_archive_name(version)
    )

def download(version, output_path):
    print('Downloading Protocol Buffers v{}...'.format(version))

    if os.path.exists(output_path):
        os.remove(output_path)

    urllib.urlretrieve(get_url(version), output_path)

def is_protobuf_installed(output_dir):
    executable = 'protoc'
    if os.name == 'nt':
        executable += '.exe'

    return os.path.exists(os.path.join(output_dir, 'bin', executable))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Download and build Protocol Buffers.')
    parser.add_argument('--output-directory', '-o', required = True)
    parser.add_argument('--target-version', '-t', required = True)

    arguments = parser.parse_args()

    output_dir = arguments.output_directory
    if is_protobuf_installed(output_dir):
        print('Protocol Buffers already installed at {}'.format(output_dir))
        sys.exit(0)

    print('Protocol Buffers not found at {}, installing...'.format(output_dir))

    archive_path = os.path.join(tempfile.gettempdir(), get_archive_name(arguments.target_version))

    download(arguments.target_version, archive_path)

    extracted_path = extract_archive(archive_path)

    build(extracted_path, output_dir)

    os.remove(archive_path)
    shutil.rmtree(extracted_path)
