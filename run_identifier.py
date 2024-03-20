
import time

NON_VOLATILE_MEMORY_FILE = 'logs/non_volatile_memory.txt'

def __reset_non_volatile_memory():
    """
    ATTENTION: Irreversibly overrides the NON_VOLATILE_MEMORY_FILE.
    """
    with open(f'{NON_VOLATILE_MEMORY_FILE}','w') as file:
        file.write('1')
        print(f'SUCCESSFULLY RESET NON VOLATILE MEMORY.')

def set_run_number():
    """
    Increases run number by 1.
    """
    with open(f'{NON_VOLATILE_MEMORY_FILE}','r') as file:
        lines = file.readlines()
        line = lines[0]
        run_number = int(line)
    with open(f'{NON_VOLATILE_MEMORY_FILE}','w') as file:
        file.write(str(run_number+1))
        print(f"writing run number: {run_number + 1}")

def get_run_number():
    """
    Reads current run number and returns it as an int().

    :returns: current run number as int()
    """
    with open(f'{NON_VOLATILE_MEMORY_FILE}','r') as file:
        lines = file.readlines()
        line = lines[0]
        run_number = line
        print(f'This is run number {run_number}.')
        return int(run_number)

if __name__ == '__main__':
    # __reset_non_volatile_memory()
    # set_run_number()
    get_run_number()
    
    
