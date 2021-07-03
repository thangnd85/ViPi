#!/usr/bin/env python

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ViPi_0.2_13_04_2014_Thay đổi trình phát nhạc Youtube
"""Sample that implements a gRPC client for the Google Assistant API."""
print('[ViPi_0.2] + [KHỞI ĐỘNG CHƯƠNG TRÌNH]')

import concurrent.futures
import json
import logging
import os
import os.path
import pathlib2 as pathlib
import sys
import time
import uuid
try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
  
import argparse
import subprocess
import click
import grpc
import psutil
import logging
import re
import requests
import random
from actions import say
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
from actions import app_music
from actions import app_music_auto
from actions import stop
from actions import radio
from actions import feed
from actions import command_read_story
from actions import chromecast_play_video
from actions import chromecast_control
from actions import vlcplayer
from actions import configuration
from actions import custom_action_keyword
from actions import app_custom_weather
import signal
from actions import command_lunar_calendar
from news import app_news_radio
import pvporcupine
import pyaudio
import soundfile
import struct
from termcolor import colored
from threading import Thread
if GPIO!=None:
    from indicator import ctr_led
    ctr_led('off')
    ctr_led('speaking')                                        
    from indicator import stoppushbutton
    GPIOcontrol=True
else:
    GPIOcontrol=False
from actions import gender

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        audio_helpers,
        browser_helpers,
        device_helpers
    )
except (SystemError, ImportError):
    import assistant_helpers
    import audio_helpers
    import browser_helpers
    import device_helpers

# logging.basicConfig(filename='/tmp/GassistPi.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger=logging.getLogger(__name__)


ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

if GPIOcontrol:
    #GPIO Declarations
#    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    pushbuttontrigger=configuration['Gpios']['pushbutton_trigger'][0]
    GPIO.setup(pushbuttontrigger, GPIO.IN, pull_up_down = GPIO.PUD_UP)
#Sonoff-Tasmota Declarations
#Make sure that the device name assigned here does not overlap any of your smart device names in the google home app
#tasmota_devicelist=configuration['Tasmota_devicelist']['friendly-names']
#tasmota_deviceip=configuration['Tasmota_devicelist']['ipaddresses']

# Check if VLC is paused
def checkvlcpaused():
    state=vlcplayer.state()
    if str(state)=="State.Paused":
        currentstate=True
    else:
        currentstate=False
    return currentstate
