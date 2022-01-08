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

TELEGRAM_TOKEN      = str(c["TELEGRAM_TOKEN"])
CHAT_ID             = str(c["CHAT_ID"])
CHAT_ID_ALERT       = str(c["CHAT_ID_ALERT"])
NODE_NAME           = str(c["NODE_NAME"])
GRAPHQL_HOST        = str(c["GRAPHQL_HOST"])
GRAPHQL_PORT        = int(c["GRAPHQL_PORT"])
WAIT_TIME_IN_CHECKS        = int(c["WAIT_TIME_IN_CHECKS"])
CHECK_FREQ_IN_MIN        = int(c["CHECK_FREQ_IN_MIN"])
VALOPER_ADDR       = str(c["VALOPER_ADDR"])

MARKDOWN_ALERT = """ 
| metric  | status |
| ------------- |:-------------:|
| tombstoned_status      | {tombstoned_status}     |
| jailed_status      | {jailed_status}    |
| missed_too_many_blocks_status      | {missed_too_many_blocks_status}     |
| no_proxy_registered_status      | {no_proxy_registered_status}    |
| tss_suspended_status      | {tss_suspended_status}     |
| proxy_insuficient_funds_status      | {proxy_insuficient_funds_status}     |
| stale_tss_heartbeat_status      | {stale_tss_heartbeat_status}     |
"""

bot=telegram.Bot(token=TELEGRAM_TOKEN)


COUNT = 0



def record_status(msg, type="standard"):
    # sending a telgram message
    chat_id = CHAT_ID
    chat_id_alert  = CHAT_ID_ALERT
    bot.sendMessage(chat_id=chat_id, text=msg, timeout=20)

    # additional message to the alert channel
    if type=="alert":
        bot.sendMessage(chat_id=chat_id_alert, text=msg, timeout=20)
    
    # this is for the console
    print(msg) 
    
    # to record in log file  
    ln = logging.getLogger('main_logger')
    ln.setLevel('INFO')  
    fh = logging.FileHandler('nodestatus_logs/nodestatus_{:%Y%m%d}.log'.format(datetime.datetime.now()))
    ln.addHandler(fh)
    ln.info(msg)
    ln.handlers.clear() # to avoid multiple instances of loggers getting created


def getminaexplorerblockheight():
    try:
        url = 'https://api.minaexplorer.com/'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req).read()
        content = json.loads(r.decode('utf-8'))
        return int(content['blockchainLength'])
    except:
        record_status("unable to retrieve height from minaexplorer")
        return None


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
            try:
                nextBlockTime = daemon_status['daemonStatus']['nextBlockProduction']['times'][0]['startTime']
            except:
                nextBlockTime = 100000

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
    sleep(60*5)
    #restart sidecar
    os.system("service mina-bp-stats-sidecar restart")
    #update telegram on restart
    record_status(NODE_NAME + " | mina daemon and sidecar has been restarted")

def checksidecarstatusandrestart():
    command = 'journalctl -u mina-bp-stats-sidecar.service --since "10 minutes ago" | grep -c "Got block data"'
    output,error  = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print(f'Total sidecar updates sent in 10 mts is {output}.')
    if int(output) < 2:
       os.system("service mina-bp-stats-sidecar restart")
       record_status(NODE_NAME + " | sidecar has been restarted")

