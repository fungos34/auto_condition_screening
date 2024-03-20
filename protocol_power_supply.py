import asyncio
from loguru import logger
import serial_asyncio
import sys
import time
import numpy as np

# functions/classes needed to be exported
__all__ = ()

###################################################################################
############# available commands for B+K PRECISION 1739 Revision 1.3 ##############
# 'OUT ON\r'              #activates power output
# 'VOLT 10.00\r'          #range 00.00 - 30.00
# 'CURR 100.0\r'          #range 000.0 - 999.9
# 'VOLT?\r'               #queries the voltage in (V) - the same value as at the display
# 'VOLT?\rCURR?\rSTAT?\r' #use multiple commands to query different settings at the same time
# 'CURR?\r'               #queries the current in (mA) - the same value as at the display
# 'STAT?\r'               #queries the mode: either constant voltage (CV) or constant current (CC)
# 'IDN?\r'                #queries the identity number of the device
# 'SAVE\r'                #sets the parameters 3 sec after the last command
# 'OUT OFF\r'             #deactivates power output
###################################################################################
####### BK Precision error responses via RS232 connection and their meaning #######

# please note: other error messages can be displayed on the voltage display: 
# Er xx, where xx is a number: Self-Test Errors, Calibration Errors(zero/full voltage/current calibration errors)

error_responses={
    "Communication Error\r": ": RS232 framing, parity, or overrun error",
    "Syntax Error\r": ": invalid syntax was found in the command string",
    "Out of range\r": ": a numeric parameter value is outside the valid range for the command"
    }
###################################################################################


