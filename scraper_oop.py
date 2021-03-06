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

    def get_master(self):
        conn = pymysql.connect(host = self.host, 
                                user = self.user,
                                password = self.password)
        cur = conn.cursor()
        cur.execute(f'select * from {self.md_manga}')
        conn.close()

        return cur.fetchall()

    def insert_recent_update(self):
        recent_update = list(zip(
            RecentChapter().get_recent_chapter()[3],
            RecentChapter().get_recent_chapter()[0],
            RecentChapter().get_recent_chapter()[1],
            RecentChapter().get_recent_chapter()[2],
            RecentChapter().get_recent_chapter()[4]
            ))

        conn = pymysql.connect(host = self.host, 
                                user = self.user,
                                password = self.password)
        cur = conn.cursor()
        sql = f'''insert into {self.md_recent_update} (manga_id, chapter_id, chapter_num, chapter_timestamp, updated_time) values (%s, %s, %s, %s, %s)
                    on duplicate key update
                        chapter_id=values(chapter_id), 
                        chapter_num=values(chapter_num), 
                        chapter_timestamp=values(chapter_timestamp),
                        updated_time=values(updated_time)'''
        cur.executemany(sql, recent_update)
        conn.commit()
        conn.close()

class RecentChapter:
    def __init__(self):
        self.manga_id = DBConnector().get_manga_id()
        self.api_prefix = 'https://mangadex.org/api/?id='
        self.api_suffix = '&type=manga'
        self.tidy_manga_id = []

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
            self.tidy_manga_id += tidy_manga_id
        
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

        return recent_chapter_id, recent_chapter_num, recent_chapter_timestamp, tidy_manga_id, [str(datetime.now())] * len(recent_chapter_id)

class RecentUpdateOffsetChecker:
    def __init__(self):
        self.initial_update = DBConnector().get_initial_update()
        self.master = DBConnector().get_master()
        self.recent_update = RecentChapter().get_recent_chapter()[0]
        self.tidy_manga_id = RecentChapter().get_recent_chapter()[3]
        self.initial_chapter_id = []
        self.manga_id_update = []
        self.chapter_id_update = []

    def get_initial_chapter_id(self):
        initial_chapter_id = []

        for i in range(len(self.initial_update)):
            initial_chapter_id.append(self.initial_update[i][1])

        self.initial_chapter_id += initial_chapter_id

        return initial_chapter_id

    def get_chapter_id_update(self):
        chapter_id_update = []

        for i in range(len(self.recent_update)):
            if int(self.recent_update[i]) not in self.get_initial_chapter_id():
                chapter_id_update.append(self.recent_update[i])

        return chapter_id_update

    def get_manga_id_update(self):
        manga_id_update = []

        for i in range(len(self.get_chapter_id_update())):
            if self.get_chapter_id_update()[i] in self.recent_update:
                manga_id_update.append(self.tidy_manga_id[self.recent_update.index(self.get_chapter_id_update()[i])])

        return manga_id_update
        
    def get_master_manga(self):
        master_manga_id = []
        master_manga_title = []

        for i in range(len(self.master)):
            master_manga_id.append(self.master[i][0])
            master_manga_title.append(self.master[i][1])

        return master_manga_id, master_manga_title

    def get_manga_title_update(self):
        manga_title_update = []

        for i in range(len(self.get_manga_id_update())):
            if int(self.get_manga_id_update()[i]) in self.get_master_manga()[0]:
                manga_title_update.append(self.get_master_manga()[1][self.get_master_manga()[0].index(int(self.get_manga_id_update()[i]))])

        return manga_title_update

class TwilioService:
    def __init__(self):
        self.twilio_sid = os.environ['TWILIO_SID']
        self.twilio_token = os.environ['TWILIO_TOKEN']
        self.twilio_phone_source = os.environ['TWILIO_PHONE_SOURCE']
        self.twilio_phone_target = '+6285706106941'

    def send_notif(self):
        notif_msg = 'updated manga = {MANGA_UPDATE}, with total updated chapter={CHAPTER_UPDATE}'.format(
                MANGA_UPDATE=str(RecentUpdateOffsetChecker().get_manga_title_update())[1:-1], 
                CHAPTER_UPDATE=len(RecentUpdateOffsetChecker().get_chapter_id_update())
                )

        if RecentUpdateOffsetChecker().get_manga_title_update() != []:
            twilio_cli = Client(self.twilio_sid, self.twilio_token)
            twilio_cli.messages.create(body=notif_msg, from_=self.twilio_phone_source, to=self.twilio_phone_target)

# aa = DBConnector()
# print(aa.get_manga_id())
# print(aa.host)
# print(len(RecentChapter().manga_id))
print(RecentChapter().get_recent_chapter()[0])
print(RecentChapter().get_recent_chapter())
# print(DBConnector().get_initial_update())
# print(RecentUpdateOffsetChecker().get_initial_chapter_id())
# print(RecentUpdateOffsetChecker().recent_update)
# print(RecentUpdateOffsetChecker().get_manga_id_update())
# print(RecentUpdateOffsetChecker().get_manga_title_update())
print(DBConnector().insert_recent_update())
print(TwilioService().send_notif())