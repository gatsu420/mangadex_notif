import pymysql
import requests
from datetime import datetime
import time
from twilio.rest import Client
from airflow.models import Variable #replacement for os package on airflow environment

tidy_manga_id = []
tidy_initial_update = []
gb_chapter_timestamp = []
recent_chapter_id = []
recent_chapter_num = []
recent_chapter_timestamp = []
chapter_list = []
initial_manga_id = []
initial_chapter_id = []
master_manga_id = []
master_manga_title = []
manga_id_update = []
chapter_id_update = []
manga_title_update = []

api_prefix = 'https://mangadex.org/api/?id='
api_suffix = '&type=manga'

twilio_sid = Variable.get('TWILIO_SID')
twilio_token = Variable.get('TWILIO_TOKEN')
twilio_phone_source = Variable.get('TWILIO_PHONE_SOURCE')
twilio_phone_target = Variable.get('TWILIO_PHONE_TARGET')

# scrape details for every manga_id in master
try:
    conn = pymysql.connect(host = Variable.get('HAKASETEST_HOST'), 
                            user = Variable.get('HAKASETEST_USER'),
                            password = Variable.get('HAKASETEST_PASS'))
    cur = conn.cursor()
    cur.execute('select manga_id from {MD_MANGA}'.format(MD_MANGA=Variable.get('MD_MANGA')))
    manga_id = cur.fetchall()
    conn.close()
except:
    print('fail to read {MD_MANGA}'.format(MD_MANGA=Variable.get('MD_MANGA')))

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

# recheck whether recent update offsets with existing update

try:
    conn = pymysql.connect(host = Variable.get('HAKASETEST_HOST'), 
                            user = Variable.get('HAKASETEST_USER'),
                            password = Variable.get('HAKASETEST_PASS'))
    cur = conn.cursor()
    cur.execute('select manga_id, chapter_id from {MD_RECENT_UPDATE}'.format(MD_RECENT_UPDATE=Variable.get('MD_RECENT_UPDATE')))
    initial_update = cur.fetchall()
    conn.close()
except:
    print('fail to read {MD_RECENT_UPDATE}'.format(MD_RECENT_UPDATE=Variable.get('MD_RECENT_UPDATE')))

for j in range(len(initial_update)):
    initial_chapter_id.append(initial_update[j][1])

for k in range(len(recent_update)):
    if int(recent_update[k][1]) not in initial_chapter_id:
        chapter_id_update.append(recent_update[k][1])

for l in range(len(chapter_id_update)):
    if chapter_id_update[l] in recent_chapter_id:
        manga_id_update.append(recent_update[recent_chapter_id.index(chapter_id_update[l])][0])

try:
    conn = pymysql.connect(host = Variable.get('HAKASETEST_HOST'), 
                            user = Variable.get('HAKASETEST_USER'),
                            password = Variable.get('HAKASETEST_PASS'))
    cur = conn.cursor()
    cur.execute('select * from {MD_MANGA}'.format(MD_MANGA=Variable.get('MD_MANGA')))
    master = cur.fetchall()
    conn.close()
except:
    print('fail to read {MD_MANGA}'.format(MD_MANGA=Variable.get('MD_MANGA')))

for m in range(len(master)):
    master_manga_id.append(master[m][0])
    master_manga_title.append(master[m][1])

for n in range(len(manga_id_update)):
    if int(manga_id_update[n]) in master_manga_id:
        manga_title_update.append(master_manga_title[master_manga_id.index(int(manga_id_update[n]))])

notif_msg = 'manga terupdate = {MANGA_UPDATE}, with total updated chapter={CHAPTER_UPDATE}'.format(MANGA_UPDATE=str(manga_title_update)[1:-1], CHAPTER_UPDATE=len(chapter_id_update))

try:
    conn = pymysql.connect(host = Variable.get('HAKASETEST_HOST'), 
                            user = Variable.get('HAKASETEST_USER'),
                            password = Variable.get('HAKASETEST_PASS'))
    cur = conn.cursor()
    sql = '''insert into {MD_RECENT_UPDATE} (manga_id, chapter_id, chapter_num, chapter_timestamp, updated_time) values (%s, %s, %s, %s, %s)
                on duplicate key update
                    chapter_id=values(chapter_id), 
                    chapter_num=values(chapter_num), 
                    chapter_timestamp=values(chapter_timestamp),
                    updated_time=values(updated_time)'''.format(MD_RECENT_UPDATE=Variable.get('MD_RECENT_UPDATE'))
    cur.executemany(sql, recent_update)
    conn.commit()
    conn.close()

    if manga_title_update != []:
        twilio_cli = Client(twilio_sid, twilio_token)
        twilio_cli.messages.create(body=notif_msg, from_=twilio_phone_source, to=twilio_phone_target)
except:
    print('fail to write {MD_RECENT_UPDATE}'.format(MD_RECENT_UPDATE=Variable.get('MD_RECENT_UPDATE')))
    print('fail to send SMS')