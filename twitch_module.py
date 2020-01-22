#twitch beholder video module
import requests
import json
import time
import subprocess
import sys
import argparse
import logging
import sqlite3
import threading
import streamlink
import os
LOCATION_REC = "./"
version = "0.1.2"
CHECK_FREQUENCY = 1 * 20  # in seconds
#запрос переменной из файла oauth_token.txt рядом со скриптом
try:
    with open('oauth_token.txt', 'r', encoding='utf-8-sig') as fp:
        OAUTH_TOKEN_TWITCH = fp.read().rstrip()
        if not OAUTH_TOKEN_TWITCH:
            logging.error('No data oauth_token.txt')
            print ("No data oauth_token.txt ! Stoped!")
            sys.exit()
        if not OAUTH_TOKEN_TWITCH[:6] == 'oauth:':
            logging.error('No valid data oauth_token.txt')
            print ("No valid oauth token in oauth_token.txt! Stoped!")
            sys.exit()
        OAUTH_TOKEN_TWITCH = OAUTH_TOKEN_TWITCH[6:]
except IOError:
    logging.error('No file oauth_token.txt')
    print ("No file oauth_token.txt ! Stoped!")
    sys.exit()
def cls():
    os.system('cls' if os.name=='nt' else 'clear')
#Парсинг аргуметов командной строки
def createParser ():
    parser = argparse.ArgumentParser(prog = 'Twitch beholder module',
            description = '''Это скрипт слежения за появлением трансляции по нужному адресу на twitch.tv, работает в цикле''',
            epilog = '''(c) zxosa, huigovnomuravei. Авторы программы, как всегда, не несут никакой ответственности ни за что, но постараются вам помочь. osa.wetl@gmail.com''')
    parser.add_argument ('-u', '--url', help = 'Ссылка на страницу стрима на Twitch.tv')
    parser.add_argument ('-q', '--quality', choices=['audio_only', '160p', '360p', '480p', '720p', '720p60', '1080p60', 'best', 'worst'], default='best', help = 'выбор качестав записи стрима')
    parser.add_argument ('-v', '--version', action='version', help = 'Вывести номер версии', version='%(prog)s {}'.format (version))
 
    return parser
#Подготовка логина из адреса
def prepare_variables_login(REC_ADRESS):
    if REC_ADRESS[-1:] == '/':
       REC_ADRESS = REC_ADRESS[:-1]
       print (REC_ADRESS)
    if REC_ADRESS[:22] == 'https://www.twitch.tv/':
       LOGIN_STREAMER = REC_ADRESS[22:]
       print (LOGIN_STREAMER)
       return (LOGIN_STREAMER)
    elif REC_ADRESS[:14] == 'www.twitch.tv/':
       LOGIN_STREAMER = REC_ADRESS[14:]
       print (LOGIN_STREAMER)
       return (LOGIN_STREAMER)
    else:
        logging.error('Not www.twitch.tv adress!')
        print ("Not www.twitch.tv adress! Stoped!")
        sys.exit()
def request_client_id():
    HEADERS_AUTH = {'Authorization': 'OAuth ' + OAUTH_TOKEN_TWITCH}
    logging.debug(HEADERS_AUTH)
    URL_AUTH = "https://id.twitch.tv/oauth2/validate"
    r = requests.get(URL_AUTH, headers=HEADERS_AUTH)
    d = json.loads(r.text)
    logging.debug(d)
    H_ID = {'Client-ID': d['client_id']}
    return (H_ID)
       
def send_sms(message_sms):
    print (message_sms)
    # URL_MESSAGE = 'https://sms.ru/sms/send'
    # p = {'api_id':'0C5DD3A1-_____-_____-_______-5776BFD68808','to':'7______________','msg':message_sms}
    # try:
        # r = requests.get(URL_MESSAGE, params=p)
        # logging.info('sms:' + message_sms)
        # print ('send sms ok')
    # except requests.exceptions.RequestException as e:  # This is the correct syntax
        # print (e)
        # print ('error sms')

def Check_Online():
    try:
        HEADERS_ID = request_client_id()
        print('\r\033[K\033[92mWatchdog online\033[0m', end='\r')    
        URL_STREAM = 'https://api.twitch.tv/helix/streams'
        p = {'user_login': LOGIN_STREAMER}
        r = requests.get(URL_STREAM, headers=HEADERS_ID, params=p)
        d = json.loads(r.text)
        logging.debug(d)
        try:
            LIVE_STREAM = d['data'][0]['type']
        except IndexError:
            return False
        if LIVE_STREAM == ('live'):
            TITLE_STREAM = d['data'][0]['title']
            print('Live - ' + TITLE_STREAM)
            return True
        else:
            return False
    except:
        print('\r\033[K\033[91m Http connect error ' + time.strftime('%Y-%m-%d-%H-%M') + '\033[0m', end="\r")
        return False