class BKPrecisionRS232:
	f"""
	Protocol methods to communicate with B+K PRECISION 1739 Revion 1.3

	:param port_name: Name of the RS-232 port (COM** on Windows, ttyS** on Linux)
	:param device_idn: Name of the device, has to equal the response of the device. Default is B+K PRECISION 1739 Revion 1.3.
	:commands:
	* 'OUT ON\r'              	activates power output
	* 'VOLT 10.00\r' 			range 00.00 - 30.00
	* 'CURR 100.0\r'          	range 000.0 - 999.9
	* 'VOLT?\r'               	queries the voltage in (V) - the same value as at the display
	* 'VOLT?\rCURR?\rSTAT?\r'  	use multiple commands to query different settings at the same time
	* 'CURR?\r'               	queries the current in (mA) - the same value as at the display
	* 'STAT?\r'               	queries the mode: either constant voltage (CV) or constant current (CC)
	* 'IDN?\r'                	queries the identity number of the device
	* 'SAVE\r'                	sets the parameters 3 sec after the last command
	* 'OUT OFF\r'             	deactivates power output
	"""
	BAUDRATE = 9600

	def __init__(self, port_name: str, device_idn: str = 'B+K PRECISION 1739 Revision 1.3'):
		self.port_name = port_name
		self.device_idn = device_idn
		self.communication_initiator = b'\x13' # Communication initiation signal.
		self.communication_terminator = b'\x11' # Communication termination signal.
		self.sol = b'' # Start of command signal "start of line".
		self.eol = b'\r' # End of command signal "end of line".

		self._reader: asyncio.StreamReader = None  
		self._writer: asyncio.StreamWriter = None  

		self.error_responses = {
		"Communication Error\r": ": RS232 framing, parity, or overrun error",
		"Syntax Error\r": ": invalid syntax was found in the command string",
		"Out Of Range\r": ": a numeric parameter value is outside the valid range for the command"
		}
		self.monitoring = True

	async def initialize_connection(self):
		future = serial_asyncio.open_serial_connection(url=self.port_name, baudrate=self.BAUDRATE)
		self._reader, self._writer = await asyncio.wait_for(future, timeout=3)
		if await self.verify_connected():
			logger.info(f'Initialisation successfull, connected to {self.device_idn}')
			return 'Initialisation successfull.'
		else:
			logger.critical(f'Connected to wrong device: {self.send_command("IDN?")}')
			return 'Initialisation failed.'

	async def close_port(self):
		self._writer.close() 

	async def send_encoded_command(self, encoded_command) -> None:
		"""Sends a command. Does not wait for a response."""
		self._writer.write(encoded_command)

	async def receive_one_byte(self) -> bytes:
		"""Receives one byte at a time from the port. Does not send anything."""
		received = await self._reader.read(1)
		return received

	async def verify_connected(self):
		idn = await self.send_command('IDN?') # valid command for "B+K PRECISION 1739 Revision 1.3". Expected to get the IDN back.
		if idn == self.device_idn:
			logger.info(f'Device verified successfully as {idn}')
			return True
		else:
			logger.critical(f'Connected to wrong device: {idn}. expected: {self.device_idn}')
			return False

	async def verify_device_active(self):
		status = await anext(await self.send_commands('STAT?'))
		if status in ['OFF','CC','CV']:
			logger.info(f'Device active.')
			return True
		else:
			logger.info(f'Device inactive.')
			return False

	def encode_command(self, uncoded_command: str, _encoding: str = 'ascii') -> bytes:
		command_encoded =self.sol + bytes(uncoded_command.encode(encoding=_encoding)) + self.eol
		return command_encoded

	async def collect_response(self) -> bytearray:
		response_bytes = bytearray()
		while True:
			response_byte = await self.receive_one_byte()
			if response_byte == self.communication_initiator:
				response_bytes.extend(response_byte)
				while True:
					body_response_byte = await self.receive_one_byte()
					if body_response_byte == bytes(self.communication_terminator):
						response_bytes.extend(body_response_byte)
						break
					else:
						response_bytes.extend(body_response_byte)
				return response_bytes
			else:
				logger.debug(f'Received invalid response: {response_byte}. Expected: {self.communication_initiator}')
				await self.verify_device_active()
				continue
	
	def format_response(self, response: bytearray) -> str:
		stripped_response = response.replace(self.sol,b'')
		stripped_response = stripped_response.replace(self.eol,b'')
		stripped_response = stripped_response.replace(self.communication_initiator,b'')
		stripped_response = stripped_response.replace(self.communication_terminator,b'')
		stripped_response = stripped_response.decode('ascii')
		return stripped_response

	def verify_response(self, initial_command: str, formatted_response: str) -> bool:
		if '?' not in initial_command:
			if formatted_response == '':
				return True
			elif formatted_response + '\r' in list(self.error_responses.keys()):
				return True 
			else:
				return False
		else:
			if formatted_response != '':
				return True
			else:
				return False

	def interpret_response(self, single_command: str, verified_response: str) -> str:
		modified_verified_response = verified_response + '\r'
		if modified_verified_response in self.error_responses.keys():
			logger.critical(f'The following error occured: {verified_response},\ninterpretation: {self.error_responses.get(modified_verified_response)}')
			return self.error_responses.get(verified_response)
		elif verified_response == '':
			return f'Device successfully set: {single_command}'
		elif verified_response != '':
			return f'Device value is: {verified_response}'

	async def send_command(self,single_command: str) -> str:
		await self.send_encoded_command(encoded_command=self.encode_command(uncoded_command=single_command))
		resp = self.format_response(await self.collect_response())
		if self.verify_response(initial_command=single_command,formatted_response=resp):
			return resp

	async def send_commands(self,*args: str):
		for i in [*args]:
			yield await self.send_command(i)
			
	async def start_monitoring(self, time_interval: float|int = 0.):
		t1 = time.time()
		logger.info(f'Start monitoring.')
		while self.monitoring:
			t3 = time.time()
			gen = self.send_commands('CURR?','VOLT?','STAT?','IDN?',)
			resp1 = await anext(gen)
			resp2 = await anext(gen)
			resp3 = await anext(gen)
			resp4 = await anext(gen)
			t2 = time.time()
			logger.info(f"{resp1,resp2,resp3,resp4}, time: {round(t2-t1,1)}")
			await asyncio.sleep(time_interval-(t2-t3))

	async def stop_monitoring(self, delay: float|int = 0.):
		await asyncio.sleep(delay)
		self.monitoring = False
		logger.info(f'Stop monitoring after {delay} (sec).')

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
                print(f'value "{n}" out of range: {RANGE_CURRENT}')
            pass
        except TypeError:
            currents_out.append(np.nan)
            print(f'value "{n}" is not a number')
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
                print(f'value "{n}" out of range: {RANGE_VOLTAGE}')
            pass
        except TypeError:
            voltages_out.append(np.nan)
            print(f'value "{n}" is not a number')
            pass
    return  voltages_out

async def bkp_test_communication():
	global bkp
	bkp = BKPrecisionRS232('COM4')
	await bkp.initialize_connection()
	i = 0
	while True:
		i += 1
		if i <= 11:
			print(await bkp.send_command('CURR 00'+str(i)+'.'+str(i)))
			# print('CURR 00'+str(i)+'.'+str(i))
			print(await bkp.send_command('ABCD'))
			print(await bkp.send_command('CURR?'))
			resp = await bkp.send_command('VOLT 0'+str(i)+'.0'+str(i))
			print(bkp.interpret_response('VOLT 0'+str(i)+'.0'+str(i), resp))
			resp2 = await bkp.send_command('VOLT?')
			print(bkp.interpret_response('VOLT?', resp2 ))
			print(bkp.interpret_response('VOLT 40.00', await bkp.send_command('VOLT 40.00')))
			await asyncio.sleep(0.5)
		else:
			await bkp.close_port()
			break

async def main():
	global bkp
	bkp = BKPrecisionRS232('COM4')
	await bkp.initialize_connection()
	await asyncio.gather(bkp.start_monitoring(time_interval=0.5), bkp.stop_monitoring(delay=10))
	await bkp.close_port()


if __name__ == '__main__':
	asyncio.run(main(bkp))