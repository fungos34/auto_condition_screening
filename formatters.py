import numpy as np
import sys

from loguru import logger

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
                logger.critical(f'value "{n}" out of range: {RANGE_CURRENT}')
            pass
        except TypeError:
            currents_out.append(np.nan)
            logger.critical(f'value "{n}" is not a number')
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
                logger.critical(f'value "{n}" out of range: {RANGE_VOLTAGE}')
            pass
        except TypeError:
            voltages_out.append(np.nan)
            logger.critical(f'value "{n}" is not a number')
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
                logger.critical(f'value "{n}" out of range: {RANGE_FLOWRATE}')
            pass
        except TypeError:
            flowrates_out.append(np.nan)
            logger.critical(f'value "{n}" is not a number')
            pass
    return flowrates_out
