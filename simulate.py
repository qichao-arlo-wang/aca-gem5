import argparse
import os
import subprocess
import re

pid = str(os.getpid())
gem5 = "/homes/lp721/aca-gem5/gem5/"
mcpat = "/homes/lp721/aca-gem5/mcpat/"
gem5tomcpat = "/homes/lp721/aca-gem5/gem5tomcpat.py"
benchmark = "/homes/lp721/aca-gem5/benchmarks/micro-lisp/mlisp89"
benchmark_args = "/homes/lp721/aca-gem5/benchmarks/micro-lisp/examples/"

parser = argparse.ArgumentParser(description="Script to run Gem5 ACA Simulations. This script will create several output files in whatever directory you run it, so you may want to create a new directory to keep things clean! Contact lp721@ic.ac.uk with any problems.")

parser.add_argument('--name', type=str, help="Name used for results file. If unspecified, process ID of the script is used.")
parser.add_argument('--pipeline-width', type=int, help="Number of instructions in each stage of the pipeline at a time. Default = 8.")
parser.add_argument('--rob-size', type=int, help="Number of reorder buffer entries. Default = 112.")
parser.add_argument('--num-int-phys-regs', type=int, help="Number of integer physical registers. Default = 112.")
parser.add_argument('--num-int-float-regs', type=int, help="Number of float physical registers. Default = 112.")
parser.add_argument('--num-int-vec-regs', type=int, help="Number of vector physical registers. Default = 112.")
parser.add_argument('--iq-size', type=int, help="Number of instruction queue entries. Default = 71.")
parser.add_argument('--lq-size', type=int, help="Number of load queue entries. Default = 30.")
parser.add_argument('--sq-size', type=int, help="Number of store queue entries. Default = 18.")
parser.add_argument('--lsq-size', type=int, help="Set load and store queue entries together.")
parser.add_argument('--window-size', type=str, help="Sets the size of the whole instruction window. Pass comma separated list of numbers to specify ROB, number of int regs, float regs, vec regs, IQ and LSQ respectively.")
parser.add_argument('--local-pred-size', type=int, help="Number of local branch predictor entries. Default = 1024.")
parser.add_argument('--global-pred-size', type=int, help="Number of global branch predictor entries. Default = 4096.")
parser.add_argument('--btb-size', type=int, help="Number of branch target buffer entries (for branch predictor). Default = 1024.")
parser.add_argument('--ras-size', type=int, help="Number of return address stack entries (for branch predictor). Default = 16.")
parser.add_argument('--branch-pred-size', type=int, help="Sets the size of the whole branch predictor. Pass comma separated list of numbers to specify local predictor size, global predictor size, branch target buffer and return address stack respectively.")
parser.add_argument('--l1-data-size', type=int, help="Size in KB of L1 data cache. Default = 128.")
parser.add_argument('--l1-inst-size', type=int, help="Size in KB of L1 instruction cache. Default = 128.")
parser.add_argument('--l2-size', type=int, help="Size in MB of L2 cache. Default = 4.")

args = parser.parse_args()

name = args.name if args.name else pid
prefix = "-P \"system.cpu[:]."
branch_prefix = "-P \"system.cpu[:].branchPred."
configs = []

if args.pipeline_width:
    stages = ["fetch", "decode", "rename", "dispatch", "issue", "wb", "squash", "commit"]
    for stage in stages:
        configs.append(prefix+stage+"Width="+args.pipeline_width+"\" ")

if args.window_size:
    values = args.window_size.split(",")
    for v in values:
        if not v.isnumeric():
            parser.print_usage()
            print("simulate.py: error: argument --window-size: invalid int value: "+v)
            exit(1)
    components = ["numROBEntries", "numPhysIntRegs", "numPhysFloatRegs", "numPhysVecRegs", "numIQEntries", "numLQEntries", "numSQEntries"]
    for component, size in zip(components,values):
        configs.append(prefix+component+"="+size+"\" ")

