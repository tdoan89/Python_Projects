import pandas as pd
from urllib2 import urlopen
import numpy as np
import datetime as dt
import zipfile
from StringIO import StringIO
import csv
import statsmodels.api as sm


# This project use source code from Fama_French
# Given a list of comparable firm, calculate bottom up Beta.
# Step 1: Regression for a list of Beta (leverage Beta)
# Step 2: Take average of the leveraged Betas
# Step 3: Retrieve a list of D/E ratio from Yahoo Finance, take the median to eliminate outlier (how about aggregate D/E?) (should have used more reliable sources)
# Step 4: Back out the unlevered Beta: unlevered Beta = levered Beta/(1+(1-t)*D/E)
# Step 5: Adjust for cash: Cash Adjusted Beta = unlevered Beta/(1-Cash/FirmValue)
# Step 6: Given a specific company, calculate Business risk Beta = Pure Beta*(1+(1-t)*D/E)

# New method to read Yahoo Key Statistics:
from bs4 import BeautifulSoup
def KeyStats(ticker):
    html = urlopen("http://finance.yahoo.com/q/ks?s="+ticker+"+Key+Statistics")
    soup = BeautifulSoup(html, 'html.parser')
    tables = [table for table in soup.find_all("table", "yfnc_datamodoutline1")]
    df = pd.DataFrame()
    datas = []
    for table in tables:

        headings = [th.get_text() for th in table.find_all("td", "yfnc_tablehead1")]
        values = [td.get_text() for td in table.find_all("td", "yfnc_tabledata1")]
        datas.append(pd.DataFrame(zip(headings, values)))

    df = pd.concat(datas, ignore_index=True)

    return df

def StockStats(alist):
    if alist == []:
        print "There is no stock in the list."
    else:
        df1 = KeyStats(alist[0])
        if alist[1:] == []:
            exit
        else:
            tables = [df1]
            for stock in alist[1:]:
                table = KeyStats(stock).ix[:,1]
                tables.append(table)
            df2 = pd.concat(tables, axis=1)
    another_list = alist[:]
    another_list.insert(0, 'Stats')
    df2.columns = another_list
    return df2


# Get data of a stock from Yahoo Finance
# Yahoo data delay 1 month
def getYahoo(Ticker, start_date, end_date, frequency):
    """Get stock price from Yahoo Finance.
        Params:
            Ticker: a string - ticker of the stock
            start_date, end_date: (datetime.date) format
            frequency:'m' for monthly data, 'd' for daily data, 'w' for weekly data (not recommended)
        Output:
            pandas.DataFrame
        Note: Yahoo csv file missing one first day compare to the displayed table. If you want that day, enter a day earlier for the start_date"""
    try:
        url = 'http://real-chart.finance.yahoo.com/table.csv?s='
        # Note 1 (droped): Yahoo monthly data delays 1 month. Output data is relabeled. Ex: August price is in September: relabeled to August
        # Note 2: The retrieving method is to offset the start_date & end_date by one month. Yahoo is weird!
        data = pd.read_csv(urlopen('%s%s&a=%s&b=%s&c=%s&d=%s&e=%s&f=%s&g=%s&ignore=.csv'%(url,Ticker, start_date.month-1,\
                                        start_date.day, start_date.year, end_date.month-1, end_date.day, end_date.year, frequency)),\
                                        index_col='Date', parse_dates= True)
        # Relabeled montly data:
        if frequency == 'm':
            # Drop the relabeled: data.index = data.index.map(lambda x: dt.date(x.year, x.month, 1) - dt.timedelta(days=1)) # Move the date back to one month
            data.index = data.index.map(lambda x: dt.date(x.year, x.month, 1)) # Bring the date to the first day of the month
        return data
    except Exception, e:
        print 'Fail to collect data :', e

# Calculating arithmetic return:
def YahooSReturn(Ticker, start_date, end_date, frequency):
    """Get annualized stock return based on Yahoo Finance data.
        Params:
            Ticker: a string - ticker of the stock
            start_date, end_date: (datetime.date) format
            frequency:'m' for monthly data, 'd' for daily data, 'w' for weekly data (not recommended)
        Output:
            pandas.DataFrame
        Note: Yahoo monthly data delays 1 month. Output data is relabeled."""
    a_dict = {'m':dt.datetime(start_date.year, start_date.month -1, 1),\
                'd': start_date - dt.timedelta(days=1),\
                'w': start_date - dt.timedelta(days=7)} # offset the start_date to get a full period of return
    data = getYahoo(Ticker, a_dict[frequency], end_date, frequency).ix[:,5:6] # pull data only take the Adj_Close column
    sreturn = ((data/data.shift(-1)) - 1)*100 # Rolling simple return
    return sreturn[:-1]

