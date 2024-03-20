from loguru import logger
import serial
import time
import inspect
import asyncio
import functools
from immortility_decorator import error_handler

def logging_handler(fun):
    """
    Decorator which loggs all input/output values and all raised errors of the decorated function.

    :param fun: function which has been decorated.
    """
    logger.info(f'Logging decorator launched for {fun.__name__}.') 

    if inspect.iscoroutinefunction(fun):
        @functools.wraps(fun)
        async def async_logging_arguments(*args,**kwargs):
            # return_values = []
            # [return_values.append(i) for i in [*fun(*args,**kwargs)]]
            return_values = await fun(*args,**kwargs)
            logger.debug(f'Input values: {args,kwargs}/types args: {[type(i) for i in [*args]]}/types kwargs: {[type(i) for i in [*kwargs]]}')
            logger.debug(f'Return values: {return_values}/types: {[type(return_values) if return_values is None or type(return_values) is str or bytearray else [type(return_values[i]) for i in range(len(return_values))]]}')
            logger.debug(f'Local namespace: {locals()}')
            logger.info(f'Logging decorator abandoned for {fun.__name__}.\n\n') 
            return return_values
        return async_logging_arguments
    else:
        @functools.wraps(fun)
        def sync_logging_arguments(*args,**kwargs):
            # return_values = []
            # [return_values.append(i) for i in [*fun(*args,**kwargs)]]
            return_values = fun(*args,**kwargs)
            logger.debug(f'Input values: {args,kwargs}/types args: {[type(i) for i in [*args]]}/types kwargs: {[type(i) for i in [*kwargs]]}')
            logger.debug(f'Return values: {return_values}/types: { [type(return_values) if return_values is None or type(return_values) is str or bytearray else [type(return_values[i]) for i in range(len(return_values))]]}')
            logger.debug(f'Local namespace: {locals()}')
            logger.info(f'Logging decorator abandoned for {fun.__name__}.\n\n')
            return return_values
        return sync_logging_arguments 

@error_handler(repititions=3)
@logging_handler
async def random_communication_module(port, commands):
    try:
        ser = serial.Serial(port,9600)
        ser.write(commands[0].encode('ascii'))
        time.sleep(3)
        ser.write(commands[-1].encode('ascii'))
        return ser.read(2)
    except KeyboardInterrupt:
        raise ValueError
    

@error_handler(repititions=3)
@logging_handler
def random_sync_communication_module(port, commands):
    try:
        ser = serial.Serial(port,9600)
        ser.write(commands[0].encode('ascii'))
        time.sleep(3)
        ser.write(commands[-1].encode('ascii'))
        return ser.read(2)
    except KeyboardInterrupt:
        raise ValueError

if __name__ == '__main__':
    asyncio.run(random_communication_module('COM4',['OUT ON\r','OUT OFF\r']))
    random_sync_communication_module('COM4',['OUT ON\r','OUT OFF\r'])