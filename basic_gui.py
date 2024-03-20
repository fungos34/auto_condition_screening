import numpy as np
import customtkinter as ctk
import sys
import serial
import gsioc
import time
import asyncio
import run_syrringe_pump
from loguru import logger
import sound
import protocol_power_supply

##### Adapt this URL to the desired OPC-UA endpoint #####
OPC_UA_SERVER_URL = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # "opc.tcp://rcpeno02341:5000/"
#########################################################

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
        print(str(f'array order is: {array_order}'))
        indices=np.where(array_order==vial_position)
        print(str(f'indices are: {indices}'))
        if len(indices)==2 and len(indices[0])==1:
            print(f'a unique vial number was chosen: {vial_position}, with indices i={indices[0]}, j={indices[1]}')
            return indices
        elif len(indices)==2 and len(indices[0])==0 and tolerance.lower()=='no':                #tolerance settings
            #REMOVE THIS STATEMENT!!!
            sys.exit(f'fatal error: zero vials with position number {vial_position}')                        #REMOVE THIS STATEMENT!!!
        else:
            print(f'warning: multiple vials with position number {vial_position}')#\n len(indices): {len(indices)}\n len(indices[0]): {len(indices[0])}')
            return indices

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
        # print('starts flying')
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

    def get_spit_command(self):
        # print('starts spitting it out')
        return ['spitting']

    def get_errcheck_command(self):
        # print('checking for errors...')
        return ['checking']

    def get_position_command(self):
        # print('checking for position...')
        return ['checking']

        
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
                    # print(f'j={j}')
                    command_list.append(self.get_xy_command(i+1,tolerance)[j])           #move to vial position i+1
                    # print(f'watch this out: {self.get_xy_command(i+1,tolerance)[j]}')
                    # print(f'the command list looks like this at the moment: {command_list}')
                    command_list.extend(self.get_dive_command())
                    command_list.extend(self.get_suck_command())
                    command_list.extend(self.get_swallow_command())
                    command_list.extend(self.get_fly_command())
                    if clean_each.lower()=='yes':                           #cleaning with blank solution
                        command_list.extend(self.get_xy_command(0,tolerance))         #moves to blank position 0
                        command_list.extend(self.get_dive_command())
                        command_list.extend(self.get_suck_command())
                        command_list.extend(self.get_swallow_command())
                        command_list.extend(self.get_fly_command())
        return command_list

    def get_goto_command(self,vial_pos,tolerance='no'):
        # print('go safe to another position, no metter where you are right now!')
        command=[]
        command.extend(self.get_fly_command())
        command.extend(self.get_xy_command(vial_pos,tolerance))
        return command
    
    def get_safe_command(self):
        # print('avoiding collision now and returning to home')
        command=[]
        command.extend(self.get_fly_command())
        command.extend(['H'])
        return command

class Vial():
    def __init__(self,vial_volume_max,vial_usedvolume_max,vial_height,vial_free_depth):
        self.vial_volume_max=vial_volume_max                #volume in mL
        self.vial_usedvolume_max=vial_usedvolume_max        #volume in mL
        self.vial_height=vial_height                        #height in mm
        self.vial_free_depth=vial_free_depth                #depth in mm
        self.sum_liquid_level = 0

