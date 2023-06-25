import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
TOKEN = 't5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=='
ORG = 'rodsic.com'
BUCKET = 'ib_prices_lab'

def testToday():
    client = InfluxDBClient(url="http://localhost:8086", token=TOKEN)
    today = datetime.datetime.today()#  - datetime.timedelta(days = 1)

    now  = datetime.datetime.now()
    todayStart = today.replace(hour = 15, minute = 10, second = 0, microsecond=0)
    todayStop = today.replace(hour = 20, minute = 15, second = 0, microsecond=0)
    print (todayStart)
    week = datetime.datetime.today() - datetime.timedelta(days = 70)
    param = {"_bucket": BUCKET, "_start": todayStart, "_stop": todayStop, "_symbol": "HEM3-2HEN3+HEQ3", "_desc": False}
    query = '''
    from(bucket: _bucket)
    |> range(start: _start, stop: _stop)
    |> filter(fn:(r) => r._measurement == "precios")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn:(r) => r._field == "ASK" or r._field == "BID" or r._field == "LAST" or r._field == "BID_SIZE" or r._field == "LAST_SIZE" or r._field == "BID_SIZE")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "ASK", "ASK_SIZE", "BID", "BID_SIZE", "LAST", "LAST_SIZE"])
    |> sort(columns: ["_time"], desc: _desc)
    '''
    # range(start: _start, stop: _stop)
    # tail(n:1)

    query_api = client.query_api()
    
    result = []
    if now > todayStart:
        result = query_api.query_data_frame(org=ORG, query=query, params = param)
    if len(result) == 0:
        result = getLast(client)

    result.rename(columns = {'_time':'timestamp'}, inplace = True)
    result.drop(columns=['result','table'], inplace=True)
    result.set_index('timestamp', inplace=True)

    try:
        result.index = result.index.tz_convert('Europe/Madrid')
    except:
        result.index = result.index.tz_localize(None)

    return result

def getLast(client):
    param = {"_symbol": "HEM3", "_desc": False}
    query = '''
    from(bucket:"ib_prices_lab")|> range(start: 0)
    |> filter(fn:(r) => r._measurement == "precios")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn:(r) => r._field == "ASK" or r._field == "BID" or r._field == "LAST" or r._field == "BID_SIZE" or r._field == "LAST_SIZE" or r._field == "BID_SIZE")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "ASK", "ASK_SIZE", "BID", "BID_SIZE", "LAST", "LAST_SIZE"])
    |> sort(columns: ["_time"], desc: _desc)
    |> tail(n:1)
    '''

    query_api = client.query_api()
    result = query_api.query_data_frame(org=ORG, query=query, params = param)

    return result

def testOhcl():
    client = InfluxDBClient(url="http://localhost:8086", token=TOKEN)
    #today = datetime.datetime.today()  - datetime.timedelta(days = 1)

    #today = today.replace(hour = 14, minute = 0, second = 0, microsecond=0)
    todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
    todayStop = datetime.datetime.today()
    todayStart = todayStart.replace(hour = 15, minute = 10, second = 0, microsecond=0)
    todayStop = todayStop.replace(hour = 20, minute = 15, second = 0, microsecond=0)
    print (todayStart)
    week = datetime.datetime.today() - datetime.timedelta(days = 70)
    param = {"_bucket": "ib_prices_1h_lab", "_start": todayStart, "_stop": todayStop, "_symbol": "HEM3-2HEN3+HEQ3", "_desc": False}
    query = '''
    from(bucket: _bucket)|> range(start: _start, stop: _stop)
    |> filter(fn:(r) => r._measurement == "precios")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn:(r) => r._field == "open" or r._field == "close" or r._field == "high" or r._field == "low")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "open", "close", "high", "low"])
    |> sort(columns: ["_time"], desc: _desc)
    '''
    # range(start: _start, stop: _stop)
    # tail(n:1)

    query_api = client.query_api()
    result = query_api.query_data_frame(org=ORG, query=query, params = param)

    result.rename(columns = {'_time':'timestamp'}, inplace = True)


    result.drop(columns=['result','table'], inplace=True)
    result.set_index('timestamp', inplace=True)

    return result