# Get Fama-French Data
def getFF():
    """Get Fama-French 3 factors data. Right now can only return monthly data."""
    try:
        url = 'http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip'
        zip_file = zipfile.ZipFile(StringIO(urlopen(url).read()), 'r') # Retrieve the zip file, can only be read in text stream data # Unzip
        csv_file = zip_file.open(zip_file.namelist()[0])             # Extract the csv file contains data (only 1 file in the zip file)
        data = csv.reader(csv_file)                                 # Read data

        # Parse the csv file to DataFrame:
        # Create a table of lists:
        table = []
        counter = 0
        for row in data:
            if row == []:
                counter += 1
                if counter == 2:
                    break
            table.append(row)

        # Create a header row
        table = table[3:] # Remove first 3 rows
        header = table.pop(0) # Assign the first row of the new table  to be header
        header[0] = 'Date'  # Name the first column to be used as Index

        # Write the table to a DataFrame
        ff = pd.DataFrame(table, columns=header, dtype=float)
        #ff['Date'].map(lambda x: dt.date(year=int(x)/100, month=int(x)%100)) - attemp to remap index but not a viable option without days
        format = '%Y%m.0'
        ff.Date = pd.to_datetime(ff.Date, format=format)
        ff.set_index('Date', drop=True, inplace=True)
        return ff
    except Exception,e:
        print "For some reasons unable to retreive data: ", e, ".Hint: Check your internet connection."


def joinData(yahoo, ff):
    """Concatenate stock returns with Fama-French data. Calculate excess returns over the Risk-free rate.
        Params:
            yahoo: Stock returns data from YahooSReturn function
            ff: Fama-French data from getFF function
        Output:
            DataFrame with additional Ri-RF column."""
    yahoo.sort_index(ascending=True, inplace=True) # resort to complie with descending order of FF data
    data = yahoo.join(ff, how='inner')
    data['Ri-RF'] = data['Adj Close'] - data['RF'] # Calculate excess return over the risk-free
    #print data.shape[0]
    #price = yahoo_data[yahoo_data.columns.values[5]]
    return data

"""# Test Case (Remove hyphens to test):
end_date = dt.date.today()
start_date = dt.date.today() - dt.timedelta(days=365*10)
ticker = 'pcln'
fre = 'm'
yahoo = YahooSReturn(ticker, start_date, end_date, fre)
ff = getFF()
data = joinData(yahoo, ff)
xdat = data['Ri-RF']
ydat = sm.add_constant(data[['Mkt-RF', 'SMB', 'HML']])
zdat = sm.add_constant(data['Mkt-RF'])
regress = sm.OLS(xdat, ydat).fit()
CAPM = sm.OLS(xdat, zdat).fit()
print "Fama French: \n", regress.summary()
print "\n \n"
print "CAPM: \n", CAPM.summary()"""


#Bottom-up Beta Calculation:
alist = ['amzn', 'msft', 'pcln', 'aapl', 'gas']

stats = StockStats(alist)
DE = stats.ix[26,1:].astype(float)
DE_median = np.median(DE)

end_date = dt.date.today()
start_date = end_date - dt.timedelta(days=365*10)

data = []
for stock in alist:
    df = YahooSReturn(stock, start_date, end_date, 'm')
    data.append(df)
stock_data = pd.concat(data, axis=1)
stock_data.columns = alist
ff = getFF()

stock_data.sort_index(ascending=True, inplace=True) # resort to complie with descending order of FF data
df = stock_data.join(ff, how='inner')
for column in df.columns[:len(alist)]:
    df[column] = df[column] - df['RF']

beta = []
ydat = sm.add_constant(df['Mkt-RF'])
for stock in alist:
    CAPM = sm.OLS(df[stock], ydat).fit().params[1]
    beta.append(CAPM)

Beta = dict(zip(alist, beta))

mean_beta = sum(beta)/len(beta)

t = 0.35
unlevered_beta = mean_beta/(1+(1-t)*DE_median/100)

def parse_string(astring):
    if astring[-1] == 'B':
        num = float(astring[:-1])*10**9
    elif astring[-1] == 'M':
        num = float(astring[:-1])*10**6
    return num
stock = KeyStats('f')
stock_cash = parse_string(stock.ix[23,1])
stock_FV = parse_string(stock.ix[1,1])
stock_DE = stock.ix[26,1:].astype(float)

CashAdjustedBeta = unlevered_beta/(1-stock_cash/stock_FV)

stock_beta = CashAdjustedBeta*(1+(1-t)*stock_DE/100)

print stock_beta
