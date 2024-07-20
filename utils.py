from datetime import datetime 
import logging

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
    
def letter2Month (letter):
    letterDict = {}
    letterDict['F'] = '01'
    letterDict['G'] = '02'
    letterDict['H'] = '03'
    letterDict['J'] = '04'
    letterDict['K'] = '05'
    letterDict['M'] = '06'
    letterDict['N'] = '07'
    letterDict['Q'] = '08'
    letterDict['U'] = '09'
    letterDict['V'] = '10'
    letterDict['X'] = '11'
    letterDict['Z'] = '12'
    if letter in letterDict:
        return letterDict[letter]
    else:
        return None
    

def month2Letter (month):
    letterDict = {}
    letterDict[1] = 'F'
    letterDict[2] = 'G'
    letterDict[3] = 'H'
    letterDict[4] = 'J'
    letterDict[5] = 'K'
    letterDict[6] = 'M'
    letterDict[7] = 'N'
    letterDict[8] = 'Q'
    letterDict[9] = 'U'
    letterDict[10] = 'V'
    letterDict[11] = 'X'
    letterDict[12] = 'Z'

    try:
        month = int(month)
    except:
        logging.error('Error al convertir mes a letra: %s', month)
        return None
    
    if month in letterDict:
        return letterDict[month]
    else:
        return None
    
def code2name (code):
    codeDict = {}
    codeDict['HE'] = 'Lean Hogs'
    codeDict['LE'] = 'Live Cattle'
    codeDict['ZL'] = 'Soybean Oil'
    codeDict['CC'] = 'Cocoa'
    codeDict['CL'] = 'Crude Oil'
    codeDict['GF'] = 'Feeder Cattle'
    codeDict['HO'] = 'Heat Oil'
    codeDict['NG'] = 'Natural Gas'
    codeDict['RB'] = 'RBOB Gasoline'
    codeDict['ZM'] = 'Soybean Meal'
    codeDict['ZS'] = 'Soybean'
    codeDict['ZC'] = 'Corn'
    codeDict['ZW'] = 'Chicago SRW Wheat'

    if code in codeDict:
        return codeDict[code]
    else:
        return None
    
def codesFromYear (res_cl_, year):
    new_cl_ = []
    for symbol in res_cl_:
        code_decomp = contractCode2list(symbol)
        codeDict = code_decomp[0]
        
        code = codeDict['code']
        while code[-1].isnumeric():
            code = code[:-1]
        try:
            yearSymbol = int(codeDict['code'][len(code):])
        except:
            logging.error('Problema leyendo en año. Codigo %s', codeDict['code']) 
            yearSymbol = 0

        if yearSymbol > year:
            new_cl_.append(symbol)

    return new_cl_

def last2yearsFromFamily (family):
    code_decomp = contractCode2list(family)

    ahora = datetime.now()
    
    # Creamos el simbolo de year1
    
    nLeg = 0
    prevMonth = 0
    symbol1 = ''
    symbol2 = ''
    year1 = ahora.year
    for codeLeg in code_decomp:
        symbol = ''
        nLeg += 1
        if codeLeg['action'] == 'SELL':
            symbol += '-'
        elif nLeg > 1:
            symbol += '+'
        if codeLeg['ratio'] > 1:
            symbol += str(codeLeg['ratio'])
        code = codeLeg['code']
        while code[-1].isnumeric():
            code = code[:-1]

        monthLetter = code[-1]
        month1 = int(letter2Month(monthLetter))

        
        if nLeg == 1 and ahora.month >= month1:
            year1 = ahora.year + 1
        
        if month1 <= prevMonth:
            year1 += 1

        prevMonth = month1
        year_srt1 = str(year1)[-2:]
        year_srt2 = str(year1 + 1)[-2:]

        symbol1 += symbol + code + year_srt1
        symbol2 += symbol + code + year_srt2

    symbols = []
    symbols.append(symbol1)
    symbols.append(symbol2)

    return symbols

        