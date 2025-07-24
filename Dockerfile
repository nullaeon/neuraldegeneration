FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    python3 \
    python3-pip \
    python3-dev \
    python-is-python3 \
    zip \
    unzip \
    software-properties-common \
    gnupg \
    tree \
    wget \
    apt-transport-https \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11 and set it as default
RUN add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libdbus-1-dev && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --set python3 /usr/bin/python3.11 && \
    python3 --version

# Install pip for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Python packages
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install Bazel
RUN wget https://github.com/bazelbuild/bazel/releases/download/7.6.0/bazel-7.6.0-linux-x86_64 -O /usr/local/bin/bazel && \
    chmod +x /usr/local/bin/bazel && \
    bazel version

# Install AWS CLI v2 and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && apt install -y jq

# Set env variables for ML workloads
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
ENV BNB_CUDA_VERSION=118
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"
ENV TRANSFORMERS_CACHE=/mnt/hf_cache/hf_transformers
ENV HF_DATASETS_CACHE=/mnt/hf_cache/hf_datasets
ENV HF_HOME=/mnt/hf_cache/hf_home

# Install gosu (lightweight su/sudo replacement)
RUN apt-get update && apt-get install -y gosu

# Script to create a user at runtime that matches host UID:GID
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Set working directory
WORKDIR /workspace

CMD ["bash"]
