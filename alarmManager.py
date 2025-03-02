import datetime
import logging
import utils


logger = logging.getLogger(__name__)

class CAlarma:
    def __init__(self):
        pass
        self.alarm_list_ = {}
    
    def add_alarma (self, data):
        alarma = {}
        alarma['type']  = None

        if 'code' in data:
            code = data['code']
            alarma = self.alarm_from_code (code)

        if alarma['type'] == None:
            if 'type' in data:
                alarma['type'] = data['type']
            else:
                alarma['type'] = 'General'
            
            if 'severity' in data:
                alarma['severity'] = data['type']
            else:
                alarma['severity'] = 'LOW'
    
            if 'msg' in data:
                alarma['msg'] = data['type']
            else:
                alarma['msg'] = ''

        if code in self.alarm_list_ and self.alarm_list_[code]['state'] == 'ACTIVE':
            return

        timestamp = datetime.datetime.today()
        timestamp = utils.dateLocal2UTC (timestamp)

        alarma['timestamp_active'] = timestamp
        alarma['timestamp_clear'] = None
        alarma['state'] = 'ACTIVE'

        self.alarm_list_[code] = alarma

    def alarm_from_code(self, code):
        alarma = {}
        if code == 1001:
            alarma['type'] = 'Connection'
            alarma['severity'] = 'CRITICAL'
            alarma['msg'] = 'Conexion estre RODSIC y TWS caida'
        elif code == 1100:
            alarma['type'] = 'Connection'
            alarma['severity'] = 'CRITICAL'
            alarma['msg'] = 'Conexion estre TWS y IB Cloud'
        else:
            alarma['type'] = None
        
        return alarma


    def clear_alarma (self, code):

        if code not in self.alarm_list_:
            return -1
        
        timestamp = datetime.datetime.today()
        timestamp = utils.dateLocal2UTC (timestamp)

        self.alarm_list_[code]['timestamp_clear'] = timestamp
        self.alarm_list_[code]['state'] = 'CLEAR'

    def get_alarms (self):
        return self.alarm_list_

    
alarmManagerG = CAlarma()