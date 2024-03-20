import time
import serial
import numpy as np
import sys
import csv
import regex as re
import binascii
import pandas as pd
import random
import string
import customtkinter as ctk
import os
import asyncio
from multiprocessing import Process
import threading
from scipy import constants
from tabulate import tabulate

from gsioc import gsioc_Protocol, check_xy_position_change, ensure_xy_position_will_be_reached
from immortility_decorator import error_handler, random_error_emulator
import run_syrringe_pump
import duration_caluclator
import run_identifier
import monitor_BKP
import sound


TESTING_ACTIVE = True
###### communication ######
PORT1   = 'COM3'    #port for GX-241 liquid handler - Ubuntu: '/dev/ttyUSB0'
PORT2   = 'COM4'    #port for BK Precision 1739 - Ubuntu: '/dev/ttyUSB1'
##### Adapt this URL to the desired OPC-UA endpoint #####
OPC_UA_SERVER_URL = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # "opc.tcp://rcpeno02341:5000/"
#########################################################


###### experimental ######
EMAIL_ADDRESS = 'automated_platform@gmx.at'
EMAIL_ENTRANCE = 'AbC456DeF123' 

DILLUTION_BA = []#[20,20,20,20,15,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20]#['1:1','10:1','100:1','1000:1']  # 'parts of parts': "1:1" = 1 volume increment out of 1 volume increments is the reagent, or "10:1" = 1 volume increments of A out of 10 volume increments of A, or 9+1 volume increments.
#[0,0,0,0]       # (uL/min)
CURRENTS = [2.5,2.5,2.5,2.7,2.7,2.7,2.9,2.9,2.9,3.1,3.1,3.1,3.3,3.3,3.3,3.5,3.5,3.5,3.7,3.7,3.7,3.9,3.9,3.9,4.2,4.2,4.2,4.5,4.5,4.5,4.8,4.8,4.8,5.2,5.2,5.2,5.6,5.6,5.6,6,6,6]
# for i in range(len(CURRENTS)):
#     CURRENTS[i] = CURRENTS[i]/11.42

FLOW_A  = []#[2400,2500,2400,2500]         # (uL/min)
FLOW_B  = []#124,124,124,124,248]

CHARGE_VALUES = [2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3]
CONCENTRATIONS = np.full(len(CURRENTS),(0.025)).tolist() # generates similar concentration values for each experiment, used in calculating the flow rates. 
FARADAY_CONST = constants.physical_constants['Faraday constant'][0] # in ((A*s)/mol)
MAX_FLOWRATE_A = 2500 # μL/min
MAX_FLOWRATE_B = 250 # μL/min
CONSTANT_A_FLOWRATE = MAX_FLOWRATE_A/3
STADY_STATE_RINSING_FACTOR = np.full(len(CHARGE_VALUES),(3)).tolist()#[1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5]#[1.5,1.5,1.5]#[1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5] # rinsing factor to gain information about the reactors stady state 
CONDUCTION_FROM_EXP = int(1)
SKIP_FILLING = False
# factor between small and big reactor: 11.42
if FLOW_B==[]:
    for i in range(len(CURRENTS)):
        FLOW_B.append(int((CURRENTS[i] * 1000) / (CONCENTRATIONS[i] * CHARGE_VALUES[i] * (FARADAY_CONST/60)))) #formula units: (mL/min) = ((mA) * 1000) / ( (mol/L) * (1) * ( ((A*sec)/mol) / (sec)) ) )
if DILLUTION_BA==[]:
    for i in range(len(FLOW_B)):
        FLOW_A.append(CONSTANT_A_FLOWRATE)
if FLOW_A==[]:
    for i in range(len(FLOW_B)):
        FLOW_A.append(int(FLOW_B[i] * DILLUTION_BA[i]))
if DILLUTION_BA==[]:
    for i in range(len(FLOW_B)):
        DILLUTION_BA.append(FLOW_A[i]/FLOW_B[i])
if CURRENTS==[]:
    for i in range(len(FLOW_B)):
        CURRENTS.append(((FLOW_B[i] * CONCENTRATIONS[i] * CHARGE_VALUES[i] * (FARADAY_CONST/60)) / 1000 ))
if CHARGE_VALUES==[]:
    for i in range(len(FLOW_B)):
        CHARGE_VALUES.append(int((CURRENTS[i] * 1000) / (CONCENTRATIONS[i] * FLOW_B[i] * (FARADAY_CONST/60)))) #formula units: (mL/min) = ((mA) * 1000) / ( (mol/L) * (1) * ( ((A*sec)/mol) / (sec)) ) )

VOLTAGES = np.full(len(FLOW_B),(12)).tolist() #[6,6,6,6,6]        # (V) float or int
################## TESTS THE VARIABLES ###################

print(f'currents: {CURRENTS}')
print(f'voltages: {VOLTAGES}')
print(f'flow A: {FLOW_A}')
print(f'flow B: {FLOW_B}')
print(f'charge values: {CHARGE_VALUES}')
print(f'concentrations: {CONCENTRATIONS}')
print(f'faraday constant: {FARADAY_CONST} (A*s/mol)')
print(f'number of experiemnts: {len(CURRENTS)}')
print(f'stady state factor: {STADY_STATE_RINSING_FACTOR}')
# sys.exit('please, delete this line to use the script')

