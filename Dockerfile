ARG BASEIMAGE=python:3.9-bookworm
#ARG BASEIMAGE=nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04

FROM ${BASEIMAGE}

WORKDIR /app

ARG DEPSLIST=requirements.txt
#ARG DEPSLIST=requirements-gpu.txt



COPY models ./models
COPY setup.py ./
COPY autosub ./autosub
COPY README.md ./
COPY webapi.py ./

RUN apt-get update && \
    apt-get -y install ffmpeg libsm6 libxext6  && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY $DEPSLIST ./requirements.txt

# make sure pip is up-to-date
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir .

RUN mkdir audio output
#run python in docker


ENV CLI_ARGS=""
EXPOSE 5000
CMD python webapi.py $CLI_ARGS