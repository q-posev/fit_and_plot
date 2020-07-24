from sys import argv,exit
from re import search as reg_search
from imp import find_module
# perform sanity check of required modules
try:
    find_module('numpy')
except ImportError:
    print("Numpy is required")
    exit()
try:
    find_module('matplotlib')
except ImportError:
    print("Matplotlib is required")
    exit()
try:
    find_module('pandas')
except ImportError:
    print("Pandas is required")
    exit()
try:
    find_module('scipy')
except ImportError:
    print("Scipy is required")
    exit()

from pandas import read_csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

print("The arguments are: " , str(argv))
print('')
plt_err = False
prt_mol = False
do_gaps = False
l1 = 0
hpc = ''
n_st = 0
init_st = 0
#------------------- SEE THE EXECUTION EXAMPLE BELOW: ----------------#
#--------   python this_script_name.py -h s10 -t 100 -n 9 -s 8 -pe ---#
#------ Data from: s10; Trajectories: 100; Number of states: 9; ------#
#-----      Initial state: 8; Plot WITH error bar (-pe option)  ------#
#---------------------------------------------------------------------#

# read file todolist with list of jobs to be processed
todo = read_csv('todolist',skiprows=0,header=None)
todo.columns = ["job"]

# read arguments and settings
for index, arg in enumerate(argv):    
    if arg in ['--info', '-i']:
        arg_list=['--hpc', '-h']+['--traj_number', '-t']
        arg_list=arg_list+['--n_states', '-n']+['--init_state', '-s']
        print('Required keywords/arguments: ',arg_list)
        print('Optional keywords/arguments: [\'--folder\', \'-f\', \'--plt_err\', \'-pe\','
                ' \'--mol_name\', \'-m\',\'--gaps\', \'-g\']')
        exit()

for index, arg in enumerate(argv):    
    if arg in ['--hpc', '-h']:
        if len(argv) > index + 1:
          hpc = str(argv[index + 1])
          if hpc not in ['s10','oly']:
            print('Available option for HPC: s10, oly')
            exit()
          else:
            del argv[index]
            del argv[index]
            break
        else:
            print('Enter the HPC name: s10 or oly (after --hpc or -h keyword)')
            exit()

if hpc=='oly':
    for index, arg in enumerate(argv):
        if arg in ['--folder', '-f']:
            if len(argv) > index + 1:
                oly_jobid = str(argv[index + 1])
                if oly_jobid=='':
                    print('Folder from OLYMPE has to be the same as slurm job_id')
                    exit()
                else:
                    del argv[index]
                    del argv[index]
                    break    
            else:
                print('Enter the name of slurm job_id from OLYMPE (after --folder or -f keyword)')
                exit()

for index, arg in enumerate(argv):    
    if arg in ['--traj_number', '-t']:
        if len(argv) > index + 1:
          l1 = int(argv[index + 1])
          if l1 < 1:
            print('Number of trajetories has to be > 0')
            exit()
          else:
            del argv[index]
            del argv[index]
            break
        else:
            print('Enter the number of trajectories in TSH (after --traj_number or -t keyword)')
            exit()

for index, arg in enumerate(argv):
    if arg in ['--n_states', '-n']:
        if len(argv) > index + 1:
          n_st = int(argv[index + 1])
          if n_st < 2:
            print('Number of states has to be > 1')
            exit()
          else:
            del argv[index]
            del argv[index]
            break
        else:
            print('Enter the number of states in TSH (after --n_states or -n keyword)')
            exit()
    
for index, arg in enumerate(argv):
    if arg in ['--init_state', '-s']:
        if len(argv) > index + 1:
          init_st = int(argv[index + 1])
          if init_st < 1:
            print('Initial state has to be > 0')
            exit()
          else:
            del argv[index]
            del argv[index]
            break
        else:
            print('Enter the initial state in TSH (after --init_state or -s keyword)')
            exit()

for index, arg in enumerate(argv):    
    if arg in ['--plt_err', '-pe']:
        plt_err= True
        print('Population will be plotted with error bar')
        del argv[index]
        break

for index, arg in enumerate(argv):    
    if arg in ['--gaps', '-g']:
        do_gaps = True
        print('Additional file with energy gaps will be generated')
        del argv[index]
        break

