import time
import datetime
import sys
import yaml
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
WAIT_TIME_IN_CHECKS        = int(c["WAIT_TIME_IN_CHECKS"])
CHECK_FREQ_IN_MIN        = int(c["CHECK_FREQ_IN_MIN"])

bot=telegram.Bot(token=TELEGRAM_TOKEN)

COUNT = 0 

def send_message(chat_id, msg):
    bot.sendMessage(chat_id=chat_id, text=msg)

def get_node_status():
    attempts = 0
    while attempts < 3: # tries 3 times to get node status before raising exception
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
                        "highestUnvalidatedBlockLengthReceived": highestUnvalidatedBlockLengthReceived,
                        "nextBlockTime": nextBlockTime
                    }
        except:
            attempts += 1
            if attempts == 2:
                return None

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
    global COUNT

    if d == None:
        msg = "unable to reach mina daemon. Attention required!!!"
        send_message(CHAT_ID, msg)
    else:
        delta_height = int(d["highestUnvalidatedBlockLengthReceived"]) -  int(d["blockchainLength"])

        current_epoch_time = int(time.time()*1000)

        next_block_in_sec = int(d["nextBlockTime"]) - current_epoch_time
        next_block_in = str(datetime.timedelta(milliseconds=next_block_in_sec))

        uptime_readable = str(datetime.timedelta(seconds=d["uptime"]))

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base_msg = current_time + "|" + NODE_NAME + "|" + d["sync_status"] + "|" + uptime_readable + "|" + str(d["blockchainLength"]) + "|" + \
                    str(d["highestBlockLengthReceived"]) + "|" + str(d["highestUnvalidatedBlockLengthReceived"]) + "|" + \
                    str(delta_height) + "|" + next_block_in + "| "
        
        # Action logic for different scenarios
        if d["sync_status"] == "SYNCED" and delta_height == 0: #perfect scenario
            msg = base_msg + "no action taken"
            send_message(CHAT_ID, msg)
            print(msg)
            COUNT = 0


        elif d["sync_status"] in {"SYNCED","CATCHUP"} and COUNT <= WAIT_TIME_IN_CHECKS: #OK to wait a few minutes    
            msg = base_msg + "waiting for few mins" 
            send_message(CHAT_ID, msg)
            print(msg)
            COUNT = COUNT + 1
            print("the attempt number is : " + str(COUNT))

        elif d["sync_status"] in {"SYNCED","CATCHUP"}  and COUNT > WAIT_TIME_IN_CHECKS: #restart routine  
            msg = base_msg + "restarting node"  
            send_message(CHAT_ID, msg)
            print(msg)
            restart_node()
            COUNT = 0   
          
        else:
            msg = base_msg + " in unknown mode. Attention required"
            send_message(CHAT_ID, msg)

if __name__ == "__main__": 
       
    while True:
        check_node_sync()
        sleep(60*CHECK_FREQ_IN_MIN)
    