#!/usr/bin/env python3
"""
============================================================
 Smart Docker Environment Launcher
 - Checks if Docker is installed (installs if missing)
 - If a Dockerfile exists, build/reuse local image
 - Otherwise use official ubuntu:24.04
 - Mounts the current directory into the container
 - Opens an interactive bash shell
 Usage: python3 run_docker_attach.py
============================================================
"""

import os
import subprocess
import sys

# --- Configuration ---
PROJECT_DIR = os.path.abspath(os.getcwd())
DOCKERFILE_PATH = os.path.join(PROJECT_DIR, "Dockerfile")
IMAGE_NAME = None  # determined dynamically

def run_cmd(cmd, check=True):
    """Run a shell command and print it."""
    print(f"💻 {cmd}")
    return subprocess.run(cmd, shell=True, check=check)

def install_docker():
    """Install Docker if it’s missing."""
    print("🐳 Installing Docker...")
    run_cmd("sudo apt update")
    run_cmd("sudo apt install -y docker.io")
    run_cmd("sudo systemctl enable --now docker")
    run_cmd(f"sudo usermod -aG docker {os.getenv('USER')}")
    print("✅ Docker installed successfully. You may need to re-login for group changes to apply.")

def check_docker():
    """Ensure Docker is installed."""
    try:
        subprocess.run("docker --version", shell=True, check=True, stdout=subprocess.DEVNULL)
        print("✅ Docker is already installed.")
    except subprocess.CalledProcessError:
        install_docker()

def ensure_image():
    """
    Build or reuse image depending on whether Dockerfile exists.
    - If Dockerfile exists and image is missing → build it.
    - If Dockerfile exists and image exists → reuse it.
    - If no Dockerfile → fallback to ubuntu:24.04.
    """
    global IMAGE_NAME
    if os.path.exists(DOCKERFILE_PATH):
        # Use folder name as image tag (e.g., aca-gem5 → aca-gem5:latest)
        folder_name = os.path.basename(PROJECT_DIR)
        IMAGE_NAME = f"{folder_name.lower()}:latest"

        print(f"📦 Dockerfile found. Target image: {IMAGE_NAME}")
        result = subprocess.run(f"docker image inspect {IMAGE_NAME}", shell=True)
        if result.returncode != 0:
            print("🛠️  Image not found. Building from Dockerfile...")
            run_cmd(f"docker build -t {IMAGE_NAME} {PROJECT_DIR}")
        else:
            print(f"✅ Image '{IMAGE_NAME}' already exists. Reusing it.")
    else:
        IMAGE_NAME = "ubuntu:24.04"
        print("⚙️ No Dockerfile found. Using default base image 'ubuntu:24.04'.")

def start_container():
    """Run a temporary container and mount the current directory."""
    print(f"🚀 Launching container using image '{IMAGE_NAME}' with {PROJECT_DIR} mounted...")
    cmd = (
        f"docker run -it --rm "
        f"-v {PROJECT_DIR}:/workspace "
        f"-w /workspace "
        f"{IMAGE_NAME} bash"
    )
    os.execvp("bash", ["bash", "-c", cmd])  # replace current process with docker shell

def main():
    print(f"🔧 Current directory: {PROJECT_DIR}")
    check_docker()
    ensure_image()
    start_container()

if __name__ == "__main__":
    main()