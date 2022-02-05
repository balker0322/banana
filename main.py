# from cgitb import handler
import alpha_rptr as ar
from datetime import datetime, timezone, timedelta
from pytz import UTC


class BinanceFuturesWs(ar.BinanceFuturesWs):

    def __init__(self, account, test=False):
        """
        constructor
        """
        self.account = account
        self.testnet = test
        self.pair='btcusdt'
        self.kline_stream_names=[]

    def get_endpoint_trail(self):
        return '/'.join(self.kline_stream_names)

    def attach(self, kline_observer):
        kline_stream_name=f'{kline_observer.pair.lower()}@kline_{kline_observer.bin_size}'
        self.kline_stream_names.append(kline_stream_name)
        self.bind_kline(kline_observer.pair, kline_observer.bin_size, kline_observer.on_update)
    
    def bind_kline(self, pair, bin_size, func):
        self.handlers[f'{pair.lower()}_{bin_size.lower()}']=func



class BinanceFuturesBackTest(ar.BinanceFuturesBackTest):
    
    def download_data_to_file(
        self,
        bin_size,
        start_time,
        end_time,
        file,
    ):
        data = super().download_data(bin_size, start_time, end_time)
        self.file=file
        file_destination=self.__get_file()
        self.save_csv(data=data, file=file_destination)


class BinanceFutures(ar.BinanceFutures):

    def __init__(self):
        self.account='binanceaccount2'
        self.__init_client()

    def get_all_pairs(self):
        self.__init_client()
        return [x['symbol'] for x in self.client.futures_exchange_info()[0]['symbols']]

    # def __update_ohlcv(self, action, new_data):
    #     print(new_data)


class Bot(ar.Sample):
    
    def __init__(self):
        self.exchange=BinanceFutures(account='binanceaccount2', pair='BTCUSDT')
        # self.test_exchange=BinanceFuturesBackTest(account='binanceaccount2', pair='BTCUSDT')
        self.bin_size='1m'
        self.exchange.hook=self.hook
    
    def hook(self, df):
        print(f'df len: {len(df)}')
        print(df.iloc[-1])

    def run(self):
        self.exchange.ohlcv_len = self.ohlcv_len()
        self.exchange.on_update(self.bin_size, self.strategy)
        while True:
            pass
    
    def download_data_to_file(self, file, start, end):
        self.test_exchange.download_data_to_file(
            bin_size=self.bin_size,
            start_time=start,
            end_time=end,
            file=file,
        )
    
    def backtest(self, file):
        self.exchange=BinanceFuturesBackTest(account='binanceaccount2', pair='BTCUSDT', file=file)
        self.exchange.ohlcv_len = 20
        self.exchange.on_update(self.bin_size, self.strategy)
        self.exchange.show_result()
        # while True:
        #     pass

    # def 

    def strategy(self, open, close, high, low, volume):
        print(close[-1])
        # print(open, close, high, low, volume)

    # def ohlcv_len(self):
    #     """
    #     The length of the OHLC to the strategy
    #     """
    #     return 10

def main():
    Bot().run()
    # Bot().backtest()


def ws_test():
    ws = BinanceFuturesWs('binanceaccount2')
    ws.start()
    while True:
        pass

def plot_ani():
    import matplotlib.pyplot as plt
    import numpy as np
    from time import sleep
    # import matplotlib.pyplot as plt
    # import numpy as np
    # print('plot_ani')

    # plt.ion()
    # for i in range(50):
    #     y = np.random.random([10,1])
    #     plt.plot(y)
    #     plt.draw()
    #     plt.pause(0.0001)
    #     print('plot_ani')
    #     plt.clf()
    
    import matplotlib.pyplot as plt
    plt.plot([1, 2, 3, 4])
    plt.ylabel('some numbers')
    plt.show()
    while True:
        pass


