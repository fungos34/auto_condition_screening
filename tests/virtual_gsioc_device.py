import asyncio
import serial_asyncio
import sys
import binascii
from loguru import logger
import os

# functions/classes needed to be exported
__all__ = ['VirtualGSIOCDevice']

class VirtualGSIOCDevice():
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
    def __init__(self, virtual_port: str = 'COM13', baudrate: int = 19200) -> None: #response_register: dict = {},
        # self.serial_port=serial.Serial(port = echo_port, baudrate = 19200, timeout=5)#,8,"N",1,0.1)   
        self.virtual_port = virtual_port
        self.baudrate = baudrate
        self.device_status1 = 'no status set'
        self.device_error_status = "'0':'No Error'"
        self.available_gsioc_devices = {
                                        int(33 + 128).to_bytes(1,'big'): 

                                        {   #bytes.fromhex('FF') : b'',
                                            int(33 + 128).to_bytes(1,'big') : int(33 + 128).to_bytes(1,'big'),
                                            b'%' : 'GX-241 II v2.0.2.5',
                                            b'\n': 'InitiateBufferedCommand',
                                            b'\r': 'TerminateBufferedCommand',  
                                            b'e': self.device_error_status
                                            }, 

                                        int(3 + 128).to_bytes(1,'big') : 

                                         {  #bytes.fromhex('FF') : b'',
                                            int(3 + 128).to_bytes(1,'big') : int(3 + 128).to_bytes(1,'big'),
                                            b'%' : 'GX D Inject v ',
                                            b'\n': 'InitiateBufferedCommand',
                                            b'\r': 'TerminateBufferedCommand',  
                                            'VL' : 'L', 
                                            'VI' : 'I',
                                            b'X' : self.device_status1, 
                                            b'e' : self.device_error_status,
                                            b'$' : '$'
                                            },

                                        int(11 + 128).to_bytes(1,'big') : 

                                        {
                                            int(11 + 128).to_bytes(1,'big') : int(11 + 128).to_bytes(1,'big'),
                                            b'%' : 'VERITY 4020',
                                            b'\n': 'InitiateBufferedCommand',
                                            b'\r': 'TerminateBufferedCommand',  
                                            b'p' : self.device_status1,
                                            b'P' : self.device_status1[0],
                                            'PN:225:4' : 'N:225',
                                            'PN:-225:4' : 'N:0',
                                            b'M' : 'EU'
                                        }
                                            }
        self.response_register = {bytes.fromhex('FF') : bytes(0)}
        self.command_buffer = []
        self.eol = b'\r'
        self.buffered_command_initiator = b'\n'
        self.buffered_command_terminator = b'\r'
        self.device_terminator = int(128).to_bytes(1,'big')
        
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamReader = None
        self.port_open = False

    async def _initialize_port(self):
        self._reader, self._writer = await serial_asyncio.open_serial_connection(url=self.virtual_port, baudrate=self.baudrate)
        self.port_open = True

    async def ignore(self):
        logger.info(f'Does not respond at all.')

    async def set_device_status(self):
        logger.critical(f'starts setting device status. the command buffer is: {self.command_buffer}')
        status = []
        print(f'status: {status}')
        for i in range(len(self.command_buffer)):
            if self.command_buffer[i] == b'\n' or self.command_buffer[i] == b'\r' or self.command_buffer[i] == b'\n\n':
                pass
            else:
                status.append(str(self.command_buffer[i].decode('ascii')))
        # status = [list().remove(self.command_buffer[i]) for i in range(len(self.command_buffer)) ] #if self.command_buffer[i] == b'\n'
        print(f'status: {status}')
        # status = [list().remove(self.command_buffer[i]) for i in range(len(self.command_buffer)) if self.command_buffer[i] == b'\r']
        status = ''.join(status)
        status.strip()
        print(f'status: {status}')
        print(f'response register is currently: {self.response_register}')
        status_new = self.response_register.get(status)
        if status_new == None:
            status_new = status
        logger.critical(f'device status will be set to: {status_new}')
        self.device_status1 = status_new
        self.response_register.update({b'X' : self.device_status1})
        self.response_register.update({b'P' : self.device_status1})
        print(f'response register updated: {self.response_register.get(b"X")}')

    async def respond(self, response):
        if type(response) == str:
            print(f'dealing with a string.')
            response_singated = binascii.a2b_qp(response) # str(response).encode('ascii') #+ self.eol
            for i in range(len(response)):
                response_singated = binascii.a2b_qp(response[i])
                self._writer.write(response_singated)
                logger.info(f'Responds with {response_singated}.')
                ready_signal = await self._reader.read(3)
                if ready_signal == bytes.fromhex('06'):
                    pass
                print(f'length of the response -1 is: {len(response)-1}, i is: {i}')
                if i == len(response)-1:
                    self._writer.write(self.device_terminator)
                    logger.info(f'Responds with {self.device_terminator}.')
        if type(response) == bytes:
            print(f'dealing with a byte, response: {response}')
            self._writer.write(response)

    async def eavesdropper(self):
        try:
            logger.info(f'{self.__class__.__name__} starts eavesdropping ... process ID: {os.getpid()}')
            future_ = self._reader.read(10)
            got_in = await asyncio.wait_for(future_, timeout=30) # future used for timeout
            if got_in:
                logger.info(f'received the following: {got_in}')
                return got_in
        except asyncio.TimeoutError:
            logger.info('nothing received before timeout.')
            pass

    async def collect_buffered_command(self,fragment):
        try:
            await self.respond(int(35).to_bytes(1,'big'))
            self.command_buffer.append(fragment)
            logger.info(f'command buffer: {self.command_buffer}')
            await self.respond(fragment)
            check = None
            while True:
                if self.response_register.get(check) == 'TerminateBufferedCommand':
                    # await self.respond(check[1:-1])
                    await self.set_device_status()
                    logger.info(f'buffered command terminated: {self.command_buffer}')
                    self.command_buffer = []
                    break
                else:
                    future_ = self._reader.read(10)
                    got_in = await asyncio.wait_for(future_, timeout=15) # future used for timeout
                    await self.respond(got_in)
                    self.command_buffer.append(got_in)
                    check = got_in
                    print(f'check is: {check}')
                    pass
        except Exception:
            self.command_buffer = []
            return self.command_buffer

    async def run_eavesdropper(self):
        while True:
            inbox = await self.eavesdropper()
            print(f'The inbox  - {inbox} - will be checked for a valid key.')
            print(f'gsioc device keys: {self.available_gsioc_devices.keys()}')
            print(f'response register keys: {self.response_register.keys()}')
            print(f'last letter is: {str(inbox)[-2]}')
            if str(inbox)[-2] == '%' and len(str(inbox)) > 6:
                inbox = bytes.fromhex((str(inbox)[4:-2])) # bytes(str(inbox)[:-2])
                print(f'inbox was modified to: {inbox}')
            if inbox in self.available_gsioc_devices.keys():
                print(f'A certain response register is selected: {self.available_gsioc_devices.get(inbox)}')
                self.response_register = self.available_gsioc_devices.get(inbox)
            if inbox in self.response_register.keys():
                valid_response = self.response_register.get(inbox)
                if valid_response == 'InitiateBufferedCommand':
                    #inbox=inbox[1:-1]
                    logger.info(f'buffered command initialised: {inbox}')
                    if inbox != b'':
                        print(f'inbox is not empty byte object: {inbox}')
                        # await self.respond(int(35).to_bytes(1,'big'))
                        #await self.respond(inbox)
                    await asyncio.sleep(0.2)
                    await self.collect_buffered_command(inbox)
                elif valid_response == b'':
                    # await self.ignore()
                    await self.respond(b'\x00\r')
                else:
                    print(f'current response register: {self.response_register}')
                    print(f'this segment is executed ... with {valid_response} of type {type(valid_response)}')
                    await self.respond(valid_response)
            else:
                logger.info(f'invalid key {inbox}')
                await self.respond(inbox)
                # print('just responded the inbox ...')
                # await self.ignore()


