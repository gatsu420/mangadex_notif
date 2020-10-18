import pymysql
import requests
from datetime import datetime
import time
from twilio.rest import Client
import os

class DBConnector:
    def __init__(self):
        #self.var_1 = var_1
        self.host = os.environ['HAKASETEST_HOST']
        self.user = os.environ['HAKASETEST_USER']
        self.password = os.environ['HAKASETEST_PASS']
        self.md_manga = os.environ['MD_MANGA']
        self.md_recent_update = os.environ['MD_RECENT_UPDATE']

    def get_manga_id(self):
        conn = pymysql.connect(host = self.host, 
                                user = self.user,
                                password = self.password)
        cur = conn.cursor()
        cur.execute(f'select manga_id from {self.md_manga}')
        conn.close()

        return cur.fetchall()

    def get_initial_update(self):
        conn = pymysql.connect(host = self.host, 
                                user = self.user,
                                password = self.password)
        cur = conn.cursor()
        cur.execute(f'select manga_id, chapter_id from {self.md_recent_update}')
        conn.close()

        return cur.fetchall()

class RecentChapter:
    def __init__(self):
        self.manga_id = DBConnector().get_manga_id()
        self.api_prefix = 'https://mangadex.org/api/?id='
        self.api_suffix = '&type=manga'

    def get_recent_chapter(self):
        chapter_list = []
        tidy_manga_id = []
        recent_chapter_id = []
        recent_chapter_num = []
        recent_chapter_timestamp = []

        for i in range(len(self.manga_id)):
            gb_chapter_timestamp = [] #flush tuple for every manga_id
            
            chapter_list.append(list(requests.get(self.api_prefix + str(self.manga_id[i][0]) + self.api_suffix).json()['chapter']))
            chapter = requests.get(self.api_prefix + str(self.manga_id[i][0]) + self.api_suffix).json()['chapter']
            tidy_manga_id.append(str(self.manga_id[i][0]))
        
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

        time.sleep(2)

        return recent_chapter_id, recent_chapter_num, recent_chapter_timestamp

class RecentUpdateOffsetChecker:
    def __init__(self):
        self.initial_update = DBConnector().get_initial_update()
        self.recent_chapter = RecentChapter().get_recent_chapter()

    def get_initial_chapter_id(self):
        initial_chapter_id = []

        for i in range(len(self.initial_update)):
            initial_chapter_id.append(self.initial_update[i][1])

        return initial_chapter_id

    def get_chapter_id_update(self, initial_chapter_id):
        for i in range(len(self.recent_chapter)):
            if int(self.recent_chapter[i][1]) not in initial_chapter_id:
                chapter_id_update.append(self.recent_chapter[i][1])
        
        return chapter_id_update

aa = DBConnector()
print(aa.get_manga_id())
print(aa.host)
print(len(RecentChapter().manga_id))
print(RecentChapter().get_recent_chapter())
print(DBConnector().get_recent_update())
p