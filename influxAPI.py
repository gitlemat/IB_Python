from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate an API token from the "API Tokens Tab" in the UI
'''
token = "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="
org = "rodsic.com"
bucket = "ib_prices"
'''



'''

with InfluxDBClient(url="http://192.168.2.131:8086", token=token, org=org) as client:

    write_api = client.write_api(write_options=SYNCHRONOUS)
    data = "mem,host=host1 used_percent=23.43234543"
    write_api.write(bucket, org, data)

query = 'from(bucket: "ib_prices") |> range(start: -1h)'
tables = client.query_api().query(query, org=org)
for table in tables:
    for record in table.records:
        print(record)


client.close()

'''

class InfluxClient:
    def __init__(self): 
        token = os.getenv('TOKEN')
        self._org = os.getenv('ORG') 
        self._bucket = os.getenv('BUCKET')
        self._client = InfluxDBClient(url="http://localhost:8086", token=token)

    def write_data(self,data,write_option=SYNCHRONOUS):
        # measurementName,tagKey=tagValue fieldKey1="fieldValue1",fieldKey2=fieldValue2 timestamp
        # There’s a space between the tagValue and the first fieldKey, and another space between the last fieldValue and timeStamp
        # timestamp is optional
        # IC.write_data(["MSFT,stock=MSFT Open=62.79,High=63.84,Low=62.13"])
        write_api = self._client.write_api(write_option)
        write_api.write(bucket=self._bucket, org=self._org, record=data, write_precision='s')

    def query_data(self,query):
        query_api = self._client.query_api()
        result = query_api.query(org=self._org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_value(), record.get_field()))
        return results