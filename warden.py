import psutil
import re
import os
import time
from run import automation_main

from loguru import logger
logger.add('logs/watchdog.log', level='INFO')

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


def get_automation_process_state() -> str:
    """Retrieves current status of the automation process."""
    with open('logs/procedural_data.txt','r') as file:
        lines = file.readlines()
        process_id = str(lines[0]).strip()
        number_successfull_experiments = str(lines[1]).strip()
        overall_experiments = str(lines[2]).strip()
        errors = '[No Errors]'
    return process_id,number_successfull_experiments, overall_experiments, errors

# @error_handler(3)
def restarter():
    """Restarts the watched process when not apparent anymore. Checks in 30 sec intervals."""
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


