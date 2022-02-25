import datetime
import json
import logging
import urllib.request
from time import sleep

import telegram
import yaml

c = yaml.load(open('config.yml', encoding='utf8'), Loader=yaml.SafeLoader)

TELEGRAM_TOKEN = str(c["TELEGRAM_TOKEN"])
CHAT_ID = str(c["CHAT_ID"])
CHAT_ID_ALERT = str(c["CHAT_ID_ALERT"])
NODE_NAME = str(c["NODE_NAME"])
GRAPHQL_HOST = str(c["GRAPHQL_HOST"])
GRAPHQL_PORT = int(c["GRAPHQL_PORT"])
WAIT_TIME_IN_CHECKS = int(c["WAIT_TIME_IN_CHECKS"])
CHECK_FREQ_IN_MIN = int(c["CHECK_FREQ_IN_MIN"])

AVAX_RPC_ENDPOINT = str(c["AVAX_RPC_ENDPOINT"])
FANTOM_RPC_ENDPOINT = str(c["FANTOM_RPC_ENDPOINT"])
ETH_RPC_ENDPOINT = str(c["ETH_RPC_ENDPOINT"])
POLYGON_RPC_ENDPOINT = str(c["POLYGON_RPC_ENDPOINT"])
MOONBEAM_RPC_ENDPOINT = str(c["MOONBEAM_RPC_ENDPOINT"])

AVAX_RPC_REQUEST = {"jsonrpc": "2.0", "id": 1, "method": "info.isBootstrapped", "params": {"chain": "C"}}
FANTOM_RPC_REQUEST = {"id": 1, "jsonrpc": "2.0", "method": "eth_syncing", "params": []}
ETH_RPC_REQUEST = {"id": 1, "jsonrpc": "2.0", "method": "eth_syncing", "params": []}
POLYGON_RPC_REQUEST = {"id": 1, "jsonrpc": "2.0", "method": "eth_syncing", "params": []}
MOONBEAM_RPC_REQUEST = {"id": 1, "jsonrpc": "2.0", "method": "eth_syncing", "params": []}


COUNT = 0

ln = logging.getLogger('main_logger')
ln.setLevel('INFO')
fh = logging.FileHandler('nodestatus_logs/nodestatus_{:%Y%m%d}.log'.format(datetime.datetime.now()))
ln.addHandler(fh)



def getrpcendpointresponse(endpoint, values):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = json.dumps(values).encode("utf-8")

    try:
        req = urllib.request.Request(endpoint, data, headers)
        with urllib.request.urlopen(req) as f:
            res = f.read()
        content = json.loads(res.decode('utf-8'))
        return content, True
    except Exception as e:
        print(e)
        return None, False

if __name__ == "__main__":

    while True:
        try:
            formatted_text = ""

            if formatted_text is None:
                formatted_text = "Testnet - All Ok ✅ "


            responseavax, responseavaxstatus = getrpcendpointresponse(AVAX_RPC_ENDPOINT, AVAX_RPC_REQUEST)
            if responseavaxstatus and responseavax['result']['isBootstrapped']:
                formatted_text += " avax_rpc_status ✅ "
            else:
                formatted_text += " avax_rpc_status ❌ "


            responsefantom, responsefantomstatus = getrpcendpointresponse(FANTOM_RPC_ENDPOINT, FANTOM_RPC_REQUEST)
            if responsefantomstatus and responsefantom['result'] is False:
                formatted_text += " fantom_rpc_status ✅ "
            else:
                formatted_text += " fantom_rpc_status ❌ "


            responseeth, responseethstatus = getrpcendpointresponse(ETH_RPC_ENDPOINT, ETH_RPC_REQUEST)
            if responseethstatus and responseeth['result'] is False:
                formatted_text += " eth_rpc_status ✅ "
            else:
                formatted_text += " eth_rpc_status ❌ "

            responsemoonbeam, responsemoonbeamstatus = getrpcendpointresponse(MOONBEAM_RPC_ENDPOINT,
                                                                              MOONBEAM_RPC_REQUEST)
            if responsemoonbeamstatus and responsemoonbeam['result'] is False:
                formatted_text += " moonbeam_rpc_status ✅ "
            else:
                formatted_text += " moonbeam_rpc_status ❌ "


            responsepolygon, responsepolygonstatus = getrpcendpointresponse(POLYGON_RPC_ENDPOINT, POLYGON_RPC_REQUEST)
            if responsepolygonstatus and responsepolygon['result'] is False:
                formatted_text += " polygon_rpc_status ✅ "
            else:
                formatted_text += " polygon_rpc_status ❌ "

            print(f'final formatted_text {formatted_text}')

            ln.info(formatted_text)
        except Exception as e:
            print(f'E {e}')
            msg = str(e)
            print(f'message {msg}')
        sleep(60 * CHECK_FREQ_IN_MIN)
