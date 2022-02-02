# from cgitb import handler
import alpha_rptr as ar


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

    ohlcv_len=100
    
    def __init__(self, pair, bin_size, controller):
        self.account='binanceaccount2'
        self.pair=pair
        self.bin_size=bin_size
        self.controller=controller
    
    def on_update(self, action, new_data):
        # print(self.pair, self.bin_size)
        super().update_data(action, new_data)

    def strategy(self, open, close, high, low, volume):
        delta=((close[-1]/open[-1])-1.0)*100.0
        if abs(delta) > 1.5:
            ar.util.logger.info(f'{self.pair}: {delta:.2f}%')
        # ar.util.logger.info('{}: {%2f}%'.format(self.pair, ((close[-1]/open[-1])-1.0)*100.0))
        # self.controller.update_df(self.pair, self.data)


import threading
from time import sleep
import pandas as pd

class Controller:

    def __init__(self):
        self.ws=BinanceFuturesWs('binanceaccount2')
        bin_size='15m'
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
        return
        print(msg.keys(), len(msg))
        print(type(msg['stream']))
        print(type(msg['data']), len(msg['data']))
        for key in msg['data'][0].keys():
            print(key, msg['data'][0][key])


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
    main2()
    # BinanceFuturesWsAll().start()
    # x=ar.util.WebsocketConnectionMonitor()
    # x.start_monitor()
    # while True:
        # pass