'''
docker exec -it axelar-core axelard q snapshot validators -oj
{"validators":[{"operator_address":"axelarvaloper1uxa5r6hpd5vla6tndduhxr8gpsv5jfjgczrlwr","moniker":"stakewithjenni.com","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1pjnjylsjqsnzencyekjfge3e5j02vfksld77qt","moniker":"axelar-core-4","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1yz6zaad8nm29lxlkxzruun999vpxeecqq8skzl","moniker":"axelar-core-2","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1s6fsqpapzgpy0wq7jd69rcnavmhnwppun6etgs","moniker":"axelar-core-3","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1msctzg2qy4m5x26u30qwmxryxx2ph2rfcxejy5","moniker":"axelar-core-0","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper178t88epaxcls5xw7x9j94v80u4yzdemkpgsh5c","moniker":"axelar-core-1","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1sk5eesurd9elqpguevnddcfhv9fzh8mfdnwprl","moniker":"QuantNode","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper12e37vdgl2uc7kk3wu0d2qpkuwgyy7w87cc34kq","moniker":"0base.vc","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1nzml6v997w56q5hgd784eq0g9mvhd7mzngyatn","moniker":"Brightlystake","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1jj77l8y967tp4ace7xauppsmzpmr58fzzjfuws","moniker":"provenance-io","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper19eh7p42svuq2acc6vt2nnq7jjjljgwz3zguztv","moniker":"Simple","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1s6zaztmpl6zw453rj6r8uhtch5ttx3sht7vh7s","moniker":"ChainodeTech","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1cmxzk4y53rqng0a67erfqq90xh4l024qm2nywf","moniker":"Imperator.co","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1xu9d223797jud23u53rkk5zy9gwy730d62rvd8","moniker":"ushakov","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1n6ngamqpex44r5tcs36qhh50qxxupfcujxl5wz","moniker":"Figment","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1uf0ndewjqarwcg9aw68xlxc66adflcfzjdnmvq","moniker":"StakeLab","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1p08lmvp7qy7zs7zsj38shuht0hp00a78q99sum","moniker":"Everstake","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1xvlsqqvdlr7kdydkfyvksnsrvnd3xwuts4653h","moniker":"Staketab","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1x5wgh6vwye60wv3dtshs9dmqggwfx2ldh0v54p","moniker":"Cosmostation","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper18s4m4m32zqq63nxr6rxy905d6z69xervxdfh7a","moniker":"qubelabs","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1243yj8nwd4c6dcqxtg7lhltsslv58dhpkjjxdf","moniker":"CoinHippo","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1trq5mef4pjg48ntxpu87pl4a22ktycsjz7ecfa","moniker":"Forbole","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper140u2t5w8pacdpf64lw8p5l7vaz48k66pje724m","moniker":"B-Harvest","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1klj7fs4d63krf2vpcts3wc5csadl9tdsfuz9mh","moniker":"KingSuper","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1j7wdwde5mwzh3t46jfr4v44vl64eu45mpvjvl2","moniker":"LunaNova","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":false,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1znh6mlka900nptlgcqpv39m79m6a6nylj3ehad","moniker":"ROOIIE","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper12axgn9a2hlk7ljjxfxaqd4xdjfsru3j3e2585m","moniker":"MZONDER_NODE","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1wsw3n6wrc0ku3jn9c46rvz4q2ueldwrx0x0rk3","moniker":"4SV","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}},{"operator_address":"axelarvaloper1rnfpyyhr3jgpe5vyn204f3gyk9r5r3lzh3dqxe","moniker":"oraclenode","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1ckg9aus8tv9xayyc9pzz8yxvrpty9mmnc09yak","moniker":"pluto","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":true}},{"operator_address":"axelarvaloper1u3z068nvy2u36tqmmul7q90as8w3tpjqtnrxrq","moniker":"BwareLabs","tss_illegibility_info":{"tombstoned":false,"jailed":false,"missed_too_many_blocks":true,"no_proxy_registered":false,"tss_suspended":false,"proxy_insuficient_funds":false,"stale_tss_heartbeat":false}}]}
docker exec -it axelar-core axelard q snapshot validators -oj | jq '.validators | .[] | select(.operator_address=="axelarvaloper1uxa5r6hpd5vla6tndduhxr8gpsv5jfjgczrlwr")'

'''
def getvalidatorsnapshot():
    command = f"docker exec -it axelar-core axelard q snapshot validators -oj | jq '.validators | .[] | select(.operator_address==\"{VALOPER_ADDR}\")'"
    output,error  = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print(f'validator state output {output}.')
    response_json = str(command)
    return response_json