if configuration['Home_Assistant']['control']=='Enabled':
    from hass_skill import *
    import hass_skill as ha
ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 600 * 3 + 5
device_model_id=configuration['Google_Assistant']['device_model_id']
project_id=configuration['Google_Assistant']['project_id']
#Function to control Sonoff Tasmota Devices
def tasmota_control(phrase,devname,devip):
    if custom_action_keyword['Dict']['On'] in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20on")
            say("Tunring on "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")
    elif custom_action_keyword['Dict']['Off'] in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20off")
            say("Tunring off "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")

#Check if custom wakeword has been enabled
if configuration['Wakewords']['Custom_Wakeword']=='Enabled':
    custom_wakeword=True
elif GPIOcontrol==False:
    print("Pushbutton trigger is not configured. So forcing custom wakeword ON.")
    custom_wakeword=True
else:
    custom_wakeword=False
picovoice_models=configuration['Wakewords']['Picovoice_wakeword_models']
keyword_paths = picovoice_models
wakeword_length=len(picovoice_models)
interrupted=False                 


def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted
mediastopbutton=True

#Custom Conversation
numques=len(configuration['Conversation']['question'])
numans=len(configuration['Conversation']['answer'])
kw=custom_action_keyword['keyword']
cw=custom_action_keyword['Cutwords']
allcmd = custom_action_keyword['commands']
class SampleAssistant(object):
    def __init__(self, language_code, device_model_id, device_id,
                 conversation_stream, display,
                 channel, deadline_sec, device_handler):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream
        self.display = display
        if GPIOcontrol:
            self.t3 = Thread(target=self.stopbutton)
            self.t3.start()
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec
        self.device_handler = device_handler

    def stopbutton(self):
        if GPIOcontrol:
            while mediastopbutton:
                time.sleep(0.25)
                if not GPIO.input(stoppushbutton):
                    print('Stopped')
                    stop()

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False
        self.conversation_stream.close()

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @retry(reraise=True, stop=stop_after_attempt(10),
           retry=retry_if_exception(is_grpc_error_unavailable))


    def data_processing(self,data):
        import fuzzywuzzy
        from fuzzywuzzy import fuzz
        match_key = []
        compare_ratio=[]
        for i in range (0,len(cw)):
            data = data.lower().replace(str(cw[i]).lower(),"")
            data = ' '.join(data.split())
        for key,value in kw.items():
            for j in range(0,len(value)):
                ratio = fuzz.partial_ratio(value[j],data)
                match_key.append(key)
                compare_ratio.append(ratio)
        for i in range (len(allcmd)):
            data=data.replace(str(allcmd[i]),'')
            data=' '.join(data.split())
        if max(compare_ratio) > 90:
            index=compare_ratio.index(max(compare_ratio))
            skill = match_key[index]
            print (skill, data)
            return skill, data 
        else:
            return None

    def assist(self):
        """Send a voice request to the Assistant and playback the response.

        Returns: True if conversation should continue.
        """
        continue_conversation = False
        device_actions_futures = []
#        ctr_led('listening')
        subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.conversation_stream.start_recording()
        if GPIOcontrol:
            ctr_led('listening')
        if vlcplayer.is_vlc_playing():
            if os.path.isfile("{}/.mediavolume.json".format(USER_PATH)):
                try:
                    with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                        volume = json.load(vol)
                    vlcplayer.set_vlc_volume(15)
                except json.decoder.JSONDecodeError:
                    currentvolume=vlcplayer.get_vlc_volume()
                    print(currentvolume)
                    with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                       json.dump(currentvolume, vol)
                    vlcplayer.set_vlc_volume(20)
            else:
                currentvolume=vlcplayer.get_vlc_volume()
                print(currentvolume)
                with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                   json.dump(currentvolume, vol)
                vlcplayer.set_vlc_volume(20)
        #logging.info('Recording audio request.')
        def iter_log_assist_requests():
            for c in self.gen_assist_requests():
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            #logging.debug('Reached end of AssistRequest iteration.')

        for resp in self.assistant.Assist(iter_log_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.event_type == END_OF_UTTERANCE:
                self.conversation_stream.stop_recording()
                #ctr_led('think')
    
            if resp.speech_results:
                print (resp.speech_results)
                logging.info('Transcript of user request: "%s".',
                             ' '.join(r.transcript
                                      for r in resp.speech_results))
                for r in resp.speech_results:            
                    usercommand=str(r)
                if "stability: 1.0" in usercommand.lower():
                    usrcmd=str(' '.join(r.transcript for r in resp.speech_results))
                    usrcmd=str(usrcmd).lower()
                    print(colored('[ViPi_0.2] + [DATA] '+usrcmd,'green'))
                    ctr_led('speaking')
                    a=self.data_processing(usrcmd)
                    if a is not None:
                        skill = str(self.data_processing(usrcmd)[0])
                        pure_data = str(self.data_processing(usrcmd)[1])
                        pre_skill = str(skill.split('_')[0])
                        action=str(skill.split('_')[1])
                        types=str(skill.split('_')[2])
                        more_data=''
                        if skill=='app_music_play':
                            vlcplayer.stop_vlc()
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            ctr_led('speaking')
                            app_music(pure_data.lower())
                            return continue_conversation
                        if skill=='app_music_auto':
                            vlcplayer.stop_vlc()
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            ctr_led('speaking')                          
                            app_music_auto(str(pure_data).lower())
                            return continue_conversation        
                        if skill=='app_read_story':
                            vlcplayer.stop_vlc()
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            ctr_led('speaking')
                            command_read_story(str(pure_data).lower())
                            return continue_conversation
                        if skill=='app_lunar_calendar':
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            ctr_led('speaking')
                            command_lunar_calendar(pure_data.lower())
                            return continue_conversation
                        if skill=='app_news_radio' and configuration['app_news_radio'] == 'Enabled' :
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            if ('thời sự' or 'hài' or 'báo mới' or 'thể thao' or 'hài' or 'báo nói' or 'âm nhạc') not in pure_data:
                                say_save('Bạn muốn nghe thời sự, âm nhạc, thể thao, hài, 18 cộng, hay tin mới?')
                                time.sleep(5)
                                pure_data = re_ask()
                            ctr_led('speaking')
                            app_news_radio(pure_data.lower())
                            return continue_conversation
                        if skill=='app_custom_weather' and configuration['Weather']['control'] == 'Enabled':
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            ctr_led('speaking')
                            app_custom_weather(pure_data.lower())
                            return continue_conversation
                        if skill=='app_chromecast_play':
                            vlcplayer.stop_vlc()
                            for i in range (0,len(kw['app_music_play'])):
                                pure_data = pure_data.lower().replace(str(kw['app_music_play'][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())                            
                            try:
                                chromecast_play_video(str(pure_data).lower())
                            except:
                                ctr_led('speaking')
                                chromecast_control(pure_data) 
                            return continue_conversation
                        if skill=='app_radio_play':
                            try:    
                                ctr_led('speaking') 
                                self.conversation_stream.stop_recording()
                                self.conversation_stream.close()
                                vlcplayer.stop_vlc()
                            except:
                                pass
                            for i in range (0,len(kw[skill])):
                                pure_data = pure_data.lower().replace(str(kw[skill][i]).lower(),"")
                                pure_data = ' '.join(pure_data.split())
                            radio(str(usrcmd).lower())
                            return continue_conversation
                        if skill=='med_stop_music':
                            try:
                                vlcplayer.stop_vlc()
                            except:
                                pass
                            return continue_conversation
                        if skill=='med_pause_player':
                            if vlcplayer.is_vlc_playing():
                                if skill=='med_pause_player':
                                    vlcplayer.pause_vlc()
                                if checkvlcpaused():
                                    if skill=='med_pause_player':
                                        vlcplayer.play_vlc()
                                    if vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                                        say("Đang không phát nhạc")
                            return continue_conversation
                        if skill=='med_next_player':
                            ctr_led('speaking')
                            if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                                vlcplayer.stop_vlc()
                                vlcplayer.change_media_next()
                                if vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                                    say("Không có nội dung đang được phát")
                            return continue_conversation
                        if skill=='med_previous_player':
                            ctr_led('speaking')
                            if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                                vlcplayer.stop_vlc()
                                vlcplayer.change_media_previous()
                            elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                                say("Không có nội dung đang được phá")
                            return continue_conversation
                        if skill=='med_volume_vlc':
                            ctr_led('speaking')
                            if vlcplayer.is_vlc_playing()==True or checkvlcpaused()==True:
                                if 'thay đổi' in str(usrcmd).lower() or 'đặt' in str(usrcmd).lower():
                                    if 'to nhất'.lower() in str(usrcmd).lower():
                                        settingvollevel=100
                                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                             json.dump(settingvollevel, vol)
                                    elif 'nhỏ nhất'.lower() in str(usrcmd).lower() :
                                        settingvollevel=0
                                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                            json.dump(settingvollevel, vol)
                                    else:
                                        for settingvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(usrcmd)):
                                            with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                                json.dump(settingvollevel, vol)
                                    print('Setting volume to: '+str(settingvollevel))
                                    vlcplayer.set_vlc_volume(int(settingvollevel))
                                elif 'tăng' or 'giảm' in str(usrcmd).lower():
                                    if os.path.isfile("{}/.mediavolume.json".format(USER_PATH)):
                                        try:
                                            with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                                                oldvollevel = json.load(vol)
                                                for oldvollevel in re.findall(r'\b\d+\b', str(oldvollevel)):
                                                    oldvollevel=int(oldvollevel)
                                        except json.decoder.JSONDecodeError:
                                            oldvollevel=vlcplayer.get_vlc_volume
                                            for oldvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                                                oldvollevel=int(oldvollevel)
                                    if 'tăng' in str(usrcmd).lower():       
                                        if any(char.isdigit() for char in str(usrcmd)):
                                            for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                                changevollevel=int(changevollevel)
                                        else:
                                            changevollevel=10
                                        newvollevel= oldvollevel+ changevollevel
                                        print(newvollevel)
                                        if int(newvollevel)>100:
                                            settingvollevel=100
                                        elif int(newvollevel)<0:
                                            settingvollevel=0
                                        else:
                                            settingvollevel=newvollevel
                                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                            json.dump(settingvollevel, vol)
                                        print('Setting volume to: '+str(settingvollevel))
                                        vlcplayer.set_vlc_volume(int(settingvollevel))
                                    if 'giảm' in str(usrcmd).lower():
                                        if any(char.isdigit() for char in str(usrcmd)):
                                            for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                                changevollevel=int(changevollevel)
                                        else:
                                            changevollevel=10
                                        newvollevel= oldvollevel - changevollevel
                                        print(newvollevel)
                                        if int(newvollevel)>100:
                                            settingvollevel=100
                                        elif int(newvollevel)<0:
                                            settingvollevel=0
                                        else:
                                           settingvollevel=newvollevel
                                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                            json.dump(settingvollevel, vol)
                                        print('Setting volume to: '+str(settingvollevel))
                                        vlcplayer.set_vlc_volume(int(settingvollevel))
                                    else:
                                        oldvollevel=vlcplayer.get_vlc_volume
                                        for oldvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                                            oldvollevel=int(oldvollevel)
                                else:
                                    say("không có nội dung đang được phát")
                            else:
                                say("không có nội dung đang được phát")
                            return continue_conversation
                        if skill=='med_volume_up':
                            ctr_led('speaking')
                            os.system("amixer set Master 10%+")
                            say("Đã tăng âm lượng thiết bị")
                            return continue_conversation
                        if skill=='med_volume_down':
                            ctr_led('speaking')
                            os.system("amixer set Master 10%-")
                            say("Đã giảm âm lượng thiết bị")
                            return continue_conversation
                        if (skill[:5]=='sma_o' and (configuration['Home_Assistant']['control']=='Enabled')) and not (skill=='sma_on_all' or skill=='sma_off_all'):
                            ctr_led('speaking')
                            ha.hass.command_single(action,types,pure_data)
                            time.sleep(3)
                            continue_conversation = configuration['continue_conversation']
                            return continue_conversation
                        if (skill=='sma_on_all' or skill=='sma_off_all') and (configuration['Home_Assistant']['control']=='Enabled'):
                            ctr_led('speaking')
                            ha.hass.command_all(action,types,pure_data)
                            time.sleep(3)
                            continue_conversation = configuration['continue_conversation']                            
                            return continue_conversation
                        if ('status' in skill) and (configuration['Home_Assistant']['control']=='Enabled'):
                            ctr_led('speaking')
                            ha.hass.check_state(action,types,pure_data)
                            time.sleep(3)
                            continue_conversation = configuration['continue_conversation']                            
                            return continue_conversation
                        if configuration['Conversation']['Conversation_Control']=='Enabled':
                            for i in range(1,numques+1):
                                try:
                                    if str(configuration['Conversation']['question'][i][0]).lower() in str(usrcmd).lower():
                                        selectedans=random.sample(configuration['Conversation']['answer'][i],1)
                                        say(selectedans[0])
                                        return continue_conversation
                                except Keyerror:
                                    say('Please check if the number of questions matches the number of answers')
                        if configuration['Raspberrypi_GPIO_Control']['GPIO_Control']=='Enabled':
                            if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usrcmd).lower():
                                Action(str(usrcmd).lower())
                                return continue_conversation
                    else:
                        ctr_led('speaking') 
                        continue_conversation = configuration['continue_conversation']
                        continue

            if len(resp.audio_out.audio_data) > 0:
                if not self.conversation_stream.playing:
                    self.conversation_stream.stop_recording()
                    self.conversation_stream.start_playback()
                   # logging.info('Playing assistant response.')
                self.conversation_stream.write(resp.audio_out.audio_data)
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                #logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state
            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.conversation_stream.volume_percentage = volume_percentage
            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                if GPIOcontrol:
                    ctr_led('listening')
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                if GPIOcontrol:
                    ctr_led('off')

                if vlcplayer.is_vlc_playing():
                    with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                        oldvolume= json.load(vol)
                    vlcplayer.set_vlc_volume(int(oldvolume))
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)
            if self.display and resp.screen_out.data:
                system_browser = browser_helpers.system_browser
                system_browser.display(resp.screen_out.data)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)
        print(colored('[ViPi_0.2] + [Finish action: Gass] ','yellow'))
        self.conversation_stream.stop_playback()
        if GPIOcontrol:
            ctr_led('off')

        if vlcplayer.is_vlc_playing():
            with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                oldvolume= json.load(vol)
            vlcplayer.set_vlc_volume(int(oldvolume))

        return continue_conversation
    def gen_assist_requests(self):
        """Yields: AssistRequest messages to send to the API."""

        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                volume_percentage=self.conversation_stream.volume_percentage,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            )
        )
        if self.display:
            config.screen_out_config.screen_mode = PLAYING
        self.is_new_conversation = False
        yield embedded_assistant_pb2.AssistRequest(config=config)
        for data in self.conversation_stream:
            yield embedded_assistant_pb2.AssistRequest(audio_in=data)


