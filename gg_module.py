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
version = "0.0.1"
CHECK_FREQUENCY = 1 * 20  # in seconds
#запрос переменной из файла oauth_token.txt рядом со скриптом

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
#Парсинг аргуметов командной строки
def createParser ():
    parser = argparse.ArgumentParser(prog = 'Twitch beholder module',
            description = '''Это скрипт слежения за появлением трансляции по нужному адресу на goodgame.ru, работает в цикле''',
            epilog = '''(c) zxosa, huigovnomuravei. Авторы программы, как всегда, не несут никакой ответственности ни за что, но постараются вам помочь. osa.wetl@gmail.com''')
    parser.add_argument ('-u', '--url', help = 'Ссылка на страницу стрима на goodgame.ru')
    parser.add_argument ('-q', '--quality', choices=['audio_only', '240p', '480p', '720p', '1080p', 'best', 'worst'], default='best', help = 'выбор качества записи стрима')
    parser.add_argument ('-v', '--version', action='version', help = 'Вывести номер версии', version='%(prog)s {}'.format (version))
 
    return parser
#Подготовка логина из адреса
def prepare_variables_login(REC_ADRESS):
    if REC_ADRESS[-10:] == '/#autoplay':
       REC_ADRESS = REC_ADRESS[:-10]
       print (REC_ADRESS)
    if REC_ADRESS[:28] == 'https://goodgame.ru/channel/':
       LOGIN_STREAMER = REC_ADRESS[28:]
       print (LOGIN_STREAMER)
       return (LOGIN_STREAMER)
    elif REC_ADRESS[:20] == 'goodgame.ru/channel/':
       LOGIN_STREAMER = REC_ADRESS[20:]
       print (LOGIN_STREAMER)
       return (LOGIN_STREAMER)
    else:
       logging.error('Not goodgame.ru adress!')
       print ("Not goodgame.ru adress! Stoped!")
       sys.exit()

def Check_Online():
    try:
        URL_STREAM = 'http://goodgame.ru/api/getchannelstatus'
        p = {'id': LOGIN_STREAMER,'fmt':'json'}
        r = requests.get(URL_STREAM, params=p)
        d = json.loads(r.text)
        logging.debug(d)
        print('\r\033[K\033[92mWatchdog online\033[0m', end='\r')    
        try:
            keys = list(d.keys())
            STREAMER_ID = (keys[0])
            LIVE_STREAM = d[STREAMER_ID]["status"]
        except IndexError:
            return False
        if LIVE_STREAM == ('Live'):
            keys = list(d.keys())
            STREAMER_ID = (keys[0])
            TITLE_STREAM = d[STREAMER_ID]['title']
            print('Live - ' + TITLE_STREAM)
            return True
        else:
            return False
    except:
        print('\r\033[K\033[91m Http connect error ' + time.strftime('%Y-%m-%d-%H-%M') + '\033[0m', end="\r")
        return False

def start_loop():
    while True:
        stream = Check_Online()
        if stream:
            q = """UPDATE {table} SET record=True WHERE id=1"""
            cursor.execute(q.format(table=LOGIN_STREAMER))
            conn.commit()
            FILENAME_STREAMLINK = LOCATION_REC + LOGIN_STREAMER + time.strftime('%Y-%m-%d-%H-%M') + '.mp4'
            q = "UPDATE {table} SET RecFile='" + FILENAME_STREAMLINK + "' WHERE id=1"
            cursor.execute(q.format(table=LOGIN_STREAMER))
            conn.commit()
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
               q = "UPDATE {table} SET PidRecorder='" + str(pidrecorder) + "' WHERE id=1"
               cursor.execute(q.format(table=LOGIN_STREAMER))
               conn.commit()
               q = "UPDATE {table} SET PidScript='" + str(os.getpid()) + "' WHERE id=1"
               cursor.execute(q.format(table=LOGIN_STREAMER))
               conn.commit()
               logging.info('pid recorder ' + str(pidrecorder))
               logging.info('pid script ' + str(os.getpid()))
               logging.info('Recorder: streamlink')
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
               
               REC_ADRESS2 = 'https://goodgame.ru/channel/' + LOGIN_STREAMER
               print (REC_ADRESS2)
               process = subprocess.Popen(['youtube-dl','-f', QUALITY,'-o',FILENAME_STREAMLINK, REC_ADRESS2],shell=False)
               pidrecorder = process.pid
               q = "UPDATE {table} SET PidRecorder='" + str(pidrecorder) + "' WHERE id=1"
               cursor.execute(q.format(table=LOGIN_STREAMER))
               conn.commit()
               q = "UPDATE {table} SET PidScript='" + str(os.getpid()) + "' WHERE id=1"
               cursor.execute(q.format(table=LOGIN_STREAMER))
               conn.commit()
               logging.info('pid recorder ' + str(pidrecorder))
               logging.info('pid script ' + str(os.getpid()))
               logging.info('Recorder: youtube-dl')
               print ('Record youtube-dl')
            code = process.wait()
            print (code)
            logging.info ('Exit code: ' + code)
            #Конец стрима
            logging.info('Stream offline, rec stop, pause 5min')
            print(time.strftime('%Y-%m-%d-%H-%M') + ' Offline stream, pause 5min')
            time_count = 300
            for i in range(time_count, 0, -1):
                print('Осталось %d секунд           ' % i , end='\r')
                time.sleep(1)
            #cls()
            q = """UPDATE {table} SET record=False WHERE Id=1"""
            cursor.execute(q.format(table=LOGIN_STREAMER))
            conn.commit()
            print(LOGIN_STREAMER)
            print(QUALITY,'\n')
            
        time.sleep(CHECK_FREQUENCY)

if __name__ == '__main__':
    
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    REC_ADRESS = namespace.url
    QUALITY = namespace.quality
    LOGIN_STREAMER = prepare_variables_login(REC_ADRESS)
    logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', filename=LOGIN_STREAMER+".log", level=logging.INFO, filemode="a")
    #запускаем базу данных для локального сервера
    conn = sqlite3.connect("twitch_module.db", check_same_thread = False) # или :memory: чтобы сохранить в RAM
    cursor = conn.cursor()
 
    # Создание таблицы
    q = """DROP TABLE IF EXISTS {table}"""
    cursor.execute(q.format(table=LOGIN_STREAMER))
    q = """CREATE TABLE {table} (id, starting, control_time, record, RecFile, PidRecorder, PidScript)"""
    cursor.execute(q.format(table=LOGIN_STREAMER))
    logging.debug (namespace)
    logging.info("Beholder started")
    print('GoodGame beholder started...\n')
    print(LOGIN_STREAMER)
    print(QUALITY,'\n')
    q = """INSERT INTO {table} VALUES(1,True,0,False,'none',0,0)"""
    cursor.execute(q.format(table=LOGIN_STREAMER))
    conn.commit()
    start_loop()
