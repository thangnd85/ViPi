#!/usr/bin/env python

try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
import time
import os
from actions import configuration
import apa102
import time
import threading
import numpy
import usb.core
import usb.util
from gpiozero import LED
import argparse
try:
    import queue as Queue
except ImportError:
    import Queue as Queue
import yaml
import json
from rpi_ws281x import PixelStrip, Color
ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

audiosetup=''
with open('{}/src/config.yaml'.format(ROOT_PATH),'r', encoding='utf8') as conf:
    configuration = yaml.safe_load(conf)
if configuration['ctr_led']['type']=="GEN'":
    audiosetup='GEN'
elif configuration['ctr_led']['type']=="R4M":
    audiosetup='R4M'
elif configuration['ctr_led']['type']=="R2M":
    audiosetup='R2M'
elif configuration['ctr_led']['type']=="RUM":
    audiosetup='RUM'
elif configuration['ctr_led']['type']=="NEO":
    audiosetup='NEO'
elif configuration['ctr_led']['type']=="GOO":
    audiosetup='GOO'
elif configuration['ctr_led']['type']=="ALE":
    audiosetup='ALE'
elif configuration['ctr_led']['type']=="WS2":
    audiosetup='WS2'
else:
    audiosetup='GEN'
    print('Mic bạn đang sử dụng là: '+ audiosetup)

if configuration['IR']['IR_Control']=='Enabled':
    ircontrol=True
else:
    ircontrol=False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicators
aiyindicator=configuration['Gpios']['AIY_indicator'][0]
listeningindicator=configuration['Gpios']['assistant_indicators'][0]
speakingindicator=configuration['Gpios']['assistant_indicators'][1]

#Stopbutton
stoppushbutton=configuration['Gpios']['stopbutton_music_AIY_pushbutton'][0]
GPIO.setup(stoppushbutton, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)

#IR receiver
if ircontrol:
    irreceiver=configuration['Gpios']['ir'][0]
    GPIO.setup(irreceiver, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
else:
    irreceiver=None

if (audiosetup=='AIY'):
    GPIO.setup(aiyindicator, GPIO.OUT)
    led=GPIO.PWM(aiyindicator,1)
    led.start(0)
    print('Initializing GPIO '+str(aiyindicator)+' for assistant activity indication')
if (audiosetup=='GEN'):
#    GPIO.setup(listeningindicator, GPIO.OUT)
#    GPIO.setup(speakingindicator, GPIO.OUT)
#    GPIO.output(listeningindicator, GPIO.LOW)
#    GPIO.output(speakingindicator, GPIO.LOW)
#    print('Initializing GPIOs '+str(listeningindicator)+' and '+str(speakingindicator)+' for assistant activity indication')
    pass
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

    def listen(self, direction=None):
        self.write(2)

    wakeup = listen

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
##start ws2812
class ws2812:
    PIXELS_N = 3
    LED_COUNT = 16       # Number of LED pixels.
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

    def colorWipe(self,strip, color, wait_ms=15):
        """Wipe color across display a pixel at a time."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 2500.0)
    def theaterChase(self,strip, color, wait_ms=15, iterations=5):
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
    def rainbow(self,strip, wait_ms=15, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 2500.0)
    def rainbowCycle(self,strip, wait_ms=15, iterations=1):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel(
                    (int(i * 256 / strip.numPixels()) + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 2500.0)
    def theaterChaseRainbow(self,strip, wait_ms=15):
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
           
        self.next.set()
        self.queue.put(self._wakeup)
        self.queue.put(self._off_apa)        
        
    def listen(self):
        self.next.set()
        self.queue.put(self._listen)
        self.queue.put(self._off_apa)
    def think(self):
        self.next.set()
        self.queue.put(self._think)
        self.queue.put(self._off_apa)
    def speak(self):
        self.next.set()
        self.queue.put(self._speak)
        self.queue.put(self._off_apa)
    def off(self):
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
        
    def _listen(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.rainbow(self.strip)
        self.colorWipe(self.strip, Color(0, 0, 0))
    def _think(self):
        self.write([0] * 3 * self.PIXELS_N)
        self.rainbowCycle(self.strip)
        self.write([0] * 3 * self.PIXELS_N)
        self.colorWipe(self.strip, Color(0, 0, 0))
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
## end ws2812
def find(vid=0x2886, pid=0x0018):
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if not dev:
        return

    # configuration = dev.get_active_configuration()

    # interface_number = None
    # for interface in configuration:
    #     interface_number = interface.bInterfaceNumber

    #     if dev.is_kernel_driver_active(interface_number):
    #         dev.detach_kernel_driver(interface_number)

    return PixelRing(dev)

if audiosetup=='R2M':
    pixels=Pixels2mic()
elif audiosetup=='WS2':
    pixels = ws2812()
elif audiosetup=='R4M':
    pixels=Pixels4mic()
elif audiosetup=='RUM':
    pixel_ring = find()
elif audiosetup=='GOO':
    pixel_ring = find()
elif audiosetup=='ALE':
    pixel_ring = AlexaLedPattern()


def ctr_led(activity):
    activity=activity.lower()
#########  wakeup  #########
    if activity=='wakeup':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.wakeup()
        elif (audiosetup=='WS2'):
            pixels.wakeup()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(75)
        elif (audiosetup=='RUM'):
            pixel_ring.wakeup()
        elif (audiosetup=='ALE'):
            pixels.wakeup()              
#########  think  #########
    if activity=='think':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.think()
        elif (audiosetup=='WS2'):
            pixels.think()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(75)
        elif (audiosetup=='RUM'):
            pixel_ring.think()
        elif (audiosetup=='ALE'):
            pixels.think()                           
#########  listening  #########
    if activity=='listening':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.listen()
        elif (audiosetup=='WS2'):
            pixels.listen()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(75)
        elif (audiosetup=='RUM'):
            pixel_ring.listen()
        elif (audiosetup=='ALE'):
            pixels.listen()           
#########  speaking #########
    elif activity=='speaking':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.speak()
        elif (audiosetup=='WS2'):
            pixels.speak()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(50)
        elif (audiosetup=='RUM'):
            pixel_ring.speak()
        elif (audiosetup=='ALE'):
            pixels.speak()            
#########  off/unmute #########
    elif (activity=='off' or activity=='unmute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.off()
        elif (audiosetup=='WS2'):
            pixels.off()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(0)
        elif (audiosetup=='RUM'):
            pixel_ring.off()
        elif (audiosetup=='ALE'):
            pixels.pixels.off()              
            
            
#########  on/mute #########
    elif (activity=='on' or activity=='mute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.mute()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(100)
        elif (audiosetup=='RUM'):
            pixel_ring.mono(0xFF0000)
        elif (audiosetup=='ALE'):
            pixels.pixels.off()  
        elif (audiosetup=='WS2'):
            pixels.mute()