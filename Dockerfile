FROM ubuntu:24.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# --- System-level dependencies ---
COPY apt-requirements.txt /tmp/apt-requirements.txt
RUN apt update && \
    apt install -y python3 python3-pip python3-venv && \
    xargs -a /tmp/apt-requirements.txt apt install -y && \
    apt clean && rm -rf /var/lib/apt/lists/*

# --- Python environment ---
COPY requirements.txt /tmp/requirements.txt

# Create isolated venv and install Python packages
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# --- Default working directory ---
WORKDIR /aca

# Default shell
CMD ["bash"]