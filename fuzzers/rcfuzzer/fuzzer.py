# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration code for libFuzzer fuzzer."""

import subprocess
import os
import shutil

from fuzzers import utils

def get_afl_based_target_dir(output_directory):
    """Return path to AFL based target directory."""
    return os.path.join(output_directory, 'afl')

def get_aflpp_based_target_dir(output_directory):
    """Return path to AFL++ based target directory."""
    return os.path.join(output_directory, 'aflpp')

def get_lafintel_target_dir(output_directory):
    """Return path to laf-intel target directory."""
    return os.path.join(output_directory, 'lafintel')

def get_angora_target_dir(output_directory):
    """Return path to Angora target directory."""
    return os.path.join(output_directory, 'angora')

def get_libfuzzer_target_dir(output_directory):
    """Return path to libFuzzer based target directory."""
    return os.path.join(output_directory, 'libfuzzer')

def get_aflasan_target_dir(output_directory):
    """Return path to aflasan based target directory."""
    return os.path.join(output_directory, 'aflasan')

def prepare_build_environment():
    """Prepare build environment."""
    os.makedirs('/out/fuzzers', exist_ok=True)
    shutil.copytree('/afl', '/out/fuzzers/afl')
    shutil.copytree('/aflpp', '/out/fuzzers/aflpp', symlinks=True)
    shutil.copytree('/MOpt-AFL', '/out/fuzzers/MOpt-AFL')
    shutil.copytree('/LearnAFL', '/out/fuzzers/LearnAFL')
    shutil.copytree('/qsym', '/out/fuzzers/qsym')
    shutil.copytree('/angora', '/out/fuzzers/angora')
    shutil.copytree('/afl-rb', '/out/fuzzers/afl-rb')
    shutil.copytree('/aflfast', '/out/fuzzers/aflfast')
    shutil.copy('/LearnAFL/learning_engine.py', '/usr/local/bin')

    afl_based_target_dir = get_afl_based_target_dir(os.environ['OUT'])
    aflpp_based_target_dir = get_aflpp_based_target_dir(os.environ['OUT'])
    lafintel_target_dir = get_lafintel_target_dir(os.environ['OUT'])
    angora_target_dir = get_angora_target_dir(os.environ['OUT'])
    libfuzzer_target_dir = get_libfuzzer_target_dir(os.environ['OUT'])

    os.makedirs(afl_based_target_dir, exist_ok=True)
    os.makedirs(aflpp_based_target_dir, exist_ok=True)
    os.makedirs(lafintel_target_dir, exist_ok=True)
    os.makedirs(angora_target_dir, exist_ok=True)
    os.makedirs(libfuzzer_target_dir, exist_ok=True)

    
    # Tell AFL to not use its terminal UI so we get usable logs.
    os.environ['AFL_NO_UI'] = '1'
    # Skip AFL's CPU frequency check (fails on Docker).
    os.environ['AFL_SKIP_CPUFREQ'] = '1'
    # No need to bind affinity to one core, Docker enforces 1 core usage.
    os.environ['AFL_NO_AFFINITY'] = '1'
    # AFL will abort on startup if the core pattern sends notifications to
    # external programs. We don't care about this.
    os.environ['AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES'] = '1'
    # Don't exit when crashes are found. This can happen when corpus from
    # OSS-Fuzz is used.
    os.environ['AFL_SKIP_CRASHES'] = '1'
    # Shuffle the queue
    os.environ['AFL_SHUFFLE_QUEUE'] = '1'

def afl_based_build():
    new_env = os.environ.copy()
    
    # cflags = ['-fsanitize-coverage=trace-pc-guard']
    # utils.append_flags('CFLAGS', cflags)
    # utils.append_flags('CXXFLAGS', cflags)
    
    new_env['CC'] = 'clang'
    new_env['CXX'] = 'clang++'
    new_env['FUZZER_LIB'] = '/libAFL.a'
    utils.build_benchmark(env=new_env)

def build_afl_based():
    """Build benchmark for afl based fuzzers."""
    print('Building with AFL')
    out_dir = os.environ['OUT']
    afl_based_target_dir = get_afl_based_target_dir(os.environ['OUT'])
    os.environ['OUT'] = afl_based_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        afl_based_build()
    os.environ['OUT'] = out_dir
    shutil.copy('/afl/afl-fuzz', afl_based_target_dir)


def aflpp_based_build():
    new_env = os.environ.copy()
        
    new_env['CC'] = '/aflpp/afl-clang-fast'
    new_env['CXX'] = '/aflpp/afl-clang-fast++'
    new_env['FUZZER_LIB'] = '/libAFLDriver.a'

    # Some benchmarks like lcms. (see:
    # https://github.com/mm2/Little-CMS/commit/ab1093539b4287c233aca6a3cf53b234faceb792#diff-f0e6d05e72548974e852e8e55dffc4ccR212)
    # fail to compile if the compiler outputs things to stderr in unexpected
    # cases. Prevent these failures by using AFL_QUIET to stop afl-clang-fast
    # from writing AFL specific messages to stderr.
    new_env['AFL_QUIET'] = '1'
    new_env['AFL_MAP_SIZE'] = '2621440'

    utils.build_benchmark(env=new_env)

