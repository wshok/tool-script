import os
import Queue
import threading
import time
import pymysql
import json
# import redis
import hashlib
import requests

starttime = time.time()

pwd = os.getcwd()

traceid = hashlib.md5(str(time.time()).encode()).hexdigest()

class Db(object):
    def __init__(self, host=None, username=None, pwd=None, dbname=None):
        self.pool = {}
        self.host = host
        self.username = username
        self.pwd = pwd
        self.dbname = dbname

    def get_instance(self):
        name = threading.current_thread().name
        if name not in self.pool:
            conn = pymysql.connect(self.host, self.username, self.pwd, self.dbname)
            self.pool[name] = conn
        return self.pool[name]


class Q(object):
    wq = Queue.Queue(101)


class Productor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.db = Db("192.168.0.1", "root", "123456", "testdb")
        self.taskList = []
        self.lock = threading.Lock()
        self.field = 'acnh'
        self.page = 0
        self.count = 1

    def run(self):
        while (self.count):
            self.queryList()

            for task in self.taskList[:]:
                if Q().wq.full():
                    time.sleep(0.05)
                #self.lock.acquire()
                Q().wq.put(task)
                #self.lock.release()

    def queryList(self):
        self.taskList = []
        sql = 'SELECT `image` FROM `table` WHERE field = \'%s\' limit %d, 100' % (self.field, self.page * 100)
        try:
            db = self.db.get_instance()
            cursor = db.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
        except Exception as e:
            log('query-sql-except, sql: %s \n %s' % (sql, e))
            return []

        for row in rows:
            self.taskList.append(row[0])

        self.page += 1
        if (len(rows) < 100):
            self.count = 0

        log('page: %d, count: %d' % (self.page, self.count))


class Consumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # self.db = Db("192.168.0.1", "root", "123456", "testdb")
        # self.r = redis.Redis(host='127.0.0.1', port=6379, db=0, password='')
        self.lock = threading.Lock()
        self.img = ''

    def run(self):
        self.process_data()

    def process_data(self):
        while not Q().wq.empty():
            self.lock.acquire()
            self.img = Q().wq.get()
            self.lock.release()
            self.download_img()

    def download_img(self):
        header = {
            "Cache-Control": "no-cache", 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
        }

        domain = 'https://img-domain.com'

        try:
            r = requests.get(domain + self.img, headers=header, stream=True)
            if r.status_code == 200:
                # mkdir
                path = os.path.dirname(self.img)

                if not os.path.exists('.'+path):
                    os.makedirs('.'+path)
                open('.' + self.img, 'wb').write(r.content)
            else:
                log("donwload-request-error: %s, %s\n" % (self.img, domain))
            del r
        except Exception as e:
            log("donwload-request-except:" + str(e))


def log(msg):
    fp = pwd + '/log.txt'
    with open(fp, 'a') as file_handle:
        file_handle.write('%s, %s, %s' % (time.strftime("%Y-%m-%d %H:%M:%S %Z"), traceid, msg))
        file_handle.write('\n')
    return True

# init
threadNum = 5
threads = []

p = Productor()
p.start()

time.sleep(0.1)

for i in range(threadNum):
    c = Consumer()
    c.start()
    threads.append(c)

for t in threads:
    t.join()

#print('run data end, time used: %.4f' % (time.time() - starttime))
log('run data end, time used: %.4f' % (time.time() - starttime))