class PairObserver(ar.BinanceFutures):

    ohlcv_len=5
    
    def __init__(self, pair, bin_size, controller):
        self.account='binanceaccount2'
        self.pair=pair
        self.bin_size=bin_size
        self.controller=controller

    def __initialize_candle_data(self):
            end_time = datetime.now(timezone.utc)
            start_time = end_time - self.ohlcv_len * ar.util.delta(self.bin_size)
            self.data = self.fetch_ohlcv(self.bin_size, start_time, end_time)
            
            # The last candle is an incomplete candle with timestamp
            # in future
            if(self.data.iloc[-1].name > end_time):
                last_candle = self.data.iloc[-1].values # Store last candle
                self.data = self.data[:-1] # exclude last candle
                self.data.loc[end_time.replace(microsecond=0)] = last_candle #set last candle to end_time

            ar.util.logger.info(f"Initial Buffer Fill - Last Candle: {self.data.iloc[-1].name}")
    
    def __update_next_action_timestamp(self):
        current_timestamp=int(datetime.now().timestamp())
        delta=ar.util.delta(self.bin_size).seconds
        self.next_action_timestamp=int(float(current_timestamp)/float(delta))+delta
    
    def __update_last_candle(self, new_data):
        self.data.iloc[-1]['close']=new_data['close']
        if new_data['close']>self.data.iloc[-1]['high']:
            self.data.iloc[-1]['high']=new_data['close']
        if new_data['close']<self.data.iloc[-1]['low']:
            self.data.iloc[-1]['low']=new_data['close']
        if new_data['volume']>self.volume_ref:
            self.data.iloc[-1]['volume']=new_data['volume']-self.volume_ref


    def __update_data(self, action, new_data):
     
        if self.data is None:
            self.__initialize_candle_data()
            self.__update_next_action_timestamp()

        else:
            new_data_timestamp=new_data.name.timestamp()

            if new_data_timestamp < self.next_action_timestamp:
                self.__update_last_candle(new_data)

            else:
                self.data.loc[new_data.name]={
                    'open':new_data['close'],
                    'high':new_data['close'],
                    'low':new_data['close'],
                    'close':new_data['close'],
                    'volume':0.0,
                }
                self.data=self.data[-self.ohlcv_len:]
                self.__update_next_action_timestamp()

        self.volume_ref=new_data['volume']

   
    
    def on_update(self, action, new_data):
        '''
        state 1: data is empty
        - download candle_stick(bin_size, ohlcv_len) -> self.data
        - save new_data['volume'] -> volume_ref
        - save new_data['close] -> market_price
        - calculate next action time stamp -> next_action_time_stamp

        state 2: new_data_time_stamp < next_action_time_stamp
        - save new_data['close] -> market_price
        - update_last_candle(new_data)
        - save new_data['volume'] -> volume_ref

        state 3: new_data_time_stamp > next_action_time_stamp
        - save new_data['close] -> market_price
        - create_new_candle(market_price)
        - recalculate next_action_time_stamp
        - save new_data['volume'] -> volume_ref
        - append new_cs to self.data
        - self.data[-ohlcv_len:] -> self.data

        '''
        super().update_data(action, new_data)

    def strategy(self, open, close, high, low, volume):
        delta=((close[-1]/open[-1])-1.0)*100.0
        if abs(delta) > 0.5:
            info=f'{self.pair}: {delta:.2f}%'
            ar.util.logger.info(info)
            ar.util.notify(info)
        # ar.util.logger.info('{}: {%2f}%'.format(self.pair, ((close[-1]/open[-1])-1.0)*100.0))
        # self.controller.update_df(self.pair, self.data)
    
    # def update_last_candle(self, new_data):
    #     '''
    #     - self.data[-1]['open'] -> new_cs['open']
    #     - new_data['close'] -> new_cs['close']
    #     - if new_data['close'] > self.data['high'] -> new_cs['high']
    #     - if new_data['close'] < self.data['low'] -> new_cs['low']
    #     - if new_data['volume'] > volume_ref, new_data['volume']-volume_ref -> new_cs['volume']
    #     - self.data[-1] w/ new_cs
    #     '''
    #     pass





import threading
from time import sleep
import pandas as pd

class Controller:

    def __init__(self):
        self.ws=BinanceFuturesWs('binanceaccount2')
        bin_size='1m'
        # self.all_pairs=self.get_all_pairs()[:5]
        self.all_pairs=self.get_all_pairs()
        self.pair_observers={}
        print(f'pair count: {len(self.all_pairs)}')
        for pair in self.all_pairs:
            pair_observer=PairObserver(pair, bin_size, self)
            self.ws.attach(pair_observer)
            self.pair_observers[pair]=pair_observer
        self.count_start=False

    def get_all_pairs(self):
        return [x for x in BinanceFutures().get_all_pairs() if x.endswith('USDT')]
    
    def start_count_countdown(self):
        self.count_start=True
        sleep(10)
        self.notify_analysis()
        self.count_start=False
    
    def update_df(self, pair, df):
        if not self.count_start:
            t = threading.Thread(target=self.start_count_countdown)   
            t.daemon = True
            t.start()

    def notify_analysis(self):
        df = self.create_df()
        print(df.head())
        # self.add_percent_change(df)
        # ar.util.logger.info('Completes')
    
    def create_df(self):
        df={
            'pair':[],
            'close':[],
            'open':[],
        }
        pairs=[]
        for pair, obj in self.pair_observers.items():
            try:
                # dummy_df:pd.DataFrame
                dummy_df = obj.data.iloc[:-1]
                df['pair'].append(pair)
                df['close'].append(dummy_df['close'].values[-1])
                df['open'].append(dummy_df['open'].values[-1])
                pairs.append(pair)
            except:
                continue
        return pd.DataFrame(df, index = pairs)



    def run(self):
        self.ws.start()
        while True:
            pass


def main2():
    c = Controller()
    c.run()




class BinanceFuturesWsAll(ar.BinanceFuturesWs):

    def __init__(self, test=False):
        """
        constructor
        """
        self.account = 'binanceaccount2'
        self.testnet = test
        # self.pair='btcusdt'
        # self.kline_stream_names=[]
        self.on_message_hook=self.on_message_handler
    
    def on_message_handler(self, msg):
        # return
        # print(msg['data'][0])
        # print(msg.keys(), len(msg))
        # print(type(msg['stream']))
        # print(type(msg['data']), len(msg['data']))
        # for key in msg['data'][0].keys():
        #     print(key, msg['data'][0][key])
        t=msg['data'][0]['E']
        print(t)
        # datetime.fromtimestamp(t/1000)
        print(int(datetime.fromtimestamp(t/1000).astimezone(UTC).timestamp()))

        print(datetime.fromtimestamp(t/1000).astimezone(UTC))
        print()

        # datetime.fromtimestamp(data[0]['timestamp']/1000).astimezone(UTC)    


    def get_endpoint_trail(self):
        return '/!miniTicker@arr'

    # def attach(self, kline_observer):
    #     kline_stream_name=f'{kline_observer.pair.lower()}@kline_{kline_observer.bin_size}'
    #     self.kline_stream_names.append(kline_stream_name)
    #     self.bind_kline(kline_observer.pair, kline_observer.bin_size, kline_observer.on_update)
    
    # def bind_kline(self, pair, bin_size, func):
    #     self.handlers[f'{pair.lower()}_{bin_size.lower()}']=func




# '!miniTicker@arr'




if __name__=="__main__":
    # ar.telegrambot.main()
    # main2()
    BinanceFuturesWsAll().start()
    # x=ar.util.WebsocketConnectionMonitor()
    # x.start_monitor()
    while True:
        pass