def testPnL():
    client = InfluxDBClient(url="http://localhost:8086", token=TOKEN)
    #today = datetime.datetime.today()  - datetime.timedelta(days = 1)

    #today = today.replace(hour = 14, minute = 0, second = 0, microsecond=0)
    today = datetime.datetime.today()
    todayStart = today.replace(hour = 0, minute = 0, second = 0, microsecond=0)
    todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
    print (todayStop)
    param = {"_bucket": BUCKET, "_start": todayStart, "_stop": todayStop, "_symbol": "HEM3-2HEN3+HEQ3", "_desc": False}
    query = '''
    from(bucket: _bucket)|> range(start: _start, stop: _stop)
    |> filter(fn:(r) => r._measurement == "pnl")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn:(r) => r._field == "dailyPnL" or r._field == "realizedPnL" or r._field == "unrealizedPnL")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "dailyPnL", "realizedPnL", "unrealizedPnL"])
    |> sort(columns: ["_time"], desc: _desc)
    '''

    query_api = client.query_api()
    result = query_api.query_data_frame(org=ORG, query=query, params = param)

    if len(result) == 0:
        print ('Cero')

    result.rename(columns = {'_time':'timestamp'}, inplace = True)

    result.drop(columns=['result','table'], inplace=True)
    result.set_index('timestamp', inplace=True)
    #result.index = result.index.tz_localize(None)

    return result


def testExec():
    client = InfluxDBClient(url="http://192.168.2.131:8086", token=TOKEN)

    print ("todayStop")
    param = {"_bucket": BUCKET, "_symbol": "HEM3-2HEN3+HEQ3", "_strategy": "Pentagrama", "_desc": False}
    query = '''
    from(bucket: _bucket)|> range(start: 0)
    |> filter(fn:(r) => r._measurement == "executions")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn:(r) => r.strategy == _strategy)
    |> filter(fn:(r) => r._field == "OrderId" or r._field == "Quantity" or r._field == "Side" or r._field == "RealizedPnL" or r._field == "Commission")
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "ExecId", "PermId", "OrderId", "Quantity", "Side", "RealizedPnL", "Commission"])
    |> sort(columns: ["_time"], desc: _desc)
    '''

    query_api = client.query_api()
    result = query_api.query_data_frame(org=ORG, query=query, params = param)

    if len(result) == 0:
        print ('Cero')

    result.rename(columns = {'_time':'timestamp'}, inplace = True)

    result.drop(columns=['result','table'], inplace=True)
    result.set_index('timestamp', inplace=True)
    #result.index = result.index.tz_localize(None)

    return result

def testExecCountSum():
    client = InfluxDBClient(url="http://localhost:8086", token=TOKEN)

    print ("todayStop")
    param = {"_bucket": BUCKET, "_symbol": "HEM3-2HEN3+HEQ3", "_desc": False}
    query = '''
    from(bucket: _bucket)|> range(start: 0)
    |> filter(fn:(r) => r._measurement == "executions")
    |> filter(fn:(r) => r.symbol == _symbol)
    |> filter(fn: (r) => r["strategy"] == "Pentagrama")
    |> filter(fn:(r) => r._field == "ExecId")
    |> aggregateWindow(every: 24h, fn: count, createEmpty: false)
    |> sort(columns: ["_time"], desc: _desc)
    |> sort(columns: ["_time"], desc: _desc)
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["_time", "ExecId"])
    '''

    query_api = client.query_api()
    result = query_api.query_data_frame(org=ORG, query=query, params = param)

    if len(result) == 0:
        print ('Cero')

    result.rename(columns = {'_time':'timestamp'}, inplace = True)
    result.drop(columns=['result','table'], inplace=True)
    result.set_index('timestamp', inplace=True)

    #result.drop(columns=['result','table'], inplace=True)
    #result.set_index('timestamp', inplace=True)
    #result.index = result.index.tz_localize(None)

    return result


