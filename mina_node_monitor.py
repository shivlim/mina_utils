import time
import sys
import yaml
import datetime
import telegram
from CodaClient import Client


c = yaml.load(open('config.yml', encoding='utf8'), Loader=yaml.SafeLoader)

TELEGRAM_TOKEN      = str(c["TELEGRAM_TOKEN"])
CHAT_ID             = str(c["CHAT_ID"])
NODE_NAME           = str(c["NODE_NAME"])
GRAPHQL_HOST        = str(c["GRAPHQL_HOST"])
GRAPHQL_PORT        = int(c["GRAPHQL_PORT"])

bot=telegram.Bot(token=TELEGRAM_TOKEN)

def get_node_status():
    coda = Client(graphql_host=GRAPHQL_HOST, graphql_port=GRAPHQL_PORT)
    daemon_status = coda.get_daemon_status()
    sync_status = daemon_status['daemonStatus']['syncStatus']
    uptime = daemon_status['daemonStatus']['uptimeSecs'] 	
    blockchainLength = daemon_status['daemonStatus']['blockchainLength']
    highestBlockLengthReceived = daemon_status['daemonStatus']['highestBlockLengthReceived']
    highestUnvalidatedBlockLengthReceived = daemon_status['daemonStatus']['highestUnvalidatedBlockLengthReceived']
    nextBlockTime = daemon_status['daemonStatus']['nextBlockProduction']['times'][0]['startTime']

    return {    "sync_status": sync_status, 
                "uptime": uptime, 
                "blockchainLength": blockchainLength, 
                "highestBlockLengthReceived": highestBlockLengthReceived, 
                "nextBlockTime": nextBlockTime
            }

def send_message(chat_id, msg):
    bot.sendMessage(chat_id=chat_id, text=msg)


def restart_node():
    #restart mina daemon
    #restart sidecar
    #update telegram on restart
    pass

if __name__ == "__main__":
    d = get_node_status()
    print(d.sync_status)
    print(d.uptime)
    print(d.blockchainLength)
    print(d.highestBlockLengthReceived)
    print(d.nextBlockTime)