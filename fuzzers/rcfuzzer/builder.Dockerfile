ARG parent_image

## QSYM
FROM vancir/qsym AS qsym

RUN git clone --depth 1 https://github.com/fuyu0425/qsym /qsym_
WORKDIR /qsym_
RUN sed -i '23,25 s/^/#/' setup.py
RUN sed -i '4,7 s/^/#/' setup.sh
RUN ./setup.sh
RUN pip2 install .

## Angora
FROM ubuntu:16.04 AS angora
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y git build-essential wget zlib1g-dev golang-go python-pip python-dev build-essential cmake && \
    apt-get clean

WORKDIR /

RUN git clone https://github.com/AngoraFuzzer/Angora /angora \
    && cd /angora \
    && git checkout 3cedcac8e65595cd2cdd950b60f654c93cf8cc2e


ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PIN_ROOT=/pin-3.7-97619-g0d0c92f4f-gcc-linux \
    GOPATH=/go \
    PATH=/angora/clang+llvm/bin:/usr/local/cargo/bin:/angora/bin/:/go/bin:$PATH \
    LD_LIBRARY_PATH=/angora/clang+llvm/lib:$LD_LIBRARY_PATH

WORKDIR /angora

RUN ./build/install_rust.sh
RUN PREFIX=/angora ./build/install_llvm.sh

# FIXME: go get cannot specify version in ubuntu 16.04 ...
RUN sed -i 's/go get/#go get/g' /angora/build/install_tools.sh
RUN ./build/install_tools.sh

# no15k
# https://github.com/unifuzz/dockerized_fuzzing/blob/master/angora/Dockerfile.no15k
RUN sed -i 's/15000/1048576/g' /angora/common/src/config.rs
RUN ./build/build.sh
RUN ./build/install_pin_mode.sh

FROM $parent_image

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3-dev \
        python3-setuptools \
        automake \
        cmake \
        curl \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        cargo \
        libgtk-3-dev \
        # for QEMU mode
        ninja-build \
        gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev \
        libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev

## AFL
# Download and compile AFL v2.57b.
# Set AFL_NO_X86 to skip flaky tests.
RUN git clone \
        --depth 1 \
        --branch v2.57b \
        https://github.com/google/AFL.git /afl && \
    cd /afl && \
    CFLAGS= CXXFLAGS= AFL_NO_X86=1 make

# Use afl_driver.cpp from LLVM as our fuzzing library.
RUN apt-get update && \
    apt-get install wget -y && \
    wget https://raw.githubusercontent.com/llvm/llvm-project/5feb80e748924606531ba28c97fe65145c65372e/compiler-rt/lib/fuzzer/afl/afl_driver.cpp -O /afl/afl_driver.cpp && \
    clang -Wno-pointer-sign -c /afl/llvm_mode/afl-llvm-rt.o.c -I/afl && \
    clang++ -stdlib=libc++ -std=c++11 -O2 -c /afl/afl_driver.cpp && \
    ar r /libAFL.a *.o

## Angora
RUN mkdir -p /angora
COPY --from=angora /angora /angora

## libFuzzer
RUN git clone https://github.com/llvm/llvm-project.git /llvm-project && \
    cd /llvm-project && \
    git checkout 5cda4dc7b4d28fcd11307d4234c513ff779a1c6f && \
    cd compiler-rt/lib/fuzzer && \
    (for f in *.cpp; do \
      clang++ -stdlib=libc++ -fPIC -O2 -std=c++11 $f -c & \
    done && wait) && \
    ar r libFuzzer.a *.o && \
    cp libFuzzer.a /usr/lib

## QSYM
RUN mkdir -p /qsym
COPY --from=qsym /qsym_ /qsym

## MOPT
WORKDIR /

RUN git clone https://github.com/puppet-meteor/MOpt-AFL &&\
    cd "MOpt-AFL/MOpt" &&\
    git checkout a9a5dc5c0c291c1cdb09b2b7b27d7cbf1db7ce7b &&\
    AFL_NO_X86=1 make

## LearnAFL
WORKDIR /
RUN apt-get install -y python2 python-dev
RUN command git clone https://github.com/MoonLight-SteinsGate/LearnAFL.git
RUN cd LearnAFL && \
    AFL_NO_X86=1 make
# RUN cp /LearnAFL/learning_engine.py /usr/local/bin

## AFLFast
WORKDIR /

RUN git clone https://github.com/mboehme/aflfast && \
    cd aflfast && \
    AFL_NO_X86=1 make

## FairFuzz
WORKDIR /

RUN git clone https://github.com/carolemieux/afl-rb.git && \
  cd afl-rb && \
  git checkout e529c1f1b366 && \
  AFL_NO_X86=1 make

## AFL++
# Download afl++.
RUN git clone -b dev https://github.com/AFLplusplus/AFLplusplus /aflpp && \
    cd /aflpp && \
    git checkout 56d5aa3101945e81519a3fac8783d0d8fad82779 || \
    true

RUN cd /aflpp && make clean && AFL_NO_X86=1 make

RUN cd /aflpp/custom_mutators/radamsa && \
    make -j

# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /aflpp && make clean && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make && \
    cp utils/aflpp_driver/libAFLDriver.a /
    