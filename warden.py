import psutil
import re
import os
import time
import sys
import asyncio
from immortility_decorator import error_handler
from run import automation_main
from loguru import logger

"""
Niklas nikl.sulz3@gmail.com
Eduardo eduardo.rial@rcpe.at
Christine schiller@student.tugraz.at
"""

def get_process_by_name_or_id(name: str = None, id: int = None):
    """finds processes by either name or ID."""
    ls = list()
    if name == None and id != None:
        for p in psutil.process_iter():
            if hasattr(p, 'pid'):
                if re.match(str(id), str(p.pid)):#(".*" + name + ".*", p.name()):
                    ls.append(p)
    elif name != None and id == None:
        for p in psutil.process_iter():
            if hasattr(p, 'pid'):
                if re.match(".*" + name + ".*", p.name()):
                    ls.append(p)
    else:
        raise Exception('Please enter only id or name, not both.')
    return ls

# print(os.getpid())

def get_automation_process_state() -> str:
    with open('logs/procedural_data.txt','r') as file:
        lines = file.readlines()
        process_id = str(lines[0]).strip()
        number_successfull_experiments = str(lines[1]).strip()
        overall_experiments = str(lines[2]).strip()
        errors = '[No Errors]'
    return process_id,number_successfull_experiments, overall_experiments, errors

# @error_handler(3)
def restarter():
    p = psutil.Process(os.getpid())
    p.nice(psutil.HIGH_PRIORITY_CLASS)
    logger.info(f'Process priority of warden process was set to {p.nice()}.')
    exps = str(0)
    while True:
        # print(get_process_by_name_or_id(id=pid)) #,id=4632))
        # python_processes = get_process_by_name_or_id(name='python3.10.exe')
        time.sleep(30)
        exps_before = int(exps)
        pid, exps, overall_exps, err = get_automation_process_state()
        exps_after = int(exps)
        # print(email_addr)
        # print(email_entr)
        if exps_before < exps_after:
            try:
                logger.critical(f'Experiments: {exps}, Errors: {err}')
            except:
                pass
        logger.info(f'warden process ID: {os.getpid()}')
        logger.info(f'watched process ID: {pid} - successfull experiments: {exps} - overall experiments: {overall_exps}')
        logger.info(f'{get_process_by_name_or_id(id=pid)}')
        if get_process_by_name_or_id(id=pid):
            if int(overall_exps) == int(exps):
                break
            else:
                continue
        else:
            if int(overall_exps) > int(exps):
                logger.critical(f'restarts the {automation_main.__name__} function, starting from experiment number {int(exps)+1}.')
                automation_main(remote=True,conduction=(int(exps)+1))
                break
            else:
                logger.info(f'Process was cancelled, but experiments where carried out to the end. Process is not restarted.')
                break

if __name__ == '__main__':
    restarter()


# import os

# print(os.getpid())
# print(os.getlogin())
# print(type(os.getpid()))
# import psutil

# processes = [p.cmdline() for p in psutil.process_iter() ]#if p.name().lower() in ['python.exe'] ]#and 'warden.py' not in p.cmdline()[1]]

# print(processes)
# while True:
#     p = next(psutil.process_iter())
#     p = p.cmdline()
#     print(p)

# import serial

# from os import getpid
# from sys import argv, exit
# import psutil  ## pip install psutil

# myname = argv[0]
# mypid = getpid()
# for process in psutil.process_iter():
#     if process.pid != mypid:
#         for path in process.cmdline():
#             if myname in path:
#                 print("process found")
#                 process.terminate()
                # exit()

# ser=serial.Serial('COM3',19200,8,"N",1,0.1) 

# i=0
# while True:
#     i+=1
#     transfered = ser.read(10)
#     print(transfered)
#     print(f'run {i}')

