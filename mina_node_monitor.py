import time
import sys
import yaml
import datetime
import telegram
import os
from MinaPyClient import Client
from time import sleep

c = yaml.load(open('config.yml', encoding='utf8'), Loader=yaml.SafeLoader)

TELEGRAM_TOKEN      = str(c["TELEGRAM_TOKEN"])
CHAT_ID             = str(c["CHAT_ID"])
NODE_NAME           = str(c["NODE_NAME"])
GRAPHQL_HOST        = str(c["GRAPHQL_HOST"])
GRAPHQL_PORT        = int(c["GRAPHQL_PORT"])
ACCEPTABLE_BLOCK_DIFFERENCE        = int(c["ACCEPTABLE_BLOCK_DIFFERENCE"])

bot=telegram.Bot(token=TELEGRAM_TOKEN)


def send_message(chat_id, msg):
    bot.sendMessage(chat_id=chat_id, text=msg)

def get_node_status():
    try:
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
    except:
        msg = "unable to reach mina daemon. Attention required!!!"
        send_message(CHAT_ID, msg)

def restart_node():
    #restart mina daemon
    os.system("systemctl --user restart mina")
    print("restarting mina daemon...")
    sleep(15)
    #restart sidecar
    os.system("service mina-bp-stats-sidecar restart")
    #update telegram on restart
    send_message(CHAT_ID, "mina daemon has been restarted")

def check_node_sync():
    d = get_node_status()

    if d["sync_status"] == "SYNCED":
        block_height_difference = int(d["highestBlockLengthReceived"]) -  int(d["highestBlockLengthReceived"])

        if block_height_difference > ACCEPTABLE_BLOCK_DIFFERENCE:
            # routine for node not in sync starts
            restart_node()
            sleep(60*15)    
        else:
            msg = NODE_NAME + " in sync. Next block in " + str(d["nextBlockTime"])
            send_message(CHAT_ID, msg)
            sleep(60*15)

        # print(d["sync_status"])
        # print(d["uptime"])
        # print(d["blockchainLength"])
        # print(d["highestBlockLengthReceived"])
        # print(d["nextBlockTime"])
            
    elif d["sync_status"] == "CATCHUP":
        msg = NODE_NAME + " in catchup mode"
        send_message(CHAT_ID, msg)
        sleep(60*15)
    
    else:
        msg = NODE_NAME + " in unknown mode. Attention required"
        send_message(CHAT_ID, msg)
        sleep(60*15)

if __name__ == "__main__":    
    while True:
        check_node_sync()
    