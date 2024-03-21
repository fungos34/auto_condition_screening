import time
import serial
import numpy as np
import sys
import os
import asyncio
from multiprocessing import Process
import threading
from scipy import constants

from gsioc import gsioc_Protocol, ensure_xy_position_will_be_reached
from immortility_decorator import error_handler
import run_syrringe_pump
import run_identifier
import monitor_BKP
import sound

from formatters import format_current, format_voltage, format_flowrate
from flow_setup import Rack, Rackcommands, Vial, SetupVolumes
from commands import config_pump, deactivate_pump, activate_pump, get_power_command, set_power_supply, dim_load, dim_inject
from documentation import get_documentation, get_run_id, get_prediction

from loguru import logger

TESTING_ACTIVE = True

#########################################################
###### BEGIN ### communication settings ### BEGIN #######
#########################################################

PORT1   = 'COM3'    #port for GX-241 liquid handler - Ubuntu: '/dev/ttyUSB0'
PORT2   = 'COM4'    #port for BK Precision 1739 - Ubuntu: '/dev/ttyUSB1'

##### Adapt this URL to the desired OPC-UA endpoint #####
OPC_UA_SERVER_URL = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop # "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop # "opc.tcp://rcpeno00472:5000/" #OPC Server on RCPE Laptop

#########################################################
####### BEGIN ### experimental settings ### BEGIN #######
#########################################################

# Volumetric relation of substance in pump B to substance in pump A (float)
DILLUTION_BA = [] 
# Experimental Current in (mA)
CURRENTS = [2.5,2.5,2.5,2.7,2.7,2.7,2.9,2.9,2.9,3.1,3.1,3.1,3.3,3.3,3.3,3.5,3.5,3.5,3.7,3.7,3.7,3.9,3.9,3.9,4.2,4.2,4.2,4.5,4.5,4.5,4.8,4.8,4.8,5.2,5.2,5.2,5.6,5.6,5.6,6,6,6] 
# Flow rate of pump A (μL/min)
FLOW_A  = [] 
# Flow rate of pump B in (μL/min)
FLOW_B  = []
# Molar charge of the redox reaction in (F/mol)
CHARGE_VALUES = [2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3] 
# Generates similar concentration values for each experiment, used in calculating the flow rates (float). 
CONCENTRATIONS = np.full(len(CURRENTS),(0.025)).tolist() 
# Faraday Constant in ((A*s)/mol)
FARADAY_CONST = constants.physical_constants['Faraday constant'][0] 
# Maximum flow rate of pump A (μL/min)
MAX_FLOWRATE_A = 2500 
# Maximum flow rate of pump B (μL/min)
MAX_FLOWRATE_B = 250 
# Operate on constant Flow Rate of pump A (float)
CONSTANT_A_FLOWRATE = MAX_FLOWRATE_A/3
# Rinsing factor to gain information about the reactors stady state (float)
STADY_STATE_RINSING_FACTOR = np.full(len(CHARGE_VALUES),(3)).tolist()
# Starting from experiment with this 1-based integer number (int)
CONDUCTION_FROM_EXP = int(1)
# Skipping the filling of the pumps (True/False)
SKIP_FILLING = False

# Calculates the flow rate of pump B from input of currents, concentrations and charge values.
if FLOW_B==[]:
    for i in range(len(CURRENTS)):
        # formula units: (mL/min) = ((mA) * 1000) / ( (mol/L) * (1) * ( ((A*sec)/mol) / (sec)) ) )
        FLOW_B.append(int((CURRENTS[i] * 1000) / (CONCENTRATIONS[i] * CHARGE_VALUES[i] * (FARADAY_CONST/60)))) 

# Calculates the dillution factors of 
if DILLUTION_BA==[]:
    for i in range(len(FLOW_B)):
        FLOW_A.append(CONSTANT_A_FLOWRATE)

if FLOW_A==[]:
    for i in range(len(FLOW_B)):
        FLOW_A.append(int(FLOW_B[i] * DILLUTION_BA[i]))

# Calculates the dillution factors pump A / pump B from the flow rate pump A and flow rate pump B. 
if DILLUTION_BA==[]:
    for i in range(len(FLOW_B)):
        DILLUTION_BA.append(FLOW_B[i]/FLOW_A[i])