###################### FORMAT INPUT ############################

def format_current(currents_in: list, max_current: float | int = 999.9) -> list:
    """
    formats an inputted list with numbers (float, int) and returns a formatted list with str() entries like: '020.0'
    prints out messages if the input is invalid and returns a NaN (Not a Number) in the output list.
    """
    
    RANGE_CURRENT = [0,max_current] # settable current values specific for BK Precision 1739 (30V / 1A)
    currents_out=[]

    for i in range(len(currents_in)):
        n=currents_in[i]
        try:
            if n>=RANGE_CURRENT[0] and n<=RANGE_CURRENT[1]:
                n=float(n)
                n="{:.1f}".format(n)
                n = str(n).zfill(5)
                currents_out.append(n)
            else:
                currents_out.append(np.nan)
                print(f'value "{n}" out of range: {RANGE_CURRENT}')
            pass
        except TypeError:
            currents_out.append(np.nan)
            print(f'value "{n}" is not a number')
            pass
    if None in currents_out:
        sys.exit(f'value "{n}" out of range: {RANGE_CURRENT}')
    else:
        return currents_out


def format_voltage(voltages_in: list, max_voltage: float | int = 30) -> list:
    """
    formats an inputted list with numbers (float, int) and returns a formatted list with str() entries like: '02.00'
    prints out messages if the input is invalid and returns a NaN (Not a Number) in the output list.
    """
    
    RANGE_VOLTAGE = [0, max_voltage] # settable current values specific for BK Precision 1739 (30V / 1A)
    voltages_out=[]

    for i in range(len(voltages_in)):
        n=voltages_in[i]
        try:
            if n>=RANGE_VOLTAGE[0] and n<=RANGE_VOLTAGE[1]:
                n=float(n)
                n="{:.2f}".format(n)
                n = str(n).zfill(5)
                voltages_out.append(n)
            else:
                voltages_out.append(np.nan)
                print(f'value "{n}" out of range: {RANGE_VOLTAGE}')
            pass
        except TypeError:
            voltages_out.append(np.nan)
            print(f'value "{n}" is not a number')
            pass
    return  voltages_out


def format_flowrate(flowrates_in: list, max_pump_flowrate: float | int ) -> list:
    """
    formats an inputted list with numbers (float, int) and returns a list with int() entries like: '[2500,234,2342, ... ]' in (uL/min).
    if the inputted flowrate exceeds the range of flowrates (depending on max flowrate of the utilized pumps) it appends a NaN (Not a Number) value to the list instead. 
    """
    RANGE_FLOWRATE = [10, max_pump_flowrate] # (μL/min)
    flowrates_out = []

    for i in range(len(flowrates_in)):
        n = flowrates_in[i]
        try:
            if RANGE_FLOWRATE[0] <= n <= RANGE_FLOWRATE[1]:
                n=round(n,0)
                n=int(n)
                flowrates_out.append(n)
            else:
                flowrates_out.append(np.nan)
                print(f'value "{n}" out of range: {RANGE_FLOWRATE}')
            pass
        except TypeError:
            flowrates_out.append(np.nan)
            print(f'value "{n}" is not a number')
            pass
    return flowrates_out

        
# print(format_current([5.5788,9902.2,12.1251223,'cat',00.1]))
# print(format_voltage([5.5788,9902.2,12.1251223,'cat',00.1]))
# print(format_flowrate([9.999,456.600,54,2600,'cat',10.1],2500))

# sys.exit('please, delete this line to run the script')

####################### GENERATE A DOCUMENTATION TABLE ###################

def get_run_id():
    id=[]
    for _ in range(4):
        id.append(random.choice(string.ascii_letters))
    id.append('-')
    for _ in range(4):
        id.append(str(random.choice(range(10))))
    id.append('-')
    for _ in range(4):
        id.append(random.choice(string.ascii_letters))
    id.append('-')
    for _ in range(4):
        id.append(str(random.choice(range(10))))
    run_id=''.join(id)
    print(run_id)
    return run_id



run_num = run_identifier.get_run_number()

def get_documentation(id):
    print(f'currents: {CURRENTS}\nvoltages: {VOLTAGES}\n dillutions b/a: {DILLUTION_BA}\ncharge values: {CHARGE_VALUES}\n concentrations: {CONCENTRATIONS}\nstady state factors: {STADY_STATE_RINSING_FACTOR}')
    df = pd.DataFrame({
        "Sample \nNumber": np.arange(start=1, stop=len(CURRENTS)+1,step=1).tolist(),
        "Currents \n(mA)": format_current(CURRENTS),
        "Voltages \n(V)": format_voltage(VOLTAGES),
        "Flow Rate \nPump A \n(μL/min)": format_flowrate(FLOW_A,MAX_FLOWRATE_A),
        "Flow Rate \nPump B \n(μL/min)": format_flowrate(FLOW_B,MAX_FLOWRATE_B),
        "Dillution \nB:A": DILLUTION_BA,
        "z-Values \n(F/mol)": CHARGE_VALUES,
        "Sample \nConcentration \n(mol/L)": CONCENTRATIONS,
        "Stady state \nrinsing factor": STADY_STATE_RINSING_FACTOR
    })

    groups=[]
    for i in range(len(CHARGE_VALUES)):
        grouped = df.groupby("z-Values (F/mol)").get_group(CHARGE_VALUES[i])
        groups.append(grouped)
    print(tabulate(df, headers='keys', tablefmt='psql'))
    df.to_excel(f'{run_num}-documentation-{id}.xlsx')
    groups = pd.concat(groups)

    
