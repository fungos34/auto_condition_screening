import pyaudio
import numpy as np
import time

def get_noice(duration,frequency):
    # Set the sample rate and duration of the sound
    sample_rate = 44100
    #duration = 1
    # Generate a sine wave with frequency 440 Hz
    #frequency = 400.0
    samples = np.sin(2 * np.pi * np.arange(sample_rate * duration) * frequency / sample_rate)
    # Create an instance of the PyAudio class
    p = pyaudio.PyAudio()
    # Open a stream to play the sound
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
    # Play the sound
    stream.write(samples.astype(np.float32).tobytes())
    # Close the stream and PyAudio instance
    stream.stop_stream()
    stream.close()
    p.terminate()
    # time.sleep(0.15)

def get_sound1():
    durations=[0.1,0.1,0.1]#[0.051,0.051,0.051,0.051,0.8]
    frequencies=[432,741,432]#[400,444,488,500,550]
    for i in range(len(durations)):
        get_noice(durations[i],frequencies[i])

def get_sound2():
    durations=[0.1,0.1,0.1]#[0.051,0.051,0.051,0.051,0.8]
    frequencies=[741,432,741]#[400,444,488,500,550]
    for i in range(len(durations)):
        get_noice(durations[i],frequencies[i])

def get_sound3():
    get_noice(0.5,900)

if __name__=='__main__':
    get_sound1()
    time.sleep(1)
    get_sound2()
    time.sleep(1)
    get_sound3()