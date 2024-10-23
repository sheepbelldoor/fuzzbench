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

FROM gcr.io/fuzzbench/base-image

RUN apt-get install -y git wget python2 python-dev python3 python3-dev curl

# RCFuzzer
RUN curl https://bootstrap.pypa.io/get-pip.py -o /get-pip.py && python3 /get-pip.py

WORKDIR /out

RUN git clone --branch fuzzbench https://github.com/sheepbelldoor/RCFuzzer_fuzzbench.git /out/rcfuzz

RUN cd /out/rcfuzz

RUN pip install /out/rcfuzz
ENV PATH="/out/rcfuzz:${PATH}"
