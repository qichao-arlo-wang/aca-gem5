import subprocess
import psutil
import time

sizes = [2**i for i in range(4,10)] #16..512
mininum_int_phys_reg_size = 49 #as informed by simulate.py

for i, rob_size in enumerate(sizes):
    for lsq_size in sizes:
        name = f"rob_{rob_size}_lsq_{lsq_size}"

        if rob_size < mininum_int_phys_reg_size: 
            int_phys_regs = mininum_int_phys_reg_size
        else: 
            int_phys_regs = rob_size

        #load balancer if running jobs in parallel. runs will crash if cpu usage gets too high.
        #while psutil.cpu_percent() > 70: time.sleep(30)
        #.run won't return until the program finishes. using .Popen returns immediately, meaning all runs execute in parallel (be mindful of your machine's resources though!). however, it has fewer features like capturing program output.
        subprocess.run("python /homes/lp721/aca-gem5/simulate.py --rob-size "+str(rob_size)+" --num-int-phys-regs "+str(int_phys_regs)+" --num-float-phys-regs "+str(rob_size)+" --num-vec-phys-regs "+str(rob_size)+" --lsq-size "+str(lsq_size)+" --name "+name, shell=True)
