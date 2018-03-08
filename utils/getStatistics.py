import os,re,math,sys
import numpy

def importData(file):
    if not os.path.exists(file):
        msg = 'File does not exist: %s' % file
        sys.exit(msg)
    f = open(file ,"r")
    data =[]
    line = f.readline()
    while line:
        words = line.split()
        datablock=[]
        for iw in range(1,len(words)) :
            datablock.append(float(words[iw]))
        data.append(datablock)
        line = f.readline()
    f.close()
    return data

inpfilename=sys.argv[1] # the output file from impact
neq=int(sys.argv[2])
nprod=int(sys.argv[3])
nskip=int(sys.argv[4])
nprnt=int(sys.argv[5])
ncol=int(sys.argv[6])

datai=importData(inpfilename)
n=len(datai)
nf=len(datai[0])

dataout=[]

file=open('lbe_statistics.dat','w')
for i in range(nskip,n/(neq+nprod)):
   for j in range(0,nprod,nprnt):
       k=i*(neq+nprod)+ neq + j 
       dataout.append(datai[k][ncol:])
   minvalue=numpy.min(dataout,axis=0)
   meanvalue=numpy.mean(dataout, axis=0)
   stdvalue=numpy.std(dataout, axis=0)
   for im in range(0,len(meanvalue)) :
       file.write("%12.6f\t%12.6f\t%12.6f\t" %(minvalue[im],meanvalue[im],stdvalue[im]))
   file.write("\n")

file.close()


#print "finishreadingfile"
#file=open('lbe.dat','a')
#
#for i in range(nskip,(n/nprnt)-1):
#    tem=datai[i*nprnt][1]
#    tot=datai[i*nprnt][3]
#    pot=datai[i*nprnt][5]
#    lmb = datai[i*nprnt][nf-2]
#    u = datai[i*nprnt][nf-1]
#    file.write('%s\t%s\t%s\t%s\t%s\n' %(tem,tot,pot,lmb,u))
#file.close()
