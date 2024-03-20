"""! Uses Pyserial instead of asynchio because the multithreading seems to cause delayed responses and therefore no suitable request-response pairs.
"""
import serial
import time
import sys
import asyncio

from loguru import logger
logger.add('logs/monitoring.log', level='INFO', filter="monitor_BKP")

###################################################################################
############################## USER SETTINGS ######################################
###################################################################################

PORT     = 'COM4'
COMMANDS = 'VOLT?\rCURR?\r' # 'CURR 010.0\r'

###################################################################################
############# available commands for B+K PRECISION 1739 Revision 1.3 ##############
# 'OUT ON\r'              #activates power output
# 'VOLT 10.00\r'          #range 00.00 - 30.00
# 'CURR 100.0\r'          #range 000.0 - 999.9
# 'VOLT?\r'               #queries the voltage in (V) - the same value as at the display
# 'VOLT?\rCURR?\rSTAT?\r' #use multiple commands to query different settings at the same time
# 'CURR?\r'               #queries the current in (mA) - the same value as at the display
# 'STAT?\r'               #queries the mode: either constant voltage (CV) or constant current (CC)
# 'IDN?\r'                #queries the identity number of the device
# 'SAVE\r'                #sets the parameters 3 sec after the last command
# 'OUT OFF\r'             #deactivates power output
###################################################################################
####### BK Precision error responses via RS232 connection and their meaning #######

# please note: other error messages can be displayed on the voltage display: 
# Er xx, where xx is a number: Self-Test Errors, Calibration Errors(zero/full voltage/current calibration errors)

error_responses={
    "Communication Error\r": ": RS232 framing, parity, or overrun error",
    "Syntax Error\r": ": invalid syntax was found in the command string",
    "Out of range\r": ": a numeric parameter value is outside the valid range for the command"
    }
###################################################################################
############################ SET SERIAL CONNECTION ################################

def get_port(logger,com_port='COM4'):
    try:
        port=serial.Serial(com_port,9600,8,'N',1,4,True)
    except FileNotFoundError:
        logger.error(f"FileNotFoundError at '{time.asctime()}'")
        sys.exit('Script ended. Propably the specified port is invalid.')    
    return port


###################################################################################
############################## KILL SERIAL PORT ###################################

def kill_port(com_port):
    com_port.close()

###################################################################################
########## GENERATES COMMANDS LIST OF B+K PRECISION 1739 Revision 1.3  ############

def get_commands(commands):
    commands_list=[commands]
    # for i in range(len(commands)):
    #     commands_list.append(commands[i])
    return commands_list

###################################################################################
############### QUERY DEVICE RESPONSES IN FOUR SEC INTEVAL ########################

def get_values(commands_list,port,logger):
    """! Sends the specified commands in a infinite loop to the device and saves the reply to two different Log Files with different details. The loop is Cancelled by a KeyboardInterrupt with 'Strg+C'.

    @param commands_list    List of valid commands which are sent to the device in every iteration.
    @param port             Serial Port (RS232), specified with PySerial module.
    """
    eol='\r'
    start=time.time()
    logger.debug(f"Data collection started at '{time.asctime()}' >>> cancel with 'Strg+C' input in Terminal <<<")
    logger.debug(f'time(sec),output,unit')
    try:
        while True:
            for j in range(len(commands_list)):
                message=commands_list[j].encode('ascii')
                port.write(message)
                reply=(port.read_until(expected=eol)).decode('ascii')
                if reply.find('V') and reply.find('mA'):
                    responses=reply.splitlines()
                    # print(responses)
                    for i in range(len(responses)):
                        if error_responses.get(responses[i]):
                            logger.debug(f"Sent Message: '{message}' Device reply: '{responses[i]}' Interpretation: '{error_responses.get(responses[i])}'")
                            left=responses[i]
                            right=f'command: {commands_list[j]}'
                        elif responses[i].endswith('V'):
                            left,right=responses[i].split("V")
                            right='V'
                        elif responses[i].endswith('mA'):
                            left,right=responses[i].split("mA")
                            right='mA'
                        elif responses[i]=='OFF':
                            left='OFF'
                            right=''
                        else:
                            left=responses[i]
                            right=f'command: {commands_list[j]}'
                        logger.debug(f'{commands_list[j]}')
                        logger.info(f'{round((time.time()-start),2)},'f'{left},'f'{right}')
    except KeyboardInterrupt:
        logger.error(f"KeyboardInterrupt at '{time.asctime()}'")
        sys.exit('Script ended. "Strg+C" was entered in the Terminal.')
    except UnicodeDecodeError:
        logger.error(f"UnicodeDecodeError at '{time.asctime()}'")
        sys.exit('Script ended. Propably the Device was switched off.')

###################################################################################
################################### RUN SCRIPT ####################################

if __name__=='__main__':
    asyncio.run(get_values(get_commands(COMMANDS),get_port(logger,PORT),logger))

###################################### END ########################################