from gsioc import gsioc_Protocol
import time
import serial
import numpy as np
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
import numpy as np
import sys
import csv
import regex as re
import binascii

#features of this programm:
#advanced user can define a arbitrary Rack type, using the class Rack()
#advanced user can input an array with arbitrary dimensions. The numbers within the array define the order for processing them by the liquid handler.
#it needs the size/volume/height of the vials within the rack, the default value is defined with the Rack(class)
#there has to be a profound error reporting and collision avoidance!
#the programm can be cancelled at any time by a defined shortcut!
#unexperienced user should be able to use the code to full extend by simply defining ALL COMPULSORY AND OPTIONAL PARAMETERS within an excel file (.csv)  
#the programm is able to move to every position in an arbitrary rack in an arbitrary order by defining:
# a Rack with all its dimensions
# an array with integer numbers, to define the processing order (it is possible to go to the same position more often than once)
# 

#Das Programm soll jede Rack-x/y-Position in einer beliebigen vorher festgelegten Reihenfolge ansteuern können, oder auch jede Position einzeln ansteuern können. An jeder Position soll es möglich sein, jede andere mögliche Operation auszuführen.
#Das Programm muss Kollisionen um jeden Preis vermeiden! >>> das kann nur sinnvoll in kombination mit den buffered und immediate commands umgesetzt werden.
#Das Programm muss zu jedem Zeitpunkt abgebrochen werden können! >>> das kann nur sinnvoll in kombination mit den buffered und immediate commands umgesetzt werden.
#Das Programm muss Fehlermeldungen erkennen und rückmelden. >>> das kann nur sinnvoll in kombination mit den buffered und immediate commands umgesetzt werden.

#############################################################################################
#############################################################################################

class Rack():
    def __init__(self,array_dimensions,offset_x,offset_y,vial2vial_x,vial2vial_y):
        self.array_dimensions=array_dimensions
        self.offset_x=offset_x
        self.offset_y=offset_y
        self.vial2vial_x=vial2vial_x
        self.vial2vial_y=vial2vial_y
        
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
        index_y,index_x=self.rack.get_vial_indices(vial_pos,self.rack_order,tolerance)#[0]
        # index_y=self.rack.get_vial_indices(vial_pos,self.rack_order)[1]
        # print(f'output of module "get_vial_indices()" is index_x: {index_x} and index_y {index_y}')
        if len(index_x)==len(index_y):
            command=[]
            for i in range(len(index_x)):
                # print(f'index x: {index_x}, \n index y: {index_y}')
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



    
############################################# ADVANCED USER SETTINGS ###########################################

# rack1=Rack([2,7],20,55,30,30) #distances in mm, CHECK IF X AND Y IS WELL DEFINED!!!

### device parameter ###

rack_position_offset_x=92       #distance in mm between rack_position=1 and =2 on x-axis
rack_position_offset_y=0        #distance in mm between rack_position=1 and =2 on y-axis

############################################# UNADVANCED USER SETTINGS #############################################