for index, arg in enumerate(argv):    
    if arg in ['--mol_name', '-m']:
        if len(argv) > index + 1:
            mol_name = str(argv[index + 1])
            prt_mol = True
            del argv[index]
            del argv[index]
            break
        else:
            print('Enter the molecule name for the output file (after --mol_name or -m keyword)')

if l1==0 or n_st==0 or init_st==0 or hpc=='':
    print('One of the main arguments is missing, use --info or -i argument for more info')
    exit()

if hpc=='oly':
    print('Data from OLYMPE machine')
if hpc=='s10':
    print('Data from s10 machine')

print('Number of trajectories   = {}'.format(l1))
print('Number of states in TSH  = {}'.format(n_st))
print('Initial state in TSH     = {}\n'.format(init_st))

# initialize the energy list
en_list=[]
for k in range(1,n_st+1):
    en_list.append('e'+str(k))
en_list.append('e_cur')

if do_gaps:
    j_gap = 0
    k_gap = 0
    N_gap = 1
    font = {'size'   : 18}
    plt.rc('font', **font)
    fig, axs = plt.subplots(1, 1)
    axs.yaxis.set_ticks_position('both')
    axs.xaxis.set_ticks_position('both')

# loop over all trajectories/jobs
for i in range(0,l1):
    # set files with data to be read
    if hpc=='oly':
        ener_file = oly_jobid+str(i)+'.demon' +'/'+'deMon.tsh'
    else :
        ener_file = str(todo.job[i])+'/'+'deMon.tsh'
    
    if i==0 :
        df0 = read_csv(ener_file,skiprows=8,sep='  ',header=None,engine='python')
        df0.columns = ['time','cur_st','gs']+en_list
        l2 = len(df0.time)
        t=df0.time
        acc = np.zeros([l2, n_st+1])
    
    df = read_csv(ener_file,skiprows=8,sep='  ',header=None,engine='python')
    df.columns = ['time','cur_st','gs']+en_list
    for k in range(0,l2):
        for j in range(1,n_st+1):
            if (df.cur_st[k]==j):
                acc[k,j]=acc[k,j]+1.0

    # plot energy gaps between Initial State and the one below for each N_spec-th trajectory
    if do_gaps:
        if ((j_gap+1)%N_gap==0):
            if ((j_gap+1)==N_gap): 
                df11 = read_csv(ener_file,skiprows=8,sep='  ',header=None,engine='python')
                df11.columns = ['time','cur_st','gs']+en_list
                df11.e_cur = 0.0
            #---------------------------------------------------------------------#
            #--- CHANGE eX and eX-1 BELOW TO BE EQUAL TO INIT_ST AND INIT_ST-1 ---#
            #---------------------------------------------------------------------#
            axs.plot(t,abs(df.e7-df.e6)*27.211,'r-')            
            if ((j_gap+1)>N_gap):
                df11.e_cur = df11.e_cur+abs(df.e7-df.e6)
            #---------------------------------------------------------------------#        
            k_gap+=1
        
        j_gap+=1

#---------------------------------------------------------------------#        
#----------------------------- PLOT GAPS -----------------------------#
#---------------------------------------------------------------------#        
if do_gaps:
    # matplotlib settings
    plt.xlim(0.0,100.0)
    plt.ylim(0.0,0.4)
    plt.xlabel('Time [fs]')
    #print("  Number of processed energy files: {}".format(k_gap))
    axs.minorticks_on()
    axs.tick_params(axis='both',which='minor',length=4,width=1,labelsize=18)
    axs.tick_params(axis='both',which='major',length=8,width=1,labelsize=18)
    
    df11.e_cur = df11.e_cur/k_gap
    axs.plot(t,df11.e_cur*27.211,'k--')
    # set Conical Intersection threshold values
    coin=np.zeros(l2)
    for i1 in range(0,l2):
        coin[i1] = 0.0004*27.211

    #plt.suptitle('Chrysene', fontsize=18)
    plt.plot(t,coin,'k-')
    plt.ylabel('$E_{'+str(init_st)+'} - E_{'+str(init_st-1)+'}$ [eV]')
    # build output filename
    fileformat = 'png'
    if prt_mol:
        output_name = '{}-'.format(mol_name)
    else:
        output_name = ''
    output_name = output_name + 'gaps-{0}traj-initST-{1}-totalST-{2}.'.format(l1,init_st,n_st)

    output_name = output_name + fileformat
    
    print('Output file: {}'.format(output_name))
    plt.savefig(output_name, bbox_inches='tight',format=fileformat,dpi=600)
    plt.clf()

