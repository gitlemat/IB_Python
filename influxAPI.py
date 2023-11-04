import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import utils
import os
from dotenv import load_dotenv
import sys
import logging

UNSET_DOUBLE = sys.float_info.max


logger = logging.getLogger(__name__)

# You can generate an API token from the "API Tokens Tab" in the UI
# influx delete --bucket "ib_prices_1h_prod" --org "rodsic.com" --predicate '_measurement="precios"' --start "2020-12-23T21:37:00Z" --stop "2023-12-23T21:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="
# influx delete --bucket "ib_prices_1h_lab" --org "rodsic.com" --predicate '_measurement="precios"' --start "2020-12-23T21:37:00Z" --stop "2023-04-03T17:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="
# influx delete --bucket "ib_prices_1h" --org "rodsic.com" --predicate '_measurement="precios" AND symbol="LEM4-2LEQ4+LEV4"' --start "2020-12-23T21:37:00Z" --stop "2023-12-03T17:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="
# influx delete --bucket "ib_prices_1h" --org "rodsic.com" --predicate '_measurement="volume" AND symbol="LEM4-2LEQ4+LEV4"' --start "2020-12-23T21:37:00Z" --stop "2023-12-03T17:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="
# influx delete --bucket "ib_prices_lab" --org "rodsic.com" --predicate '_measurement="executions" AND symbol="HEZ3-2HEG4+HEJ4"' --start "2020-12-23T21:37:00Z" --stop "2023-09-03T17:39:00Z" --token "t5bQAqy-7adBzGjFCaKkNcqAJxMBEGOGlYk8X4E2AMQWb20xI-TFFOcOYb60k0Ewnt6lgnIPByzh8Cof5JTADA=="

# Buscar zeros:
# influx query 'from(bucket:"ib_prices_lab") |> range(start:-130d) |> filter(fn: (r) => r["_measurement"] == "precios") |> filter(fn: (r) => r["_field"] == "LAST") |> filter(fn: (r) => r["symbol"] == "LEQ3") |> filter(fn: (r) => r["_value"] == 0)'
# Borrar rango
# influx delete --bucket "ib_prices_lab" --predicate '_measurement="precios" AND symbol="LEQ3"' --start 2023-02-24T15:10:01.944930000Z --stop 2023-02-24T15:40:05.447333000Z 
# Work
# influx query 'from(bucket:"ib_prices_lab") |> range(start:-130d) |> filter(fn: (r) => r["_measurement"] == "executions") |> filter(fn: (r) => r["_field"] == "LAST") |> filter(fn: (r) => r["symbol"] == "LEQ3") |> filter(fn: (r) => r["_value"] == 0)'


