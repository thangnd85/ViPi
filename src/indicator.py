#!/usr/bin/env python
try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
import time, os, re, apa102, threading, numpy, argparse, json
try: 
    import usb.core, usb.util
except:
    os.system('pip install pyusb >> /dev/null')
    import usb.core, usb.util                             
from gpiozero import LED
from termcolor import colored
try:
    import queue as Queue
except ImportError:
    import Queue as Queue
import yaml
from rpi_ws281x import PixelStrip, Color
ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))
CURENT_PATH =  os.path.realpath(os.path.join(__file__, '..',))
#1: Config_Mic
# R2M: ReSpeaker 2-Mics
# R4M: ReSpeaker 4-Mics
# RUM: ReSpeaker Mic Array v2.0
# USB: Usb soudcard

#2: Config_Led:
# R2M: 3 Led ReSpeaker 2-Mics
# R4M: 12 Led ReSpeaker 4-Mics
# RUM: 12 led ReSpeaker Mic Array v2.0
# WS2: Led WS28x hoặc SK68XX

#3: Config_Audio out:
# RPI_H: Headphone 3.5 Raspberry
# R2M_H: Headphone ReSpeaker 2-Mics
# R2M_J: SPEAK ReSpeaker 2-Mics (cổng JST)
# RUM_H: Headphone 3.5 ReSpeaker Mic Array v2.0


#ctr_led
#ctr_led

with open('{}/config.json'.format(CURENT_PATH),'r', encoding='utf8') as conf:
    configuration = json.load(conf)
try:
    led_number=int(configuration['led_setup']['pixels'])
except:
    led_number=12
#1: Config_Mic

if configuration['mic_setup']['type']=="USB":
    mic_setup=''
elif configuration['mic_setup']['type']=="R4M":
    mic_setup='R4M'
elif configuration['mic_setup']['type']=="R2M":
    mic_setup='R2M'
elif configuration['mic_setup']['type']=="RUM":
    mic_setup='RUM'
elif configuration['mic_setup']['type']=="HAT":
    mic_setup='HAT'
else:
    mic_setup=''

    

# if configuration['IR']['IR_Control']=='Enabled':
    # ircontrol=True
# else:
    # ircontrol=False

# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)

# #Indicators
# aiyindicator=configuration['Gpios']['AIY_indicator'][0]
# listeningindicator=configuration['Gpios']['assistant_indicators'][0]
# speakingindicator=configuration['Gpios']['assistant_indicators'][1]

# #Stopbutton
# stoppushbutton=configuration['Gpios']['stopbutton_music_AIY_pushbutton'][0]
# GPIO.setup(stoppushbutton, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)

# #IR receiver
# if ircontrol:
    # irreceiver=configuration['Gpios']['ir'][0]
    # GPIO.setup(irreceiver, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# else:
    # irreceiver=None


class GoogleHomeLedPattern(object):
    def __init__(self, show=None):
        self.basis = numpy.array([0] * 4 * 12)
        self.basis[0 * 4 + 1] = 2
        self.basis[3 * 4 + 1] = 1
        self.basis[3 * 4 + 2] = 1
        self.basis[6 * 4 + 2] = 2
        self.basis[9 * 4 + 3] = 2
        self.pixels = self.basis * 24

        if not show or not callable(show):
            def dummy(data):
                pass
            show = dummy
        self.show = show
        self.stop = False

    def wakeup(self, direction=0):
        position = int((direction + 15) / 30) % 12

        basis = numpy.roll(self.basis, position * 4)
        for i in range(1, 25):
            pixels = basis * i
            self.show(pixels)
            time.sleep(0.005)
        pixels =  numpy.roll(pixels, 4)
        self.show(pixels)
        time.sleep(0.1)
        for i in range(2):
            new_pixels = numpy.roll(pixels, 4)
            self.show(new_pixels * 0.5 + pixels)
            pixels = new_pixels
            time.sleep(0.1)
        self.show(pixels)
        self.pixels = pixels

    def listen(self):
        pixels = self.pixels
        for i in range(1, 25):
            self.show(pixels * i / 24)
            time.sleep(0.01)

    def think(self):
        pixels = self.pixels
        while not self.stop:
            pixels = numpy.roll(pixels, 4)
            self.show(pixels)
            time.sleep(0.2)
        t = 0.1
        for i in range(0, 5):
            pixels = numpy.roll(pixels, 4)
            self.show(pixels * (4 - i) / 4)
            time.sleep(t)
            t /= 2
        self.pixels = pixels

    def speak(self):
        pixels = self.pixels
        step = 1
        brightness = 5
        while not self.stop:
            self.show(pixels * brightness / 24)
            time.sleep(0.02)
            if brightness <= 5:
                step = 1
                time.sleep(0.4)
            elif brightness >= 24:
                step = -1
                time.sleep(0.4)
            brightness += step

    def off(self):
        self.show([0] * 4 * 12)

    def red(self):
        self.show([0,1,0,0] * 12)
        