# Calculates the currents from inputted flow rate of pump B, concentrations and charge values.
if CURRENTS==[]:
    for i in range(len(FLOW_B)):
        CURRENTS.append(((FLOW_B[i] * CONCENTRATIONS[i] * CHARGE_VALUES[i] * (FARADAY_CONST/60)) / 1000 ))

# Calculates the charge values from inputted flow rate of pump B, currents and concentrations.
if CHARGE_VALUES==[]:
    for i in range(len(FLOW_B)):
        CHARGE_VALUES.append(int((CURRENTS[i] * 1000) / (CONCENTRATIONS[i] * FLOW_B[i] * (FARADAY_CONST/60)))) #formula units: (mL/min) = ((mA) * 1000) / ( (mol/L) * (1) * ( ((A*sec)/mol) / (sec)) ) )

# experimental maximum voltages in (V)
VOLTAGES = np.full(len(FLOW_B),(12)).tolist() 

RUN_ID = get_run_id()

#########################################################
######### END ### experimental settings ### END #########
#########################################################



###############################################################################################################    
############################################ ADVANCED USER SETTINGS ###########################################
###############################################################################################################          

def get_automation_setup(port1, port2):
    """Sets up the flow setup specific parameters and initializes setup instances, ports and threads."""
    ########################################################################################################################################################
    # SETTINGS
    rack_position_offset_x=92       #distance in mm between rack_position=1 and =2 on x-axis
    rack_position_offset_y=0        #distance in mm between rack_position=1 and =2 on y-axis
    ############################# RACK 3 DEFINITION #################################
    rack3=Rack([4,12],8.7,40,(2.11+15.6),(2.72+15.6+0.35),65)
    array_order3=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
        [1,2,3,4],
        [5,6,7,8],
        [9,10,11,12],
        [13,14,15,16],
        [17,18,19,20],
        [21,22,23,24],                     #int(0) denotes the blank solution
        [25,26,27,28],                    #int(-1) denotes an empty slot, int(-2) marks the waste
        [29,30,31,32],
        [33,34,35,36],
        [37,38,39,40],
        [41,42,43,44],
        [45,46,47,48]    
        ])
    rack_pos3=1
    global rack3_commands
    rack3_commands=Rackcommands(rack3,array_order3,rack_pos3,rack_position_offset_x,rack_position_offset_y)
    global vial_selfmade
    vial_selfmade=Vial(1.5,1,42,31.08)
    ############################## RACK 4 DEFINITION #################################
    global rack4
    rack4=Rack([2,7],20,55,(28.55+2.17),(28.55+1.38),15.2)
    array_order4=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
        [1,2],
        [3,4],
        [5,6],
        [7,8],
        [9,10],
        [11,12],                     #int(0) denotes the blank solution
        [13,14]                    #int(-1) denotes an empty slot, int(-2) marks the waste   
        ])
    rack_pos4=2
    global rack4_commands
    rack4_commands=Rackcommands(rack4,array_order4,rack_pos4,rack_position_offset_x,rack_position_offset_y)
    global vial_large
    vial_large=Vial(40,40,94.74,93.25)
    ############################## Serial Port initialisation ##########################
    global ser
    ser=serial.Serial(port1,19200,8,"N",1,0.1)   
    global g
    g = gsioc_Protocol(ser,'GX-241 II',33) # full device name GX-241 II v2.0.2.57
    global g2
    g2 = gsioc_Protocol(ser,'GX D Inject',3) # full device name GX-241 II v2.0.2.5
    ########################### EXPERIMENTAL SETUP ############################
    global volumes_setup1
    volumes_setup1=SetupVolumes(460,73,50,17,170,50,520,1.1)
    ######################## MONITOR VIAL LOAD #######################
    vial_load_rack3={}
    for i in range(len(array_order3)):
        for j in range(len(array_order3[i])):
            vial_load_rack3.update({array_order3[i][j]:float(0)})
    ##################### SETTINGS FOR BK PRECISION DEVICE ####################
    global bkp_port
    bkp_port=monitor_BKP.get_port(logger,port2)
    global monitoring_thread
    monitoring_thread=CustomThread(1,'MonitorBKP',bkp_port)
    monitoring_thread.setDaemon(True)