RUN_ID = get_run_id()

#############################################################################################
#############################################################################################

class Rack():
    def __init__(self,array_dimensions,offset_x,offset_y,vial2vial_x,vial2vial_y,groundlevel_height):
        self.array_dimensions=array_dimensions
        self.offset_x=offset_x
        self.offset_y=offset_y
        self.vial2vial_x=vial2vial_x
        self.vial2vial_y=vial2vial_y
        self.groundlevel_height=groundlevel_height
        
    #get indices of a specific vial in a rack with a certain order of the vials
    #returns a tuple of (i,j) with i=vial-position along x-axis, and j=vial-position along y-axis
    #improve: verify that input is valid in terms of type(), array dimensions and validation of the inputted values
    #improve: implement error messages and logg messages
    def get_vial_indices(self,vial_position,array_order,tolerance):
        # print(str(f'array order is: {array_order}'))
        indices=np.where(array_order==vial_position)
        # print(str(f'indices are: {indices}'))
        if len(indices)==2 and len(indices[0])==1:
            print(f'a unique vial number was chosen: {vial_position}, with indices i={indices[0]}, j={indices[1]}')
            return indices
        elif len(indices)==2 and len(indices[0])==0 and tolerance.lower()=='no':                #tolerance settings
            #REMOVE THIS STATEMENT!!!
            sys.exit(f'fatal error: zero vials with position number {vial_position}')                        #REMOVE THIS STATEMENT!!!
        else:
            print(f'warning: multiple vials with position number {vial_position}')#\n len(indices): {len(indices)}\n len(indices[0]): {len(indices[0])}')
            return indices
        
#########################################################################################
#########################################################################################

class Rackcommands(): #returns a str() object command suitable for the liquid handler rx-241
    def __init__(self,rack,rack_order,rack_position,rack_position_offset_x=92,rack_position_offset_y=0):
        self.rack=rack
        self.rack_order=rack_order
        self.rack_position=rack_position
        self.rack_position_offset_x=rack_position_offset_x
        self.rack_position_offset_y=rack_position_offset_y
        
    ############################# FUNDAMENTAL POSITIONAL COMMANDS #####################################

    def get_xy_command(self,vial_pos,tolerance='no'): #speed 125mm/s, force 100%
        index_y,index_x=self.rack.get_vial_indices(vial_pos,self.rack_order,tolerance)
        if len(index_x)==len(index_y):
            command=[]
            for i in range(len(index_x)):
                i_x=index_x[i]
                i_y=index_y[i]
                distance_x=self.rack.offset_x + self.rack.vial2vial_x * i_x + (self.rack_position-1)*self.rack_position_offset_x    
                distance_y=self.rack.offset_y + self.rack.vial2vial_y * i_y + (self.rack_position-1)*self.rack_position_offset_y    
                command.append(str(f'X{distance_x}/{distance_y}'))
            return command
        else:
            print("error: len(index_x) != len(index_y) ")

    def get_fly_command(self): #speed 125mm/s, force 100%
        command=['Z125']
        return command

    def get_dive_command(self): #speed 125mm/s, force 100%
        # print('starts diving')
        command=['Z110:20:10']
        return command

    def get_suck_command(self):
        # print('starts sucking it')
        return ['Z95:10:10']

    def get_swallow_command(self):
        # print('stops sucking and starts swallowing it')
        return ['Z110']

        
    ############################# COMBINED POSITIONAL COMMANDS ###################################

    def get_defaultmode_commands(self,clean_each='no',tolerance='no'):
        #if defaultmode is called it runs the positioning in the order of denotation in self.rack_order 
        #if clean_each=='yes' it flushes after each position with blank solution, error if no blank solution is defined in self.rack_order
        #if tolerance=='yes' missing vial numbers within the array are tolerated. multiple same vial numbers are choosen after each other.
        print(f'gets commands for defaultmode...')
        command_list=[]
        ##### allows missing vial numbers ######
        number_entries=0
        for i in range(len(self.rack_order)):
            for _ in range(len(self.rack_order[i])):
                number_entries+=1
        for i in range(number_entries):
            print(f'number of entries is: {number_entries}, i={i}')
            print(f'see what range(1,max(self.rack_order)) is outputting: {range(1,np.max(self.rack_order))}')
            if (i+1) in range(1,np.max(self.rack_order)+1):
                command_list.extend(self.get_fly_command())
                print(f'this is causing problems: {i+1}')
                for j in range(len(self.get_xy_command((i+1),tolerance))):
                    command_list.append(self.get_xy_command(i+1,tolerance)[j])  # move to vial position i+1
                    command_list.extend(self.get_dive_command())
                    command_list.extend(self.get_suck_command())
                    command_list.extend(self.get_swallow_command())
                    command_list.extend(self.get_fly_command())
                    if clean_each.lower()=='yes':                               # cleaning with blank solution
                        command_list.extend(self.get_xy_command(0,tolerance))   # moves to blank position 0
                        command_list.extend(self.get_dive_command())
                        command_list.extend(self.get_suck_command())
                        command_list.extend(self.get_swallow_command())
                        command_list.extend(self.get_fly_command())
        return command_list

    def get_goto_command(self,vial_pos,tolerance='no'):
        command=[]
        command.extend(self.get_fly_command())
        command.extend(self.get_xy_command(vial_pos,tolerance))
        return command
    
    def get_safe_command(self):
        command=[]
        command.extend(self.get_fly_command())
        command.extend(['H'])
        return command

