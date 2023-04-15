import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import utils


import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

# You can generate an API token from the "API Tokens Tab" in the UI
# influx delete --bucket "ib_prices_1h_prod" --org "rodsic.com" --predicate '_measurement="precios"' --start "2020-12-23T21:37:00Z" --stop "2023-12-23T21:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="

# Buscar zeros:
# influx query 'from(bucket:"ib_prices_lab") |> range(start:-130d) |> filter(fn: (r) => r["_measurement"] == "precios") |> filter(fn: (r) => r["_field"] == "LAST") |> filter(fn: (r) => r["symbol"] == "LEQ3") |> filter(fn: (r) => r["_value"] == 0)'
# Borrar rango
# influx delete --bucket "ib_prices_lab" --predicate '_measurement="precios" AND symbol="LEQ3"' --start 2023-02-24T15:10:01.944930000Z --stop 2023-02-24T15:40:05.447333000Z 


class InfluxClient:
    def __init__(self): 
        load_dotenv()
        token = os.getenv('TOKEN')
        self._mode = os.getenv('MODE')
        self._org = 'rodsic.com'
        if self._mode == 'Lab':
            self._bucket_prices = 'ib_prices_lab'
            self._bucket_ohcl = 'ib_prices_1h_lab'
            self._bucket_pnl = 'ib_prices_lab'
            self._bucket_execs = 'ib_prices_lab'

        else:
            self._bucket_prices = 'ib_prices_lab' #Utilizo lab para tener todos. Asi están juntos
            self._bucket_ohcl = 'ib_prices_1h_lab'
            self._bucket_pnl = 'ib_prices_prod'
            self._bucket_execs = 'ib_prices_prod'
        self._client = InfluxDBClient(url="http://localhost:8086", token=token)
        

    def write_data(self,data, type='precios', write_option=SYNCHRONOUS):
        # measurementName,tagKey=tagValue fieldKey1="fieldValue1",fieldKey2=fieldValue2 timestamp
        # There’s a space between the tagValue and the first fieldKey, and another space between the last fieldValue and timeStamp
        # timestamp is optional
        # IC.write_data(["MSFT,stock=MSFT Open=62.79,High=63.84,Low=62.13"])

        
        write_api = self._client.write_api(write_option)
        if type == 'precios':
            lbucket = self._bucket_prices
        elif type == 'pnl':
            lbucket = self._bucket_pnl
        elif type == 'executions':
            lbucket = self._bucket_execs
        else:
            lbucket = self._bucket_prices

        try:
            logging.debug ('Escribiendo en influx esto: %s', data)
            write_api.write(bucket=lbucket, org=self._org, record=data)
        except:
            logging.error ("Exception occurred", exc_info=True)

    def influxGetTodayDataFrame (self, symbol):
        logging.info('Leyendo precios de hoy de Influx para: %s', symbol)
        now  = datetime.datetime.now()
        now = utils.date2UTC (now) # Para poder comparar
        today = datetime.datetime.today()
        todayStart = today.replace(hour = 15, minute = 0, second = 0, microsecond=0)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.date2UTC (todayStart)
        todayStop = utils.date2UTC (todayStop)
        param = {"_bucket": self._bucket_prices, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_desc": False}
        logging.info('      Params: %s', param)

        query = '''
        from(bucket:_bucket)
        |> range(start: _start)
        |> filter(fn:(r) => r._measurement == "precios")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r._field == "ASK" or r._field == "BID" or r._field == "LAST" or r._field == "ASK_SIZE" or r._field == "LAST_SIZE" or r._field == "BID_SIZE")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "ASK", "ASK_SIZE", "BID", "BID_SIZE", "LAST", "LAST_SIZE"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = []
        if now > todayStart:
            result = self.query_data_frame(query, param)
        if len(result) == 0:
            result = self.influxGetLastPrice(symbol)
            logging.info ('Influx de Last: %s', result)

        if len(result) == 0:
            df_ = pd.DataFrame(columns = ['timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE'])
            return df_
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        logging.info('%s', result.iloc[-1])

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)

        #result.index = result.index + pd.DateOffset(hours=1)
        
        logging.info('%s', result.iloc[-1])

        return result

    def influxGetLastPrice(self, symbol):
        param = {"_bucket": self._bucket_prices, "_symbol": symbol, "_desc": False}

        query = '''
        from(bucket: _bucket)
        |> range(start: 0)
        |> filter(fn:(r) => r._measurement == "precios")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r._field == "ASK" or r._field == "BID" or r._field == "LAST" or r._field == "ASK_SIZE" or r._field == "LAST_SIZE" or r._field == "BID_SIZE")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "ASK", "ASK_SIZE", "BID", "BID_SIZE", "LAST", "LAST_SIZE"])
        |> sort(columns: ["_time"], desc: _desc)
        |> tail(n:1)
        '''
    
        result = self.query_data_frame(query, param)
        return result

    def influxGetOchlDataFrame (self, symbol):
        logging.info('Leyendo precios OCHL de Influx para: %s', symbol)
        todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
        todayStop = datetime.datetime.today()
        todayStart = todayStart.replace(hour = 15, minute = 0, second = 0, microsecond=0)
        todayStop = todayStop.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.date2UTC (todayStart)
        todayStop = utils.date2UTC (todayStop)
        param = {"_bucket": self._bucket_ohcl, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_desc": False}
        
        query = '''
        from(bucket: _bucket)
        |> range(start: _start)
        |> filter(fn:(r) => r._measurement == "precios")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r._field == "open" or r._field == "close" or r._field == "high" or r._field == "low")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "open", "close", "high", "low"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            dfcomp_ = pd.DataFrame(columns = ['timestamp','open','high','low','close'])
            return dfcomp_
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetPnLDataFrame (self, symbol):
        logging.info('Leyendo PnL de Influx para: %s', symbol)


        today = datetime.datetime.today()
        todayStart = today.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.date2UTC (todayStart)
        todayStop = utils.date2UTC (todayStop)
        param = {"_bucket": self._bucket_pnl, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_desc": False}
        query = '''
        from(bucket: _bucket)
        |> range(start: _start, stop: _stop)
        |> filter(fn:(r) => r._measurement == "pnl")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r._field == "dailyPnL" or r._field == "realizedPnL" or r._field == "unrealizedPnL")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "dailyPnL", "realizedPnL", "unrealizedPnL"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            df_temp = pd.DataFrame(columns = ['timestamp', 'dailyPnL','realizedPnL','unrealizedPnL'])
            return df_temp
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetExecDataFrame (self, symbol, strategyType):
        logging.info('Leyendo Execs de Influx para: %s', symbol)

        today = datetime.datetime.today()
        todayStart = today.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.date2UTC (todayStart)
        todayStop = utils.date2UTC (todayStop)
        param = {"_bucket": self._bucket_execs, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_strategyType": strategyType, "_desc": False}
        query = '''
        from(bucket: _bucket)
        |> range(start: _start, stop: _stop)
        |> filter(fn:(r) => r._measurement == "executions")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r.strategy == _strategyType)
        |> filter(fn:(r) => r._field == "OrderId" or r._field == "Quantity" or r._field == "Side")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "OrderId", "Quantity", "Side"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            df_temp = pd.DataFrame(columns = ['timestamp', 'OrderId','Quantity','Side'])
            return df_temp
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetExecCountDataFrame (self, symbol, strategyType):
        logging.info('Leyendo Execs de Influx para: %s', symbol)

        todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
        todayStop = datetime.datetime.today()
        todayStart = todayStart.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStop = todayStop.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.date2UTC (todayStart)
        todayStop = utils.date2UTC (todayStop)
        param = {"_bucket": self._bucket_execs, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_strategyType": strategyType, "_desc": False}
        query = '''
        from(bucket: _bucket)
        |> range(start: 0)
        |> filter(fn:(r) => r._measurement == "executions")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn: (r) => r["strategy"] == _strategyType)
        |> filter(fn:(r) => r._field == "ExecId")
        |> aggregateWindow(every: 24h, fn: count, createEmpty: false, timeSrc: "_start")
        |> sort(columns: ["_time"], desc: _desc)
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "ExecId"])
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            df_temp = pd.DataFrame(columns = ['timestamp', 'ExecCount'])
            return df_temp
    
        result.rename(columns = {'_time':'timestamp', 'ExecId':'ExecCount'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def query_data_frame(self,query, param):

        query_api = self._client.query_api()
        try:
            result = query_api.query_data_frame(org=self._org, query=query, params = param)
        except:
            logging.info('Error leyendo en influx', exc_info=True)
            result = []
        return result


        