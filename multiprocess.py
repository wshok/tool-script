import queue
import threading
import time
import pymysql
import requests
import redis
import random
import hashlib
import asyncio
from aiohttp import ClientSession

exitFlag = 0
offset = 0
imgurl = 'http://s3.amazonaws.com/'

traceid = hashlib.md5(str(time.time()).encode()).hexdigest()

try:
    db = pymysql.connect("192.168.0.1", "user", "password", "dbname", charset='utf8', connect_timeout=10, read_timeout=10)
    cursor = db.cursor()

    r = redis.Redis(host='127.0.0.1', port=6379, db=15, password='test')
except Exception as e:
    log('connect db or redis excepte \n %s' % e)
    exit()


async def send(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            return response.status

class myThread (threading.Thread):

    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
        self.redis = r

    def run(self):
#        print ("开启线程：" + self.name)
        process_data(self.name, self.q)
#        print ("退出线程：" + self.name)

def process_data(threadName, q):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            data = q.get()
            queueLock.release()
            # do something...
            if myThread.offset < data['up_time']:
                myThread.offset = data['up_time']
                r.set('check-images:feeltimes:offset', myThread.offset)

            if (data['img'] is None) or len(data['img']) < 1 or (data['img'][-3:] != 'jpg'):
                r.zadd('check-images:feeltimes:err-image-sku', {data['shop_id']:1})
                continue

            try:
                response = requests.get(imgurl + data['img'], timeout=(3, 10))
                if (response.status_code != 200):
                    r.zadd('check-images:feeltimes:err-image-sku', {data['shop_id']:1})
            except Exception as err:
                r.zadd('check-images:feeltimes:err-image-sku', {data['shop_id']:1})
                log('check-images error, request timeout \n %s' % err)
        else:
            queueLock.release()
        time.sleep(0.01)


def queryRows():
    offset = r.get('check-images:feeltimes:offset')

    if (offset is None):
        offset = 0
    else:
        offset = int(offset.decode())
        if offset < 1:
            offset = 1

    myThread.offset = offset
 
    if int(time.time()) - offset < 3600:
        return []
 
    try:
        page_size = 5
        site_id = 0

        sql = 'SELECT shop_id, img, thumb,up_time FROM `table`' \
        ' WHERE site_id = %d and up_time > %d ORDER BY up_time LIMIT %d' % (site_id, offset, page_size)

        cursor.execute(sql)
        rows = cursor.fetchall()
    except Exception as e:
        log('queryRows excepte, sql: %s \n %s' % (sql, e))
        return []
    
    return rows

def queryErrorImages():
    ranges = r.zrange('check-images:feeltimes:err-image-sku', 0, -1)
    ranges_len = len(ranges)
    if ranges_len < 1:
        log('queryErrorImages empty')
        return
    key = random.randint(0, ranges_len-1)

    skus = r.zrange('check-images:feeltimes:err-image-sku', key, key)

    try:
        site_id = 0

        sql = 'SELECT shop_id, img, thumb, up_time FROM `table`' \
        ' WHERE site_id = %d and shop_id in (%s)' % (site_id, ','.join(i.decode() for i in skus))

        cursor.execute(sql)
        rows = cursor.fetchall()
    except Exception as e:
        log('queryErrorImages db exception, sql: %s \n %s' % (sql, e) )     # 写入
        return

    response = []
    for row in rows:
        if row[1] is not None:
            response.append(asyncio.ensure_future(send(imgurl + row[1])))
        else:
            log('not remove data, %s' % row[0])
            return
        if row[2] is not None: 
            response.append(asyncio.ensure_future(send(imgurl + row[2])))
        else:
            log('not remove data, %s' % row[0])
            return

    try:
        result = loop.run_until_complete(asyncio.gather(*response))
    except Exception as e:
        log('queryErrorImages network exception: %s\n' % e)
        return

    for i in result:
       if i != 200:
           log('not remove data, %s' % rows[0][0])
           return

    for sku in skus:
        r.zrem('check-images:feeltimes:err-image-sku', sku.decode())

    log('remove data, %s' % (','.join(i.decode() for i in skus)))     # 写入


def log(msg):
    with open('/home/code/log.txt','a') as file_handle:   # .txt可以不自己新建,代码会自动新建
        file_handle.write('%s, %s, %s' % (time.strftime("%Y-%m-%d %H:%M:%S %Z"), traceid, msg))
        file_handle.write('\n')
    return True

# init
threadList = ["Thread-1", "Thread-2", "Thread-3"]
taskList = queryRows()

if len(taskList) < 1:
    log('empty data, offset: %d' % (myThread.offset))     # 写入

    loop = asyncio.get_event_loop()
    queryErrorImages()
    exit()

queueLock = threading.Lock()
workQueue = queue.Queue(15)
threads = []
threadID = 1


# 创建新线程
for tName in threadList:
    thread = myThread(threadID, tName, workQueue)
    thread.start()
    threads.append(thread)
    threadID += 1

# 填充队列
queueLock.acquire()
for task in taskList:
    t = {
        # shop_id, img, thumb,up_time
        'shop_id': task[0],
        'img': task[1],
        'up_time': task[3]
    }
    workQueue.put(t)

for task in taskList:
    t = {
        # shop_id, img, thumb,up_time
        'shop_id': task[0],
        'img': task[2],
        'up_time': task[3]
    }
    workQueue.put(t)    
queueLock.release()

# 等待队列清空
while not workQueue.empty():
    pass

# 通知线程是时候退出
exitFlag = 1

# 等待所有线程完成
for t in threads:
    t.join()
#print ("退出主线程")

db.close()

log('run data end, offset: %d' % (myThread.offset))     # 写入

