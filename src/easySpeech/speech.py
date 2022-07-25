# import required libraries
import sounddevice as sd
from .recognize import *
from .record import *
from .ml import *
import requests, time, random
from bs4 import BeautifulSoup
# from knowledge_base import header
def get_free_proxies():
    url = "https://free-proxy-list.net/"
    # request and grab content
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    # to store proxies
    proxies = []
    for row in soup.find("table", attrs={"class": "table table-striped table-bordered"}).find_all("tr")[1:]:
        tds = row.find_all("td")
        try:
            ip = tds[0].text.strip()
            port = tds[1].text.strip()
            proxies.append(str(ip) + ":" + str(port))
        except IndexError:
            continue
    return proxies
proxies = get_free_proxies()
def header(req_url):
    proxy = random.choice(proxies)
    phttp = "http://" + proxy
    proxi = {'http': phttp}
    #print (proxi)
    session = requests.Session()
    session.proxies = proxi
    session.get(req_url)
    session_cookies = session.cookies
    cookies_dictionary = session_cookies.get_dict()
    headers = {'origin': 'https://zalo.ai', 'referer': 'https://zalo.ai/experiments/vietnamese-questions-answering'}
    return cookies_dictionary,headers,proxi
def speech(using,freq = 44100,duration = 3,key=None, language="vi-VN", show_all=False):
    # Start recorder with the given values of 
    # duration and sample frequency
    recording = sd.rec(int(duration * freq), 
                    samplerate=freq, channels=2)

    # Record audio for the given number of seconds
    sd.wait()
    write("recording.wav", recording, freq, sampwidth=2)
    if using.lower()=='google':
        tic = time.perf_counter()
        r = Recognizer()
        recording = AudioFile('recording.wav')
        with recording as source:
            audio = r.record(source)
        text=r.recognize_google(audio,key, language, show_all)
        toc = time.perf_counter()
        #print("Google: " + text)
        print(f"[ViPi] Time_Google_free_take:  {toc - tic:0.4f} giây")      

    elif using.lower()=='ml':
        text=ml('recording.wav')
    elif using.lower() == 'zstt':
        tic = time.perf_counter()
        url = 'https://zalo.ai/api/demo/v1/asr'
        files = {'file': open('recording.wav','rb')}
        req_url = 'https://zalo.ai/experiments/automation-speech-recognition'
        cookies_dictionary,headers,proxies=header(req_url)
        try:
            resp = requests.post(url, files = files, headers=headers,cookies=cookies_dictionary, proxies=proxies).json()
            text = resp['result']['text']
        except:
            text = ''
        toc = time.perf_counter()
        #print("Zalo: " + text)
        print(f"[ViPi] Time_Zalo_take:   {toc - tic:0.4f} giây")                
    else:
        text='engine not found'
    return text

def google_audio(file,key=None, language="en-US", show_all=False):
    r = Recognizer()
    recording = AudioFile(file)
    with recording as source:
        audio = r.record(source)
    text=r.recognize_google(audio,key, language, show_all)
    return text

def recorder(name,duration = 5,freq = 44100):  
    recording = sd.rec(int(duration * freq),samplerate=freq, channels=2)
    sd.wait()
    write(name, recording, freq, sampwidth=2)