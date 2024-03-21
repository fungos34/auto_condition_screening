import numpy as np
import customtkinter as ctk
import serial
import gsioc
import asyncio
import run_syrringe_pump
import sound
import protocol_power_supply

from flow_setup import Rack, Rackcommands, Vial
from commands import config_pump, activate_pump, deactivate_pump, dim_load, dim_inject
import run_syrringe_pump

##### Adapt this URL to the desired OPC-UA endpoint #####
OPC_UA_SERVER_URL = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # "opc.tcp://rcpeno02341:5000/"
#########################################################

def main():
    root_ctk = ctk.CTk()
    root_ctk.geometry("800x1225")
    root_ctk.title('Automation Enabled Electroorganic Synthesis in Flow')
    ctk.set_appearance_mode("dark")

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
    button4.place(relx=0.1, rely=0.5, anchor=ctk.NW)
    button5.place(relx=0.1, rely=0.6, anchor=ctk.NW)
    button6.place(relx=0.1, rely=0.7, anchor=ctk.NW)
    button7.place(relx=0.1, rely=0.8, anchor=ctk.NW)
    root_ctk.mainloop() # Rest of the script won't execute until startButton pressed


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
    asyncio.run(config_pump(flowrate_levels = run_syrringe_pump.Level(2500,0,0), url = OPC_UA_SERVER_URL))

def set_pump_b_to_max_flow_rate():
    sound.get_sound3()
    asyncio.run(config_pump(flowrate_levels = run_syrringe_pump.Level(0,250,0), url = OPC_UA_SERVER_URL))

def stop_pump_a():
    sound.get_sound3()
    asyncio.run(config_pump(flowrate_levels = run_syrringe_pump.Level(0,0,0), url = OPC_UA_SERVER_URL))

def stop_pump_b():
    sound.get_sound3()
    asyncio.run(config_pump(flowrate_levels = run_syrringe_pump.Level(0,0,0), url = OPC_UA_SERVER_URL))

def monitore_bkp_in_gui():
    sound.get_sound3()
    asyncio.run(protocol_power_supply.main())



if __name__=='__main__':
    ser=serial.Serial('COM3',19200,8,"N",1,0.1)   
    g = gsioc.gsioc_Protocol(ser,'GX-241 II',33)       #full device name GX-241 II v2.0.2.5
    g2 = gsioc.gsioc_Protocol(ser,'GX D Inject',3)

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
    
    
    
    
