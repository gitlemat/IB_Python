import argparse
from datetime import datetime 
import logging

def formatCurrencySmall (cantidad, digits_integer):
    try:
        cantidad = float(cantidad)
    except:
        logging.error ('La cantidad no es correcta')
        return None
    if digits_integer < 1:
        return canidad

    template = 1
    fin = False

    tens_lim = 10**digits_integer
    
    while not fin:
        if (cantidad / template) < tens_lim:
            fin = True
            break
        template = template * 1000

    if template >= 1000000000:
        cantidad_out = cantidad/1000000000
        symbol = 'B'
    elif template >= 1000000:
        cantidad_out = cantidad/1000000
        symbol = 'M'
    elif template >= 1000:
        cantidad_out = cantidad/1000
        symbol = 'K'
    else:
        cantidad_out = cantidad
        symbol = ''
    
    if cantidad_out < 10: 
        currency = "${:,.2f}".format(cantidad_out)
    else:
        currency = "${:,.1f}".format(cantidad_out)
    currency += symbol

    print (currency, cantidad_out)

def main():
    '''
    cmdLineParser = argparse.ArgumentParser("api tests")
    cmdLineParser.add_argument("-b", "--brief", action="store_true", default=False, help="Only brief prints")

    args = cmdLineParser.parse_args()
    '''

    formatCurrencySmall(12367.1223445, 2)

if __name__ == '__main__':
    main()