#print("  Number of processed trajectories: {}".format(l1))
# average populations over the ensemble of trjaectories
acc /= l1

# output occupation of a given state at the end of the propagation
#print(acc[l2-1,init_st-1])

# fitting parameters
A_step = min(acc[:,init_st])
A_decay = 1./(1.+A_step)
A_step2 = A_step/(1.+A_step)
# fitting function
def exp_func(x, b):
        return (np.exp(-b*x)+A_step)*A_decay
t=df0.time
fit_s2 = np.zeros(l2)
#---------------------------------------------------------------------#
#--------- FIT THE INITIAL STATE POPULATION WITH EXPONENT ------------#
#---------------------------------------------------------------------#
popt,pcov = curve_fit(exp_func,t,acc[:,init_st],p0=(0.025))
#---------------------------------------------------------------------#
print('  Decay time of S{0} = {1:.3f} fs \n'.format(init_st,float(1./popt)))
fit_s2 = exp_func(t,*popt)
#---------------------------------------------------------------------#
#---------------- STATISTICAL ERROR ESTIMATION -----------------------#
#---------------------------------------------------------------------#
if plt_err:
    fit_max = np.zeros(l2)
    fit_min = np.zeros(l2)
    eps = 0.98/np.sqrt(l1)
    tau_fit = 1.0/popt
    tau_max = (1.+eps)*tau_fit
    tau_min = (1.-eps)*tau_fit
    #print(tau_max,tau_min)
    fit_max = exp_func(t,1./tau_max)
    fit_min = exp_func(t,1./tau_min)
#---------------------------------------------------------------------#
#--------------------- MATPLOTLIB SETTINGS ---------------------------#
#---------------------------------------------------------------------#
font = {'size'   : 18}
plt.rc('font', **font)
ax1 = plt.subplot(111)
ax1.grid()
#-------- DO NOT FORGET TO CHANGE THE X-AXIS LIMIT/RANGE BELOW -------#
ax1.set_xlim((0.0, 300.0)) 
ax1.set_ylim((0.0, 1.0))
#---------------------------------------------------------------------#
ax1.minorticks_on()
ax1.tick_params(axis='both',which='minor',length=4,width=1,labelsize=18)
ax1.tick_params(axis='both',which='major',length=8,width=1,labelsize=18)
ax1.set_xlabel('Time [fs]')
ax1.set_ylabel('Occupation')
#---------------------------------------------------------------------#
#------ MODIFY THE PART BELOW TO PLOT THE POPULATIONS OF INTEREST  ---#
#---------------------------------------------------------------------#
ax1.plot(t,acc[:,1]+acc[:,2]+acc[:,3]+acc[:,4],t,acc[:,init_st-2],t,acc[:,init_st-1],t,acc[:,init_st],t,acc[:,init_st+1],linewidth=2.0)
ax1.plot(t,fit_s2,dashes=[6, 2],color='black',linewidth=2.0) 
#------------------- PLOT STATISTICAL ERROR --------------------------#
if plt_err:
    ax1.fill_between(t, fit_min, fit_max, facecolor='lightcoral', alpha=0.5)
#---------------------------------------------------------------------#
ax1.legend(('$S_{1-4}$', '$S_{'+str(init_st-2)+'}$', '$S_{'+str(init_st-1)+'}$', '$S_{'+str(init_st)+'}$', '$S_{'+str(init_st+1)+'}$', '$S_{'+str(init_st)+'}$ fit'),loc='upper center', bbox_to_anchor=(0.515, 1.28),ncol=3, fancybox=True, shadow=True) 
#------------------------- SET OUTPUT FILENAME -----------------------#
if prt_mol:
    output_name = '{}-'.format(mol_name)
else:
    output_name = ''
output_name = output_name + 'occ-{0}traj-initST-{1}-totalST-{2}-tau-{3:.0f}.'.format(l1,init_st,n_st,float(1./popt))
#------------------------- SET OUTPUT FORMAT -------------------------#
fileformat = 'png'
output_name = output_name + fileformat
#------------------------- SAVE THE FIGURE  --------------------------#
print('Output file: {}'.format(output_name))
plt.savefig(output_name, bbox_inches='tight',format=fileformat,dpi=600)
