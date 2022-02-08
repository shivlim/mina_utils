import time
import datetime
import sys
import yaml
import telegram
import os
from MinaPyClient import Client
from time import sleep
import logging
import subprocess
import urllib.request
import json

c = yaml.load(open('config.yml', encoding='utf8'), Loader=yaml.SafeLoader)

TELEGRAM_TOKEN = str(c["TELEGRAM_TOKEN"])
CHAT_ID = str(c["CHAT_ID"])
CHAT_ID_ALERT = str(c["CHAT_ID_ALERT"])
NODE_NAME = str(c["NODE_NAME"])
GRAPHQL_HOST = str(c["GRAPHQL_HOST"])
GRAPHQL_PORT = int(c["GRAPHQL_PORT"])
WAIT_TIME_IN_CHECKS = int(c["WAIT_TIME_IN_CHECKS"])
CHECK_FREQ_IN_MIN = int(c["CHECK_FREQ_IN_MIN"])
VALOPER_ADDR = str(c["VALOPER_ADDR"])

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

bot = telegram.Bot(token=TELEGRAM_TOKEN)

COUNT = 0


def record_status(msg, type="standard"):
    # sending a telgram message
    chat_id = CHAT_ID
    chat_id_alert = CHAT_ID_ALERT
    bot.sendMessage(chat_id=chat_id, text=msg, timeout=20)

    # additional message to the alert channel
    if type == "alert":
        bot.sendMessage(chat_id=chat_id_alert, text=msg, timeout=20)

    # this is for the console
    print(msg)

    # to record in log file  
    ln = logging.getLogger('main_logger')
    ln.setLevel('INFO')
    fh = logging.FileHandler('nodestatus_logs/nodestatus_{:%Y%m%d}.log'.format(datetime.datetime.now()))
    ln.addHandler(fh)
    ln.info(msg)
    ln.handlers.clear()  # to avoid multiple instances of loggers getting created


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


def getvalidatorsnapshot():
    command = f"docker exec -it axelar-core axelard q snapshot validators -oj | jq '.validators | .[] | select(.operator_address==\"{VALOPER_ADDR}\")'"
    output, error = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).communicate()
    print(f'validator state output {output}.')
    return output


{'tombstoned': False, 'jailed': False, 'missed_too_many_blocks': False, 'no_proxy_registered': False,
 'tss_suspended': False, 'proxy_insuficient_funds': False, 'stale_tss_heartbeat': False}
{'tombstoned': False, 'jailed': False, 'missed_too_many_blocks': False, 'no_proxy_registered': False,
 'tss_suspended': False, 'proxy_insuficient_funds': False, 'stale_tss_heartbeat': False}


def formatinmarkdown(input):
    if input is not None:
        input = json.loads(input)
        tss_illegibility_info = input['tss_illegibility_info']
        if tss_illegibility_info is not None:
            tombstonedstatus = tss_illegibility_info['tombstoned']
            jailedstatus = tss_illegibility_info['jailed']
            missedtoomanyblocksstatus = tss_illegibility_info['missed_too_many_blocks']
            noproxyregisteredstatus = tss_illegibility_info['no_proxy_registered']
            tsssuspendedstatus = tss_illegibility_info['tss_suspended']
            proxyinsuficientfundsstatus = tss_illegibility_info['proxy_insuficient_funds']
            staletssheartbeatstatus = tss_illegibility_info['stale_tss_heartbeat']
            print(f'status is {tss_illegibility_info}')
            if tombstonedstatus or jailedstatus or missedtoomanyblocksstatus or \
                    noproxyregisteredstatus or tsssuspendedstatus or proxyinsuficientfundsstatus \
                    or staletssheartbeatstatus:
                print(f'status is not correct {tss_illegibility_info}.Sending telegram RED alert ❌')
                tombstoned_status = "❌" if tombstonedstatus else "✅"
                jailed_status = "❌" if jailedstatus else "✅"
                missed_too_many_blocks_status = "❌" if missedtoomanyblocksstatus else "✅"
                no_proxy_registered_status = "❌" if noproxyregisteredstatus else "✅"
                tss_suspended_status = "❌" if tsssuspendedstatus else "✅"
                proxy_insuficient_funds_status = "❌" if proxyinsuficientfundsstatus else "✅"
                stale_tss_heartbeat_status = "❌" if staletssheartbeatstatus else "✅"

                formatted_text = f""" 
                                tombstoned_status {tombstoned_status}
                                jailed_status {jailed_status}
                                missed_too_many_blocks_status {missed_too_many_blocks_status}
                                tss_suspended_status {tss_suspended_status}
                                proxy_insuficient_funds_status {proxy_insuficient_funds_status}
                                no_proxy_registered_status {no_proxy_registered_status}
                                stale_tss_heartbeat_status {stale_tss_heartbeat_status}
                                """
                print(f'formatted_text {formatted_text}')
                return formatted_text
    else:
        return None


if __name__ == "__main__":

    while True:
        try:
            validator_snapshot = getvalidatorsnapshot()
            formatted_text = formatinmarkdown(validator_snapshot)

            if formatted_text is None:
                formatted_text = "Testnet - All Ok ✅ "

            print(f' formatted_text {formatted_text}')

            responseavax, responseavaxstatus = getrpcendpointresponse(AVAX_RPC_ENDPOINT, AVAX_RPC_REQUEST)
            if responseavaxstatus and responseavax['result']['isBootstrapped']:
                formatted_text += " avax_rpc_status ✅ "
            else:
                formatted_text += " avax_rpc_status ❌ "

            print(f' formatted_text {formatted_text}')

            responsefantom, responsefantomstatus = getrpcendpointresponse(FANTOM_RPC_ENDPOINT, FANTOM_RPC_REQUEST)
            if responsefantomstatus and responsefantom['result'] is False:
                formatted_text += " fantom_rpc_status ✅ "
            else:
                formatted_text += " fantom_rpc_status ❌ "

            print(f' formatted_text {formatted_text}')

            responseeth, responseethstatus = getrpcendpointresponse(ETH_RPC_ENDPOINT, ETH_RPC_REQUEST)
            if responseethstatus and responseeth['result'] is False:
                formatted_text += " eth_rpc_status ✅ "
            else:
                formatted_text += " eth_rpc_status ❌ "
            print(f' formatted_text {formatted_text}')

            responsemoonbeam, responsemoonbeamstatus = getrpcendpointresponse(MOONBEAM_RPC_ENDPOINT,
                                                                              MOONBEAM_RPC_REQUEST)
            if responsemoonbeamstatus and responsemoonbeam['result'] is False:
                formatted_text += " moonbeam_rpc_status ✅ "
            else:
                formatted_text += " moonbeam_rpc_status ❌ "

            print(f' formatted_text {formatted_text}')

            responsepolygon, responsepolygonstatus = getrpcendpointresponse(POLYGON_RPC_ENDPOINT, POLYGON_RPC_REQUEST)
            if responsepolygonstatus and responsepolygon['result'] is False:
                formatted_text += " polygon_rpc_status ✅ "
            else:
                formatted_text += " polygon_rpc_status ❌ "

            print(f'final formatted_text {formatted_text}')

            bot.sendMessage(chat_id=CHAT_ID, text=formatted_text, timeout=20)
        except Exception as e:
            msg = str(e)
            record_status(msg, type='alert')
        sleep(60 * CHECK_FREQ_IN_MIN)
