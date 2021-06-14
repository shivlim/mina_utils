## Usage


```bash
pip3 install -r requirements.txt
```




## Using the export_mina_logs.py script

```bash
1. Update config.yml with KEY and SECRET from AWS
2. pip3 install boto3
3. CRON job to run every 6 hours

0 */6 * * * $(which python3) /root/mina_utils/export_mina_logs.py >> ~/cron.log 2>&1

```