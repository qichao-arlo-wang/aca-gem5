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
parser.add_argument('--gen-trace', action='store_true', help="Generate an instruction trace for Konata (warning: can use up disk space fast!)")
parser.add_argument('--pipeline-width', type=int, help="Number of instructions in each stage of the pipeline at a time. Default = 8.")
parser.add_argument('--rob-size', type=int, help="Number of reorder buffer entries. Default = 512.")
parser.add_argument('--num-int-phys-regs', type=int, help="Number of integer physical registers. Default = 512.")
parser.add_argument('--num-float-phys-regs', type=int, help="Number of float physical registers. Default = 512.")
parser.add_argument('--num-vec-phys-regs', type=int, help="Number of vector physical registers. Default = 512.")
parser.add_argument('--iq-size', type=int, help="Number of instruction queue entries. Default = 337.")
parser.add_argument('--lq-size', type=int, help="Number of load queue entries. Default = 169.")
parser.add_argument('--sq-size', type=int, help="Number of store queue entries. Default = 93.")
parser.add_argument('--lsq-size', type=int, help="Set load and store queue entries together.")
parser.add_argument('--window-size', type=str, help="Sets the size of the whole instruction window. Pass comma separated list of numbers to specify ROB, IQ and LSQ respectively. Number of physical regs is set to match ROB size.")
parser.add_argument('--local-pred-size', type=int, help="Number of local branch predictor entries. Default = 1024.")
parser.add_argument('--global-pred-size', type=int, help="Number of global branch predictor entries. Default = 2048.")
parser.add_argument('--btb-size', type=int, help="Number of branch target buffer entries (for branch predictor). Default = 1024.")
parser.add_argument('--ras-size', type=int, help="Number of return address stack entries (for branch predictor). Default = 16.")
parser.add_argument('--branch-pred-size', type=str, help="Sets the size of the whole branch predictor. Pass comma separated list of numbers to specify local predictor size, global predictor size, branch target buffer and return address stack respectively.")
parser.add_argument('--l1-data-size', type=int, help="Size in KB of L1 data cache. Default = 128.")
parser.add_argument('--l1-inst-size', type=int, help="Size in KB of L1 instruction cache. Default = 128.")
parser.add_argument('--l2-size', type=int, help="Size in MB of L2 cache. Default = 8.")

args = parser.parse_args()

name = args.name if args.name else pid
prefix = "-P \"system.cpu[:]."
branch_prefix = "-P \"system.cpu[:].branchPred."
configs = []

if args.pipeline_width is not None:
    if not args.pipeline_width:
        print("Pipeline width cannot be 0!")
        exit(1)
    if args.pipeline_width < 4:
        print("Pipeline width must be at least 4!")
        exit(1)
    stages = ["fetch", "decode", "rename", "dispatch", "issue", "wb", "squash", "commit"]
    for stage in stages:
        configs.append(prefix+stage+"Width="+str(args.pipeline_width)+"\" ")

if args.window_size:
    values = args.window_size.split(",")
    for v in values:
        if not v.isnumeric():
            parser.print_usage()
            print("simulate.py: error: argument --window-size: invalid int value: "+v)
            exit(1)
    components = ["numROBEntries", "numIQEntries", "LQEntries"]
    if len(values) != len(components): 
        print("Please provide "+str(len(components))+" values for --window-size as follows:")
        print("Number of ROB entries, number of IQ entries, number of LSQ entries")
        exit(1)
    for component, size in zip(components,values):
        if component == components[0] and int(size) < 16:
            print("Mininum ROB size must be at least 16!")
            exit(1)
        elif int(size) <= 0:
            print("Instruction window sizes must be non-zero!")
            exit(1)
        configs.append(prefix+component+"="+size+"\" ")
    configs.append(prefix+"SQEntries"+"="+values[-1]+"\" ")
    num_regs = values[0] if int(values[0]) >= 49 else 49
    regs = ["numPhysIntRegs", "numPhysFloatRegs", "numPhysVecRegs"]
    for reg in regs:
        configs.append(prefix+reg+"="+str(num_regs)+"\" ")

