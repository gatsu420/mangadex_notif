import pymysql 
import os
import requests
from datetime import datetime
import time

tidy_manga_id = []
tidy_initial_update = []
gb_chapter_timestamp = []
recent_chapter_id = []
recent_chapter_num = []
recent_chapter_timestamp = []
chapter_list = []

api_prefix = 'https://mangadex.org/api/?id='
api_suffix = '&type=manga'

try:
    conn = pymysql.connect(host = os.environ['HAKASETEST_HOST'], 
                            user = os.environ['HAKASETEST_USER'],
                            password = os.environ['HAKASETEST_PASS'])
    cur = conn.cursor()
    cur.execute('select manga_id from {MD_MANGA}'.format(MD_MANGA=os.environ['MD_MANGA']))
    manga_id = cur.fetchall()
    conn.close()
except:
    print('fail to read mangadex_notif.py_manga')

for i in range(len(manga_id)):
    gb_chapter_timestamp = [] #flush tuple for every manga_id
    chapter_list.append(list(requests.get(api_prefix + str(manga_id[i][0]) + api_suffix).json()['chapter']))
    chapter = requests.get(api_prefix + str(manga_id[i][0]) + api_suffix).json()['chapter']
    tidy_manga_id.append(str(manga_id[i][0]))

    for ii in range(len(chapter_list[i])):
        if chapter[str(chapter_list[i][ii])]['lang_code'] == 'gb':
            gb_chapter_timestamp.append(chapter[str(chapter_list[i][ii])]['timestamp'])

    for ij in range(len(gb_chapter_timestamp)):
        if gb_chapter_timestamp[ij] == max(gb_chapter_timestamp):
            for iji in range(len(chapter_list[i])):
                if chapter[str(chapter_list[i][iji])]['timestamp'] == max(gb_chapter_timestamp):
                    recent_chapter_id.append(chapter_list[i][iji])
                    recent_chapter_num.append(chapter[str(chapter_list[i][iji])]['chapter'])
                    recent_chapter_timestamp.append(datetime.fromtimestamp(chapter[str(chapter_list[i][iji])]['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

    time.sleep(2) #to make the request less harmful

updated_time = [str(datetime.now())] * len(recent_chapter_id)

recent_update = list(zip(tidy_manga_id, recent_chapter_id, recent_chapter_num, recent_chapter_timestamp, updated_time))

try:
    conn = pymysql.connect(host = os.environ['HAKASETEST_HOST'], 
                            user = os.environ['HAKASETEST_USER'],
                            password = os.environ['HAKASETEST_PASS'])
    cur = conn.cursor()
    sql = '''insert into {MD_RECENT_UPDATE} (manga_id, chapter_id, chapter_num, chapter_timestamp, updated_time) values (%s, %s, %s, %s, %s)
                on duplicate key update chapter_id=values(chapter_id), 
                    chapter_num=values(chapter_num), 
                    chapter_timestamp=values(chapter_timestamp)'''.format(MD_RECENT_UPDATE=os.environ['MD_RECENT_UPDATE'])
    cur.executemany(sql, recent_update)
    conn.commit()
    conn.close()
except:
    print('fail to write mangadex_notif.py_recent_update')