#####################################################################################################

class Vial():
    def __init__(self,vial_volume_max,vial_usedvolume_max,vial_height,vial_free_depth):
        self.vial_volume_max=vial_volume_max                #volume in mL
        self.vial_usedvolume_max=vial_usedvolume_max        #volume in mL
        self.vial_height=vial_height                        #height in mm
        self.vial_free_depth=vial_free_depth                #depth in mm
        self.sum_liquid_level = 0

#####################################################################################################

class SetupVolumes(): #A1-B1-B2-AB1-AB2
    def __init__(self,volume_valve_to_needle,volume_reactor_to_valve,volume_before_reactor,volume_reactor,volume_only_pump_a,volume_only_pump_b,volume_pump_a_and_pump_b,excess=1.5):     #volume in [uL], excess as %/100
        self.volume_valve_to_needle=volume_valve_to_needle
        self.volume_reactor_to_valve=volume_reactor_to_valve
        self.volume_before_reactor=volume_before_reactor
        self.volume_reactor=volume_reactor
        self.excess=excess
        self.volume_only_pump_a=volume_only_pump_a
        self.volume_only_pump_b=volume_only_pump_b
        self.volume_pump_a_and_pump_b=volume_pump_a_and_pump_b

    def get_time_fill_needle(self,flowrate_a,flowrate_b,flowrate_sum):        #flow rate in [uL/min] #returns duration in [sec]
        duration=((self.volume_valve_to_needle/flowrate_sum)*(self.excess))*60
        return duration         #returns duration in [sec]

    def get_time_stady_state_rinsing(self,flowrate_a,flowrate_b,flowrate_sum,stady_state_rinsing_factor):         #flow rate in [uL/min] #returns duration in [sec]
        duration=((((self.volume_reactor * stady_state_rinsing_factor)/flowrate_b)+(self.volume_pump_a_and_pump_b/flowrate_sum))*self.excess)*60
        return duration         #returns duration in [sec]

    def get_time_fill_reactor(self,flowrate_a,flowrate_b,flowrate_sum):
        duration=(((self.volume_before_reactor + self.volume_reactor)/flowrate_b)*self.excess)*60
        return duration


    
############################################# ADVANCED USER SETTINGS ###########################################

### device parameter ###

rack_position_offset_x=92       #distance in mm between rack_position=1 and =2 on x-axis
rack_position_offset_y=0        #distance in mm between rack_position=1 and =2 on y-axis

############################################# UNADVANCED USER SETTINGS #############################################

def get_command_list():
    
    with open("array_order.csv") as csvfile:
        read_in=csv.reader(csvfile)
        line=0
        array=list()
        for row in read_in:
            line+=1
            if line==1:
                rack_pos=int(row[1])
            elif line==2:
                rack_type=str(row[1])
            else:
                x=row
                for i in range(len(x)):
                    x[i]=int(x[i])
                array.append(x)
        array_order=np.array(array)

    if rack_type=='a':
        rack1=Rack([2,7],20,55,(28.55+2.17),(28.55+1.38),15.2) #distances in mm, CHECK IF X AND Y IS WELL DEFINED!!!
    if rack_type=='b':
        rack1=Rack([4,12],8.7,40,(2.11+15.6),(2.72+15.6+0.35),65)

    ############### ASSIGNING THE CLASS TO A VARIABLE #################

    rack1_command=Rackcommands(rack1,array_order,rack_pos,rack_position_offset_x,rack_position_offset_y) #the user has to define on which rack he wants to process a command!
    
    ########## EXAMPLE 1: INITIALIZING THE COMMAND LIST ###############

    executable_rack1_command=[]

    ########## EYAMPLE 2: APPENDING DEFAULT MODE COMMANDS #############

    executable_rack1_command.extend(rack1_command.get_defaultmode_commands('no','no'))

    ###########
    print(f'the following list of commands is ready for sending to the device: {executable_rack1_command}')
    return executable_rack1_command
    
position_workflow=get_command_list()

# approach for error checking and collision avoidance:

def expected_move_feedback(gsioc_class_object,commandclass_object,command):      #use only it the awaited response equals to the sent command. returns bool(True) if response equals command, returns bool(False) if not.
    gsioc_class_object.logger.debug(f'starting expected_move_feedback() with arguments: {commandclass_object}')
    response=(binascii.b2a_qp(commandclass_object)).decode('utf-8').strip()
    gsioc_class_object.logger.debug(f'converted arguments: {response}')
    gsioc_class_object.logger.debug(f'unconverted command: {command}')
    catch=re.search(response,command)

    if catch:
        gsioc_class_object.logger.debug('response euqals command: ready for the next command!')
        return True
    else:
        gsioc_class_object.logger.debug('response does not equal command: process cancelled!')
        return False