if args.branch_pred_size:
    values = args.branch_pred_size.split(",")
    for v in values:
        if not v.isnumeric():
            parser.print_usage()
            print("simulate.py: error: argument --branch-pred-size: invalid int value: "+v)
            exit(1)
    components = ["localPredictorSize", "globalPredictorSize", "btb.numEntries", "ras.numEntries"]
    if len(values) != len(components):
        print("Please provide "+str(len(components))+" values for --branch-pred-size as follows:")
        print("Local predictor size, global predictor size, branch target buffer size, return address stack size")
        exit(1)
    for component, size in zip(components,values):
        if int(size) & (int(size)-1) or int(size) <= 0:
            print("Branch predictor sizes must be powers of 2 and non-zero!")
            exit(1)
        if component == components[-1] and int(values[-1]) < 16:
            print("Minimum return address stack entries must be at least 16!")
            exit(1)
        if component == components[-2] and int(values[-2]) < 128:
            print("Minimum branch target buffer entries must be at least 128!")
            exit(1)
        configs.append(branch_prefix+component+"="+size+"\" ")
    #hacking this in so students have less to worry about
    configs.append(branch_prefix+"localHistoryTableSize="+values[0]+"\" ")

if args.rob_size is not None: 
    if args.rob_size < 16:
        print("Minimum ROB size must be at least 16!")
        exit(1)
    configs.append(prefix+"numROBEntries="+str(args.rob_size)+"\" ")

if args.num_int_phys_regs: 
    if args.num_int_phys_regs < 49:
        print("Minimum number of physical registers must be at least 49!")
        exit(1)
    configs.append(prefix+"numPhysIntRegs="+str(args.num_int_phys_regs)+"\" ")
if args.num_float_phys_regs is not None: 
    if args.num_float_phys_regs < 49:
        print("Minimum number of physical registers must be at least 49!")
        exit(1)
    configs.append(prefix+"numPhysFloatRegs="+str(args.num_float_phys_regs)+"\" ")
if args.num_vec_phys_regs is not None: 
    if args.num_vec_phys_regs < 49:
        print("Minimum number of physical registers must be at least 49!")
        exit(1)
    configs.append(prefix+"numPhysVecRegs="+str(args.num_vec_phys_regs)+"\" ")
if args.iq_size is not None: 
    if not args.iq_size:
        print("Number of IQ entries cannot be zero!")
        exit(1)
    configs.append(prefix+"numIQEntries="+str(args.iq_size)+"\" ")
if args.lsq_size is not None:
    if not args.lsq_size:
        print("Number of LSQ entries cannot be zero!")
        exit(1)
    configs.append(prefix+"LQEntries="+str(args.lsq_size)+"\" ")
    configs.append(prefix+"SQEntries="+str(args.lsq_size)+"\" ")
if args.lq_size is not None: 
    if not args.lq_size:
        print("Number of LQ entries cannot be zero!")
        exit(1)
    configs.append(prefix+"LQEntries="+str(args.lq_size)+"\" ")
if args.sq_size is not None: 
    if not args.sq_size:
        print("Number of SQ entries cannot be zero!")
        exit(1)
    configs.append(prefix+"SQEntries="+str(args.sq_size)+"\" ")
if args.local_pred_size:
    if args.local_pred_size & (args.local_pred_size-1):
        print("Branch predictor sizes must be powers of 2!")
        exit(1)
    configs.append(branch_prefix+"localPredictorSize="+str(args.local_pred_size)+"\" ")
    configs.append(branch_prefix+"localHistoryTableSize="+str(args.local_pred_size)+"\" ")
if args.global_pred_size is not None:
    if args.global_pred_size & (args.global_pred_size-1) or args.global_pred_size <= 0:
        print("Branch predictor sizes must be powers of 2 and non-zero!")
        exit(1)
    configs.append(branch_prefix+"globalPredictorSize="+str(args.global_pred_size)+"\" ")
if args.btb_size is not None: 
    if args.btb_size < 128:
        print("Minimum branch target buffer entries must be at least 128!")
        exit(1)
    if args.btb_size & (args.btb_size-1):
        print("Branch predictor sizes must be powers of 2!")
        exit(1)
    configs.append(branch_prefix+"btb.numEntries="+str(args.btb_size)+"\" ")
