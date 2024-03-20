import asyncio
from asyncua import Client, ua
from loguru import logger
import sys

LOG_LEVEL = "INFO"

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




# async def main():
#     # ----------- Defining url of OPCUA and flowRate levels -----------
#     # url = "opc.tcp://rcpeno00472:5000/" #OPC Server on RCPE Laptop
#     url = "opc.tcp://rcpeno02341:5000/" # OPC Server on new RCPE laptop

#     # url = "opc.tcp://18-nf010:5000/" #OPC Server on FTIR Laptop
    
#     # -----------------------------------------------------------------


#     logger.info(f"OPC-UA Client: Connecting to {url} ...")
#     async with Client(url=url) as client:
#         # ------ Here you can define and operate all your pumps -------
#         pump13A = await Pump.create(client, "24196", "A")
#         pump13B = await Pump.create(client, "24196", "B")
#         # await asyncio.gather(pump13A.activate(), pump13B.activate())
        
        
#         flowrate_levels = (Level(310, 250, 5), # filling the system with reaction mixture
#                            Level(310, 200, 5), # running the reaction 1
#                            Level(310, 200, 5),) # collecting 1 mL
#                         #    Level(620, 62, 88), # running the reaction 2
#                         #    Level(620, 62, 10), # collecting for cleaning the tip
#                         #    Level(620, 62, 97), # collecting 1 mL
#                         #    Level(310, 31, 176), # running the reaction 3
#                         #    Level(310, 31, 15), # collecting for cleaning the tip
#                         #    Level(310, 31, 194), # collecting 1 mL
#                         #    Level(500, 50, 110), # running the reaction 4
#                         #    Level(500, 50, 10), # collecting for cleaning the tip
#                         #    Level(500, 50, 120), # collecting 1 mL
#                         #    Level(620, 62, 88), # running the reaction 5
#                         #    Level(620, 62, 10), # collecting for cleaning the tip
#                         #    Level(620, 62, 97), # collecting 1 mL
#                         #    Level(1000, 0, 60), # cleaning the system, going to waste
#                         #    Level(1000, 0, 10),) # collecting, cleaning the tip


#         for flowrate_level in flowrate_levels:
#             # await asyncio.sleep(10) # Add a delay (in seconds) before pumps start
#             if  flowrate_level.flowrate_A == 0: 
#                 await pump13A._call_method(pump13A.METHOD_STOP)
#                 logger.info(f"{pump13A.name}: Pump stopped.")
#             else: 
#                 await pump13A.set_flowrate_to(flowrate_level.flowrate_A)
            
#             if flowrate_level.flowrate_B == 0: 
#                 await pump13B._call_method(pump13B.METHOD_STOP)
#                 logger.info(f"{pump13B.name}: Pump stopped.")
#             else:
#                 await pump13B.set_flowrate_to(flowrate_level.flowrate_B)
#             await asyncio.sleep(flowrate_level.time_in_seconds)
            
#         await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())
      
# if __name__ == "__main__":
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
# asyncio.run(main())
