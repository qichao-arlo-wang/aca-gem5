#!/usr/bin/env python3
import subprocess
import psutil
import time
import os
import re
import pandas as pd
from pathlib import Path

# -------------------------------
# Configurations
# -------------------------------
sizes = [2**i for i in range(4, 10)]  # 16, 32, 64, 128, 256, 512
mininum_phys_reg_size = 49
max_parallel_jobs = 24

base_results_dir = Path("results")
base_results_dir.mkdir(exist_ok=True)

output_excel = base_results_dir / "vary_rob_lsq_results.xlsx"

running = []  # list of (process, name)
results = []  # collected results


def parse_results(folder_name):
    """Parse results file for CPI, simSeconds, and power info."""
    result_file = base_results_dir / folder_name / "results"
    if not result_file.exists():
        print(f"⚠️ Warning: results file not found for {folder_name}")
        return None

    data = {
        "name": folder_name,
        "rob": None,
        "lsq": None,
        "SimulatedSeconds": None,
        "CPI": None,
        "Area_mm2": None,
        "PeakDynamic_W": None,
        "SubthresholdLeakage_W": None,
        "GateLeakage_W": None,
        "RuntimeDynamic_W": None,
    }

    # extract rob and lsq from folder name
    match = re.match(r"rob_(\d+)_lsq_(\d+)", folder_name)
    if match:
        data["rob"], data["lsq"] = match.groups()

    # Read and extract metrics
    with open(result_file) as f:
        for line in f:
            if "Simulated seconds" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["SimulatedSeconds"] = float(m.group())
            elif "CPI" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["CPI"] = float(m.group())
            elif "Area" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["Area_mm2"] = float(m.group())
            elif "Peak Dynamic" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["PeakDynamic_W"] = float(m.group())
            elif "Subthreshold Leakage" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["SubthresholdLeakage_W"] = float(m.group())
            elif "Gate Leakage" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["GateLeakage_W"] = float(m.group())
            elif "Runtime Dynamic" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["RuntimeDynamic_W"] = float(m.group())

    return data


def write_excel(data_list, path):
    """Write results to Excel (.xlsx)."""
    if not data_list:
        print("⚠️ No results to write.")
        return

    df = pd.DataFrame(data_list)
    df_sorted = df.sort_values(by=["rob", "lsq"], key=pd.to_numeric, ascending=True)
    df_sorted.to_excel(path, index=False)
    print(f"✅ Results saved to Excel: {path}")


# -------------------------------
# Simulation loop
# -------------------------------
for rob_size in sizes:
    for lsq_size in sizes:
        name = f"rob_{rob_size}_lsq_{lsq_size}"
        sim_dir = base_results_dir / name
        sim_dir.mkdir(exist_ok=True)

        phys_regs = max(rob_size, mininum_phys_reg_size)

        cmd = [
            "python3", "./simulate.py",
            "--rob-size", str(rob_size),
            "--num-int-phys-regs", str(phys_regs),
            "--num-float-phys-regs", str(phys_regs),
            "--num-vec-phys-regs", str(phys_regs),
            "--lsq-size", str(lsq_size),
            "--name", str(sim_dir)
        ]

        # control CPU load & concurrency
        while len(running) >= max_parallel_jobs or psutil.cpu_percent(interval=3) > 80:
            still_running = []
            for p, n in running:
                if p.poll() is None:
                    still_running.append((p, n))
                else:
                    res = parse_results(n)
                    if res:
                        results.append(res)
            running = still_running
            time.sleep(5)

        # start async process
        print(f"🚀 Starting simulation: {name}")
        p = subprocess.Popen(cmd)
        running.append((p, name))

# -------------------------------
# Wait for remaining processes
# -------------------------------
for p, n in running:
    p.wait()
    res = parse_results(n)
    if res:
        results.append(res)

# -------------------------------
# Save final Excel
# -------------------------------
write_excel(results, output_excel)
print("🎯 All simulations completed successfully.")