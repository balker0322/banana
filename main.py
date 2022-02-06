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

    def strategy(self, open, close, high, low, volume):
        print(close[-1])

def main():
    Bot().run()
    # Bot().backtest()


def ws_test():
    ws = BinanceFuturesWs('binanceaccount2')
    ws.start()
    while True:
        pass


class MiniTickerObserver(ar.BinanceFutures):

    ohlcv_len=5
    
    def __init__(self, pair, bin_size, controller):
        self.account='binanceaccount2'
        self.pair=pair
        self.bin_size=bin_size
        self.controller=controller
        self.__bind_ws(controller.ws)

    def __bind_ws(self, ws):
        ws.bind_24hr_mini_ticker(self.pair, self.__update_data)

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

            # ar.util.logger.info(f"Initial Buffer Fill - Last Candle: {self.data.iloc[-1].name}")
    
    def __update_next_action_timestamp(self):
        current_timestamp=int(datetime.now().timestamp())
        delta=ar.util.delta(self.bin_size).seconds
        self.next_action_timestamp=(int(float(current_timestamp)/float(delta))+1)*delta
    
    def __update_last_candle(self, new_data):
        nd=new_data.iloc[0]
        last_data_timestamp=self.data.iloc[-1].name
        self.data.loc[last_data_timestamp, 'close']=nd['close']
        if float(nd['close'])>float(self.data.loc[last_data_timestamp, 'high']):
            self.data.loc[last_data_timestamp, 'high']=nd['close']
        if float(nd['close'])<float(self.data.loc[last_data_timestamp, 'low']):
            self.data.loc[last_data_timestamp, 'low']=nd['close']
        if float(nd['volume'])>float(self.volume_ref):
            delta_v=nd['volume']-self.volume_ref
            self.data.loc[last_data_timestamp, 'volume']+=delta_v

    def __update_data(self, action, new_data):
     
        if self.data is None:
            self.__initialize_candle_data()
            self.__update_next_action_timestamp()
            self.on_data_init()

        else:
            new_data_timestamp=new_data.iloc[0].name.timestamp()

            # print(f'**{new_data_timestamp}\t{self.next_action_timestamp}')
            if new_data_timestamp < self.next_action_timestamp:
                self.__update_last_candle(new_data)

            else:
                self.__update_next_action_timestamp()
                index=datetime.fromtimestamp(self.next_action_timestamp).astimezone(UTC)

                self.on_action_timestamp()

                nd_close=new_data.iloc[0]['close']
                self.data.loc[index]={
                    'open':nd_close,
                    'high':nd_close,
                    'low':nd_close,
                    'close':nd_close,
                    'volume':0.0,
                }
                self.data=self.data[-self.ohlcv_len:]
                
        self.volume_ref=new_data.iloc[0]['volume']
        self.on_data_change()
            
    def on_data_init(self):
        pass
            
    def on_data_change(self):
        pass
            
    def on_action_timestamp(self):
        pass

    def strategy(self, open, close, high, low, volume):
        pass


class PairObserver(MiniTickerObserver):
            
    def on_data_init(self):
        open = self.data['open'].values
        close = self.data['close'].values
        high = self.data['high'].values
        low = self.data['low'].values
        volume = self.data['volume'].values  
        self.strategy(open[:-1], close[:-1], high[:-1], low[:-1], volume[:-1])
        self.__announce=True

            
    def on_data_change(self):
        # print(self.volume_ref)

        open = self.data['open'].values
        close = self.data['close'].values
        high = self.data['high'].values
        low = self.data['low'].values
        volume = self.data['volume'].values  
        self.strategy(open, close, high, low, volume)
        # o=open[-1]
        # c=close[-1]
        # h=high[-1]
        # l=low[-1]
        # v=volume[-1]
        # print(f'__update_data {self.pair}:\tclose:{c}\topen:{o}\thigh:{h}\tlow:{l}\tvolume:{v}')

        # percent_change=((close[-1]/open[-1])-1.0)*100.0
        # if abs(percent_change) > 2.00 and not self.__stop_announce:
        #     ar.util.logger.info('{}: {:.2f}%'.format(self.pair, percent_change))
            
    def on_action_timestamp(self):

        open = self.data['open'].values
        close = self.data['close'].values
        high = self.data['high'].values
        low = self.data['low'].values
        volume = self.data['volume'].values  
        self.__announce=True
        self.strategy(open, close, high, low, volume)
        self.__announce=True

    def strategy(self, open, close, high, low, volume):
        percent_change=((close[-1]/open[-1])-1.0)*100.0
        if self.__announce:
            if abs(percent_change) > 1.00:
                ar.util.logger.info('{}: {:.2f}%'.format(self.pair, percent_change))
            if abs(percent_change) > 2.00:
                ar.util.notify('{}: {:.2f}%'.format(self.pair, percent_change))
            self.__announce=False



import threading
from time import sleep
import pandas as pd

class Controller:

    def __init__(self):
        self.ws=BinanceFuturesWsMiniTickerAll()
        bin_size='15m'
        self.all_pairs=self.get_all_pairs()
        self.pair_observers={}
        print(f'pair count: {len(self.all_pairs)}')
        for pair in self.all_pairs:
            pair_observer=PairObserver(pair, bin_size, self)
        self.count_start=False
        ar.util.notify(f'starting')

    def get_all_pairs(self):
        return [x for x in BinanceFutures().get_all_pairs() if x.endswith('USDT')]

    def run(self):
        self.ws.start()
        while True:
            pass


def main2():
    c = Controller()
    c.run()




class BinanceFuturesWsMiniTickerAll(ar.BinanceFuturesWs):

    def __init__(self, test=False):
        """
        constructor
        """
        self.account = 'binanceaccount2'
        self.testnet = test  

    def get_endpoint_trail(self):
        return '/!miniTicker@arr'
    
    def bind_24hr_mini_ticker(self, pair, func):
        self.handlers[f'24hrMiniTicker_{pair.lower()}']=func



if __name__=="__main__":
    # ar.telegrambot.main()
    main2()
    # BinanceFuturesWsMiniTickerAll().start()
    # # x=ar.util.WebsocketConnectionMonitor()
    # # x.start_monitor()
    # while True:
    #     pass