def get_vod_1():
    try:
        HEADERS_ID = request_client_id()
        #запрос user_id по нику
        URL_REQ = "https://api.twitch.tv/helix/users"
        payload = {'login': LOGIN_STREAMER}
        r = requests.get(URL_REQ, headers=HEADERS_ID, params=payload)
        d = json.loads(r.text)
        STREAMER_ID = d['data'][0]['id']
        logging.debug (STREAMER_ID)
        #запрос последнего vod
        URL_REQ = "https://api.twitch.tv/helix/videos"
        payload = {'user_id': STREAMER_ID}
        r = requests.get(URL_REQ, headers=HEADERS_ID, params=payload)
        d = json.loads(r.text)
        LAST_VOD = d['data'][0]['url']
        logging.info('LAST VOD ' + LAST_VOD)
        print ('\nLast VOD ' + LAST_VOD + '\n')
        streams = streamlink.streams(LAST_VOD)
        stream = streams["best"]
        fd = stream.open()
        url = fd.writer.stream.url
        fd.close()
        print ('\n' + url + '\n')
        logging.info('Last VOD url ' + url)
    except:
        logging.warning('Streamlink error, alternative request')
        HEADERS_ID = request_client_id()
        #запрос user_id по нику
        URL_REQ = "https://api.twitch.tv/helix/users"
        payload = {'login': LOGIN_STREAMER}
        r = requests.get(URL_REQ, headers=HEADERS_ID, params=payload)
        d = json.loads(r.text)
        STREAMER_ID = d['data'][0]['id']
        logging.debug (STREAMER_ID)
        #запрос последнего vod
        URL_REQ = "https://api.twitch.tv/helix/videos"
        payload = {'user_id': STREAMER_ID}
        r = requests.get(URL_REQ, headers=HEADERS_ID, params=payload)
        d = json.loads(r.text)
        LAST_VOD = d['data'][0]['url']
        logging.info('LAST VOD ' + LAST_VOD)
        print ('\nLast VOD ' + LAST_VOD + '\n')
        URL_REQ = "https://pwn.sh/tools/streamapi.py"
        payload = {'url': LAST_VOD}
        r = requests.get(URL_REQ, params=payload)
        d = json.loads(r.text)
        url = d['urls']['1080p60']
        #streams = streamlink.streams(LAST_VOD)
        #stream = streams["best"]
        #fd = stream.open()
        #url = fd.writer.stream.url
        #fd.close()
        print ('\n' + url + '\n')
        logging.info('Last VOD url ' + url)    


def start_loop():
    while True:
        stream = Check_Online()
        if stream:
            FILENAME_STREAMLINK = LOCATION_REC + LOGIN_STREAMER + time.strftime('%Y-%m-%d-%H-%M') + '.mp4'
            logging.info('Stream online, rec ' + FILENAME_STREAMLINK )
            print('Stream online, rec ' + FILENAME_STREAMLINK )
            #Выбор рекордера
            #Стримлинк по умолчанию
            try:
               #raise Exception('TEST!')
               #Логирование урл стрима
               streams = streamlink.streams(REC_ADRESS)
               stream = streams["best"]
               fd = stream.open()
               url = fd.writer.stream.url
               fd.close()
               print (url)
               logging.info('Stream url ' + url)
               #Выхов стримлинка, запись.
               
               process = subprocess.Popen(['streamlink', REC_ADRESS, QUALITY,'--hls-live-restart','-o',FILENAME_STREAMLINK],shell=False)
               pidrecorder = process.pid
               logging.info('pid recorder ' + str(pidrecorder))
               logging.info('pid script ' + str(os.getpid()))
               #Запрос последнего vod
               time.sleep(30)
               logging.info('Recorder: streamlink')
               try:
                   get_vod_1()
               except:
                   logging.warning('No VOD or network error')
                   print ('No VOD or network error')
               send_sms('rec_started_via_streamlink')
               code = process.wait()
            #Youtube-dl резерв
            except:
               logging.warning('Streamlink error, change recorder')
               print ("Внимание, переход на резервный рекордер!")
               #Логирование урл стрима
               #streams = streamlink.streams(REC_ADRESS)
               #stream = streams["best"]
               #fd = stream.open()
               #url = fd.writer.stream.url
               #fd.close()
               #print (url)
               #logging.info('Stream url ' + url)
               #Выхов стримлинка, запись.
               
               REC_ADRESS2 = 'https://www.twitch.tv/' + LOGIN_STREAMER
               print (REC_ADRESS2)
               process = subprocess.Popen(['youtube-dl','-f', QUALITY,'-o',FILENAME_STREAMLINK, REC_ADRESS2],shell=False)
               pidrecorder = process.pid
               logging.info('pid recorder ' + str(pidrecorder))
               logging.info('pid script ' + str(os.getpid()))
               logging.info('Recorder: youtube-dl')
               print ('Record youtube-dl')
               #Запрос последнего vod
               time.sleep(30)
               try:
                   get_vod_1()
               except:
                   logging.warning('No VOD or network error')
                   print ('No VOD or network error')
               send_sms('rec_started_via_youtube-dl')
               code = process.wait()

            #Конец стрима
            logging.info('Stream offline, rec stop, pause 5min')
            print(time.strftime('%Y-%m-%d-%H-%M') + ' Offline stream, pause 5min')
            time_count = 300
            for i in range(time_count, 0, -1):
                print('Осталось %d секунд           ' % i , end='\r')
                time.sleep(1)
            #cls()
            send_sms('rec_stop')
            print(LOGIN_STREAMER)
            print(QUALITY,'\n')
            
        time.sleep(CHECK_FREQUENCY)
#def Watchdog_script():
#    while True:
#      a = input()
#      if a == 'e':
#          logging.info('exit')
#          sys.exit()
#      elif  a == 'E':
#          logging.info('exit')
#          sys.exit()
if __name__ == '__main__':
    
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    REC_ADRESS = namespace.url
    QUALITY = namespace.quality
    LOGIN_STREAMER = prepare_variables_login(REC_ADRESS)
    logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', filename=LOGIN_STREAMER+".log", level=logging.INFO, filemode="a")
    logging.debug (namespace)
    logging.info("Beholder started")
    print('Twitch beholder started...\n')
    print(LOGIN_STREAMER)
    print(QUALITY,'\n')
#    thread1 = threading.Thread(target=start_loop)
#    thread1.start()
#    thread2 = threading.Thread(target=Watchdog_script)
#    thread2.start()
    send_sms('script_started')
    start_loop()
