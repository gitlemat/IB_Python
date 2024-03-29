from datetime import datetime   
import pytz
import glob
import re

def dateLocal2UTC (fecha_local):

    local = pytz.timezone("Europe/Madrid")
 
    if fecha_local.tzinfo == None or fecha_local.tzinfo.utcoffset(fecha_local) == None:
        fecha_local = local.localize(fecha_local)
    
    utc_dt = fecha_local.astimezone(pytz.utc)

    return utc_dt

def date2UTC (fecha_local):

    if fecha_local.tzinfo == None or fecha_local.tzinfo.utcoffset(fecha_local) == None:
        fecha_local = pytz.utc.localize(fecha_local)
    else:
        fecha_local = fecha_local.astimezone(pytz.utc)

    return fecha_local

def date2Chicago (fecha_local):

    cme = pytz.timezone("America/Chicago")
    if fecha_local.tzinfo == None or fecha_local.tzinfo.utcoffset(fecha_local) == None:
        fecha_local = cme.localize(fecha_local)
    else:
        fecha_local = fecha_local.astimezone(cme)

    return fecha_local

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

def contractCode2list (contractCode):
    contractList = []
    if contractCode[0] != '+' and contractCode[0] != '-':
        contractCode = '+' + contractCode
    contractCode = contractCode.replace('-',',-')
    contractCode = contractCode.replace('+',',+')
    if contractCode[0] == ',':   # Va a pasar siempre
        contractCode = contractCode[1:]
    codesList = contractCode.split(',')
    
    for code in codesList:
        cont = {}
        if code[0] == '-':
            cont['action'] = 'SELL'
        else:
            cont['action'] = 'BUY'
        code = code[1:]
        if code[0].isnumeric():
            cont['ratio'] = int(code[0])
            code = code [1:]
        else:
            cont['ratio'] = 1
        cont ['code'] = code
        contractList.append(cont)
    return contractList

def getLotesContratoBySymbol(symbol):
    
    mapping = {
        'HE': 400,
        'LE': 400,
    }

    pos = re.search(r'\d', symbol).start()
    main_symbol = symbol[0:pos]

    if not main_symbol in mapping:
        return 400
    else:
        return mapping[main_symbol]
    
