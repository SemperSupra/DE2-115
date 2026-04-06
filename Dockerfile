FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/riscv/bin:/opt/intelFPGA_lite/quartus/bin:${PATH}"

# Install core dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    bison \
    flex \
    git \
    make \
    ninja-build \
    python3 \
    python3-pip \
    python3-setuptools \
    libevent-dev \
    libjson-c-dev \
    verilator \
    wget \
    curl \
    xz-utils \
    libtinfo5 \
    libncurses5 \
    usbutils \
    udev \
    device-tree-compiler \
    libpython3-dev \
    libfdt-dev \
    meson \
    && rm -rf /var/lib/apt/lists/*

# Install RISC-V Toolchain (RV32IMAC support for VexRiscv)
RUN mkdir -p /opt/riscv && \
    wget https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz && \
    tar -xzf riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz -C /opt/riscv --strip-components=1 && \
    rm riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz

# Install LiteX and its ecosystem
RUN wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py && \
    chmod +x litex_setup.py && \
    ./litex_setup.py --init --install --user

# Add litex to PATH for non-interactive shells
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

# Container expects Quartus to be mounted at /opt/intelFPGA_lite/