async def config_pump(flowrate_levels=run_syrringe_pump.Level(0,0,0)):
    # ----------- Defining url of OPCUA and flowRate levels -----------
    # url = "opc.tcp://rcpeno00472:5000/" #OPC Server on RCPE Laptop
    url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
    # # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    # # -----------------------------------------------------------------
    g.logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
        
        if  flowrate_levels.flowrate_A == 0: 
            await pump13A._call_method(pump13A.METHOD_STOP)
            g.logger.info(f"{pump13A.name}: Pump stopped.")
        else: 
            await pump13A.set_flowrate_to(flowrate_levels.flowrate_A)

        if flowrate_levels.flowrate_B == 0: 
            await pump13B._call_method(pump13B.METHOD_STOP)
            g.logger.info(f"{pump13B.name}: Pump stopped.")
        else:
            await pump13B.set_flowrate_to(flowrate_levels.flowrate_B)
        await asyncio.sleep(flowrate_levels.time_in_seconds)

    
async def deactivate_pump():
    url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
    # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    # -----------------------------------------------------------------
    g.logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
        await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())

async def activate_pump(a=False,b=False):
    url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
    # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    # -----------------------------------------------------------------
    g.logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")

        if a==True and b==True:
            await asyncio.gather(pump13A.activate(), pump13B.activate())
        elif a==True:
            await asyncio.gather(pump13A.activate())
        elif b==True:
            await asyncio.gather(pump13B.activate())
        else:
            await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())


def dim_load(gsioc_protocol_object):
    gsioc_protocol_object.connect()
    time.sleep(5)
    gsioc_protocol_object.bCommand('VL')
    resp=gsioc_protocol_object.iCommand('X')
    while resp=='R':
        time.sleep(1)
        resp=gsioc_protocol_object.iCommand('X')
        pass
    if resp=='L':
        return True        
    else:
        if TESTING_ACTIVE == True:
            return True
        else:
            error=gsioc_protocol_object.iCommand('e')
            gsioc_protocol_object.logger.debug(f'the direct injection module returned the following error: {error}')
            return False

def dim_inject(gsioc_protocol_object):
    gsioc_protocol_object.connect()
    time.sleep(5)
    gsioc_protocol_object.bCommand('VI')
    resp=gsioc_protocol_object.iCommand('X')
    while resp=='R':
        time.sleep(1)
        resp=gsioc_protocol_object.iCommand('X')
        pass
    if resp=='I':
        return True
    else:
        if TESTING_ACTIVE == True:
            return True
        else:
            error=gsioc_protocol_object.iCommand('e')
            gsioc_protocol_object.logger.debug(f'the direct injection module returned the following error: {error}')
            return False

        