if args.branch_pred_size:
    values = args.branch_pred_size.split(",")
    for v in values:
        if not v.isnumeric():
            parser.print_usage()
            print("simulate.py: error: argument --branch-pred-size: invalid int value: "+v)
            exit(1)
    components = ["localPredictorSize", "globalPredictorSize", "btb.numEntries", "ras.numEntries"]
    for component, size in zip(components,values):
        configs.append(branch_prefix+component+"="+size+"\" ")
    #hacking this in so students have less to worry about
    configs.append(branch_prefix+"localHistoryTableSize="+values[0]+"\" ")

if args.rob_size: configs.append(prefix+"numROBEntries="+str(args.rob_size)+"\" ")
if args.iq_size: configs.append(prefix+"numIQEntries="+args.iq_size+"\" ")
if args.lsq_size:
    configs.append(prefix+"numLQEntries="+args.lq_size+"\" ")
    configs.append(prefix+"numSQEntries="+args.sq_size+"\" ")
if args.lq_size: configs.append(prefix+"numLQEntries="+args.lq_size+"\" ")
if args.sq_size: configs.append(prefix+"numSQEntries="+args.sq_size+"\" ")
if args.local_pred_size:
    configs.append(branch_prefix+"localPredictorSize="+args.local_pred_size+"\" ")
    configs.append(branch_prefix+"localHistoryTableSize="+args.local_pred_size+"\" ")
if args.global_pred_size: configs.append(branch_prefix+"globalPredictorSize="+args.global_pred_size+"\" ")
if args.btb_size: configs.append(branch_prefix+"btb.numEntries="+args.btb_size+"\" ")
if args.ras_size: configs.append(branch_prefix+"ras.numEntries="+args.ras_size+"\" ")
if args.l1_data_size: configs.append("--l1d_size="+args.l1_data_size+"KiB ")
else: configs.append("--l1d_size=128KiB ")
if args.l1_inst_size: configs.append("--l1i_size="+args.l1_inst_size+"KiB ")
else: configs.append("--l1i_size=128KiB ")
if args.l2_size: configs.append("--l2_size="+args.l2_size+"MB ")
else: configs.append("--l2_size=4MB ")

gem5_outdir = name+".out"
gem5_run = gem5+"build/X86/gem5.fast --outdir="+gem5_outdir+" configs/deprecated/examples/se.py --cpu-type=DerivO3CPU --caches --l2cache -c "+benchmark+" --options=\""+benchmark_args+"\" "
gem5_run += ' '.join(configs)
subprocess.run(gem5_run, shell=True, check=True)

gem5tomcpat_run = "python "+gem5tomcpat+" --config "+gem5_outdir+"/config.json --stats "+gem5_outdir+"/stats --template "+mcpat+"/ProcessorDescriptionFiles/template_x86.xml --output "+name+".xml"
subprocess.run(gem5tomcpat_run, shell=True, check=True, capture_output=True)

mcpat_run = mcpat+" -infile "+name+".xml -print_level 1 -opt_for_clk 0"
mcpat_output = subprocess.run(mcpat_run, shell=True, check=True, capture_output=True, text=True).stdout
power_output = mcpat_output.split("\n")[19:26]
del power_output[1]
power_output[0] = "Core"
power_output = '\n'.join(power_output)

with open(name+".out", "r") as gem5_output:
    for line in gem5_output:
        if 'system.cpu.cpi' in line:
            match = re.search(r'\d+.\d+', line)
            if not match:
                print("Error grepping gem5 output")
                exit(1)
            cpi = match.group(0)
            print("Cycles per instruction: "+cpi)
            with open("power_usage."+name, "w") as f:
                f.write("Cycles per instruction: "+cpi+"\n")
                f.write(power_output)
            f.close()

print("Core power usage:")
print(power_output)
print("Results have been written to: power_usage."+name)
