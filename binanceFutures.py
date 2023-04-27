import json
import time
import ccxt
import random
import string

with open('config.json') as config_file:
    config = json.load(config_file)

if config['EXCHANGES']['BINANCE-FUTURES']['TESTNET']:
    exchange = ccxt.binance({
        'apiKey': config['EXCHANGES']['BINANCE-FUTURES']['API_KEY'],
        'secret': config['EXCHANGES']['BINANCE-FUTURES']['API_SECRET'],
        'options': {
            'defaultType': 'future',
        },
        'urls': {
            'api': {
                'public': 'https://testnet.binancefuture.com/fapi/v1',
                'private': 'https://testnet.binancefuture.com/fapi/v1',
            }, }
    })
    exchange.set_sandbox_mode(True)
else:
    exchange = ccxt.binance({
        'apiKey': config['EXCHANGES']['BINANCE-FUTURES']['API_KEY'],
        'secret': config['EXCHANGES']['BINANCE-FUTURES']['API_SECRET'],
        'options': {
            'defaultType': 'future',
        },
        'urls': {
            'api': {
                'public': 'https://fapi.binance.com/fapi/v1',
                'private': 'https://fapi.binance.com/fapi/v1',
            }, }
    })

class Bot:
    def __init__(self):
        self.current_position = None

    def create_string(self):
        N = 7
        res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
        baseId = 'x-40PTWbMI'
        self.clientId = baseId + str(res)
        return

    def close_position(self, symbol):
        position = exchange.fetch_positions(symbol)[0]['info']['positionAmt']
        self.create_string()
        params = {
            "newClientOrderId": self.clientId,
            'reduceOnly': True
        }
        if float(position) > 0:
            print("Closing Long Position")
            exchange.create_order(symbol, 'Market', 'Sell', float(position), price=None, params=params)
        else:
            print("Closing Short Position")
            exchange.create_order(symbol, 'Market', 'Buy', -float(position), price=None, params=params)
        self.current_position = None

    def execute_signal(self, data):
        if data.get('action') == 'closelong':
            if self.current_position == 'long':
                self.close_position(data['symbol'])
        elif data.get('action') == 'closeshort':
            if self.current_position == 'short':
                self.close_position(data['symbol'])
        elif self.current_position is None:
            if data['side'] == 'Buy':
                self.current_position = 'long'
            else:
                self.current_position = 'short'
            self.run(data)

    def run(self, data):
        if 'type' in data:
            print("Placing Order")
            if 'price' in data:
                price = data['price']
            else:
                price = 0

            self.create_string()
            params = {
                "newClientOrderId": self.clientId,
                'reduceOnly': False
            }

            if data['type'] == 'Limit':
                exchange.create_order(data['symbol'], data['type'], data['side'], float(data['qty']),
                                      price=float(price), params=params)
            else:
                exchange.create_order(data['symbol'], data['type'], data['side'], float(data['qty']),
                                      price=None, params=params)
        else:
            print("Invalid Signal Data")
            return


def main():
    bot = Bot()

    while True:
        try:
            with open('signal.json') as signal_file:
                signal_data = json.load(signal_file)

            if signal_data:
                bot.execute_signal(signal_data)
                signal_data = None
                with open('signal.json', 'w') as signal_file:
                    json.dump(signal_data, signal_file)

            time.sleep(10)

        except Exception as e:
            print(e)
            time.sleep(10)


if __name__ == '__main__':
    main()
