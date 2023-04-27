import json
from flask import Flask, render_template, request, jsonify
from pybit import HTTP
import time
import ccxt
from binanceFutures import Bot


app = Flask(__name__)

# load config.json
with open('config.json') as config_file:
    config = json.load(config_file)

use_bybit = False
if 'BYBIT' in config['EXCHANGES']:
    if config['EXCHANGES']['BYBIT']['ENABLED']:
        print("Bybit is enabled!")
        use_bybit = True

    session = HTTP(
        endpoint='https://api.bybit.com',
        api_key=config['EXCHANGES']['BYBIT']['API_KEY'],
        api_secret=config['EXCHANGES']['BYBIT']['API_SECRET']
    )

use_binance_futures = False
if 'BINANCE-FUTURES' in config['EXCHANGES']:
    if config['EXCHANGES']['BINANCE-FUTURES']['ENABLED']:
        print("Binance is enabled!")
        use_binance_futures = True

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


@app.route('/')
def index():
    return {'message': 'Server is running!'}


position_open = False

@app.route('/webhook', methods=['POST'])
def webhook():
    global position_open
    print("Hook Received!")
    data = json.loads(request.data)
    print(data)

    if int(data['key']) != config['KEY']:
        print("Invalid Key, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Key, Please Try Again!"
        }

    if data['exchange'] == 'bybit':
        if use_bybit:
            if 'close_position' in data and data['close_position'].lower() in ['closeshort', 'closelong']:
                print("Closing Position")
                session.close_position(symbol=data['symbol'])
                position_open = False
            else:
                if position_open:
                    print("Position already open, ignoring new signals.")
                    return {
                        "status": "error",
                        "message": "Position already open, ignoring new signals."
                    }

                if 'type' in data:
                    print("Placing Order")
                    if 'price' in data:
                        price = data['price']
                    else:
                        price = 0

                    session.place_active_order(
                        symbol=data['symbol'],
                        order_type=data['type'],
                        side=data['side'],
                        qty=data['qty'],
                        time_in_force="GoodTillCancel",
                        reduce_only=False,
                        close_on_trigger=False,
                        price=price,
                    )
                    position_open = True

        return {
            "status": "success",
            "message": "Bybit Webhook Received!"
        }

    if data['exchange'] == 'binance-futures':
        if use_binance_futures:
            bot = Bot()
            bot.run(data)
            return {
                "status": "success",
                "message": "Binance Futures Webhook Received!"
            }

    else:
        print("Invalid Exchange, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Exchange, Please Try Again!"
        }

if __name__ == '__main__':
    app.run(debug=False)