class AlexaLedPattern(object):
    def __init__(self, show=None, number=12):
        self.pixels_number = number
        self.pixels = [0] * 4 * number

        if not show or not callable(show):
            def dummy(data):
                pass
            show = dummy

        self.show = show
        self.stop = False

    def wakeup(self, direction=0):
        position = int((direction + 15) / (360 / self.pixels_number)) % self.pixels_number

        pixels = [0, 0, 0, 24] * self.pixels_number
        pixels[position * 4 + 2] = 48

        self.show(pixels)

    def listen(self):
        pixels = [0, 0, 0, 24] * self.pixels_number

        self.show(pixels)

    def think(self):
        pixels  = [0, 0, 12, 12, 0, 0, 0, 24] * self.pixels_number

        while not self.stop:
            self.show(pixels)
            time.sleep(0.2)
            pixels = pixels[-4:] + pixels[:-4]

    def speak(self):
        step = 1
        position = 12
        while not self.stop:
            pixels  = [0, 0, position, 24 - position] * self.pixels_number
            self.show(pixels)
            time.sleep(0.01)
            if position <= 0:
                step = 1
                time.sleep(0.4)
            elif position >= 12:
                step = -1
                time.sleep(0.4)

            position += step

    def off(self):
        self.show([0] * 4 * 12)

class Pixels4mic:
    PIXELS_N = 12
    def __init__(self, pattern=AlexaLedPattern):
        self.pattern = pattern(show=self.show)
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        self.power = LED(5)
        self.power.on()
        self.queue = Queue.Queue()
        self.t4 = threading.Thread(target=self._run)
        self.t4.daemon = True
        self.t4.start()
        self.last_direction = None

    def wakeup(self, direction=0):
        self.last_direction = direction
        def f():
            self.pattern.wakeup(direction)
        self.put(f)

    def listen(self):
        if self.last_direction:
            def f():
                self.pattern.wakeup(self.last_direction)
            self.put(f)
        else:
            self.put(self.pattern.listen)

    def think(self):
        self.put(self.pattern.think)

    def speak(self):
        self.put(self.pattern.speak)

    def off(self):
        self.put(self.pattern.off)

    def put(self, func):
        self.pattern.stop = True
        self.queue.put(func)

    def _run(self):
        while True:
            func = self.queue.get()
            self.pattern.stop = False
            func()

    def show(self, data):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(data[4*i + 1]), int(data[4*i + 2]), int(data[4*i + 3]))
        self.dev.show()

    def mute(self):
        self.put(self.pattern.red)

class Pixels2mic:
    PIXELS_N = 3
    def __init__(self):
        self.basis = [0] * 3 * self.PIXELS_N
        self.basis[0] = 1
        self.basis[4] = 1
        self.basis[8] = 2
        self.colors = [0] * 3 * self.PIXELS_N
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        self.next = threading.Event()
        self.queue = Queue.Queue()
        self.t5 = threading.Thread(target=self._run)
        self.t5.daemon = True
        self.t5.start()


    def wakeup(self, direction=0):
        def f():
            self._wakeup(direction)
        self.next.set()
        self.queue.put(f)

    def listen(self):
        self.next.set()
        self.queue.put(self._listen)

    def think(self):
        self.next.set()
        self.queue.put(self._think)

    def speak(self):
        self.next.set()
        self.queue.put(self._speak)

    def off(self):
        self.next.set()
        self.queue.put(self._off)

    def _run(self):
        while True:
            func = self.queue.get()
            func()
        

    def _wakeup(self, direction=0):
        for i in range(1, 25):
            colors = [i * v for v in self.basis]
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _listen(self):
        for i in range(1, 25):
            colors = [i * v for v in self.basis]
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _think(self):
        colors = self.colors
        self.next.clear()
        while not self.next.is_set():
            colors = colors[3:] + colors[:3]
            self.write(colors)
            time.sleep(0.2)
        t = 0.1
        for i in range(0, 5):
            colors = colors[3:] + colors[:3]
            self.write([(v * (4 - i) / 4) for v in colors])
            time.sleep(t)
            t /= 2
        # time.sleep(0.5)
        self.colors = colors

    def _speak(self):
        colors = self.colors
        self.next.clear()
        while not self.next.is_set():
            for i in range(5, 25):
                self.write([(v * i / 24) for v in colors])
                time.sleep(0.01)
            time.sleep(0.3)
            for i in range(24, 4, -1):
                self.write([(v * i / 24) for v in colors])
                time.sleep(0.01)
            time.sleep(0.3)
        self._off()

    def _off(self):
        self.write([0] * 3 * self.PIXELS_N)

    def write(self, colors):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(colors[3*i]), int(colors[3*i + 1]), int(colors[3*i + 2]))
        self.dev.show()

    def mute(self):
        self.write([1,0,0] * self.PIXELS_N)

