#!/usr/bin/env python3
import subprocess
import psutil
import time
import os
import csv
import re

# -------------------------------
# Configurations
# -------------------------------
sizes = [2**i for i in range(4, 10)]  # 16, 32, 64, 128, 256, 512
mininum_phys_reg_size = 49
max_parallel_jobs = 14
output_csv = "vary_rob_lsq_results.csv"

running = []  # list of (process, name)
results = []  # collected results


def parse_results(name):
    """Parse results file for CPI, simSeconds, and power info."""
    result_file = os.path.join(name, "results")
    if not os.path.exists(result_file):
        print(f"⚠️ Warning: results file not found for {name}")
        return None

    data = {
        "name": name,
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
    match = re.match(r"rob_(\d+)_lsq_(\d+)", name)
    if match:
        data["rob"], data["lsq"] = match.groups()

    # Read and extract metrics
    with open(result_file) as f:
        for line in f:
            if "Simulated seconds" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["SimulatedSeconds"] = m.group()
            elif "CPI" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["CPI"] = m.group()
            elif "Area" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["Area_mm2"] = m.group()
            elif "Peak Dynamic" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["PeakDynamic_W"] = m.group()
            elif "Subthreshold Leakage" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["SubthresholdLeakage_W"] = m.group()
            elif "Gate Leakage" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["GateLeakage_W"] = m.group()
            elif "Runtime Dynamic" in line:
                m = re.search(r"[\d.]+", line)
                if m:
                    data["RuntimeDynamic_W"] = m.group()

    return data


def write_csv(data_list, path):
    """Write results to CSV."""
    if not data_list:
        print("⚠️ No results to write.")
        return

    keys = [
        "name", "rob", "lsq", "SimulatedSeconds", "CPI",
        "Area_mm2", "PeakDynamic_W", "SubthresholdLeakage_W",
        "GateLeakage_W", "RuntimeDynamic_W"
    ]

    with open(path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)
    print(f"✅ Results saved to {path}")


# -------------------------------
# Simulation loop
# -------------------------------
for rob_size in sizes:
    for lsq_size in sizes:
        name = f"rob_{rob_size}_lsq_{lsq_size}"
        phys_regs = max(rob_size, mininum_phys_reg_size)

        cmd = [
            "python3", "./simulate.py",
            "--rob-size", str(rob_size),
            "--num-int-phys-regs", str(phys_regs),
            "--num-float-phys-regs", str(phys_regs),
            "--num-vec-phys-regs", str(phys_regs),
            "--lsq-size", str(lsq_size),
            "--name", name
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
# Save final CSV
# -------------------------------
write_csv(results, output_csv)
print("🎯 All simulations completed successfully.")