class CustomThread(threading.Thread):
    def __init__(self, threadID, name, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port=port

    def run(self):
        if TESTING_ACTIVE == True:
            a = monitor_BKP.get_commands('CURR?\r')
        else:
            a = monitor_BKP.get_commands('VOLT?\rCURR?\r')
        monitor_BKP.get_values(a,self.port,g.logger)

# class BKPThread(threading.Thread):
#     def __init__(self, threadID, name):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name

#     def run(self):
#         print('bkp responder works')
#         asyncio.run(bkp_responder.main())

# class GSIOCThread(threading.Thread):
#     def __init__(self, threadID, name):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name

#     def run(self):
#         print('gsioc responder works')
#         asyncio.run(gsioc_responder.main())


def get_power_command(current='000.0',voltage='00.00'):
    command1=str('CURR '+f'{current}'+'\r')
    command2=str('VOLT '+f'{voltage}'+'\r')
    if current=='000.0' and voltage=='00.00':
        commands_list=['OUT OFF\r']
    else:
        commands_list=[command2,'SAVE\r',command1,'SAVE\r','OUT ON\r']
    return commands_list

async def set_power_supply(power_suppl,commands_list):
    for i in range(len(commands_list)):
        eol='\r'
        message=commands_list[i].encode('ascii')
        power_suppl.write(message)
        reply=power_suppl.read_until(expected=eol)
        if reply:
            reply.decode('ascii')
            g.logger.debug(f'command: {commands_list[i]}, reply: {reply}')
        else:
            g.logger.debug(f'command: {commands_list[i]}, but no reply.')
        time.sleep(3)
    return True

######################## WORKING ROUTINE ###############################################################################################################

def get_prediction(flow_rates_a,flow_rates_b,plot:bool=True):
    cummulated_flowrates=duration_caluclator.get_cummulated_flows(flow_rates_a,flow_rates_b)
    predicted_times=duration_caluclator.get_times(cummulated_flowrates)
    g.logger.debug(f'<<< predicted durations of the experiments (setup1 fitted curve model) in ascending order: {predicted_times} >>>')
    if plot:
        duration_caluclator.plot_time_func(cummulated_flowrates)
    return predicted_times

def run_experiments(flow_rates_pump_a, flow_rates_pump_b,repeats,predicted_times):
    waste_vial_num = [5,5,5,5,5,4,4,4,4,4,3,3,3,3,3,2,2,2,2,2,1,1,1,1,1,5,5,5,5,5,4,4,4,4,4,3,3,3,3,3,2,2,2,2,2,1,1,1,1,1]
    beginning=time.time()
    g.bCommand('WBB')
    asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
    g.logger.debug(f'<<< starting with the actual process: at {beginning} >>>')
    if SKIP_FILLING == False:
        if sum(flow_rates_pump_a)!=0:
            a=True
        else:
            a=False
        if sum(flow_rates_pump_b)!=0:
            b=True
        else:
            b=False
        asyncio.run(activate_pump(a,b))
    else:
        a=False
        b=False
    if fill_system(flow_rate_max_a,flow_rate_max_b,volumes_setup1,waste_vial_num[0],g,g2,a,b):
        monitoring_thread.start()
        for j in range(repeats):
            times=[]
            time_diff=[]
            start=time.time()
            g.logger.debug(start-beginning)
            g.logger.debug(f'<<< going on with experiment 1 (flowrates: {flow_rates_pump_a[0],flow_rates_pump_b[0]} uL/min) after {start-beginning} sec >>>')
            for i in range(len(flow_rates_pump_a)):
                if i+1 <= 99:
                    g.connect()
                    g.bCommand(f'W{str(i+1).zfill(2)}')
                asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
                if i+1 < CONDUCTION_FROM_EXP:
                    continue
                if collect_rxn(flow_rates_pump_a[i],flow_rates_pump_b[i],volumes_setup1,int((j*len(flow_rates_pump_a))+i+1),waste_vial_num[i],vial_selfmade,vial_large,g,g2,currents[i],voltages[i],STADY_STATE_RINSING_FACTOR[i]):
                    end=time.time()
                    g.logger.debug(end-start)
                    if (i+1)<len(flow_rates_pump_a):
                        g.logger.debug(f'<<< going on with experiment {i+2} (flowrates: {flow_rates_pump_a[i+1],flow_rates_pump_b[i+1]} uL/min) after another {end-start} sec >>>')
                    times.append(end-start)
                    time_diff.append((end-start)-predicted_times[i])
                    g.logger.debug(f'current times list: {times} (sec)')
                    start=time.time()
                if i+1 <= 99:
                    g.connect()
                    g.bCommand(f'WBB')
            end=time.time()
            g.logger.debug(end-start)
            g.logger.debug(f'<<< finished all {len(flow_rates_pump_a)} experiments after another {end-start} sec >>>')
            g.logger.debug(f'<<< predicted times: {predicted_times} (sec); meassured times: {times} (sec); time differences: {time_diff} >>>')
    asyncio.run(set_power_supply(bkp_port,commands_list=['OUT OFF\r']))
    asyncio.run(deactivate_pump())


@error_handler(num=2) # this awesome decorator catches any error and restarts the whole experiment for num times.
def collect_rxn(flow_rate_A,flow_rate_B,volumes_of_setup,collect_vial_number,waste_vial_number,vial_type_object,waste_vial_object,gsioc_liquidhandler,gsioc_directinjectionmodule,current_commands,voltage_commands,stadystaterinsingfactor):
    flush_system_time=(volumes_of_setup.get_time_stady_state_rinsing(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B),stadystaterinsingfactor))#get_time_fill_next_rxn(flow_rate_B)#(flow_rate_A + flow_rate_B))
    collect_fraction_time=((vial_type_object.vial_usedvolume_max * 1000)/(flow_rate_A+flow_rate_B))*60
    if dim_load(gsioc_directinjectionmodule):
        gsioc_liquidhandler.logger.debug('<<< Experiment is starting right now >>>')
        asyncio.run(config_pump(run_syrringe_pump.Level(0,flow_rate_max_b,0)))        # starting the reaction: dont stop the pumps anymore
        time.sleep(15)
        #time.sleep(volumes_of_setup.get_time_rinse_reactor(flow_rate_max_b)) # flush it without rxn
        asyncio.run(config_pump(run_syrringe_pump.Level(flow_rate_A,flow_rate_B,0)))
        runtime_start=time.time()
        if asyncio.run(set_power_supply(bkp_port,get_power_command(current=current_commands,voltage=voltage_commands))):
            time.sleep(5)
            ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=g.logger,xy_positioning_command=rack4_commands.get_xy_command(waste_vial_number,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
            gsioc_liquidhandler.bCommand('Z100:20:20')  # improve this
            if dim_inject(gsioc_directinjectionmodule):
                runtime_end=time.time()
                if (flush_system_time - (runtime_end-runtime_start)) > volumes_of_setup.get_time_fill_needle(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B)):
                    time.sleep(flush_system_time - (runtime_end-runtime_start))
                else:
                    time.sleep(volumes_of_setup.get_time_fill_needle(flow_rate_A,flow_rate_B,(flow_rate_A + flow_rate_B)))
    if dim_load(gsioc_directinjectionmodule):
        ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=g.logger,xy_positioning_command=rack3_commands.get_xy_command(collect_vial_number,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
        gsioc_liquidhandler.bCommand('Z100:20:20')  # improve this
        start=time.time()
        if dim_inject(gsioc_directinjectionmodule):
            end=time.time()
            if ((collect_fraction_time)-(end-start))>0:
                gsioc_liquidhandler.logger.debug(f'<<< collecting {(((flow_rate_A+flow_rate_B)*(collect_fraction_time/60))/1000)} [mL] >>>')
                time.sleep(collect_fraction_time-(end-start))
            else:
                g.logger.debug(f'<<< switching time ({end-start} sec) is longer than collecting time ({collect_fraction_time} sec) (fraction collection) >>>')
                pass
    if dim_load(gsioc_directinjectionmodule):
        with open('procedural_data.txt','r') as file:
            lines = file.readlines()
            exp_finished = int(str(lines[1]).strip())
            addr = str(lines[3]).strip()
            entr = str(lines[4]).strip()
            g.logger.info(f'opened file "procedural_data.txt" successfully. value for finished experiments is {exp_finished}.')
        with open('procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(exp_finished+1)+'\n'+str(len(CURRENTS))+'\n'+str(addr)+'\n'+str(entr))
            g.logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(exp_finished+1)}.')
        gsioc_liquidhandler.connect()
        time.sleep(5)
        gsioc_liquidhandler.bCommand('Z125')
        gsioc_liquidhandler.bCommand('H')
        asyncio.run(set_power_supply(bkp_port,['OUT OFF\r']))
        return True

def fill_system(flow_rate_A_max,flow_rate_B_max,volumes_of_setup,waste_vial_object,gsioc_liquidhandler,gsioc_directinjectionmodule,a=False,b=False):
    """Fills the reactor and the tubing before with reaction mixture."""
    if SKIP_FILLING == True:
        return True
    if SKIP_FILLING == False:
        fill_system_time=volumes_of_setup.get_time_fill_reactor(flow_rate_A_max,flow_rate_B_max,(flow_rate_A_max + flow_rate_B_max))
        ensure_xy_position_will_be_reached(gsioc_liqhan=gsioc_liquidhandler,attempts=2,logging_entity=g.logger,xy_positioning_command=rack4_commands.get_xy_command(waste_vial_object,'no')[0], TESTING_ACTIVE=TESTING_ACTIVE)
        gsioc_liquidhandler.bCommand('Z100:20:20')
        if dim_inject(gsioc_directinjectionmodule):
            if a==False:
                flow_rate_A_max=0
            if b==False:
                flow_rate_B_max=0
            asyncio.run(config_pump(run_syrringe_pump.Level(0,flow_rate_B_max,0)))     #this flowrate could be faster?!
            time.sleep(fill_system_time)
            asyncio.run(config_pump(run_syrringe_pump.Level(0,0,0)))
            return True
    else:
        raise Exception(f'No desition made up for the filling procedure. Choose either "True" or "False". Current value: {SKIP_FILLING}')

#############################################################################################
####################################### GUI #################################################

def gui_main():
    root_ctk = ctk.CTk()
    root_ctk.geometry("500x500")
    root_ctk.title('automation') #'Automation Enabled Electroorganic Synthesis in Flow
    ctk.set_appearance_mode("white")
    start_button = ctk.CTkButton(master=root_ctk, text='Set Both Pumps to Flow Rate 0 uL/min', command=switch_pumps)
    homewaste_button = ctk.CTkButton(master=root_ctk, text='Go', command=go_home_and_switch_to_waste)
    start_button.place(relx=1, rely=1, anchor=ctk.SW)
    homewaste_button.place(relx=0.5, rely=0.5, anchor=ctk.NW)
    root_ctk.mainloop() # Rest of the script won't execute until startButton pressed

def go_home_and_switch_to_waste():
    sound.get_sound3()
    g.connect()
    g.bCommand('H')
    g2.connect()
    g2.bCommand('VL')

def go_to_waste_vial(waste_vial_number: int = 1):
    sound.get_sound3()
    g.connect()
    g.bCommand('H')
    g.bCommand(rack4_commands.get_xy_command(waste_vial_number,'no')[0])
    g.bCommand('Z100:20:20')
    g2.connect()
    g2.bCommand('VI')

def switch_pumps(flowrate_a=0,flowrate_b=0):
    sound.get_sound3()
    min_flowrate = 10
    if flowrate_a < min_flowrate:
        flowrate_a = 0
    else:
        flowrate_a = format_flowrate([flowrate_a],2500)[0]
    if flowrate_b < min_flowrate:
        flowrate_b = 0
    else:
        flowrate_b = format_flowrate([flowrate_b],250)[0]
    asyncio.run(config_pump(run_syrringe_pump.Level(1000,125,0)))

def deactivate_both_pumps():
    sound.get_sound3()
    asyncio.run(deactivate_pump())


##############################################################################################
def get_automation_setup():
    ########################################################################################################################################################
                    # SETTINGS
    ############################################### RACK 3 DEFINITION ####################################################
    global rack3
    rack3=Rack([4,12],8.7,40,(2.11+15.6),(2.72+15.6+0.35),65)
    global array_order3
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
    global rack_pos3
    rack_pos3=1
    global rack3_commands
    rack3_commands=Rackcommands(rack3,array_order3,rack_pos3,rack_position_offset_x,rack_position_offset_y)
    global vial_selfmade
    vial_selfmade=Vial(1.5,1,42,31.08)
    ############################################### RACK 4 DEFINITION ####################################################
    global rack4
    rack4=Rack([2,7],20,55,(28.55+2.17),(28.55+1.38),15.2)
    global array_order4
    array_order4=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
        [1,2],
        [3,4],
        [5,6],
        [7,8],
        [9,10],
        [11,12],                     #int(0) denotes the blank solution
        [13,14]                    #int(-1) denotes an empty slot, int(-2) marks the waste   
        ])
    global rack_pos4
    rack_pos4=2
    global rack4_commands
    rack4_commands=Rackcommands(rack4,array_order4,rack_pos4,rack_position_offset_x,rack_position_offset_y)
    global vial_large
    vial_large=Vial(40,40,94.74,93.25)
    ############################################### Serial Port initialisation ############################################
    global ser
    ser=serial.Serial(PORT1,19200,8,"N",1,0.1)   
    global g
    g = gsioc_Protocol(ser,'GX-241 II',33) # full device name GX-241 II v2.0.2.57
    global g2
    g2 = gsioc_Protocol(ser,'GX D Inject',3) # full device name GX-241 II v2.0.2.5
    ############################################### EXPERIMENTAL SETUP ####################################################
    global volumes_setup1
    volumes_setup1=SetupVolumes(460,73,50,17,170,50,520,1.1)
    global flow_rate_max_a
    flow_rate_max_a=MAX_FLOWRATE_A
    global flow_rate_max_b
    flow_rate_max_b=MAX_FLOWRATE_B
    #######################################################################################################################
    ####################################### MONITORE VIAL LOAD ############################################################
    global vial_load_rack3
    vial_load_rack3={}
    for i in range(len(array_order3)):
        for j in range(len(array_order3[i])):
            vial_load_rack3.update({array_order3[i][j]:float(0)})
    ################################################################################################################
    global currents
    currents=format_current(CURRENTS)
    global voltages
    voltages=format_voltage(VOLTAGES)

    ####### SETTINGS FOR BK PRECISION DEVICE ######
    global bkp_port
    bkp_port=monitor_BKP.get_port(g.logger,PORT2)
    global monitoring_thread
    monitoring_thread=CustomThread(1,'MonitorBKP',bkp_port)
    monitoring_thread.setDaemon(True)