def get_command_list():
    # array_order=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
    # [1,2],
    # [3,4],
    # [5,6],
    # [7,8],
    # [9,10],
    # [11,0],                     #int(0) denotes the blank solution
    # [-1,-2],                    #int(-1) denotes an empty slot, int(-2) marks the waste
    # ])

    # array_order=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
    # [1,2,3,4],
    # [5,6,7,8],
    # [9,10,11,12],
    # [13,14,15,16],
    # [17,18,19,0],
    # [21,22,23,24],                     #int(0) denotes the blank solution
    # [25,26,27,28],                    #int(-1) denotes an empty slot, int(-2) marks the waste
    # [29,30,31,32],
    # [33,34,35,36],
    # [37,38,39,40],
    # [41,42,43,44],
    # [45,46,47,48]    
    # ])

    # array_order=np.array([      #user is obligated to define a integer number i>=1 for each vial in the rack in ascending order 
    # [2,2,2,2],
    # [2,2,2,2],
    # [2,2,2,2],
    # [2,2,2,2],
    # [2,2,2,2],
    # [2,2,2,2],                     #int(0) denotes the blank solution
    # [2,2,2,0],                    #int(-1) denotes an empty slot, int(-2) marks the waste
    # ])

    # array_order=np.array([
    # [1,2],
    # [3,4]
    # ])

    with open("array_order.csv") as csvfile:
        read_in=csv.reader(csvfile)
        line=0
        array=list()
        for row in read_in:
            line+=1
            if line==1:
                rack_pos=int(row[1])
                # x=row[0].split(';') 
                # rack_pos=int(x[1])
            elif line==2:
                rack_type=str(row[1])
                # x=row[0].split(';')
                # rack_type=str(x[1])
            else:
                # x=row[0].split(';')
                x=row
                for i in range(len(x)):
                    x[i]=int(x[i])
                array.append(x)
        array_order=np.array(array)


    # print(array_order)
    # print(rack_type)
    # print(rack_pos)
    
    

    if rack_type=='a':
        rack1=Rack([2,7],20,55,(28.55+2.17),(28.55+1.38)) #distances in mm, CHECK IF X AND Y IS WELL DEFINED!!!
    if rack_type=='b':
        rack1=Rack([4,12],8.7,40,(2.11+15.6),(2.72+15.6+0.35))

    
    # rack_pos=1                #rack is positioned either in the Left (int(1)), or the Right (int(2)) postion of the liquid handler

    ############### ASSIGNING THE CLASS TO A VARIABLE #################

    rack1_command=Rackcommands(rack1,array_order,rack_pos,rack_position_offset_x,rack_position_offset_y) #the user has to define on which rack he wants to process a command!
    
    ########## EXAMPLE 3: INITIALIZING THE COMMAND LIST ###############

    executable_rack1_command=[]

    ########## EXAMPLE 2: APPENDING SINGLE POSITIONAL COMMAND #############

    # executable_rack1_command=rack1_command.get_xy_command(vial_pos=2)
    # executable_rack1_command.extend(rack1_command.get_xy_command(4))

    ########## EYAMPLE 3: APPENDING DEFAULT MODE COMMANDS #############

    executable_rack1_command.extend(rack1_command.get_defaultmode_commands('yes','yes'))
    ###########
    print(f'the following list of commands is ready for sending to the device: {executable_rack1_command}')
    return executable_rack1_command
    
position_workflow=get_command_list()
# position_workflow=['H','Z100','Z20','Z125','X25/25','H']

# print(f'therefore the workflow consists of the following commands: {position_workflow}')
# for i in range(len(position_workflow)): 
#     print(str(position_workflow[i]))



# approach for error checking and collision avoidance:
ser=serial.Serial("COM8",19200,8,"N",1,0.1)      
g = gsioc_Protocol(ser,'VERITY 4020',11)#[X-241',"2.0.2.5"],33)       #full device name GX-241 II v2.0.2.5

g.connect()

def expected_move_feedback(gsioc_class_object,commandclass_object,command):      #use only it the awaited response equals to the sent command. returns bool(True) if response equals command, returns bool(False) if not.
    gsioc_class_object.logger.debug(f'starting expected_move_feedback() with arguments: {commandclass_object}')
    response=(binascii.b2a_qp(commandclass_object)).decode('utf-8').strip()
    # prev_elem=str(binascii.b2a_qp(previous_positional_element))
    gsioc_class_object.logger.debug(f'converted arguments: {response}')
    gsioc_class_object.logger.debug(f'unconverted command: {command}')
    catch=re.search(response,command)

    # gsioc_class_object.logger.debug(f'starts searching for X positional command')
    # check_xy=re.search('X',response)
    
    # if check_xy:
        
    #     koord_xy=[2,4]
    #     resp_xy=gsioc_class_object.iCommand('X')
    #     catch_xy=re.search('(\d+)(\.\d+)/(\d+)(\.*\d+)',resp_xy)
        
    #     if catch_xy:
    #         koord_xy[0]=catch_xy.group(0)
    #         koord_xy[1]=catch_xy.group(2)
    #         koord_xy='/'.join(koord_xy)
    #     else:
    #         gsioc_class_object.logger.debug(f"didn't catch_xy")
    #         pass
        
    #     koord2_xy=[1,3]
    #     catch2_xy=re.search('(\d+)(\.\d+)/(\d+)(\.*\d+)',command)

    #     if catch2_xy:
    #         koord2_xy=[]
    #         koord2_xy[0]=catch2_xy.group(0)
    #         koord2_xy[1]=catch2_xy.group(2)
    #         koord2_xy='/'.join(koord2_xy)
    #     else:
    #         gsioc_class_object.logger.debug(f"didn't catch2_xy")
    #         pass
        
    # else:
    #     gsioc_class_object.logger.debug(f'did not find X positional command, starts searching for Z positional command')
    #     check_z=re.search('Z',commandclass_object)
    #     if check_z:
    #         resp_z=gsioc_class_object.iCommand('Z')

    if catch: #and koord_xy==koord2_xy:
        gsioc_class_object.logger.debug('response euqals command: ready for the next command!')
        # print('response euqals command: ready for the next command!')
        return True
    else:
        gsioc_class_object.logger.debug('response does not equal command: process cancelled!')
        # print('response does not equal command: process cancelled!')
        return False
    
