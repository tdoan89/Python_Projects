import pandas as pd
from urllib2 import urlopen
import datetime as dt
import zipfile
from StringIO import StringIO
import csv
import statsmodels.api as sm


# Take stock time series data from Yahoo Finance
# Take zip_file time series data from Farma-French 3 factors monthly
# Unzip
# Take out the .csv file
# Read table
# Join table with stock data
# Check for time mismatch
# Anualize data
# Run regression


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


# Problem: mismatch index: Fama-French(2015-07-01 hh:mm:ss) vs Yahoo(2015-09-03) # ReIndexed Yahoo monthly data --> the problem no longer relevent for monthly data.
# Problem: missing data: Fama-French stops @ July: missing 1 months of data

def joinData(yahoo, ff):
    """Concatenate stock returns with Fama-French data. Calculate excess returns over the Risk-free rate.
        Params:
            yahoo: Stock returns data from YahooSReturn function
            ff: Fama-French data from getFF function
        Output:
            DataFrame with additional Ri-RF column."""
    yahoo.sort_index(ascending=True, inplace=True) # resort to complie with descending order of FF data

    #ff = ff[(ff.index.date>=start_date & (ff.index.date<=end_date)] # pick FF data according to Yahoo data
    #yahoo = yahoo.iloc[:,5:6]
    #print yahoo.shape[0]
    #print ff.shape[0]
    #ff.set_index(yahoo.index, inplace=True)

    data = yahoo.join(ff, how='inner')
    data['Ri-RF'] = data['Adj Close'] - data['RF'] # Calculate excess return over the risk-free
    #print data.shape[0]
    #price = yahoo_data[yahoo_data.columns.values[5]]
    return data

# Test Case (Remove hyphens to test):
# end_date = dt.date(dt.date.today().year, dt.date.today().month, 1) # For monthly data purpose bring the date to the beginning of the month # No longer needed
# start_date = dt.date(dt.date(2010,9,1).year, dt.date(2010,9,1).month, 1) # This one can be improve by dt.timedelta for a duration. ex: 10 years

end_date = dt.date.today()
start_date = dt.date.today() - dt.timedelta(days=365*10)
ticker = 'msft'
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
print "CAPM: \n", CAPM.summary()

# yahoo = getYahoo(ticker, start_date, end_date, fre)

# Remove hyphens to run program:
"""if __name__ == "__main__":
    while True:
        start_date = dt.datetime.strptime(raw_input('Enter the start date MM/DD/YYYY: '), "%m/%d/%Y")
        end_date = dt.datetime.strptime(raw_input('Enter the end date MM/DD/YYYY: '), "%m/%d/%Y")
        if start_date >= end_date:
            print "Start date has to be smaller then End date."
        else:
            break
    #start_date = dt.date.today() - dt.timedelta(days=365*10)
    ticker = raw_input('Enter the ticker of the stock: ')
    fre = 'm'
    yahoo = YahooSReturn(ticker, start_date, end_date, fre)
    ff = getFF()
    data = joinData(yahoo, ff)
    xdat = data['Ri-RF']
    ydat = sm.add_constant(data[['Mkt-RF', 'SMB', 'HML']])
    zdat = sm.add_constant(data['Mkt-RF'])
    regress = sm.OLS(xdat, ydat).fit()
    CAPM = sm.OLS(xdat, zdat).fit()
    a = regress.params
    b = CAPM.params
    print 'Fama French:\n alpha    : %s   \n Mkt_RF   : %s   \n SMB      : %s   \n HML      : %s   \n R-squared: %s \
    \nCAPM     : \n Intercept: %s \n Beta      : %s \n R-squared: %s' \
    %(a[0], a[1], a[2], a[3], regress.rsquared, b[0], b[1], CAPM.rsquared)"""


#ff[ff.index.year == 2015] - return specific year
#ff[(ff.index.date >= start_date) & (ff.index.date <=end_date)] - return a range of date
#ff.iloc[:,0:3] - return range of columns
#pd.DataFrame.isin()
#ff.sort_index(ascending=False, inplace=True)
#ff.columns.values
#pd.unique(DataFrame)
#yahoo['Adj Close'].describe() - return statistic for a data range
#DataFrame.groupby(.) - group data by a specific charateristic





#print getData(ticker,start_date,end_date)
# Monthly: http://real-chart.finance.yahoo.com/table.csv?s=AMZN&a=08&b=16&c=2010&d=08&e=9&f=2015&g=m&ignore=.csv
# Daily:   http://real-chart.finance.yahoo.com/table.csv?s=AMZN&a=08&b=16&c=2010&d=08&e=9&f=2015&g=d&ignore=.csv
#          http://real-chart.finance.yahoo.com/table.csv?s=AMZN&a=08&b=13&c=2014&d=08&e=13&f=2015&g=d&ignore=.csv
