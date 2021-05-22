from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import os
from time import sleep


file_dir = 'data'
f= os.path.join(file_dir, 'uptime_data.csv')

def get_data():
    url=['http://uptime.minaprotocol.com/getPageData.php?pageNumber=1', 'http://uptime.minaprotocol.com/getPageData.php?pageNumber=2', 'http://uptime.minaprotocol.com/getPageData.php?pageNumber=3']
    data = pd.DataFrame([])
    t = str(datetime.now())

    for x in range(0, 2):  # try 3 times
        try:
            for u in url:
                html_content = requests.get(u).text    
                soup = BeautifulSoup(html_content, "lxml")
                for tr in soup.find_all("tr",  attrs={'class': None}):
                    x0 = tr.find_all("td")[0].text
                    x1 = tr.find_all("td")[1].text
                    x2 = tr.find_all("td")[2].text
                    x3 = tr.find_all("td")[3].text
                    d = {'ts': t, 'rank' : x0, 'bp': x1, 'score' : x2, 'uptime_score' : x3}
                    data = data.append(d, ignore_index=True)
            str_error = None
            print(t + '  data build success..')
        except Exception as str_error:
            print(str_error)
            pass

        if str_error:
            sleep(2)  # wait for 2 seconds before trying to fetch the data again
        else:
            break
    
    return(data)    

def write_data_to_file(df):
    if os.path.isfile(f): 
        df.to_csv(f, mode='a', header=False, index=False)            
    else:
        df.to_csv(f, index=False)


if __name__ == "__main__": 
    while True:
        df = get_data()
        write_data_to_file(df)
        sleep(60*5)