# def expected_position_feedback(gsioc_class_object,previous_positional_element):
#     gsioc_class_object.logger.debug(f'starting expected_position_feedback() with arguments: {gsioc_class_object} and {previous_positional_element}')
#     response_xy=gsioc_class_object.iCommand('X')
#     response_z=gsioc_class_object.iCommand('Z')
#     g.logger.debug(f'response for x/y: {response_xy} and for z: {response_z}')
#     # response=(binascii.b2a_qp(response_x)).decode('utf-8').strip()
#     # g.logger.debug(f'converted arguments: {response}')
#     # previous_positional_element=(binascii.b2a_qp(previous_positional_element)).decode('utf-8').strip()
#     g.logger.debug(f'previous_positional_argument: {previous_positional_element}')

#     catch_xy=re.search('(\d+.*)/(\d+.*)',response_xy)#'(\d+(\.\d+)?/\d+(\.\d+)?)',response_xy)
#     catch_z=re.search('(^\d+(\.\d+)?$)',response_z)

#     g.logger.debug(f'catch_xy: {catch_xy}')
#     g.logger.debug(f'catch_z: {catch_z}')

#     if catch_xy:
#         koords=[]
#         for i in range(len(catch_xy.groups())):
#             koords.append(str(catch_xy.group(i)))
#             koords[i]=round(float(koords[i]))
#         new_koords1_xy='/'.join(koords)

#     g.logger.debug('step1 successfull')

#     if catch_z:
#         koords=catch_z.group()
#         new_koords1_z=round(float(str(koords)))
    
#     g.logger.debug('step2 successfull')

#     catch2_xy=re.search('(\d+.*)/(\d+.*)',previous_positional_element)#'(\d+(\.\d+)?/\d+(\.\d+)?)',response_xy)
#     catch2_z=re.search('(^\d+(\.\d+)?$)',previous_positional_element)

#     g.logger.debug('step3 successfull')

#     g.logger.debug(f'catch2_xy: {catch2_xy.group()}')
#     g.logger.debug(f'catch2_z: {catch2_z.group()}')

#     g.logger.debug('step4 successfull')

#     if catch2_xy:
#         koords=[]
#         for i in range(len(catch2_xy.groups())):
#             koords.append(str(catch2_xy[i]))
#             koords[i]=round(float(koords[i]))
#         new_koords2_xy='/'.join(koords)

#     g.logger.debug('step5 successfull')

#     if catch2_z:
#         koords=catch2_z.group()
#         new_koords2_z=round(float(koords))

#     # catch2_xy=re.search(catch_xy,str(previous_positional_element))
#     # catch2_z=re.search(catch_z,str(previous_positional_element))

#     g.logger.debug(f'catch2_xy: {catch2_xy}')
#     g.logger.debug(f'catch2_z: {catch2_z}')

#     # if catch_xy and catch2_xy:
#     #     catch3_xy=re.search(str(catch_xy.group(0)),str(catch2_xy.group(0)))
#     # else:
#     #     catch3_xy=False
#     # if catch_z and catch2_z:
#     #     catch3_z=re.search(str(catch_z.group(0)),str(catch2_z.group(0)))
#     # else:
#     #     catch3_z=False
#     # # catch2_xy=re.search('\d+.*/\d+',str(previous_positional_element))
#     # # catch2_z=re.search('(^\d+(\.\d+)?$)',str(previous_positional_element))

#     # g.logger.debug(f'catch3_xy: {catch3_xy}')
#     # g.logger.debug(f'catch3_z: {catch3_z}')
    
#     if new_koords1_z==new_koords2_z or new_koords1_xy==new_koords2_xy:#
#         # print('positional response promising: current position equals the positional argument of the previous command')
#         g.logger.debug('positional response promising: current position equals the positional argument of the previous command')
#         return True
#     else:
#         # print('positional response problematic: current position does not equal the positional argument of the previous command')
#         g.logger.debug('positional response problematic: current position does not equal the positional argument of the previous command')
#         return False

# g.iCommand('e')

#g.bCommand('p')

g.bCommand('@4')
time.sleep(1)
g.iCommand('@')
# g.bCommand('PN:100:1.23')
# time.sleep(5)

# g.bCommand('PN:-100:1.23')



    
    

