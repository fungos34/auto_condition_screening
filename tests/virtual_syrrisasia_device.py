# url = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # OPC Server on private laptop

import sys
# sys.path.insert(0, "..")
import time
import asyncio
from loguru import logger

from opcua import ua, Server, uamethod

from loguru import logger

SERVER_URL = "opc.tcp://127.0.0.1:36090/freeopcua/server/" # OPC Server on private laptop # "opc.tcp://rcpeno02341:5000/" RCPE laptop

def start_opcua_syrris_asia_server(serial_number: str = '24196', pump_identificators: list = ['A','B'], server_url: str = "opc.tcp://127.0.0.1:36090/freeopcua/server/"):
    # setup our server
    server = Server()
    server.set_endpoint(server_url)

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)
    nodeid = ua.NodeId.from_string(f'ns={idx};i={5001}')

    STATES = ["EMPTY", "EMPTYING", "IDLE", "FILLING", "FULL", "PUMPING"]
    SERIAL_NUMBER = serial_number
    PUMP_IDENTIFICATORS = pump_identificators

    TRIGGER_EMPTY = False
    TRIGGER_FULL = False

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # populating our address space
    
    device_set = objects.add_object(nodeid, "SyrrisAsiaPumps")

    for i in range(len(PUMP_IDENTIFICATORS)):
        pump_object = device_set.add_object(1, f"AsiaPump_{SERIAL_NUMBER}{PUMP_IDENTIFICATORS[i]}")
        State = pump_object.add_variable(5, "State", STATES[2])
        Pressure = pump_object.add_variable(5, "Pressure", 2.0)
        FlowRate = pump_object.add_variable(5, "FlowRate", 0.0)
        SyringeVolume = pump_object.add_variable(5, "SyringeVolume", 1000.0)

        State.set_writable()
        Pressure.set_writable()
        FlowRate.set_writable()    # Set MyVariable to be writable by clients
        SyringeVolume.set_writable()
        
        @uamethod
        def stop(parent):
            """Coro: Simulating pump stopping by waiting 2 sec.
            :returns: 'OK'"""
            logger.info(f'{parent}carries out stop()')
            time.sleep(1)
            logger.info(f'Pump stopped.')
            FlowRate.set_value(0) 
            State.set_value(STATES[2])
            return "OK"

        @uamethod
        def pump(parent,flowrate):
            """Coro: Simulating pump starting by waiting 2 sec.
            :returns: 'OK'"""
            logger.info(f'{parent} carries out pump()')
            time.sleep(1)
            logger.info(f'Pump flowrate set to {flowrate} (μL/min)')
            FlowRate.set_value(flowrate) 
            State.set_value(STATES[5])
            return "OK"

        @uamethod
        def fill(parent,flowrate):
            """Coro: Simulating pump filling by waiting 5 sec."""
            logger.info(f'{parent} carries out fill() at flowrate {flowrate} (μL/min).')
            State.set_value(STATES[3])
            FlowRate.set_value(flowrate) 
            wait = 1
            for sec in range(wait):
                time.sleep(1)
                logger.info(f'Filling pump for {wait - sec} more seconds.', end='\r')
            FlowRate.set_value(0) 
            State.set_value(STATES[4])

        @uamethod
        def empty(parent,flowrate):
            """Coro: Simulating pump emptying by waiting 5 sec."""
            logger.info(f'{parent} carries out empty() at flowrate {flowrate} (μL/min).')
            State.set_value(STATES[1])
            FlowRate.set_value(flowrate) 
            wait = 1
            for sec in range(wait):
                time.sleep(1)
                logger.info(f'Emptying pump for {wait - sec} more seconds.', end='\r')
            FlowRate.set_value(0) 
            State.set_value(STATES[0])

        @uamethod
        def tare(parent):
            """Coro: Simulating pump taring by waiting 5 sec.
            :returns: 'OK'"""
            logger.info(f'{parent} carries out tare()')
            State.set_value(STATES[2])
            wait = 1
            for sec in range(wait):
                time.sleep(1)
                logger.info(f'Taring pump for {wait - sec} more seconds.', end='\r')
            State.set_value(STATES[0])
            return 'OK'

        # Add method to server
        # Declare the input and output arguments

        inarg = ua.Argument()
        inarg.Name = 'Flowrate'
        inarg.DataType = ua.VariantType.Float
        inarg.ValueRank = -1 # what is this?
        inarg.ArrayDimensions = []
        inarg.Description = ua.LocalizedText('Description of arg1')

        outarg = ua.Argument()
        outarg.Name = 'Return'
        outarg.DataType = ua.VariantType.String
        outarg.ValueRank = -1
        outarg.ArrayDimensions = []
        outarg.Description = ua.LocalizedText('Method Return Value -> OK')

        pump_object.add_method(5, "Stop", stop, [], [outarg] )
        pump_object.add_method(5, "Pump", pump, [inarg], [outarg] )
        pump_object.add_method(5, "Empty", empty, [inarg], [])
        pump_object.add_method(5, "Fill", fill, [inarg], [])
        pump_object.add_method(5, "Tare", tare, [], [outarg])
   

    # starting!
    server.start()
    
    try:
        count = 0
        while True:
            time.sleep(1)
            count += 0.1
            Pressure.set_value(count)
    finally:
        #close connection, remove subcsriptions, etc
        server.stop()


if __name__ == '__main__':
    start_opcua_syrris_asia_server('24196',['A','B'],SERVER_URL)