###############################################################################################################
###############################################################################################################
###############################################################################################################

        
class CustomThread(threading.Thread):
    """Separate thread for querying BKPrecission Power Source parameters parallel to other operations."""

    def __init__(self, threadID, name, port):
        """Thread initialisation."""
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port=port

    def run(self):
        """Start up routine for BKP Power Source monitoring.
        :expects: Global variable TESTING_ACTIVE.
        """
        if TESTING_ACTIVE == True:
            a = monitor_BKP.get_commands('CURR?\r')
        else:
            a = monitor_BKP.get_commands('VOLT?\rCURR?\r')
        monitor_BKP.get_values(a,self.port,logger)


######################## WORKING ROUTINE ###############################################################################################################


def run_experiments(flow_rates_pump_a: list, flow_rates_pump_b: list, repeats: int, predicted_times: list) -> None:
    """Runs the whole experimental procedure, one experiment after another. Expects devices being set to an default initial state.
    
    :param flow_rates_pump_a: List, experiment specific flow rates for pump A.
    :param flow_rates_pump_b: List, experiment specific flow rates for pump B.
    :param repeats: Int, number of repeats for the whole set of experiments.
    :predicted_times: List, predicted times for each experiment.
    :expects: Global variable (bool) SKIP_FILLING."""
    waste_vial_num = [5,5,5,5,5,4,4,4,4,4,3,3,3,3,3,2,2,2,2,2,1,1,1,1,1,5,5,5,5,5,4,4,4,4,4,3,3,3,3,3,2,2,2,2,2,1,1,1,1,1]
    formatted_currents = format_current(CURRENTS.copy())
    formatted_voltages = format_voltage(VOLTAGES.copy())
    beginning=time.time()
    g.bCommand('WBB')
    asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
    logger.info(f'<<< starting with the actual process: at {beginning} >>>')
    if SKIP_FILLING == False:
        if sum(flow_rates_pump_a)!=0:
            a=True
        else:
            a=False
        if sum(flow_rates_pump_b)!=0:
            b=True
        else:
            b=False
        asyncio.run(activate_pump(a,b,OPC_UA_SERVER_URL))
    else:
        a=False
        b=False
    if fill_system(MAX_FLOWRATE_A, MAX_FLOWRATE_B, volumes_setup1, waste_vial_num[0], g, g2, a, b):
        monitoring_thread.start()
        for j in range(repeats):
            times=[]
            time_diff=[]
            start=time.time()
            logger.debug(start-beginning)
            logger.info(f'<<< going on with experiment 1 (flowrates: {flow_rates_pump_a[0],flow_rates_pump_b[0]} uL/min) after {start-beginning} sec >>>')
            for i in range(len(flow_rates_pump_a)):
                if i+1 <= 99:
                    g.connect()
                    g.bCommand(f'W{str(i+1).zfill(2)}')
                asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
                if i+1 < CONDUCTION_FROM_EXP:
                    continue
                if collect_rxn(flow_rates_pump_a[i], flow_rates_pump_b[i], volumes_setup1, int((j*len(flow_rates_pump_a))+i+1), waste_vial_num[i], vial_selfmade, vial_large, g, g2, formatted_currents[i], formatted_voltages[i], STADY_STATE_RINSING_FACTOR[i]):
                    end=time.time()
                    logger.debug(end-start)
                    if (i+1)<len(flow_rates_pump_a):
                        logger.info(f'<<< going on with experiment {i+2} (flowrates: {flow_rates_pump_a[i+1],flow_rates_pump_b[i+1]} uL/min) after another {end-start} sec >>>')
                    times.append(end-start)
                    time_diff.append((end-start)-predicted_times[i])
                    logger.info(f'current times list: {times} (sec)')
                    start=time.time()
                if i+1 <= 99:
                    g.connect()
                    g.bCommand(f'WBB')
            end=time.time()
            logger.debug(end-start)
            logger.info(f'<<< finished all {len(flow_rates_pump_a)} experiments after another {end-start} sec >>>')
            logger.info(f'<<< predicted times: {predicted_times} (sec); meassured times: {times} (sec); time differences: {time_diff} >>>')
    asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
    asyncio.run(deactivate_pump(OPC_UA_SERVER_URL))


