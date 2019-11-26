
import json
import threading
import time
import mysql.connector
import gzip
import websocket
import redis
import pickle
import zlib
import numpy
class DepthInfo:
    def __init__(self):
        self.up_time=0
        self.forbuy=[]
        self.forsell=[]
        self.order_coin=''
        self.base_coin=''
    def dump(self):
        print('==================')
        print(self.up_time)
        print(self.forbuy)
        print(self.forsell)
        print(self.order_coin)
        print(self.base_coin)

class myThread (threading.Thread):
    def __init__(self, coin_list):
        threading.Thread.__init__(self)
        self.coin_list = coin_list
        self.coin_dict = {}
        self.ws = websocket.WebSocket()
        self.timer = None
        self.redis_db = redis.Redis(host='localhost', port=6379)
        self.info = DepthInfo()

    def connect(self):
        self.ws.connect("wss://real.okex.com:8443/ws/v3", http_proxy_host="127.0.0.1", http_proxy_port=50617)
    def on_recv(self, str):
        print("recive:"+str)
        self.reset_timer()
        json_data = json.loads(str)
        if 'event' not in json_data and json_data['action'] == 'partial':
            self.info.order_coin = json_data['data'][0]['instrument_id'].split("-")[0]
            self.info.base_coin = json_data['data'][0]['instrument_id'].split("-")[1]
            self.info.forbuy = numpy.array(json_data['data'][0]['bids'])[:,0:2].tolist()
            self.info.forsell = numpy.array(json_data['data'][0]['asks'])[:,0:2].tolist()
            self.info.up_time = json_data['data'][0]['timestamp']
            self.info.dump()
            exit()
        '''
        {"table":"spot/depth","action":"partial","data":[{"instrument_id":"BTC-USDT","asks":[["7091.8","2.03619305","4"],["7092.4","2","1"],["7092.6","0.00282049","1"],["7092.8","0.01","1"],["7092.9","0.001","1"],["7093.5","0.05318","2"],["7093.6","2.1028199","3"],["7093.7","0.0082","1"],["7093.8","0.00222058","1"],["7093.9","0.3","1"],["7094.4","0.2","1"],["7094.5","0.044","1"],["7094.7","2.03503541","2"],["7094.8","0.29","2"],["7095","0.1","1"],["7095.1","2","1"],["7095.5","0.813","1"],["7095.6","0.3","1"],["7095.8","0.0497179","1"],["7096","0.06877058","1"],["7096.7","1.284","2"],["7096.8","0.20414356","1"],["7097.4","0.28884094","1"],["7097.5","0.2","1"],["7097.7","0.04","1"],["7097.8","0.51932416","1"],["7098.1","0.02819483","1"],["7098.3","0.03","1"],["7098.4","5.1","1"],["7098.5","0.3","1"],["7098.6","1.12823123","1"],["7098.7","0.3","1"],["7099","0.99396707","4"],["7099.4","1.4101552","2"],["7099.5","0.0558562","1"],["7099.6","0.05638965","1"],["7099.7","0.074","1"],["7099
        self.reset_timer()
        json_data = json.loads(str)
        #对ping pong 的处理
        if 'ping' in json_data:
            send_data = {'pong':json_data['ping']}
            self.send_data(send_data)
        elif 'ch' in json_data:
            print(json_data['ch'].split(".")[1])
            print(self.coin_dict[json_data['ch'].split(".")[1].upper()])
            key = "0_"+self.coin_dict[json_data['ch'].split(".")[1].upper()][0]+"_"+self.coin_dict[json_data['ch'].split(".")[1].upper()][1]
            self.redis_db.set(key, pickle.dumps(json_data))
            
        '''
    def shutdown(self):
        print("shutdown")
        self.ws.shutdown()
        self.ws.close()
    def send_data(self, obj):
        str = json.dumps(obj)
        print('send:'+str)
        self.ws.send(str.encode())
    def sub_depth(self):
        for item in self.coin_list:
            print(item)
            symbel = item[0].upper()+item[1].upper()
            self.coin_dict[symbel] = (item[0].upper(), item[1].upper())
            self.send_data({"op": "subscribe", "args": ["spot/depth:%s-%s"%(item[0].upper(),item[1].upper())]})
    #重置超时时间
    def reset_timer(self):
        if self.timer and self.timer.isAlive():
            self.timer.cancel()
        self.timer = threading.Timer(6, self.shutdown)
        self.timer.start()
    def run(self):
        while True:
            #try:
                print('-------0.1')
                self.connect()
                print('-------0.2')
                #启动定时器
                if self.ws.connected:
                    self.reset_timer()
                #设置要监听的币种
                print('-------1')
                self.sub_depth()
                print('-------2')
                while True:
                    print('-------3')
                    recv_data = self.ws.recv()
                    print('-------4')
                    if recv_data == '':
                        print("huobi recive 空")
                        break
                    decompress = zlib.decompressobj(
                            -zlib.MAX_WBITS  # see above
                    )
                    inflated = decompress.decompress(recv_data)
                    inflated += decompress.flush()
                    self.on_recv(inflated.decode())
            #except:
                print("huobi socket error")
                pass

coin_list=[("BTC","USDT")]
thread_ = myThread(coin_list)
thread_.start()
thread_.join()
print("exit")
