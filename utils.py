from datetime import datetime   
import pytz
import glob

def date2UTC (fecha_local):

    local = pytz.timezone("Europe/Madrid")
    if fecha_local.tzinfo == None or fecha_local.tzinfo.utcoffset(fecha_local) == None:
        fecha_local = local.localize(fecha_local)
    
    utc_dt = fecha_local.astimezone(pytz.utc)

    return utc_dt

def date2local (fecha):

    local = pytz.timezone("Europe/Madrid")

    if fecha.tzinfo == None or fecha.tzinfo.utcoffset(fecha) == None:
        fecha_local_tz = local.localize(fecha)    
    else:
        fecha_local_tz = fecha.astimezone(local)

    return fecha_local_tz

def getLongestFileName ():
    max_len = 0
    for file in glob.glob("*.py"):
        l_len = len (file) - 3
        if l_len > max_len:
            max_len = l_len

    for file in glob.glob("webFE/*.py"):
        l_len = len (file) - 3
        if l_len > max_len:
            max_len = l_len

    return max_len
    