import time
from loguru import logger
import run_syrringe_pump
import asyncio


async def config_pump(flowrate_levels = run_syrringe_pump.Level(0,0,0), url: str = "opc.tcp://127.0.0.1:36090/freeopcua/server/"):
    """Configuration of the Syrris Asia pumps according to set flowrates."""
    # ----------- Defining url of OPCUA and flowRate levels -----------
    url = url # OPC_UA_SERVER_URL 
    # # -----------------------------------------------------------------
    logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
        
        if  flowrate_levels.flowrate_A == 0: 
            await pump13A._call_method(pump13A.METHOD_STOP)
            logger.info(f"{pump13A.name}: Pump stopped.")
        else: 
            await pump13A.set_flowrate_to(flowrate_levels.flowrate_A)

        if flowrate_levels.flowrate_B == 0: 
            await pump13B._call_method(pump13B.METHOD_STOP)
            logger.info(f"{pump13B.name}: Pump stopped.")
        else:
            await pump13B.set_flowrate_to(flowrate_levels.flowrate_B)
        await asyncio.sleep(flowrate_levels.time_in_seconds)

    
async def deactivate_pump(url: str = "opc.tcp://127.0.0.1:36090/freeopcua/server/") -> None:
    """Deactivation of both pumps."""
    url = url # OPC_UA_SERVER_URL
    # -----------------------------------------------------------------
    logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")
        await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())


async def activate_pump(a: bool = False, b: bool = False, url: str = "opc.tcp://127.0.0.1:36090/freeopcua/server/") -> None:
    """Activation of the pumps.

    :param a: bool, pump A gets activated if True, else not.
    :param b: bool, pump B gets activated if True, else not.
    """
    url = url # OPC_UA_SERVER_URL 
    # -----------------------------------------------------------------
    logger.info(f"OPC-UA Client: Connecting to {url} ...")
    async with run_syrringe_pump.Client(url=url) as client:
        # ------ Here you can define and operate all your pumps -------
        pump13A = await run_syrringe_pump.Pump.create(client, "24196", "A")
        pump13B = await run_syrringe_pump.Pump.create(client, "24196", "B")

        if a==True and b==True:
            await asyncio.gather(pump13A.activate(), pump13B.activate())
        elif a==True:
            await asyncio.gather(pump13A.activate())
        elif b==True:
            await asyncio.gather(pump13B.activate())
        else:
            await asyncio.gather(pump13A.deactivate(), pump13B.deactivate())



def get_power_command(current='000.0', voltage='00.00') -> list:
    """Generates a proper formatted command string for the BKPrecission Power Source.

    :param current: String, Current porperly formatted with three leading digits and one digit after the comma: "000.0" 
    :param voltage: String, Voltage porperly formatted with two leading digits and two digits after the comma: "00.00" 
    :returns: List of properly formatted BKP commands.
    """
    command1=str('CURR '+f'{current}'+'\r')
    command2=str('VOLT '+f'{voltage}'+'\r')
    if current=='000.0' and voltage=='00.00':
        commands_list=['OUT OFF\r']
    else:
        commands_list=[command2,'SAVE\r',command1,'SAVE\r','OUT ON\r']
    return commands_list


async def set_power_supply(power_suppl, commands_list: list) -> bool:
    """Sets the BKPrecission Power Source.

    :param power_suppl: BKP instance for sending commands to.
    :param commands_list: List, properly formatted commands for the BKP.  
    :returns: True when finishing the action.
    """
    for i in range(len(commands_list)):
        eol='\r'
        message=commands_list[i].encode('ascii')
        power_suppl.write(message)
        reply=power_suppl.read_until(expected=eol)
        if reply:
            reply.decode('ascii')
            logger.info(f'command: {commands_list[i]}, reply: {reply}')
        else:
            logger.info(f'command: {commands_list[i]}, but no reply.')
        time.sleep(3)
    return True



def dim_load(gsioc_protocol_object, testing_active: bool = False):
    """Switches Direct Injection Module (DIM) to Load position. Queries the switching position for assuring success.

    :expects: Global variable TESTING_ACTIVE.
    :param gsioc_protocol_object: GSIOC Instance for commands to DIM.
    """
    gsioc_protocol_object.connect()
    time.sleep(5)
    gsioc_protocol_object.bCommand('VL')
    resp=gsioc_protocol_object.iCommand('X')
    while resp=='R':
        time.sleep(1)
        resp=gsioc_protocol_object.iCommand('X')
        pass
    if resp=='L':
        return True        
    else:
        if testing_active == True:
            return True
        else:
            error=gsioc_protocol_object.iCommand('e')
            logger.debug(f'the direct injection module returned the following error: {error}')
            return False


def dim_inject(gsioc_protocol_object, testing_active: bool = False):
    """Switches Direct Injection Module (DIM) to Inject position. Queries the switching position for assuring success.

    :expects: Global variable TESTING_ACTIVE.
    :param gsioc_protocol_object: GSIOC Instance for commands to DIM.
    """
    gsioc_protocol_object.connect()
    time.sleep(5)
    gsioc_protocol_object.bCommand('VI')
    resp=gsioc_protocol_object.iCommand('X')
    while resp=='R':
        time.sleep(1)
        resp=gsioc_protocol_object.iCommand('X')
        pass
    if resp=='I':
        return True
    else:
        if testing_active == True:
            return True
        else:
            error=gsioc_protocol_object.iCommand('e')
            logger.debug(f'the direct injection module returned the following error: {error}')
            return False
