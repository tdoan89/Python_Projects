import pandas as pd
from urllib2 import urlopen
import datetime as dt
import zipfile
from StringIO import StringIO
import csv
import statsmodels.api as sm
from bs4 import BeautifulSoup

# This project use source code from Fama_French
# Given a list of comparable firm, calculate bottom up Beta.
# Step 1: Regression for a list of Beta (leverage Beta)
# Step 2: Take average of the leveraged Betas
# Step 3: Retrieve a list of D/E ratio from Yahoo Finance, take the median to eliminate outlier (how about aggregate D/E?) (should have used more reliable sources)
# Step 4: Back out the unlevered Beta: unlevered Beta = levered Beta/(1+(1-t)*D/E)
# Step 5: Adjust for cash: Cash Adjusted Beta = unlevered Beta/(1-Cash/FirmValue)
# Step 6: Given a specific company, calculate Business risk Beta = Pure Beta*(1+(1-t)*D/E)

# New method to read Yahoo Key Statistics:

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
    alist.insert(0, 'Stats')
    df2.columns = alist
    return df2

alist = ['amzn', 'msft','pcln','aapl','gas']