######### TESTING SECTION ##########

async def main(virtual):
    await virtual._initialize_port()
    logger.info(f'port {virtual.virtual_port} open: {virtual.port_open}')
    await virtual.run_eavesdropper()


if __name__ == '__main__':
    try:
        vrtl = VirtualGSIOCDevice()#valid_response_register)
        asyncio.run(main(vrtl))
    except KeyboardInterrupt:
        sys.exit(f'KeyboardInterrupt: virtual port {vrtl.virtual_port} was closed.')


"""
####### identify valid commands with ranges of values by safing its regular expression in a dict ########
import regex as re

valid_command_response = {
    'X([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?/([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?':'response something' # valid example command structure
}


command_strings_list = ['X123.27/923e12','X12/92',b'X0/890', '12/1231.2']

def check_command_list_validity():
    for j in range(len(command_strings_list)):
        command_string = command_strings_list[j]
        response = check_command_validity(command_string)
        print(f'Device Echos "{response}".')


def check_command_validity(command_string):
    # checks
    regexs = list(valid_command_response.keys())
    for i in range(len(regexs)):
        match = re.search(regexs[i], str(command_string))
        if match:
            response = valid_command_response.get(regexs[i])
            print('valid command')
            return response
        else:
            print('invalid command')
            return b''

if __name__ == '__main__':
    check_command_list_validity()
    """