@error_handler(num=2) # this awesome decorator catches any error and restarts the whole experiment for num times.
def collect_rxn(flow_rate_A: int, flow_rate_B: int, volumes_of_setup: SetupVolumes, collect_vial_number: int, waste_vial_number: int, vial_type_object: Vial, waste_vial_object: Vial, gsioc_liquidhandler: gsioc_Protocol, gsioc_directinjectionmodule: gsioc_Protocol, current_commands: list, voltage_commands: list, stadystaterinsingfactor: float) -> bool:
    """Conducts the repeated experimental procedure, which is by default to collect 1mL of reaction solution in the proper vial.
    
    :param flow_rate_A: Int, flow rate (μL) of pump A for the current experiment.
    :param flow_rate_B: Int, flow rate (μL) of pump B for the current experiment.
    :param volumes_of_setup: Volumes instance of the current setup.
    :param collect_vial_number: Int, position number of the vial where the reaction mixture will be collected. 
    :param waste_vial_number: Int, position number of the vial where the waste will be collected. 
    :param vial_type_object: Vial instance of the collecting vial with according dimensions.
    :param waste_vial_object: Vial instance of the waste vial with according dimensions.
    :param gsioc_liquidhandler: GSIOC Liquid handler instance for sending commands.
    :param gsioc_directinjectionmodule: GSIOC Direct Injection Module instance for sending commands.
    :param current_commands: List, containing float values for the current to apply in each experiment (in mA).
    :param voltage_commands: List, containing float values for the maximum voltage (in constant current mode) to apply during each experiment (in V).
    :param stadystaterinsingfactor: Float, the rinsing of the reactor under experimental conditions will be conducted for the regular residence time of the reactor times this stadystaterinsingfactor.

    :returns: True if finished experiment successfully.
    """
    flush_system_time=(volumes_of_setup.get_time_stady_state_rinsing(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B),stadystaterinsingfactor))#get_time_fill_next_rxn(flow_rate_B)#(flow_rate_A + flow_rate_B))
    collect_fraction_time=((vial_type_object.vial_usedvolume_max * 1000)/(flow_rate_A+flow_rate_B))*60
    if dim_load(gsioc_directinjectionmodule, TESTING_ACTIVE):
        logger.info('<<< Experiment is starting right now >>>')
        asyncio.run(config_pump(run_syrringe_pump.Level(0,MAX_FLOWRATE_B,0), OPC_UA_SERVER_URL))        # starting the reaction: dont stop the pumps anymore
        time.sleep(15)
        #time.sleep(volumes_of_setup.get_time_rinse_reactor(MAX_FLOWRATE_B)) # flush it without rxn
        asyncio.run(config_pump(run_syrringe_pump.Level(flow_rate_A,flow_rate_B,0), OPC_UA_SERVER_URL))
        runtime_start=time.time()
        if asyncio.run(set_power_supply(bkp_port,get_power_command(current=current_commands,voltage=voltage_commands))):
            time.sleep(5)
            ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=logger,xy_positioning_command=rack4_commands.get_xy_command(waste_vial_number,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
            gsioc_liquidhandler.bCommand('Z100:20:20')  # improve this
            if dim_inject(gsioc_directinjectionmodule, TESTING_ACTIVE):
                runtime_end=time.time()
                if (flush_system_time - (runtime_end-runtime_start)) > volumes_of_setup.get_time_fill_needle(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B)):
                    time.sleep(flush_system_time - (runtime_end-runtime_start))
                else:
                    time.sleep(volumes_of_setup.get_time_fill_needle(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B)))
    if dim_load(gsioc_directinjectionmodule, TESTING_ACTIVE):
        ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=logger,xy_positioning_command=rack3_commands.get_xy_command(collect_vial_number,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
        gsioc_liquidhandler.bCommand('Z100:20:20')  # improve this
        start=time.time()
        if dim_inject(gsioc_directinjectionmodule, TESTING_ACTIVE):
            end=time.time()
            if ((collect_fraction_time)-(end-start))>0:
                logger.info(f'<<< collecting {(((flow_rate_A+flow_rate_B)*(collect_fraction_time/60))/1000)} [mL] over the course of {round(collect_fraction_time)} (sec) >>>')
                time.sleep(collect_fraction_time-(end-start))
            else:
                logger.debug(f'<<< switching time ({end-start} sec) is longer than collecting time ({collect_fraction_time} sec) (fraction collection) >>>')
                pass
    if dim_load(gsioc_directinjectionmodule, TESTING_ACTIVE):
        with open('logs/procedural_data.txt','r') as file:
            lines = file.readlines()
            exp_finished = int(str(lines[1]).strip())
            logger.debug(f'opened file "procedural_data.txt" successfully. value for finished experiments is {exp_finished}.')
        with open('logs/procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(exp_finished+1)+'\n'+str(len(CURRENTS)))
            logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(exp_finished+1)}.')
        gsioc_liquidhandler.connect()
        time.sleep(5)
        gsioc_liquidhandler.bCommand('Z125')
        gsioc_liquidhandler.bCommand('H')
        asyncio.run(set_power_supply(bkp_port,['OUT OFF\r']))
        return True


def fill_system(flow_rate_A_max: int, flow_rate_B_max: int, volumes_of_setup: SetupVolumes, waste_vial_object: int, gsioc_liquidhandler, gsioc_directinjectionmodule, a: bool = False, b: bool = False) -> bool:
    """Fills the reactor and the tubing before the reactor with reaction mixture.
    :param flow_rage_A_max: maximum flow rate pump A can take. Depends on global variable MAX_FLOWRATE_A.
    :param flow_rage_B_max: maximum flow rate pump B can take. Depends on global variable MAX_FLOWRATE_B.
    :param volumes_of_setup: Volumes of the current setup.
    :param waste_vial_object: Int, position number of the waste vial.
    :param gsioc_liquidhandler: GSIOC Liquid Handler instance for sending commands to.
    :param gsioc_directinjectionmodule: GSIOC Direct Injection Module instance for sending commands to.
    :param a: Bool, True if pump A is used.
    :param b: Bool, True if pump B is used.
    :expects: Global variable (bool) SKIP_FILLING.
    :returns: True when finished system filling successfully.
    """
    if SKIP_FILLING == True:
        return True
    if SKIP_FILLING == False:
        fill_system_time=volumes_of_setup.get_time_fill_reactor(flow_rate_A_max,flow_rate_B_max,(flow_rate_A_max + flow_rate_B_max))
        ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=logger,xy_positioning_command=rack4_commands.get_xy_command(waste_vial_object,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
        gsioc_liquidhandler.bCommand('Z100:20:20')
        if dim_inject(gsioc_directinjectionmodule, TESTING_ACTIVE):
            if a==False:
                flow_rate_A_max=0
            if b==False:
                flow_rate_B_max=0
            asyncio.run(config_pump(run_syrringe_pump.Level(0,flow_rate_B_max,0), OPC_UA_SERVER_URL))     #this flowrate could be faster?!
            time.sleep(fill_system_time)
            asyncio.run(config_pump(run_syrringe_pump.Level(0,0,0), OPC_UA_SERVER_URL))
            return True
    else:
        raise Exception(f'No desition made up for the filling procedure. Choose either "True" or "False". Current value: {SKIP_FILLING}')


def start_watchdog() -> None:
    """Runs the warden.py file for ensuring the main process is not killed arbitrary.
    :expects: the overall process is started from the same directory as "warden.py". Tested only on WINDOWS OS, python has to be on PATH.
    """
    os.system('python warden.py')

def start_gui() -> None:
    """Runs the GUI for basic commands towards the flow setup devices.
    :expects: the overall process is started from the same directory as "basic_gui.py". Tested only on WINDOWS OS, python has to be on PATH.
    """
    os.system('python basic_gui.py')



def automation_main(remote: bool = False, conduction: int = 1) -> None:
    """Main entry point for the automated reactions condition screening. Sets setup devices to default initial state. 
    :param remote: Bool, retrieves data from previous experiments when set to True and circumvents the CLI initialisation questions.
    :param conduction: Int, the number of the experiment from which the process should start.
    """
    get_automation_setup(PORT1, PORT2)
    
    if remote == False:
        with open('logs/procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(0)+'\n'+str(len(CURRENTS)))
            logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(0)}.')
        while True:
            allowance1 = input('starting position change? (y/n): ')
            if allowance1.lower() == 'y':
                bkp_port.close()
                ser.close()
                proc_gui = Process(target=start_gui)
                proc_gui.start()
                sys.exit('sys.exit(): Code stopped without positional changes.\nIf you want to run experiments start again and answer "starting position change?" with "n".')
            elif allowance1.lower() == 'n':
                break
            else:
                continue
        while True:
            allowance2 = input('starting experiments (further settings are queried afterwards)? (y/n): ')
            if allowance2.lower() == 'n':
                sys.exit('Script was stopped on user input.')
            elif allowance2.lower() == 'y':
                break
            else: 
                continue
        while True:
            try:
                conducting_experiments = 1
                conducting_experiments = int(input('from which experiment number do you want to start? (integer number) '))
                break
            except BaseException as e:
                logger.error(f'The following error occured:\n{e}\nPlease Note: Enter only integer numbers for probe number.')
                continue
        if 1 <= conducting_experiments <= len(CURRENTS):
            global CONDUCTION_FROM_EXP 
            CONDUCTION_FROM_EXP = conducting_experiments
            while True:
                filling_procedure = input('Do you want to carry out the initialisation procedure including filling the reactor? (y/n) ')
                if filling_procedure.lower() == 'n':
                    global SKIP_FILLING
                    SKIP_FILLING = True
                    logger.info('Filling procedure is going to be skipped.')
                    break
                elif filling_procedure.lower() == 'y':
                    SKIP_FILLING = False
                    logger.info('Filling procedure is going to be carried out.')
                    break
                else:
                    continue
        else:
            raise Exception(f'Please choose an experiment out of 1 to {len(CURRENTS)}.')
    elif remote == True:
        with open('logs/procedural_data.txt','r') as file:
            lines = file.readlines()
            exp_finished = int(str(lines[1]).strip())
            logger.info(f'opened file "procedural_data.txt" successfully. value for finished experiments is {exp_finished}.')
        with open('logs/procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(exp_finished)+'\n'+str(len(CURRENTS)))
            logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(exp_finished+1)}.')
        allowance2 = 'y'
        CONDUCTION_FROM_EXP = conduction
        SKIP_FILLING = True
    proc = Process(target=start_watchdog)
    proc.start()
    if allowance2.lower() == 'y':
        sound.get_sound1()
        get_documentation(RUN_ID, CURRENTS, VOLTAGES, FLOW_A, FLOW_B, MAX_FLOWRATE_A, MAX_FLOWRATE_B, DILLUTION_BA, CHARGE_VALUES, CONCENTRATIONS, STADY_STATE_RINSING_FACTOR)
        run_identifier.set_run_number()
        logger.info(f'run ID: {RUN_ID}')
        g2.connect()
        g2.bCommand('VL')
        g.connect()
        g.bCommand('H')
        run_experiments(format_flowrate(FLOW_A,MAX_FLOWRATE_A), format_flowrate(FLOW_B,MAX_FLOWRATE_B), 1, get_prediction(FLOW_A, FLOW_B, plot=False))         # starts pumps and liquid handler and pumps 1mL to each defined Vial.
        proc.join()
        asyncio.run(set_power_supply(bkp_port,['OUT OFF\r']))
        asyncio.run(deactivate_pump(OPC_UA_SERVER_URL))
        logger.debug(f'run ID: {RUN_ID}')
        sound.get_sound2()


# Genauigkeit 1mL abfüllen bei 2500uL/min
# 3.5641g-2.5774g=0.9867g
# Genauigkeit 1mL abfüllen bei 2000uL/min
# 3.5684-2.5755g=0.9929g
# normwert bei r.t. und Normaldruck: 0.997g
# accuracy = 0.992778335005015

##################################################################################
if __name__ == '__main__':
    logger.add(sink="logs/general.log", level='INFO', format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>', filter=lambda log_details: log_details['module'] != 'monitor_BKP')
    automation_main()
