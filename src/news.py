import requests
import re
import time
import threading
from actions import vlcplayer
import random
headers = requests.utils.default_headers()
headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
})
def app_news_radio(data):
    if 'thời sự' in data.lower():
        url="https://netnews.vn/audio-thoi-su.html"
    elif 'nhạc' in data.lower():
        url = "https://netnews.vn/audio-am-nhac.html"
    elif 'tâm sự' in data.lower():
        url = "https://netnews.vn/audio-tam-su.html"
    elif "hài" in data.lower():
        url = "https://netnews.vn/audio-hai.html"
    elif 'thể thao' in data.lower():
        url = "https://netnews.vn/audio-the-thao.html"
    elif '18' in data.lower():
        url = "https://netnews.vn/audio-gioi-tinh.html"
    elif 'mới' in data:
        url = "https://netnews.vn/bao-noi.html"
    else:
        url = "https://netnews.vn/bao-noi.html"
    print (url)
    request = requests.get(url, headers=headers)
    url_find='https://mcnewsmd1.keeng.net/netnews/archive/radio/'
    link = re.findall(url_find+'([a-zA-Z0-9/a-zA-Z0-9_a-zA-Z0-9.mp3]{0,60})', request.text)
    urllist=[]
    currenttrackid=0
    for i in range (1,len(link)):
        streamurl = url_find+str(link[i])
        urllist.append(streamurl)
#    random.shuffle(urllist) 
    if not urllist==[]:
            vlcplayer.media_manager(urllist,'YouTube')
            vlcplayer.youtube_player(currenttrackid)
    return urllist
if __name__ == '__main__':
    app_news_radio()