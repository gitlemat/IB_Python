import pandas as pd
import matplotlib.pyplot as plt


symbols = []
symbol1 = {'symbol':'HEM23.CME', 'symbolSort':'HEM3', 'ratio': 1, 'used': False, 'last' : 0}
symbol2 = {'symbol':'HEN23.CME', 'symbolSort':'HEN3', 'ratio': -2, 'used': False, 'last' : 0 }
symbol3 = {'symbol':'HEQ23.CME', 'symbolSort':'HEQ3', 'ratio': 1, 'used': False, 'last' : 0 }

symbols.append(symbol1)
symbols.append(symbol2)
symbols.append(symbol3)

df_ = pd.DataFrame()

for symbol in symbols:
    df_local = pd.read_csv ('../market/' + symbol['symbol'] + '.csv')
    df_local.rename( columns={'Unnamed: 0':'timestamp'}, inplace=True )
    df_local['symbol'] = symbol['symbolSort']
    df_ = pd.concat([df_local, df_],ignore_index=True)
    df_sort = df_.sort_values(by=['timestamp'])
    df_sort.reset_index(drop=True, inplace=True)

df_sort['Butt_Close'] = 0

for index,tick in df_sort.iterrows():
    Close = 0
    AllUsed = True
    for symbol in symbols:
        if symbol['symbolSort'] == tick['symbol']:
            symbol['used'] = True
            symbol['last'] = tick['Close']
        elif symbol['used'] == False:
            AllUsed = False
        Close = Close + symbol['last'] * symbol['ratio']

    if not AllUsed:
        Close = 0
    df_sort.at[index, ['Butt_Close']] = Close

df_sort.plot(x='timestamp', y='Butt_Close')

plt.plot (df_sort['Butt_Close']) 
plt.show()

            


