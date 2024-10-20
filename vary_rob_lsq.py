import subprocess

sizes = [2**i for i in range(4,10)] #16..512
mininum_int_phys_reg_size = 49 #as informed by simulate.py

for i, size in enumerate(sizes):
    name = "run_"+str(i)

    if size < mininum_int_phys_reg_size: 
        int_phys_regs = mininum_int_phys_reg_size
    else: 
        int_phys_regs = size

    #run in paralell
    subprocess.Popen("python simulate.py --rob-size "+str(size)+" --num-int-phys-regs "+str(int_phys_regs)+" --num-float-phys-regs "+str(size)+" --num-vec-phys-regs "+str(size)+" --lsq-size "+str(size)+" --name "+name, shell=True) 
