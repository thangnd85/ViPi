import requests
from bs4 import BeautifulSoup
from actions import vlcplayer

def vnp_podcast():
    url = 'https://www.vietnamplus.vn/podcast.vnp'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # last_links = soup.find(class_='story__title cms-link')
    # print(last_links.decompose())

    artist_name_list = soup.find(class_="cate__focus")
    artist_name_list_items = artist_name_list.find_all('a')
    # print(artist_name_list_items)

    table_links = []
    for artist_name in artist_name_list_items:

        # names = artist_name.contents[0]
        links = 'https://vietnamplus.vn/' + artist_name.get('href')
        table_links.append(links)
    table_links_set = set(table_links)
    # table_links_list = list(table_links_set)
    #for i in table_links_set:
    #    print(i)

    return table_links_set

def podcast_link(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "html.parser")
    artist_name_list = soup.find(class_="article-video")
    artist_name_list_items = artist_name_list.find_all('audio')
    table_links = []
    for artist_name in artist_name_list_items:
        # print(artist_name)
        mp3_link = artist_name.get('src')
        if '.mp3' in mp3_link:
            table_links.append(mp3_link)
    return table_links

# Link Podcast mp4
# def podcast_link_video(link='https://www.vietnamplus.vn/hinh-anh-nhieu-cam-xuc-trong-ngay-khai-giang-va-nam-hoc-moi-dac-biet/738871.vnp'):
#     response = requests.get(link)
#     soup = BeautifulSoup(response.text, "html.parser")
#
#     artist_name_list = soup.find(class_="vnpplayer")
#     artist_name_list_items = artist_name_list.find('video').find('source')
#     # print(artist_name_list_items)
#     artist_name_list_items_finall = str(artist_name_list_items).replace('<source src="', '').replace('" type="video/mp4"/>', '')
#     return artist_name_list_items_finall


def app_podcast_play():
    table_links_set = vnp_podcast()
    link_list = []
    for link_mp3 in table_links_set:
        mp3_url = podcast_link(link_mp3)
        if len(mp3_url) > 0:
            mp3_url_str = str(mp3_url).replace("['", "").replace("']", "")
            link_list.append(mp3_url_str)

    # for link_mp4 in table_links_set:
    #     mp4_url = podcast_link_video(link_mp4)
    #     link_list.append(mp4_url)

#    for i in link_list:
#        print(i)
    currenttrackid=0
    if not link_list==[]:
            vlcplayer.media_manager(link_list,'YouTube')
            vlcplayer.youtube_player(currenttrackid)
    return link_list