def formatinmarkdown(input):
    if input is not None:
        tss_illegibility_info = input['tss_illegibility_info']
        if tss_illegibility_info is not None:
            tombstoned_status = tss_illegibility_info['tombstoned']
            jailed_status = tss_illegibility_info['jailed']
            missed_too_many_blocks_status = tss_illegibility_info['missed_too_many_blocks']
            no_proxy_registered_status = tss_illegibility_info['no_proxy_registered']
            tss_suspended_status = tss_illegibility_info['tss_suspended']
            proxy_insuficient_funds_status = tss_illegibility_info['proxy_insuficient_funds']
            stale_tss_heartbeat_status = tss_illegibility_info['stale_tss_heartbeat']
            print(f'status is {tss_illegibility_info}')
            if not tombstoned_status or not jailed_status or not missed_too_many_blocks_status or \
                not no_proxy_registered_status or not tss_suspended_status or not proxy_insuficient_funds_status \
                or not stale_tss_heartbeat_status:
                print(f'status is not correct {tss_illegibility_info}.Sending telegram RED alert ❌')
                MARKDOWN_ALERT.format(
                    tombstoned_status="❌" if tss_illegibility_info['tombstoned'] else "✅",
                    jailed_status="❌" if tss_illegibility_info['jailed'] else "✅",
                    missed_too_many_blocks_status="❌" if tss_illegibility_info['missed_too_many_blocks'] else "✅",
                    no_proxy_registered_status="❌" if tss_illegibility_info['no_proxy_registered'] else "✅",
                    tss_suspended_status="❌" if tss_illegibility_info['tss_suspended'] else "✅",
                    proxy_insuficient_funds_status="❌" if tss_illegibility_info['proxy_insuficient_funds'] else "✅",
                    stale_tss_heartbeat_status="❌" if tss_illegibility_info['stale_tss_heartbeat'] else "✅"
                )
                return MARKDOWN_ALERT
    else:
        return None




def check_node_sync():
    d = get_node_status()
    global COUNT

    if d == None:
        msg = NODE_NAME + " | unable to reach mina daemon. Attention required!!!"
        record_status(msg, type='alert')
    else:
        try: #fix for issue with length provided as NoneType by daemon
            delta_height = int(d["highestUnvalidatedBlockLengthReceived"]) -  int(d["blockchainLength"])
        except:
            delta_height = "NA"
    
        current_epoch_time = int(time.time()*1000)
        next_block_in_sec = int(d["nextBlockTime"]) - current_epoch_time
        next_block_in = str(datetime.timedelta(milliseconds=next_block_in_sec)).split(".")[0]
        uptime_readable = str(datetime.timedelta(seconds=d["uptime"]))
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base_msg = current_time + "|" + NODE_NAME + "|" + d["sync_status"] + "|" + uptime_readable + "|" + str(d["blockchainLength"]) + "|" + \
                    str(d["highestBlockLengthReceived"]) + "|" + str(d["highestUnvalidatedBlockLengthReceived"]) + "|" + \
                    str(delta_height) + "|" + next_block_in + "| "

        minaexplorerblockheight = getminaexplorerblockheight()
        if minaexplorerblockheight is not None and minaexplorerblockheight - int(d["blockchainLength"]) > 2:
            restart_node()
            msg = base_msg + " synced on wrong height.Actual height is " + "|" + str(minaexplorerblockheight)
            record_status(msg, type='alert')

        
        # Action logic for different scenarios
        if d["sync_status"] == "SYNCED" and delta_height == 0: #perfect scenario
            msg = base_msg + "no action taken"
            record_status(msg)
            COUNT = 0


        elif d["sync_status"] in {"SYNCED","CATCHUP"} and COUNT <= WAIT_TIME_IN_CHECKS: #OK to wait a few minutes    
            msg = base_msg + "waiting for few mins" 
            record_status(msg, type='alert')
            COUNT = COUNT + 1

        elif d["sync_status"] in {"SYNCED","CATCHUP"}  and COUNT > WAIT_TIME_IN_CHECKS: #restart routine  
            msg = base_msg + "restarting node"  
            record_status(msg, type='alert')
            restart_node()
            COUNT = 0   
          
        else:
            msg = base_msg + " in unknown mode. Attention required"
            record_status(msg, type='alert')

if __name__ == "__main__": 
       
    while True:
        try:
            validator_snapshot = getvalidatorsnapshot()
            formatted_text = formatinmarkdown(validator_snapshot)
            bot.sendMessage(chat_id=CHAT_ID, text=formatted_text, timeout=20,parse_mode='MarkdownV2')
        except Exception as e:
            msg = str(e)
            record_status(msg, type='alert')
        sleep(60*CHECK_FREQ_IN_MIN)
    