class InfluxClient:
    def __init__(self): 
        load_dotenv()
        token = os.getenv('TOKEN')
        self._mode = os.getenv('MODE')
        self._org = 'rodsic.com'
        if self._mode == 'Lab':
            self._bucket_prices = 'ib_prices'
            self._bucket_ohcl = 'ib_prices_1h'
            self._bucket_pnl = 'ib_data_lab'
            self._bucket_execs = 'ib_data_lab'
            self._bucket_account = 'ib_data_lab'
            self._bucket_volume = 'ib_prices_1h'
        else:
            self._bucket_prices = 'ib_prices' 
            self._bucket_ohcl = 'ib_prices_1h'
            self._bucket_pnl = 'ib_data_prod'
            self._bucket_execs = 'ib_data_prod'
            self._bucket_account = 'ib_data_prod'
            self._bucket_volume = 'ib_prices_1h'
        self._client = InfluxDBClient(url="http://192.168.2.131:8086", token=token)
        

    def get_bucket (self, type):
        if type == 'precios':
            lbucket = self._bucket_prices
        if type == 'comp':
            lbucket = self._bucket_ohcl
        elif type == 'pnl':
            lbucket = self._bucket_pnl
        elif type == 'executions':
            lbucket = self._bucket_execs
        elif type == 'account':
            lbucket = self._bucket_account
        elif type == 'volume':
            lbucket = self._bucket_volume
        else:
            lbucket = self._bucket_prices

        return lbucket

    def write_data(self,data, type='precios', write_option=SYNCHRONOUS):
        # measurementName,tagKey=tagValue fieldKey1="fieldValue1",fieldKey2=fieldValue2 timestamp
        # There’s a space between the tagValue and the first fieldKey, and another space between the last fieldValue and timeStamp
        # timestamp is optional
        # IC.write_data(["MSFT,stock=MSFT Open=62.79,High=63.84,Low=62.13"])

        
        #write_api = self._client.write_api(write_option)
        lbucket = self.get_bucket(type)

        with self._client.write_api(write_option) as write_api:
            try:
                logging.debug ('Escribiendo en influx esto (%s): %s', type, data)
                write_api.write(bucket=lbucket, org=self._org, record=data)
            except:
                logging.error ("Exception al escribir en Influx occurred", exc_info=True)
                logging.error ("Ha sido al escribir esto (%s): %s", type, data)

    def write_dataframe(self,dataframe, params, write_option=SYNCHRONOUS):
        # measurementName,tagKey=tagValue fieldKey1="fieldValue1",fieldKey2=fieldValue2 timestamp
        # There’s a space between the tagValue and the first fieldKey, and another space between the last fieldValue and timeStamp
        # timestamp is optional
        # IC.write_data(["MSFT,stock=MSFT Open=62.79,High=63.84,Low=62.13"])

        
        #write_api = self._client.write_api(write_option)

        type = params['type']
        meassurement = params['measurement']
        tags = params['tags']
        
        lbucket = self.get_bucket(type)

        with self._client.write_api(write_option) as write_api:

            try:
                logging.debug ('Escribiendo en influx esto: %s', dataframe)
                write_api.write(bucket=lbucket, org=self._org, record=dataframe, 
                    data_frame_measurement_name=meassurement, data_frame_tag_columns=[tags])
            except:
                logging.error ("Exception occurred", exc_info=True)
                return False
            else:
                return True

    def influxGetTodayDataFrame (self, symbol):
        logging.info('Leyendo precios de hoy de Influx para: %s', symbol)
        now  = datetime.datetime.now()
        now = utils.dateLocal2UTC (now) # Para poder comparar
        today = datetime.datetime.today()
        todayStart = today.replace(hour = 15, minute = 0, second = 0, microsecond=0)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
        param = {"_bucket": self._bucket_prices, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_desc": False}
        logging.debug('      Params: %s', param)

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
            logging.debug ('Influx de Last: %s', result)

        if len(result) == 0:
            df_ = pd.DataFrame(columns = ['timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE'])
            df_.set_index('timestamp', inplace=True)
            df_.index = pd.to_datetime(df_.index)
            return df_
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            logging.error('[%s] - Fallo al normalizar fechas con TZ', symbol)
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')

        #result.index = result.index + pd.DateOffset(hours=1)
        
        logging.debug('%s', result.iloc[-1])

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
        logging.debug('Leyendo precios OCHL de Influx para: %s', symbol)
        todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
        todayStop = datetime.datetime.today()
        todayStart = todayStart.replace(hour = 15, minute = 0, second = 0, microsecond=0)
        todayStop = todayStop.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
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
            dfcomp_.set_index('timestamp', inplace=True)
            return dfcomp_
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetVolumelDataFrame (self, symbol):
        logging.debug('Leyendo Volumenes de Influx para: %s', symbol)
        todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
        todayStop = datetime.datetime.today()
        todayStart = todayStart.replace(hour = 15, minute = 0, second = 0, microsecond=0)
        todayStop = todayStop.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
        param = {"_bucket": self._bucket_volume, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_desc": False}
        
        query = '''
        from(bucket: _bucket)
        |> range(start: _start)
        |> filter(fn:(r) => r._measurement == "volume")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r._field == "Volume")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "Volume"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            dfvol_ = pd.DataFrame(columns = ['timestamp','Volume'])
            dfvol_.set_index('timestamp', inplace=True)
            return dfvol_
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetPnLDataFrame (self, symbol):
        logging.info('Leyendo PnL de Influx para: %s', symbol)


        today = datetime.datetime.today()
        todayStart = today.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
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
            df_temp.set_index('timestamp', inplace=True)
            return df_temp
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetExecDataFrame (self, symbol, strategyType):
        logging.info('Leyendo Execs de Influx para: %s', symbol)

        today = datetime.datetime.today()
        todayStart = today.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStart = todayStart - datetime.timedelta(days=180)
        todayStop = today.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
        param = {"_bucket": self._bucket_execs, "_start": todayStart, "_stop": todayStop, "_symbol": symbol, "_strategyType": strategyType, "_desc": False}
        query = '''
        from(bucket: _bucket)
        |> range(start: _start, stop: _stop)
        |> filter(fn:(r) => r._measurement == "executions")
        |> filter(fn:(r) => r.symbol == _symbol)
        |> filter(fn:(r) => r.strategy == _strategyType)
        |> filter(fn:(r) => r["_field"] == "Commission" or r["_field"] == "OrderId" or r["_field"] == "ExecId" or r["_field"] == "Quantity" or r["_field"] == "Side" or r["_field"] == "RealizedPnL" or r["_field"] == "FillPrice" or r["_field"] == "Side" or r["_field"] == "RealizedPnL" or r["_field"] == "PermId")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "ExecId", "PermId", "OrderId", "Quantity", "Side", "RealizedPnL", "Commission", "FillPrice"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            df_temp = pd.DataFrame(columns = ['timestamp', 'ExecId', 'PermId', 'OrderId', 'Quantity', 'Side', 'RealizedPnL', 'Commission', 'FillPrice'])
            df_temp.set_index('timestamp', inplace=True)
            return df_temp
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetExecCountDataFrame (self, symbol, strategyType):
        logging.info('Leyendo Execs de Influx para: %s', symbol)

        todayStart = datetime.datetime.today() - datetime.timedelta(days=180)
        todayStop = datetime.datetime.today()
        todayStart = todayStart.replace(hour = 0, minute = 0, second = 0, microsecond=0)
        todayStop = todayStop.replace(hour = 23, minute = 59, second = 59, microsecond=999999)
        todayStart = utils.dateLocal2UTC (todayStart)
        todayStop = utils.dateLocal2UTC (todayStop)
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
            df_temp.set_index('timestamp', inplace=True)
            return df_temp
    
        result.rename(columns = {'_time':'timestamp', 'ExecId':'ExecCount'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxGetAccountDataFrame (self, accountId):
        logging.info('Leyendo Account Data de Influx para: %s', accountId)

        keys_account = [
            'timestamp', 'accountId', 'Cushion', 'LookAheadNextChange', 'AccruedCash', 
            'AvailableFunds', 'BuyingPower', 'EquityWithLoanValue', 'ExcessLiquidity', 'FullAvailableFunds',
            'FullExcessLiquidity','FullInitMarginReq','FullMaintMarginReq','GrossPositionValue','InitMarginReq',
            'LookAheadAvailableFunds','LookAheadExcessLiquidity','LookAheadInitMarginReq','LookAheadMaintMarginReq',
            'MaintMarginReq','NetLiquidation','TotalCashValue'
        ]

        param = {"_bucket": self._bucket_account, "_accountId": accountId, "_desc": False}

        query = '''
        from(bucket: _bucket)
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "account")
        |> filter(fn: (r) => r["accountId"] == _accountId)
        |> drop(columns: ["accountId"])
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> drop(columns: ["_measurement", "_start", "_stop"])
        |> sort(columns: ["_time"], desc: _desc)
        '''

        result = self.query_data_frame(query, param)

        if len(result) == 0:
            df_temp = pd.DataFrame(columns = keys_account)
            df_temp.set_index('timestamp', inplace=True)
            return df_temp
    
        result.rename(columns = {'_time':'timestamp'}, inplace = True)
        result.drop(columns=['result','table'], inplace=True)
        result.set_index('timestamp', inplace=True)

        try:
            result.index = result.index.tz_convert('Europe/Madrid')
        except:
            result.index = result.index.tz_localize(None)
            result.index = result.index.tz_localize('Europe/Madrid')
        #result.index = result.index + pd.DateOffset(hours=1)

        logging.debug('%s', result)

        return result

    def influxUpdatePrices (self, symbol_, datadf):
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']

        records = []
        datadf['timestamp'] = datadf.index
        for index, row in datadf.iterrows():
            
            data = row.to_dict()
            record = {}
            tags = {'symbol': symbol_}
            time = data['timestamp']
            time = utils.dateLocal2UTC (time)
            
            fields_prices = {}
    
            
            for key in keys_prices:
                if key in data:
                    fields_prices[key] = data[key]
    
            record = {
                "measurement": "precios", 
                "tags": tags,
                "fields": fields_prices,
                "time": time,
            }
            if len(fields_prices) > 0:
                records.append(record)

        #logging.info ('Escribo valor para %s: %s', symbol, records)

        if len(records) > 0:
            self.write_data(records, 'precios')

    def influxUpdatePnL (self, symbol_, datadf):
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        
        records = []
        datadf['timestamp'] = datadf.index
        for index, row in datadf.iterrows():
            
            data = row.to_dict()
            record = {}
            tags = {'symbol': symbol_}
            time = data['timestamp']
            time = utils.dateLocal2UTC (time)
            
            fields_pnl = {}
    
            for key in keys_pnl:
                if key in data:
                    fields_pnl[key] = data[key]
    
    
            record = {
                "measurement": "pnl", 
                "tags": tags,
                "fields": fields_pnl,
                "time": time,
            }
            if len(fields_pnl) > 0:
                records.append(record)

        if len(records) > 0:
            self.write_data(records, 'pnl')

    def influxUpdateVolume (self, symbol_, data):
        keys_pnl = ['Volume']
        
        records = []
        record = {}
        tags = {'symbol': symbol_}
        time = data['timestamp']
        time = utils.date2UTC (time)
        
        fields_volume = {}

        for key in keys_pnl:
            if key in data:
                fields_volume[key] = data[key]


        record = {
            "measurement": "volume", 
            "tags": tags,
            "fields": fields_volume,
            "time": time,
        }
        records.append(record)

        if len(fields_volume) > 0:
            self.write_data(records, 'volume')

    def influxUpdateAccountData (self, accountId_, data):
        keys_account = [
            'accountId', 'Cushion', 'LookAheadNextChange', 'AccruedCash', 
            'AvailableFunds', 'BuyingPower', 'EquityWithLoanValue', 'ExcessLiquidity', 'FullAvailableFunds',
            'FullExcessLiquidity','FullInitMarginReq','FullMaintMarginReq','GrossPositionValue','InitMarginReq',
            'LookAheadAvailableFunds','LookAheadExcessLiquidity','LookAheadInitMarginReq','LookAheadMaintMarginReq',
            'MaintMarginReq','NetLiquidation','TotalCashValue'
        ]
        
        records = []
        record = {}
        tags = {'accountId': accountId_}
        time = data['timestamp']
        time = utils.dateLocal2UTC (time)
        
        fields_influx = {}

        for key in keys_account:
            if key in data:
                if data[key] != None and data[key] != UNSET_DOUBLE:
                    fields_influx[key] = data[key]


        record = {
            "measurement": "account", 
            "tags": tags,
            "fields": fields_influx,
            "time": time,
        }

        records.append(record)

        if len(fields_influx) > 0:
            self.write_data(records, 'account')
    

    def query_data_frame(self,query, param):

        query_api = self._client.query_api()
        try:
            result = query_api.query_data_frame(org=self._org, query=query, params = param)
        except:
            logging.info('Error leyendo en influx', exc_info=True)
            result = []
        return result


        