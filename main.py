import alpha_rptr as ar


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

    pass

    # def __update_ohlcv(self, action, new_data):
    #     print(new_data)


class Bot(ar.Sample):
    
    def __init__(self):
        self.exchange=BinanceFutures(account='binanceaccount2', pair='BTCUSDT')
        # self.test_exchange=BinanceFuturesBackTest(account='binanceaccount2', pair='BTCUSDT')
        self.bin_size='1d'

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

    # def strategy(self, open, close, high, low, volume):
    #     pass
    #     print(close[-1])
    #     # print(open, close, high, low, volume)

    # def ohlcv_len(self):
    #     """
    #     The length of the OHLC to the strategy
    #     """
    #     return 10


def main():
    # Bot().run()
    Bot().backtest()



if __name__=="__main__":
    main()