@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--project-id',
              metavar='<project id>',
              help=('Google Developer Project ID used for registration '
                    'if --device-id is not specified'))
@click.option('--device-model-id',
              metavar='<device model id>',
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--device-config', show_default=True,
              metavar='<device config>',
              default=os.path.join(
                  click.get_app_dir('googlesamples-assistant'),
                  'device_config.json'),
              help='Path to save and restore the device configuration')
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='en-US',
              help='Language code of the Assistant')
@click.option('--display', is_flag=True, default=False,
              help='Enable visual display of Assistant responses in HTML.')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--input-audio-file', '-i',
              metavar='<input file>',
              help='Path to input audio file. '
              'If missing, uses audio capture')
@click.option('--output-audio-file', '-o',
              metavar='<output file>',
              help='Path to output audio file. '
              'If missing, uses audio playback')
@click.option('--audio-sample-rate',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE,
              metavar='<audio sample rate>', show_default=True,
              help='Audio sample rate in hertz.')
@click.option('--audio-sample-width',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH,
              metavar='<audio sample width>', show_default=True,
              help='Audio sample width in bytes.')
@click.option('--audio-iter-size',
              default=audio_helpers.DEFAULT_AUDIO_ITER_SIZE,
              metavar='<audio iter size>', show_default=True,
              help='Size of each read during audio stream iteration in bytes.')
