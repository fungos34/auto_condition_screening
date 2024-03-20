import psutil
import re
import os
import time
# from run import automation_main
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


def get_automation_process_state():
    with open('procedural_data.txt','r') as file:
        lines = file.readlines()
        process_id = str(lines[0]).strip()
        number_successfull_experiments = str(lines[1]).strip()
        overall_experiments = str(lines[2]).strip()
    return process_id,number_successfull_experiments, overall_experiments


def proc_killer(process_id: int):
    """Stopps the process with the inputted process ID."""
    os.kill(process_id,signal.SIGILL)


if __name__ == '__main__':
    # print(get_process_by_name_or_id(id=11564)) # automation Process
    # print(get_process_by_name_or_id(id=1316)) # warden process
    proc_killer(15120)


