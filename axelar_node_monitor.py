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
\| metric  \| status \|
\| \-\-\-\-\-\-\-\-\-\-\-\-\- \|:\-\-\-\-\-\-\-\-\-\-\-\-\-:\|
\| tombstonedstatus      \| \{tombstonedstatus\}     \|
\| jailedstatus      \| \{jailedstatus\}    \|
\| missedtoomanyblocksstatus      \| \{missedtoomanyblocksstatus\}     \|
\| noproxyregisteredstatus      \| \{noproxyregisteredstatus\}    \|
\| tsssuspendedstatus      \| \{tsssuspendedstatus\}     \|
\| proxyinsuficientfundsstatus      \| \{proxyinsuficientfundsstatus\}     \|
\| staletssheartbeatstatus      \| \{staletssheartbeatstatus\}     \|
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


def getvalidatorsnapshot():
    command = f"docker exec -it axelar-core axelard q snapshot validators -oj | jq '.validators | .[] | select(.operator_address==\"{VALOPER_ADDR}\")'"
    output,error  = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print(f'validator state output {output}.')
    #response_json = str(command)
    return output

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
            if not tombstonedstatus or not jailedstatus or not missedtoomanyblocksstatus or \
                not noproxyregisteredstatus or not tsssuspendedstatus or not proxyinsuficientfundsstatus \
                or not staletssheartbeatstatus:
                print(f'status is not correct {tss_illegibility_info}.Sending telegram RED alert ❌')
                MARKDOWN_ALERT.format(
                    tombstonedstatus="❌" if tss_illegibility_info['tombstoned'] else "✅",
                    jailedstatus="❌" if tss_illegibility_info['jailed'] else "✅",
                    missedtoomanyblocksstatus="❌" if tss_illegibility_info['missed_too_many_blocks'] else "✅",
                    noproxyregisteredstatus="❌" if tss_illegibility_info['no_proxy_registered'] else "✅",
                    tsssuspendedstatus="❌" if tss_illegibility_info['tss_suspended'] else "✅",
                    proxyinsuficientfundsstatus="❌" if tss_illegibility_info['proxy_insuficient_funds'] else "✅",
                    staletssheartbeatstatus="❌" if tss_illegibility_info['stale_tss_heartbeat'] else "✅"
                )
                return MARKDOWN_ALERT
    else:
        return None



if __name__ == "__main__": 
       
    while True:
        try:
            validator_snapshot = getvalidatorsnapshot()
            print(f'validator_snapshot is {validator_snapshot}')
            formatted_text = formatinmarkdown(validator_snapshot)
            print(f'formatted_text is {formatted_text}')
            bot.sendMessage(chat_id=CHAT_ID, text=formatted_text, timeout=20,parse_mode='MarkdownV2')
        except Exception as e:
            msg = str(e)
            record_status(msg, type='alert')
        sleep(60*CHECK_FREQ_IN_MIN)
    
