import subprocess

sizes = [2**i for i in range(4,10)] #16..512

for i, size in enumerate(sizes):
    name = "run_"+str(i)

    #run in paralell
    subprocess.Popen("python simulate.py --rob-size "+str(size)+" --lsq-size "+str(size)+" --name "+name, shell=True) 