def build_aflpp_based():
    """Build benchmark for AFL++ based fuzzers."""
    print('Building with AFL++')
    out_dir = os.environ['OUT']
    aflpp_based_target_dir = get_aflpp_based_target_dir(os.environ['OUT'])
    os.environ['OUT'] = aflpp_based_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        aflpp_based_build()
    os.environ['OUT'] = out_dir
    shutil.copy('/aflpp/afl-fuzz', aflpp_based_target_dir)

def lafintel_based_build():
    new_env = os.environ.copy()
        
    new_env['CC'] = '/aflpp/afl-clang-fast'
    new_env['CXX'] = '/aflpp/afl-clang-fast++'
    new_env['FUZZER_LIB'] = '/libAFLDriver.a'

    # Some benchmarks like lcms. (see:
    # https://github.com/mm2/Little-CMS/commit/ab1093539b4287c233aca6a3cf53b234faceb792#diff-f0e6d05e72548974e852e8e55dffc4ccR212)
    # fail to compile if the compiler outputs things to stderr in unexpected
    # cases. Prevent these failures by using AFL_QUIET to stop afl-clang-fast
    # from writing AFL specific messages to stderr.
    new_env['AFL_QUIET'] = '1'
    new_env['AFL_MAP_SIZE'] = '2621440'
    new_env['AFL_LLVM_LAF_ALL'] = '1'
    utils.build_benchmark(env=new_env)

def build_lafintel_based():
    """Build benchmark for laf-intel fuzzers."""
    print('Building with LearnAFL')
    out_dir = os.environ['OUT']
    lafintel_target_dir = get_lafintel_target_dir(os.environ['OUT'])
    os.environ['OUT'] = lafintel_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        lafintel_based_build()
    os.environ['OUT'] = out_dir
    shutil.copy('/aflpp/afl-fuzz', lafintel_target_dir)

def angora_build():
    new_env = os.environ.copy()
    new_env['CC'] = '/angora/bin/angora-clang'
    new_env['CXX'] = '/angora/bin/angora-clang++'
    new_env['FUZZER_LIB'] = ''
    utils.build_benchmark(env=new_env)

def build_angora():
    """Build benchmark for angora."""
    print('Building with Angora')
    out_dir = os.environ['OUT']
    angora_target_dir = get_angora_target_dir(os.environ['OUT'])
    os.environ['OUT'] = angora_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        angora_build()
    os.environ['OUT'] = out_dir
    shutil.copy('/angora/angora_fuzzer', angora_target_dir)

def libfuzzer_build():
    new_env = os.environ.copy()

    cflags = ['-fsanitize=fuzzer-no-link']
    utils.append_flags('CFLAGS', cflags)
    utils.append_flags('CXXFLAGS', cflags)

    # new_env['CFLAGS'] = '-fsanitize=fuzzer-no-link'
    # new_env['CXXFLAGS'] = '-fsanitize=fuzzer-no-link'

    new_env['CC'] = 'clang'
    new_env['CXX'] = 'clang++'
    new_env['FUZZER_LIB'] = '/usr/lib/libFuzzer.a'
    utils.build_benchmark(env=new_env)

def build_libfuzzer():
    """build benchmark for libFuzzer"""
    print('Building with libFuzzer')
    out_dir = os.environ['OUT']
    libfuzzer_target_dir = get_libfuzzer_target_dir(os.environ['OUT'])
    os.environ['OUT'] = libfuzzer_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        libfuzzer_build()
    os.environ['OUT'] = out_dir

def aflasan_build():
    new_env = os.environ.copy()
    
    # cflags = ['-fsanitize=address']
    # utils.append_flags('CFLAGS', cflags)
    # utils.append_flags('CXXFLAGS', cflags)
    new_env['CFLAGS'] = '-fsanitize=address'
    new_env['CXXFLAGS'] = '-fsanitize=address'
    new_env['CC'] = 'clang'
    new_env['CXX'] = 'clang++'
    new_env['FUZZER_LIB'] = '/libAFL.a'
    utils.build_benchmark(env=new_env)


def build_aflasan():
    """build benchmark for aflasan"""
    print('Building with afl+asan')
    out_dir = os.environ['OUT']
    aflasan_target_dir = get_aflasan_target_dir(os.environ['OUT'])
    os.environ['OUT'] = aflasan_target_dir
    src = os.getenv('SRC')
    work = os.getenv('WORK')
    with utils.restore_directory(src), utils.restore_directory(work):
        aflasan_build()
    os.environ['OUT'] = out_dir


def build():
    prepare_build_environment()
    
    build_afl_based()
    build_aflpp_based()
    build_lafintel_based()
    # build_angora() # Broken
    build_libfuzzer()
    # build_aflasan() # TODO for check coverage

def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer."""

    # Seperate out corpus and crash directories as sub-directories of
    # |output_corpus| to avoid conflicts when corpus directory is reloaded.
    crashes_dir = os.path.join(output_corpus, 'crashes')
    output_corpus = os.path.join(output_corpus, 'corpus')
    os.makedirs(crashes_dir)
    os.makedirs(output_corpus)

    basename = os.path.basename(target_binary)
    print(basename)

    command = ['rcfuzz',
               '-i', input_corpus,
               '-o', output_corpus,
            #    "-T", "24h", # default=24h
               '-f', 'afl',
               '-t', os.getenv['BENCHMARK']]
    print('[run_fuzzer] Running command: ' + ' '.join(command))
    subprocess.check_call(command)
