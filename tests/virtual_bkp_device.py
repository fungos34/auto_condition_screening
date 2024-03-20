import asyncio
import serial_asyncio
import sys
import binascii
from loguru import logger
import os
import regex as re

# functions/classes needed to be exported
__all__ = ['VirtualBKPDevice']

class VirtualBKPDevice():
    """
    This Virtual Device (VD) simulates the asynchronous response behaviour via RS232.
    External Software Requirements:
        * Virtual Port of type "Connnector".
            For operation on windows it's recommended to use (VSPR)
            'Virtual Serial Ports Emulator (x32) 1.2.6.788'
    
    This class is able to emulate 'Gilson' equipment with GSIOC communication behaviour (buffered, immediate).

    :param response_register: VD responses according to this register.
    :param virtual_port: Name of the virtual port.
    :param baudrate: baudrate of the virtual port.
    """
    def __init__(self, virtual_port: str = 'COM14', baudrate: int = 19200) -> None: 
        self.virtual_port = virtual_port
        self.baudrate = baudrate
        self.voltage = '00.00V'
        self.current = '000.0mA'
        self.status = 'OFF'
        self.update_response_register()
        self.command_buffer = []
        self.sol = b''
        self.eol = b'\r'
        self.device_initiator = b'\x13'
        self.device_terminator = b'\x11'
        
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamReader = None
        self.port_open = False

    async def _initialize_port(self):
        self._reader, self._writer = await serial_asyncio.open_serial_connection(url=self.virtual_port, baudrate=self.baudrate)
        self.port_open = True

    async def ignore(self):
        logger.info(f'Does not respond at all.')

    def update_response_register(self):
        self.response_register = {    
            b'SAVE\r' : '',
            b'VOLT?\r' : f'{self.voltage}\r',
            b'CURR?\r': f'{self.current}\r',
            b'STAT?\r': f'{self.status}\r',  
            b'IDN?\r': 'B+K PRECISION 1739 Revision 1.3\r',
            # b'OUT ON\r' : '',
            # b'OUT OFF\r' : '',
            } 

    async def update_voltage(self, state):
        print(f'updating voltage state to {state}')
        self.voltage = state
        self.update_response_register()

    async def update_current(self, state):
        print(f'updating current state to {state}')
        self.current = state
        self.update_response_register()

    async def update_status(self, state):
        print(f'updating status to {state}')
        self.status = state
        self.update_response_register()

    async def respond(self, response):
        if type(response) == str and response == '':
            print(f'response is an empty string.')
            self._writer.write(self.device_initiator)
            logger.info(f'Responds with {self.device_initiator}.')
            self._writer.write(self.device_terminator)
            logger.info(f'Responds with {self.device_terminator}.')
        elif type(response) == str:
            print(f'response was a string.')
            response_singated = binascii.a2b_qp(response) # str(response).encode('ascii') #+ self.eol
            self._writer.write(self.device_initiator)
            logger.info(f'Responds with {self.device_initiator}.')
            for i in range(len(response)):
                response_singated = binascii.a2b_qp(response[i])
                self._writer.write(response_singated)
                logger.info(f'Responds with {response_singated}.')
                if i == len(response)-1:
                    self._writer.write(self.device_terminator)
                    logger.info(f'Responds with {self.device_terminator}.')
        if type(response) == bytes:
            print(f'response was a byte: {response}')
            self._writer.write(response)

    async def eavesdropper(self):
        try:
            logger.info(f'{self.__class__.__name__} starts eavesdropping ... process ID: {os.getpid()}')
            future_ = self._reader.read(15)
            got_in = await asyncio.wait_for(future_, timeout=30) # future used for timeout
            if got_in:
                logger.info(f'received the following: {got_in}')
                return got_in
        except asyncio.TimeoutError:
            logger.info('nothing received before timeout.')
            pass

    async def run_eavesdropper(self):
        while True:
            inbox = await self.eavesdropper()
            print(inbox)
            if inbox in self.response_register.keys():
                valid_response = self.response_register.get(inbox)
                if valid_response == '':
                   await self.respond('')
                elif valid_response == 'ignore':
                    await self.ignore()
                else:
                    # print(f'current response register: {self.response_register}')
                    # print(f'this segment is executed ... with {valid_response} of type {type(valid_response)}')
                    await self.respond(valid_response)
            elif inbox != None:
                print('1')
                print(inbox.decode('ascii').strip())
                match_volt_command = re.search('^VOLT (\d{2})\.(\d{2})$',inbox.decode('ascii').strip())
                print('2')
                match_curr_command = re.search('^CURR (\d{3})\.(\d{1})$',inbox.decode('ascii').strip())
                print('2.1')
                match_output_command = re.search('^OUT (O(N|(FF)))$',inbox.decode('ascii').strip())
                if match_volt_command:
                    print('3')
                    matches = match_volt_command.groups()
                    voltage = float(matches[0])+(float(matches[1])/100)
                    if 30. >= voltage >= 0.:
                        print('5')
                        await self.update_voltage(inbox.decode('ascii').strip().replace('VOLT ','') + 'V')
                        # self.voltage = inbox.decode('ascii').strip().replace('VOLT ','') + 'V'
                        await self.respond('')
                    else:
                        await self.respond('Out Of Range\r')
                elif match_curr_command:
                    print('4')
                    matches = match_curr_command.groups()
                    current = float(matches[0])+(float(matches[1])/10)
                    if 999.9 >= current >= 0.:
                        print('6')
                        await self.update_current(inbox.decode('ascii').strip().replace('CURR ','') + 'mA')
                        # self.current = inbox.decode('ascii').strip().replace('CURR ','') + 'mA'
                        await self.respond('')
                    else:
                        await self.respond('Out Of Range\r')
                elif match_output_command:
                    print('7')
                    matches = match_output_command.groups()
                    output = matches[0]
                    await self.update_status(output)#inbox.decode('ascii').strip().replace('OUT ',''))
                    await self.respond('')
                else:
                    logger.info(f'invalid key {inbox}')
                    await self.respond('Syntax Error\r')
                # print('just responded the inbox ...')
                # await self.ignore()

####### TESTING SECTION #########

async def main(virtual):
    await virtual._initialize_port()
    logger.info(f'port {virtual.virtual_port} open: {virtual.port_open}')
    await virtual.respond('')
    await virtual.run_eavesdropper()


if __name__ == '__main__':
    try:
        vrtl = VirtualBKPDevice()#valid_response_register)
        asyncio.run(main(vrtl))
    except KeyboardInterrupt:
        sys.exit(f'KeyboardInterrupt: virtual port {vrtl.virtual_port} was closed.')



