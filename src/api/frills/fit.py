import numpy as np
from scipy.optimize import leastsq
from lmfit import minimize, Parameters, Parameter, fit_report

from nexpy.api.nexus import NXdata, NXparameters, NeXusError

class Fit(object):

    def __init__(self, data=None, functions=None):
        self.x = None
        self.y = None
        self.e = None
        self.set_data(data)
        self.functions = functions
        self.fit = None

    def set_data(self, data):
        if isinstance(data, NXdata):
            self.data = data
            signal = data.nxsignal
            axes = data.nxaxes[0]
            errors = data.nxerrors
            if len(signal.shape) != 1:
                raise ValueError("Fit only possible on one-dimensional data")
            self.x = axes.nxdata.astype(np.float64)
            self.y = signal.nxdata.astype(np.float64)
            if errors:
                self.e = errors.nxdata.astype(np.float64)
        else:
            raise TypeError("Must be an NXdata group")

    def get_model(self, x=None, f=None):
        if x is None: x = self.x
        model = np.zeros(x.shape,np.float64)
        if f:
            model = f.module.values(x, [p.value for p in f.parameters])
        else:
            for f in self.functions:
                model += f.module.values(x, [p.value for p in f.parameters])
        return model

    def residuals(self, parameters):
        if self.e is not None:
             return (self.y - self.get_model()) / self.e
        else:
            return self.y - self.get_model()

    def fit_data(self):
        """Run a scipy leastsq regression"""
        self.parameters = Parameters()
        for f in self.functions:
            for p in f.parameters:
                p.original_name = p.name
                self.parameters[f.name+p.name] = p
                if p.value is None:
                    p.value = 1.0
        self.result = minimize(self.residuals, self.parameters)
        for f in self.functions:
            for p in f.parameters:
                p.name = p.original_name

    def fit_report(self):
        return str(fit_report(self.parameters))

class Function(object):

    def __init__(self, name=None, module=None, parameters=[], function_index=0):
        self.name = name
        self.module = module
        self.parameters = parameters
        self.function_index = function_index

    def __lt__(self, other):
         return self.function_index < other.function_index