def main():
    root_ctk = ctk.CTk()
    root_ctk.geometry("800x1225")
    root_ctk.title('Automation Enabled Electroorganic Synthesis in Flow')
    ctk.set_appearance_mode("dark")

    # start_button = ctk.CTkButton(master=root_ctk, text='Set Pumps Flow Rate', command=switch_pumps)
    homewaste_button = ctk.CTkButton(master=root_ctk, text='Go Home and Switch to Waste', command=go_home_and_switch_to_waste)
    deactivate_button = ctk.CTkButton(master=root_ctk, text='Deactivate Both Pumps', command=deactivate_both_pumps) 
    wastevial_button = ctk.CTkButton(master=root_ctk, text='Go to Waste Vial #1 and Switch Valve', command=go_to_waste_vial)
    monitore_bkp_button = ctk.CTkButton(master=root_ctk, text='Start Monitoring BKP', command=monitore_bkp_in_gui)
    quit_button = ctk.CTkButton(master=root_ctk, text='Quit', command=root_ctk.destroy)

    button1 = ctk.CTkButton(master=root_ctk, text='Activate both Pumps', command=activate_both_pumps)
    button2 = ctk.CTkButton(master=root_ctk, text='Switch Valve to LOAD', command=switch_to_load)
    button3 = ctk.CTkButton(master=root_ctk, text='Switch Valve to INJECT', command=switch_to_inject) 
    button4 = ctk.CTkButton(master=root_ctk, text='Set Pump A to max Flow Rate', command=set_pump_a_to_max_flow_rate)
    button5 = ctk.CTkButton(master=root_ctk, text='Set Pump B to max Flow Rate', command=set_pump_b_to_max_flow_rate)
    button6 = ctk.CTkButton(master=root_ctk, text='Stop Pump A', command=stop_pump_a)
    button7 = ctk.CTkButton(master=root_ctk, text='Stop Pump B', command=stop_pump_b)
    
    
    label = ctk.CTkLabel(master=root_ctk, text="This Graphical User Interface enables to control the \nSyrris Asia Pumps, \nGSIOC Liquid Handler, \nGSIOC Direct Injection Module and \nBKP Power Supply (future implementation) \nin a half automated manner.\nPress the Buttons to carry out the operations.\n('Set Pumps Flow Rate' is without function so far)", width=120, height=25)
    entry = ctk.CTkEntry(master=root_ctk, width=120, height=25)
    entry.place(relx=0.1, rely=1, anchor=ctk.NW)
    text = entry.get()
    
    def slider_event(value):
        slider = ctk.CTkSlider(master=root_ctk, width=160, height=16, border_width=5.5, command=slider_event)
        slider.place(relx=0.1, rely=1, anchor=ctk.NW)
        print(value)
        return value
    

    label.place(relx=0.5, rely=0.1, anchor=ctk.CENTER)
    button3.place(relx=0.5, rely=0.2, anchor=ctk.NW)
    button2.place(relx=0.5, rely=0.3, anchor=ctk.NW)
    homewaste_button.place(relx=0.5, rely=0.4, anchor=ctk.NW)
    wastevial_button.place(relx=0.5, rely=0.5, anchor=ctk.NW)
    monitore_bkp_button.place(relx=0.5, rely=0.6, anchor=ctk.NW)
    quit_button.place(relx=0.5, rely=0.7, anchor=ctk.NW)
    button1.place(relx=0.1, rely=0.2, anchor=ctk.NW)
    deactivate_button.place(relx=0.1, rely=0.3, anchor=ctk.NW)
    # start_button.place(relx=0.1, rely=0.4, anchor=ctk.NW)
    button4.place(relx=0.1, rely=0.5, anchor=ctk.NW)
    button5.place(relx=0.1, rely=0.6, anchor=ctk.NW)
    button6.place(relx=0.1, rely=0.7, anchor=ctk.NW)
    button7.place(relx=0.1, rely=0.8, anchor=ctk.NW)
    root_ctk.mainloop() # Rest of the script won't execute until startButton pressed


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


async def config_pump(keyword = None, flowrate_levels=run_syrringe_pump.Level(0,0,0)):
    if keyword == None:
        # ----------- Defining url of OPCUA and flowRate levels -----------
        # url = "opc.tcp://rcpeno00472:5000/" #OPC Server on RCPE Laptop
        url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
        # # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
        # # -----------------------------------------------------------------
        logger.info(f"OPC-UA Client: Connecting to {url} ...")
        async with run_syrringe_pump.Client(url=url) as client:
            # ------ Here you can define and operate all your pumps -------
            pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
            pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
            # await asyncio.gather(pump13A.activate(), pump13B.activate())
            # flowrate_levels = (run_syrringe_pump.Level(310, 250, 5), # filling the system with reaction mixture
                            #    run_syrringe_pump.Level(310, 200, 5), # running the reaction 1
                            #    run_syrringe_pump.Level(310, 200, 5),) # collecting 1 mL
                            #    Level(620, 62, 88), # running the reaction 2
                            #    Level(620, 62, 10), # collecting for cleaning the tip
                            #    Level(620, 62, 97), # collecting 1 mL
                            #    Level(310, 31, 176), # running the reaction 3
                            #    Level(310, 31, 15), # collecting for cleaning the tip
                            #    Level(310, 31, 194), # collecting 1 mL
                            #    Level(500, 50, 110), # running the reaction 4
                            #    Level(500, 50, 10), # collecting for cleaning the tip
                            #    Level(500, 50, 120), # collecting 1 mL
                            #    Level(620, 62, 88), # running the reaction 5
                            #    Level(620, 62, 10), # collecting for cleaning the tip
                            #    Level(620, 62, 97), # collecting 1 mL
                            #    Level(1000, 0, 60), # cleaning the system, going to waste
                            #    Level(1000, 0, 10),) # collecting, cleaning the tip

            # for flowrate_level in flowrate_levels:
                # await asyncio.sleep(10) # Add a delay (in seconds) before pumps start
            if  flowrate_levels.flowrate_A == 0: 
                await pump13A._call_method(pump13A.METHOD_STOP)
                logger.info(f"{pump13A.name}: Pump stopped.")
            else: 
                await pump13A.set_flowrate_to(flowrate_levels.flowrate_A)

            if flowrate_levels.flowrate_B == 0: 
                await pump13B._call_method(pump13B.METHOD_STOP)
                logger.info(f"{pump13B.name}: Pump stopped.")
            else:
                await pump13B.set_flowrate_to(flowrate_levels.flowrate_B)
            await asyncio.sleep(flowrate_levels.time_in_seconds)
                
            # await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())
            # return True
    if keyword == 'max_a':
        url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
        logger.info(f"OPC-UA Client: Connecting to {url} ...")
        async with run_syrringe_pump.Client(url=url) as client:
            pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
            await pump13A.set_flowrate_to(2500)
            await asyncio.sleep(0)
    if keyword == 'max_b':
        url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
        logger.info(f"OPC-UA Client: Connecting to {url} ...")
        async with run_syrringe_pump.Client(url=url) as client:
            pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
            await pump13B.set_flowrate_to(250)
            await asyncio.sleep(0)
    if keyword == 'stop_a':
        url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
        logger.info(f"OPC-UA Client: Connecting to {url} ...")
        async with run_syrringe_pump.Client(url=url) as client:
            pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
            await pump13A._call_method(pump13A.METHOD_STOP)
            logger.info(f"{pump13A.name}: Pump stopped.")
    if keyword == 'stop_b':
        url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
        logger.info(f"OPC-UA Client: Connecting to {url} ...")
        async with run_syrringe_pump.Client(url=url) as client:
            pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
            await pump13B._call_method(pump13B.METHOD_STOP)
            logger.info(f"{pump13B.name}: Pump stopped.")


