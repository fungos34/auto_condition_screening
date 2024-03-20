# calculates the time according to function which is specific for a certain setup
# this script is meant to predict the duration of each experimental cycle for this specific setup (in terms of tubing volumes, excess on flushing, rector volumes, pumps, collected fraction size, the exact python script, etc. )
# it ultimately should be used to output the times which have to be set for the power source during experiments.
############################################ SETUP 1 #########################################################

import numpy as np
from matplotlib import pyplot as plt

##############################################################################################################
########################################  SETUP FUNCTION  ####################################################

#this function has to be modified for each experimental setup
def f(x): #input as flowrate (uL/min)
    y=(22400*(pow(x,-0.72))) 
    return y    #output as time (sec)

###############################################################################################################
########################################  CUMMULATE FLOWRATES  ################################################

def get_cummulated_flows(x,y):
    a=np.array(x)
    b=np.array(y)
    a+=b
    return a

###############################################################################################################
########################################  PLOTTING FUNCTION  ##################################################

def plot_time_func(x_2):
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    x = np.linspace(0, 2500, 1000)
    plt.plot(x, f(x), color='red')
    for i in range(len(x_2)):
        plt.plot(float(x_2[i]), f(float(x_2[i])), 'go-',)
        if len(x_2)==1:
            plt.annotate(f'duration: {f(float(x_2[i]))} (sec) at a flowrate of {x_2[i]} (uL/min)' , xy=(x_2[i], f(float(x2[i]))), xytext=(x_2[i], f(float(x_2[i]))))#, arrowprops=dict(facecolor='black', shrink=0.05))
        else:
            plt.annotate(f'{f(float(x_2[i]))} (sec); {x_2[i]} (uL/min)' , xy=(x_2[i], f(float(x_2[i]))), xytext=(x_2[i], f(float(x_2[i]))))
    plt.show()

#################################################################################################################
########################################  CALCULATE TIMES LIST  #################################################

def get_times(x):
    times=[]
    for i in range(len(x)):
        times.append(f(x[i]))
    return times

#################################################################################################################
################################################# RUN ###########################################################

# x2=[2500,2000,1500,1000,600,300,150,100,75,50]
# x2 = [50,150,2525,2000]

# print(get_times(x2))
# plot_time_func(x2)

##### results experiment 2 ######
# a=[80.1182052703279, 94.0819740846531, 115.73435931619903, 154.9701374858418, 223.86134979623182, 368.74039361114114, 607.3825517636901, 813.2948426850271, 1000.4696273552639, 1339.6446536508647] 
# b=[96.6335678100586, 102.73170828819275, 116.86458659172058, 140.37947607040405, 190.13879370689392, 315.1688537597656, 566.8297400474548, 815.3758766651154, 1065.2787101268768, 1565.6909964084625] 
# d=[16.51536253973069, 8.649734203539651, 1.1302272755215483, -14.59066141543775, -33.7225560893379, -53.57153985137552, -40.55281171623528, 2.0810339800882502, 64.8090827716129, 226.0463427575978]
#################################

