from math import exp, log, sqrt
from scipy.stats import norm
import scipy.optimize as optimize
from tabulate import tabulate

class optionsBS(object):
    def __init__(self, s0, k, q, rf, sig, t):
        self.s0 = float(s0)
        self.q = float(q)
        self.k = float(k)
        self.rf = float(rf)
        self.t = t/365.0
        self.sig = float(sig)
        self.s_adj =  self.s0*exp(-self.q*self.t)
        self.d1 = (log(self.s_adj/self.k) + (self.rf+(self.sig**2)/2)*self.t)/(self.sig*sqrt(self.t))
        self.d2 = self.d1 - self.sig*self.t**0.5

    def call(self):
        return self.s_adj*norm.cdf(self.d1) - self.k*exp(-self.rf*self.t)*norm.cdf(self.d2)

    def put(self):
        return self.k*exp(-self.rf*self.t)*norm.cdf(-self.d2) - self.s_adj*norm.cdf(-self.d1)

    def call_delta(self):
        return exp(-self.q*self.t)*norm.cdf(self.d1)

    def put_delta(self):
        return  -exp(-self.q*self.t)*norm.cdf(-self.d1)

    # Rho:
    def call_rho(self):
        return self.k*self.t*exp(-self.rf*self.t)*norm.cdf(self.d2)

    def put_rho(self):
        return -self.k*self.t*exp(-self.rf*self.t)*norm.cdf(-self.d2)

    # Theta:
    def theta_call(self):
        theta =  -self.s0*norm.pdf(self.d1)*self.sig*exp(-self.q*self.t)/(2*sqrt(self.t)) + \
               self.q*self.s0*norm.cdf(self.d1)*exp(-self.q*self.t) - self.k*self.rf*exp(-self.rf*self.t)*norm.cdf(self.d2)
        return theta/365

    def theta_put(self):
        theta =  -self.s0*norm.pdf(self.d1)*self.sig*exp(-self.q*self.t)/(2*sqrt(self.t)) - \
               self.q*self.s0*norm.cdf(-self.d1)*exp(-self.q*self.t) + self.k*self.rf*exp(-self.rf*self.t)*norm.cdf(-self.d2)
        return theta/365

    # Gamma:
    def gamma(self):
        return norm.pdf(self.d1)*exp(-self.q*self.t)/(self.s0*self.sig*sqrt(self.t))

    # Vega:
    def vega(self):
        return self.s0*sqrt(self.t)*norm.pdf(self.d1)*exp(-self.q*self.t)

    def __call__(self):
        table = [["Call", self.call(), self.call_delta(), self.call_rho(), self.theta_call(), self.gamma(), self.vega()],
             ["Put", self.put(), self.put_delta(), self.put_rho(), self.theta_put(), self.gamma(), self.vega()]]
        return tabulate(table, headers=['Options', 'Price', 'Delta', 'Rho', 'Theta', 'Gamma', 'Vega'], tablefmt='grid')

    def impVol_call(self, call):
        func = lambda sig_est: optionsBS(self.s0, self.k, self.q, self.rf, sig_est, self.t*365).call() - call
        sig_est = optimize.fsolve(func, x0=0.20)
        return sig_est

    def impVol_put(self, put):
        func = lambda sig_est: optionsBS(self.s0, self.k, self.q, self.rf, sig_est, self.t*365).put() - put
        sig_est = optimize.fsolve(func, x0=0.20)
        return sig_est
