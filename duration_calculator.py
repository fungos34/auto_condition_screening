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