if args.ras_size is not None: 
    if args.ras_size < 16:
        print("Minimum return address stack entries must be at least 16!")
        exit(1)
    if args.ras_size & (args.ras_size-1):
        print("Branch predictor sizes must be powers of 2!")
        exit(1)
    configs.append(branch_prefix+"ras.numEntries="+str(args.ras_size)+"\" ")
if args.l1_data_size is not None: 
    if args.l1_data_size < 2:
        print("Minimum l1 cache sizes must be at least 2KiB!")
        exit(1)
    if args.l1_data_size & (args.l1_data_size-1):
        print("Cache sizes must be powers of 2!")
        exit(1)
    configs.append("--l1d_size="+str(args.l1_data_size)+"KiB ")
else: configs.append("--l1d_size=128KiB ")
if args.l1_inst_size is not None: 
    if args.l1_inst_size < 2:
        print("Minimum l1 cache sizes must be at least 2KiB!")
        exit(1)
    if args.l1_inst_size & (args.l1_inst_size-1):
        print("Cache sizes must be powers of 2!")
        exit(1)
    configs.append("--l1i_size="+str(args.l1_inst_size)+"KiB ")
else: configs.append("--l1i_size=128KiB ")
if args.l2_size is not None: 
    if args.l2_size & (args.l2_size-1) or args.l2_size <= 0:
        print("Cache sizes must be powers of 2 and non-zero!")
        exit(1)
    configs.append("--l2_size="+str(args.l2_size)+"MB ")
else: configs.append("--l2_size=8MB ")

if args.gen_trace: name = "/vol/bitbucket/lp721/"+name
os.makedirs(name, exist_ok=True)

gem5_outdir = name+"/gem5.out"
gem5_bin = "build/X86/gem5.opt --debug-flags=O3PipeView --debug-file=trace.out" if args.gen_trace else "build/X86/gem5.fast"
gem5_run = gem5+gem5_bin+" --outdir="+gem5_outdir+" "+gem5+"configs/deprecated/example/se.py --cpu-type=DerivO3CPU --caches --l2cache -c "+benchmark+" --options=\""+benchmark_args+"\" "
gem5_run += ' '.join(configs)
subprocess.run(gem5_run, shell=True, check=True)

gem5tomcpat_run = "python "+gem5tomcpat+" --config "+gem5_outdir+"/config.json --stats "+gem5_outdir+"/stats.txt --template "+mcpat+"/ProcessorDescriptionFiles/template_x86.xml --output "+name+"/mcpat-in.xml"
subprocess.run(gem5tomcpat_run, shell=True, check=True, capture_output=True)

mcpat_run = mcpat+"mcpat -infile "+name+"/mcpat-in.xml -print_level 1 -opt_for_clk 1"
mcpat_output = subprocess.run(mcpat_run, shell=True, check=True, capture_output=True, text=True).stdout
power_output = mcpat_output.split("\n")[21:26]
power_output = '\n'.join(power_output)
with open(name+"/gem5.out/stats.txt", "r") as gem5_output:
    cpi = None
    simseconds = None
    print()
    for line in gem5_output:
        if 'system.cpu.cpi' in line:
            match = re.search(r'\d+.\d+', line)
            if not match:
                print("Error grepping gem5 output")
                exit(1)
            cpi = match.group(0)
        elif 'simSeconds' in line:
            match = re.search(r'\d+.\d+', line)
            if not match:
                print("Error grepping gem5 output")
                exit(1)
            simseconds = match.group(0)
    if not cpi or not simseconds:
        print("Error grepping gem5 output")
        exit(1)
    print("    Simulated seconds = "+simseconds)
    print("    CPI = "+cpi)
    with open(name+"/results", "w") as f:
        f.write("    Simulated seconds = "+simseconds+"\n")
        f.write("    CPI = "+cpi+"\n")
        f.write(power_output)
        f.write("\n")
    f.close()

print(power_output)
print()
print("Results have been written to: "+name+"/results")