async def deactivate_pump():
    url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
    # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    # -----------------------------------------------------------------
    logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
        # await asyncio.gather(pump13A.activate(), pump13B.activate())
        await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())

async def activate_pump(a=False,b=False):
    url = OPC_UA_SERVER_URL # "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop
    # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    # -----------------------------------------------------------------
    logger.info(f"OPC-UA Client: Connecting to {url} ...")
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
        print(f'response of the Direct Injection Module was {resp}')
        return True        
    else:
        error=gsioc_protocol_object.iCommand('e')
        logger.debug(f'the direct injection module returned the following error: {error}')
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
        print(f'response of the Direct Injection Module was {resp}')
        return True
    else:
        error=gsioc_protocol_object.iCommand('e')
        logger.debug(f'the direct injection module returned the following error: {error}')
        return False

def go_home_and_switch_to_waste():
    sound.get_sound3()
    g2.connect()
    g2.bCommand('VL')
    g.connect()
    g.bCommand('H')
    g.bCommand('WBB')
    

def go_to_waste_vial(waste_vial_number: int = 1):
    sound.get_sound3()
    g.connect()
    g.bCommand('H')
    g.bCommand(rack4_commands.get_xy_command(waste_vial_number,'no')[0])
    g.bCommand('Z100:20:20')
    g2.connect()
    g2.bCommand('VI')

# def switch_pumps(flowrate_a=0,flowrate_b=0):
#     sound.get_sound3()
#     min_flowrate = 10
#     if flowrate_a < min_flowrate:
#         flowrate_a = 0
#     else:
#         flowrate_a = format_flowrate([flowrate_a],2500)[0]
#     if flowrate_b < min_flowrate:
#         flowrate_b = 0
#     else:
#         flowrate_b = format_flowrate([flowrate_b],250)[0]
#     asyncio.run(config_pump(run_syrringe_pump.Level(1000,125,0)))

def deactivate_both_pumps():
    sound.get_sound3()
    asyncio.run(deactivate_pump())

def activate_both_pumps():
    sound.get_sound3()
    asyncio.run(activate_pump(a=True,b=True))

def switch_to_load():
    sound.get_sound3()
    if dim_load(g2):
        print(f'Valve switched successfully.')

def switch_to_inject():
    sound.get_sound3()
    if dim_inject(g2):
        print(f'Valve switched successfully.')

def set_pump_a_to_max_flow_rate():
    sound.get_sound3()
    asyncio.run(config_pump(keyword='max_a'))

def set_pump_b_to_max_flow_rate():
    sound.get_sound3()
    asyncio.run(config_pump(keyword='max_b'))

def stop_pump_a():
    sound.get_sound3()
    asyncio.run(config_pump(keyword='stop_a'))
    
def stop_pump_b():
    sound.get_sound3()
    asyncio.run(config_pump(keyword='stop_b'))

# def run_preset_experiments():
    # pass

def monitore_bkp_in_gui():
    sound.get_sound3()
    # asyncio.run(protocol_power_supply.bkp_test_communication())
    asyncio.run(protocol_power_supply.main())


def set_voltage():
    pass

if __name__=='__main__':
    ser=serial.Serial('COM3',19200,8,"N",1,0.1)   
    g = gsioc.gsioc_Protocol(ser,'GX-241 II',33)#[X-241',"2.0.2.5"],33)       #full device name GX-241 II v2.0.2.5
    g2 = gsioc.gsioc_Protocol(ser,'GX D Inject',3)
    # global bkp
    # bkp = protocol_power_supply.BKPrecisionRS232('COM4')
    # bkp.initialize_connection()

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
    
    rack_position_offset_x=92       #distance in mm between rack_position=1 and =2 on x-axis
    rack_position_offset_y=0        #distance in mm between rack_position=1 and =2 on y-axis

    rack_pos4=2
    rack4_commands=Rackcommands(rack4,array_order4,rack_pos4,rack_position_offset_x,rack_position_offset_y)
    vial_large=Vial(40,40,94.74,93.25)

    main()
    
    
    
    