class PixelRing:
    TIMEOUT = 8000

    def __init__(self, dev):
        self.dev = dev

    def trace(self):
        self.write(0)

    def mono(self, color):
        self.write(1, [(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF, 0])

    def set_color(self, rgb=None, r=0, g=0, b=0):
        if rgb:
            self.mono(rgb)
        else:
            self.write(1, [r, g, b, 0])

    def off(self):
        self.mono(0)

    def wakeup(self,color,direction=None):
        if color == None:
            self.write(2)
        else:
            self.write(1, [(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF, 0])
    def listen(self):
        self.write(2)
    def speak(self):
        self.write(3)

    def think(self):
        self.write(4)

    wait = think

    def spin(self):
        self.write(5)

    def show(self, data):
        self.write(6, data)

    customize = show

    def set_brightness(self, brightness):
        self.write(0x20, [brightness])

    def set_color_palette(self, a, b):
        self.write(0x21, [(a >> 16) & 0xFF, (a >> 8) & 0xFF, a & 0xFF, 0, (b >> 16) & 0xFF, (b >> 8) & 0xFF, b & 0xFF, 0])

    def set_vad_led(self, state):
        self.write(0x22, [state])

    def set_volume(self, volume):
        self.write(0x23, [volume])

    def change_pattern(self, pattern=None):
        print('Not support to change pattern')

    def write(self, cmd, data=[0]):
        self.dev.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, cmd, 0x1C, data, self.TIMEOUT)

    def close(self):
        """
        close the interface
        """
        usb.util.dispose_resources(self.dev)
#W2812
class ws2812:
    PIXELS_N = 3
    LED_COUNT = led_number       # Number of LED pixels.
    #LED_PIN = 12         # GPIO pin connected to the pixels (18 uses PWM!).
    LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10          # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 250  # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    
    def __init__(self):
        self.basis = [0] * 3 * self.PIXELS_N
        self.basis[0] = 2
        self.basis[3] = 1
        self.basis[4] = 1
        self.basis[7] = 2
        self.colors = [0] * 3 * self.PIXELS_N
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        self.next = threading.Event()
        self.queue = Queue.Queue()
        self.ws2 = threading.Thread(target=self._run)
        self.ws2.daemon = True
        self.ws2.start()
        self.strip.begin()
##

    def colorWipe(self,strip, color, wait_ms=5):
        """Wipe color across display a pixel at a time."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 2000.0)
    def theaterChase(self,strip, color, wait_ms=5, iterations=1):
        """Movie theater light style chaser animation."""
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.strip.numPixels(), 3):
                    strip.setPixelColor(i + q, color)
                self.strip.show()
                time.sleep(wait_ms / 2000.0)
                for i in range(0, strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)
    def wheel(self,pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)
    def rainbow(self,strip, wait_ms=5, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 2000.0)
    def rainbowCycle(self,strip, wait_ms=5, iterations=1):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel(
                    (int(i * 256 / strip.numPixels()) + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 2000.0)
    def theaterChaseRainbow(self,strip, wait_ms=5):
        """Rainbow movie theater light style chaser animation."""
        for j in range(256):
            for q in range(1):
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, self.wheel((i + j) % 255))
                self.strip.show()
                time.sleep(wait_ms / 2500.0)
                for i in range(0, strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)

##

    def wakeup(self):
        self.queue.put(self._off_apa)   
        self.next.set()
        self.queue.put(self._wakeup)
                
        
    def listen(self):
        self.queue.put(self._off_apa)
        self.next.set()
        self.queue.put(self._listen)
        
    def think(self):
        self.queue.put(self._off_apa)
        self.next.set()
        self.queue.put(self._think)
        self.queue.put(self._off_apa)
    def speak(self):
        self.queue.put(self._off_apa)
        self.next.set()
        self.queue.put(self._speak)
        self.queue.put(self._off_apa)
    def off(self):
        self.queue.put(self._off_apa)
        self.next.set()
        self.queue.put(self._off)
        self.queue.put(self._off_apa)
    def mute(self):
        self.next.set()
        self.queue.put(self._mute)
    def _run(self):
        while True:
            func = self.queue.get()
            func()
          
    def _wakeup(self,direction=0):
        self.write([0] * 3 * self.PIXELS_N)
        self.colorWipe(self.strip, Color(0, 255, 0))
        self.colorWipe(self.strip, Color(127, 0, 0))
        self.colorWipe(self.strip, Color(0, 0, 0))
        self.write([0] * 3 * self.PIXELS_N)
    def _listen(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.rainbow(self.strip)
        self.colorWipe(self.strip, Color(0, 0, 0))
        self.write([0] * 3 * self.PIXELS_N)
    def _think(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.theaterChaseRainbow(self.strip)
        self.colorWipe(self.strip, Color(0, 127, 255))         
        self.colorWipe(self.strip, Color(0, 0, 0))
        self.write([0] * 3 * self.PIXELS_N)                
    def _speak(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.theaterChaseRainbow(self.strip)
        self.write([0] * 3 * self.PIXELS_N)
        self.colorWipe(self.strip, Color(0, 0, 0))
    def _off(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.colorWipe(self.strip, Color(0, 0, 0))
        self.write([0] * 3 * self.PIXELS_N)
    def _mute(self):
        self.colorWipe(self.strip, Color(255, 0, 0))
    def _off_apa(self):
        self.write([0] * 3 * self.PIXELS_N)
    def write(self, colors):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(colors[3*i]), int(colors[3*i + 1]), int(colors[3*i + 2]))
        self.dev.show()
    def _volume(self, volume):
        LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
        LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA = 10          # DMA channel to use for generating signal (try 10)
        LED_BRIGHTNESS = 250  # Set to 0 for darkest and 255 for brightest
        LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
        LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
        LED_COUNT_1=round(volume/(100/led_number))
        st = PixelStrip(LED_COUNT_1, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        st.begin()    
        for i in range(st.numPixels()):
            st.setPixelColor(i, Color(0, 0, 255))
            st.show()
            time.sleep(0.05)
## end ws2812
def find(vid=0x2886, pid=0x0018):
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if not dev:
        return
    return PixelRing(dev)
class gen():
    def wakeup(self):
        pass

    def listen(self):
        pass
        
    def think(self):
        pass
    def speak(self):
        pass
    def off(self):
        pass
    def mute(self):
        pass
    def _volume(self, volume):
        pass
## end gen

    # find =find()
#2: Config_Led:
led_setup=''
if configuration['led_setup']['type']=="USB":
    led_setup=''
if configuration['led_setup']['type']=="R4M":
    led_setup='R4M'
    pixels = Pixels4mic()
if configuration['led_setup']['type']=="R2M":
    led_setup='R2M'
    pixels=Pixels2mic()
elif configuration['led_setup']['type']=="RUM":
    led_setup='RUM'
    pixels = find()
elif configuration['led_setup']['type']=="WS2":
    led_setup='WS2'
    pixels = ws2812()
else:
    led_setup=''
    pixels = gen() 

#3: Config_Audio out:
vol_setup=''
if configuration['vol_setup']['type']=="RPI_H":
    vol_setup='RPI_H'
if configuration['vol_setup']['type']=="R2M_H":
    vol_setup='R2M_H'
if configuration['vol_setup']['type']=="R2M_J":
    vol_setup='R2M_J'
if configuration['vol_setup']['type']=="RUM_H":
    vol_setup='RUM_H'
if configuration['vol_setup']['type']=="HAT":
    vol_setup='HAT'
else:
    ctr_vol='bạn chưa chọn cổng xuất âm thanh'
   
    
print('Mic setup: '+ mic_setup+ ', Led setup: '+ led_setup+ ', Pixels_led: '+ str(led_number))


    
def off_led_ring():
    off_led_ring=find()
    off_led_ring.off()

def ctr_led(state):
    state=state.lower()
    if state=='wakeup':
        if led_setup=='RUM':
        #tra bảng màu tại: https://www.usbhddboot.xyz/2019/10/hex-code.html
            pixels.wakeup(0xFF0000)
        else:
            pixels.wakeup()
    elif state=='think':
        pixels.think()                
    elif state=='listen':
        pixels.listen()
    elif state=='speak'  or 'speaking':
        pixels.speak()
    elif (state=='on' or state=='mute'):
        if (led_setup=='RUM'):
            pixels.mono(0xFF6600)#màu cam:
        else:
            pixels.mute()
    elif (state=='off' or state=='unmute'):
        pixels.off()
    else:
        pass
def ctr_vol_led(volume):
    if led_setup=='WS2':
        pixels._volume(volume)
        time.sleep(1.0)
        pixels.off()       
    elif led_setup=='RUM':
        if volume<9:
            pixels.set_volume(0)
        else:
            pixels.set_volume(round(volume/10)-1)
    else:
        pass

#########  vol_level  #########
def off_led_ring():
    off_led_ring=find()
    off_led_ring.off()