def start_watchdog():
    os.system('python warden.py')

def start_gui():
    os.system('python basic_gui.py')

def automation_main(remote: bool = False, conduction: int = 1):
    get_automation_setup()
    if remote == False:
        my_addr = EMAIL_ADDRESS
        my_entrance = EMAIL_ENTRANCE
        with open('procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(0)+'\n'+str(len(CURRENTS))+'\n'+str(my_addr)+'\n'+str(my_entrance))
            g.logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(0)}.')
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
                g.logger.critical(f'The following error occured:\n{e}\nPlease Note: Enter only integer numbers for probe number.')
                continue
        if 1 <= conducting_experiments <= len(CURRENTS):
            global CONDUCTION_FROM_EXP 
            CONDUCTION_FROM_EXP = conducting_experiments
            while True:
                filling_procedure = input('Do you want to carry out the initialisation procedure including filling the reactor? (y/n) ')
                if filling_procedure.lower() == 'n':
                    global SKIP_FILLING
                    SKIP_FILLING = True
                    g.logger.info('Filling procedure is going to be skipped.')
                    break
                elif filling_procedure.lower() == 'y':
                    SKIP_FILLING = False
                    g.logger.info('Filling procedure is going to be carried out.')
                    break
                else:
                    continue
        else:
            raise Exception(f'Please choose an experiment out of 1 to {len(CURRENTS)}.')
    elif remote == True:
        with open('procedural_data.txt','r') as file:
            lines = file.readlines()
            exp_finished = int(str(lines[1]).strip())
            addr = str(lines[3]).strip()
            entr = str(lines[4]).strip()
            g.logger.info(f'opened file "procedural_data.txt" successfully. value for finished experiments is {exp_finished}.')
        with open('procedural_data.txt','w') as file:
            file.write(str(os.getpid())+'\n'+str(exp_finished)+'\n'+str(len(CURRENTS))+'\n'+str(addr)+'\n'+str(entr))
            g.logger.info(f'wrote file "procedural_data.txt" successfully to finished experiments {str(exp_finished+1)}.')
        allowance2 = 'y'
        CONDUCTION_FROM_EXP = conduction
        SKIP_FILLING = True
    proc = Process(target=start_watchdog)
    proc.start()
    if allowance2.lower() == 'y':
        sound.get_sound1()
        get_documentation(RUN_ID)
        run_identifier.set_run_number()
        g.logger.debug(f'run ID: {RUN_ID}')
        g2.connect()
        g2.bCommand('VL')
        g.connect()
        g.bCommand('H')
        run_experiments(format_flowrate(FLOW_A,MAX_FLOWRATE_A),format_flowrate(FLOW_B,MAX_FLOWRATE_B),1,get_prediction(FLOW_A,FLOW_B,plot=False))         # starts pumps and liquid handler and pumps 1mL to each defined Vial.
        proc.join()
        asyncio.run(set_power_supply(bkp_port,['OUT OFF\r']))
        asyncio.run(deactivate_pump())
        g.logger.debug(f'run ID: {RUN_ID}')
        sound.get_sound2()
        # Genauigkeit 1mL abfüllen bei 2500uL/min
        # 3.5641g-2.5774g=0.9867g
        # Genauigkeit 1mL abfüllen bei 2000uL/min
        # 3.5684-2.5755g=0.9929g
        # normwert bei r.t. und Normaldruck: 0.997g
        # accuracy = 0.992778335005015

##################################################################################
if __name__ == '__main__':
    automation_main()
