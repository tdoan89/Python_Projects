from OptionsBS import optionsBS
from numpy import exp

goog = optionsBS(50, 55, 0.02, 0.05, 0.4, 91)

print goog()
print goog.impVol_call(3)
print goog.impVol_put(6)
#print goog.theta_call()

#put-call-parity check
print 'put-call-parity: ' + str(goog.s0*exp(-goog.q*goog.t) + goog.put() - goog.call() - goog.k*exp(-goog.rf*goog.t))

###  First trade: Gamma Scalp

###  Position: (long call - short underlying)
###  Position: C - delta*S
###  First derivatives: dC - delta = 0
###  Second derivatives: d2C
###  Taylor Expansion:
###  Beginning Outflow:


# States  of the stock during the day:
stock = optionsBS(100, 100, 0.02, 0.05, 0.4, 91)
stock1 = optionsBS(110, 100, 0.02, 0.05, 0.4, 91)
stock2 = optionsBS(80, 100, 0.02, 0.05, 0.4, 91)
stock3 = optionsBS(100, 100, 0.02, 0.05, 0.4, 91)

print "Price Movement during the day: ", stock.s0, " === ", stock1.s0, " === ", stock2.s0, " === ", stock3.s0

# Calculate the initial cashflow:
neutral = stock.call() - stock.call_delta()*stock.s0
print "Initial delta neutral: ", neutral

# Calculate transaction cost during the day::
t1 = (stock1.call_delta() - stock.call_delta())*stock1.s0
t2 = (stock2.call_delta() - stock1.call_delta())*stock2.s0
t3 = (stock3.call_delta() - stock2.call_delta())*stock3.s0

print "P&L during the day: ", t1, t2, t3

netPosition = t1 + t2 + t3

print "Total P&L: ", netPosition
print "Total P&L minus theta:", netPosition + stock.theta_call()


#  Construct a test case

#s0 =
