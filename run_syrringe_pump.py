import asyncio
from asyncua import Client, ua
from loguru import logger
import sys

# LOG_LEVEL = "INFO"

def get_node(client, idx, name):
    nodeid = build_nodeid(idx, name)
    node = client.get_node(nodeid)
    return node

def build_nodeid(idx, name) -> ua.NodeId:
    nodeid = ua.NodeId.from_string(f'ns={idx};i={name}')
    return nodeid


class Level():
    def __init__(self, flowrate_A: int, flowrate_B: int, time_in_seconds: float):
        self.flowrate_A = flowrate_A
        self.flowrate_B = flowrate_B
        self.time_in_seconds = time_in_seconds

class State():
    EMPTY = "EMPTY"
    EMPTYING = "EMPTYING"
    IDLE = "IDLE"
    FILLING = "FILLING"
    FULL = "FULL"
    PUMPING = "PUMPING"

class Pump(State):
    '''
    Pump class for Syrris Pump

    :param client: OPCUA client object
    :param serial_number: serial number of the pump
    :param pump_identificator: A or B as str
    '''

    NAME = "AsiaPump_"
    METHOD_STOP = "stop"
    METHOD_PUMP = "pump"
    METHOD_FILL = "fill"
    METHOD_EMPTY = "empty"
    METHOD_TARE = "tare"

    @classmethod
    async def create(cls, client, serial_number: str, pump_identificator: str):
        #Creates instance for communication to the pump via OPC-UA protocol.
        self = Pump()
        self.client = client
        self.serial_number = serial_number
        self.DeviceSet = get_node(self.client, 2, 5001)
        self.name = f"AsiaPump_{serial_number}{pump_identificator}"
        pump_browse_name = f"1:{self.name}"
        self.pump_object    = await self.DeviceSet.get_child([pump_browse_name])
        self.State          = await self.pump_object.get_child(["5:State"])
        self.Pressure       = await self.pump_object.get_child(["5:Pressure"])
        self.SyringeVolume  = await self.pump_object.get_child(["5:SyringeVolume"])
        self.FlowRate       = await self.pump_object.get_child(["5:FlowRate"])
        self.FlowRate_type  = await self.FlowRate.read_data_type_as_variant_type()
        
        self.methods = {
            self.METHOD_STOP: await self.pump_object.get_child(["5:Stop"]),
            self.METHOD_PUMP: await self.pump_object.get_child(["5:Pump"]),
            self.METHOD_FILL: await self.pump_object.get_child(["5:Fill"]),
            self.METHOD_EMPTY: await self.pump_object.get_child(["5:Empty"]),
            self.METHOD_TARE: await self.pump_object.get_child(["5:Tare"])
        }
        
        self.MAX_FLOWRATE = 4 * (await self.SyringeVolume.read_value())
        return self

    async def activate(self):
        #Activates the pump: stops and filles the valve
        logger.info(f"{self.name}: Starting the activation process...")
        await self._call_method(self.METHOD_STOP)
        await self._call_method(self.METHOD_FILL, self.MAX_FLOWRATE)
        await self._wait_for_value(self.State, self.FULL)
        logger.info(f"{self.name}: Activation process completed. -> Ready to use.")


    async def set_flowrate_to(self, value):
        #Sets the flowRate parameter to desired value and awaits this change
        reply = await self._call_method(self.METHOD_PUMP, value)
        if reply == "OK":
            logger.debug(f"{self.name}: FlowRate sent")
            #await self._wait_for_value(self.FlowRate, value)
            logger.info(f"{self.name}: FlowRate set to {value}")

        else:
            raise Exception(f"Coro set_flowrate_to got unexpected reply: {reply}.")
        

    async def read_pressure(self):
        #Reads the pressure
        value = await self.Pressure.read_value()
        logger.info(f"{self.name}: Pressure is {value}")
        return value


    async def deactivate(self):
        #Deactivates the pump: stops and empties the valve.
        logger.info(f"{self.name}: Starting the deactivation process...")
        await self._call_method(self.METHOD_STOP)
        await self._call_method(self.METHOD_EMPTY, self.MAX_FLOWRATE)
        await self._wait_for_value(self.State, self.EMPTY)
        logger.info(f"{self.name}: Deactivation process completed.")


    async def _call_method(self, method_name, value=None):
        if value is None:
            reply = await self.pump_object.call_method(self.methods[method_name])
            return reply

        else:
            input_argument = ua.Variant(value, self.FlowRate_type)
            reply = await self.pump_object.call_method(self.methods[method_name], input_argument)
            return reply
            

    async def _wait_for_value(self, opcua_variable, desired_value):
        current_value = await opcua_variable.read_value()
        logger.debug(f"Coro _wait_for_value: current {current_value}, desired {desired_value}")
        while not current_value == desired_value:
            await asyncio.sleep(1)
            current_value = await opcua_variable.read_value()
            logger.debug(f"Coro _wait_for_value: current {current_value}, desired {desired_value}")


# logger.remove()
# logger.add(sys.stderr, level=LOG_LEVEL)
