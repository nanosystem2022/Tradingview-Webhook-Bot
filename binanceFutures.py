import json
import time
import ccxt
import random
import string
from flask import Flask, request

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

app = Flask(__name__)

class Bot:

    def __init__(self):
        pass

    def create_string(self):
        N = 7
        res = ''.join(random.choices(string.ascii_uppercase +
                                     string.digits, k=N))
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

    def run(self, data):
        if data['action'] == 'close_short' or data['action'] == 'close_long':
            print("Closing Position")
            self.close_position(symbol=data['symbol'])
        else:
            print("Placing Order")
            self.create_string()
            params = {
                "newClientOrderId": self.clientId,
                'reduceOnly': False
            }

            if data['type'] == 'Limit':
                exchange.create_order(data['symbol'], data['type'], data['side'], float(data['qty']),
                                      price=float(data['price']), params=params)
            else:
                exchange.create_order(data['symbol'], data['type'], data['side'], float(data['qty']),
                                      params=params)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    print(data)
    bot = Bot()
    bot.run(data)
    return {
        'status': 'ok'
    }

if __name__ == '__main__':
    app.run(debug=False)