@click.option('--audio-block-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
              metavar='<audio block size>', show_default=True,
              help=('Block size in bytes for each audio device '
                    'read and write operation.'))
@click.option('--audio-flush-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE,
              metavar='<audio flush size>', show_default=True,
              help=('Size of silence data in bytes written '
                    'during flush operation'))
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
@click.option('--once', default=False, is_flag=True,
              help='Force termination after a single conversation.')
def main(api_endpoint, credentials, project_id,
         device_model_id, device_id, device_config,
         lang, display, verbose,
         input_audio_file, output_audio_file,
         audio_sample_rate, audio_sample_width,
         audio_iter_size, audio_block_size, audio_flush_size,
         grpc_deadline, once, *args, **kwargs):

    ctr_led('wakeup')
    if gender=='Male' and configuration['Startup_voice'] == 'Enabled':
        subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Male.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if gender=='Female' and configuration['Startup_voice'] == 'Enabled':
        subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Female.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Setup logging.
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        sys.exit(-1)

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)

    # Configure audio source and sink.
    audio_device = None
    if input_audio_file:
        audio_source = audio_helpers.WaveSource(
            open(input_audio_file, 'rb'),
            sample_rate=audio_sample_rate,
            sample_width=audio_sample_width
        )
    else:
        audio_source = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
    if output_audio_file:
        audio_sink = audio_helpers.WaveSink(
            open(output_audio_file, 'wb'),
            sample_rate=audio_sample_rate,
            sample_width=audio_sample_width
        )
    else:
        audio_sink = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
    # Create conversation stream with the given audio source and sink.
    conversation_stream = audio_helpers.ConversationStream(
        source=audio_source,
        sink=audio_sink,
        iter_size=audio_iter_size,
        sample_width=audio_sample_width,
    )

    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
                logging.info("Using device model %s and device id %s",
                             device_model_id,
                             device_id)
        except Exception as e:
            logging.warning('Device config not found: %s' % e)
            logging.info('Registering device')
            if not device_model_id:
                logging.error('Option --device-model-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            if not project_id:
                logging.error('Option --project-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            device_base_url = (
                'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                             project_id)
            )
            device_id = str(uuid.uuid1())
            payload = {
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_SERVICE'
            }
            session = google.auth.transport.requests.AuthorizedSession(
                credentials
            )
            r = session.post(device_base_url, data=json.dumps(payload))
            if r.status_code != 200:
                logging.error('Failed to register device: %s', r.text)
                sys.exit(-1)
            logging.info('Device registered: %s', device_id)
            pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
            with open(device_config, 'w') as f:
                json.dump(payload, f)

    device_handler = device_helpers.DeviceRequestHandler(device_id)

    with SampleAssistant(lang, device_model_id, device_id,
                         conversation_stream, display,
                         grpc_channel, grpc_deadline,
                         device_handler) as assistant:
        # If file arguments are supplied:
        # exit after the first turn of the conversation.
        if input_audio_file or output_audio_file:
            assistant.assist()
            
            return
        def detected():
            continue_conversation=assistant.assist()
            if continue_conversation:
                print('Continuing conversation')
                time.sleep(2)
                assistant.assist()
                                              

        signal.signal(signal.SIGINT, signal_handler)
        _sensitivities = [configuration['Wakewords']['sensitivities']]*wakeword_length


        _library_path = pvporcupine.LIBRARY_PATH
        _model_path = pvporcupine.MODEL_PATH
        _keyword_paths = picovoice_models
        _input_device_index = None


        def picovoice_run():
            """
             Creates an input audio stream, instantiates an instance of Porcupine object, and monitors the audio stream for
             occurrences of the wake word(s). It prints the time of detection for each occurrence and the wake word.
             """
            keywords = list()
            for x in _keyword_paths:
                keywords.append(os.path.basename(x).replace('.ppn', '').split('_')[0])

            porcupine = None
            pa = None
            audio_stream = None
            try:
                                     
                porcupine = pvporcupine.create(
                    library_path=_library_path,
                    model_path=_model_path,
                    keyword_paths=_keyword_paths,
                    sensitivities=_sensitivities)

                pa = pyaudio.PyAudio()

                audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length,
                    input_device_index=_input_device_index)

                while True:
                    pcm = audio_stream.read(porcupine.frame_length,exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                    result = porcupine.process(pcm)
                    if result >= 0:
                        detected()

            except KeyboardInterrupt:
                print('Stopping ...')
            finally:
                if porcupine is not None:
                    porcupine.delete()
                if audio_stream is not None:
                    audio_stream.close()
                if pa is not None:
                    pa.terminate()

        # If no file arguments supplied:
        # keep recording voice requests using the microphone
        # and playing back assistant response using the speaker.
        # When the once flag is set, don't wait for a trigger. Otherwise, wait.

        wait_for_user_trigger = not once
        while True:
            if wait_for_user_trigger:
                if custom_wakeword:
                    if configuration['Wakewords']['Wakeword_Engine']=='Picovoice':
                        picovoice_run()

                else:
                    button_state=GPIO.input(pushbuttontrigger)
                    if button_state==True:
                       continue
                    else:
                       pass
            continue_conversation = assistant.assist()
#            ctr_led('off')
            wait_for_user_trigger = not continue_conversation
#            if once and (not continue_conversation):
#                break
        while continue_conversation:
            continue_conversation = assistant.assist()

import speech_recognition as sr
r = sr.Recognizer()
import time
from ctypes import *
from contextlib import contextmanager
import pyaudio

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
    
def re_ask():
    tic = time.perf_counter()
    with noalsaerr() as n,sr.Microphone() as source:
        print("Say something!")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        data = r.recognize_google(audio,language = "vi-VN")
        toc = time.perf_counter()
        print("Google: " + data)
        print(f"Google take {toc - tic:0.4f} seconds")  
    return data

##


if __name__ == '__main__':
    main()