"""

####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################
####################################################################################################################################################################

# g.__init__
# g = gsioc_Protocol
# ser=serial.Serial("COM8",19600,8,"N",1)
# g(ser,"gx-241",33)
# g.connect
# g.verify_open
# g.verify_device

# g.iCommand(self=g,commandstring="$")

ser=serial.Serial("COM8",19200,8,"N",1,0.1)
# g(ser,"gx-241",33)
g = gsioc_Protocol(ser,'GX-241 II',33)#[X-241',"2.0.2.5"],33)#GX-241 II v2.0.2.5
# g = gsioc_Protocol(ser,'204',6) # Modification for fraction collector
g.connect()
# g.verify_open()
# g.verify_device()
# g.iCommand("$")
# time.sleep(5)
# g.connect
g.bCommand('H')
# # g.bCommand('e')
time.sleep(0.1)
# # # g.bCommand('T001')
g.bCommand('X20/55')
time.sleep(0.1)
g.bCommand('H')

# class Rack():
#     def __init__(self,rack_position,size):
#         self.rack_position=rack_position
#         self.size=size

#     def 

#arr.shape=(2,7)

# arr=np.array([
# [1,2,3,4],
# [5,6,7,8],
# [9,10,,11,12],
# [13,14,15,16],
# [17,18,19,20],
# [21,22,23,24],
# [25,26,27,28],
# [29,30,31,32],
# [33,34,35,36],
# [37,38,38,39],
# [40,41,42,43],
# [44,45,46,47]
# ])

# arr=np.array([
# [1,2],
# [3,4],
# [5,6],
# [7,8],
# [9,10],
# [11,12],
# [13,14]
# ])

# rack_position=['left','right']

# rack_type=['big','small']

# class Rack():
#     def __init__(self,array,rack_type,rack_position):
#         self.array=array
#         self.rack_type=rack_type
#         self.rack_position=rack_position

#     def get_xypos_command(self,position_number):
#         #if position_number in self.array: # make a input check!!!
#         indices=self.array.index(position_number)
#         x=20
#         y=55
#         x_offset=30
#         y_offset=30
#         xy_command=f'X{x+indices[0]*x_offset}/{y+indices[1]*y_offset}'
#         return xy_command
         
# r1=Rack(arr,'big','left')
# print(r1.get_xypos_command(1))

# for i in range(14):
#     if i<7:
#         g.bCommand(f'X{20}/{55+30*i}')
#         # if i==6:
#         #     print("sleeping for 3 sec...")
#         #     time.sleep(3)
#     else:
#         g.bCommand(f'X{20+30}/{55+30*(i-7)}')
#     # time.sleep(0.3)
#     # print("sleeping for 0.3 sec...")
# g.bCommand('H')        



# print(arr.index(arr[0][0]))

# for i in range(len(arr)):
#     if (i+1)%2==0:
#         j=1
#     else:
#         j=0
#     arr[1][j]



# g.bCommand('X [10[:25]:25][/10[:25[:25]]]')

# for i in range(5):
#     g.bCommand(f"Z {i*15+1}")
#     time.sleep(5)

# g.bCommand('H')

# def main():
#     valid_commands_list:[
#         ['%','I'],
#         ['$','I'],
#         ['*','I'],
#         ['@','I'],
#         ['Ex[y[z]]','B'],
#         ['F','I'],
#         ['Fs','B'],
#         ['H','B'],
#         ['J','I'],
#         ['Ja[b[c[d]]]','B'],
#         ['Jc[:t]','B'],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],
#         ['',''],

#         ['@a[=v]','B'],
#         ['~n','B'],
#         ['.','I'],
#         ['.str','B'],
#         ['e','I'],
#         ['e[n]','B'],
#     ]

#     # for i in len(valid_commands_list):






# # ser.close()

# # g.iCommand(self=g,commandstring="$")

# # g.verify_open
# # g.verify_device
# #g.iCommand(6,"$")

# # what serial port/device name/ID number for the ROAR script
# # does the device have to be registered at OPC UA to control it over this platform?
# # is there a documentation of the GILSON devices which provides more details?
# # how to run the ROAR script successfully+

# # device IDs
# # 3 injection valve/module
# # 33 liquid handler
# # 6 fraction collector 

# #when liquid handler is reset, it cannot be resetted again by the python script
# #it is possible to query the error status many times, if the response is 0
# #could it have a problem with responds of more than one character? propably not, since the full response is "0 errors", if there are no errors
# #it should read out the whole response message!
# #what is the problem with the buffered commands?
"""
#################################################################################################################################################