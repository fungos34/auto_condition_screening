import psutil
import re
import os
import time

from automated_platform.module.lab_equipment.active_components.gsioc.virtual_device import VirtualDevice, main
from immortility_decorator import error_handler
from run import automation_main
from loguru import logger
import signal

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

def get_automation_process_state():
    with open('procedural_data.txt','r') as file:
        lines = file.readlines()
        process_id = str(lines[0]).strip()
        number_successfull_experiments = str(lines[1]).strip()
        overall_experiments = str(lines[2]).strip()
    return process_id,number_successfull_experiments, overall_experiments

# @error_handler(3)
def restarter():
    pid, exps, overall_exps = get_automation_process_state()
    while True:
        # print(get_process_by_name_or_id(id=pid)) #,id=4632))
        # python_processes = get_process_by_name_or_id(name='python3.10.exe')
        time.sleep(10)
        logger.info(f'warden process ID: {os.getpid()}')
        logger.info(f'watched process ID: {pid} - successfull experiments: {exps} - overall experiments: {overall_exps}')
        logger.info(f'{get_process_by_name_or_id(id=pid)}')
        if get_process_by_name_or_id(id=pid):
            continue
        else:
            if int(overall_exps) > int(exps):
                logger.critical(f'restarts the {automation_main.__name__} function, starting from experiment number {int(exps)+1}.')
                automation_main(remote=True,conduction=(int(exps)+1))
                break
            else:
                logger.info(f'Process was cancelled, but experiments where carried out to the end. Process is not restarted.')
                break

def proc_killer(process_id: bool):
    os.kill(process_id,signal.SIGILL)


if __name__ == '__main__':
    print(get_process_by_name_or_id(id=11564)) # automation Process
    print(get_process_by_name_or_id(id=1316)) # warden process
    proc_killer(11564)


