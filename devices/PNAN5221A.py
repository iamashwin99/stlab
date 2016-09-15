import visa
import numpy as np
from stlab.devices.instrument import instrument
from collections import OrderedDict

def numtostr(mystr):
    return '%20.15e' % mystr
#    return '%20.10f' % mystr

class PNAN5221A(instrument):
    def __init__(self,addr='TCPIP::192.168.1.105::INSTR',reset=True,verb=True):
        super(PNAN5221A, self).__init__(addr,reset,verb)
        #Remove timeout so long measurements do not produce -420 "Unterminated Query"
        self.dev.timeout = None 
        self.id()
        if reset:
            self.write('INIT:CONT 0') #Turn off continuous mode
            self.TwoPortSetup()
    def SinglePortSetup(self):
        trcnames = self.GetTrcNames()
        if len(trcnames) == 1:
            if trcnames[0] == 'S11':
                return
        self.ClearAll()
        self.write('DISP:WIND1 ON')
        tracenames = ['CH1_S11']
        measnames = ['S11']
        for i,(meas,trc) in enumerate(zip(measnames,tracenames)):
            self.write("CALC:PAR:DEF:EXT '%s', '%s'" % (trc,meas))
            self.write("DISP:WIND:TRAC%d:FEED '%s'" % (i+1,trc))
    def TwoPortSetup(self):
        trcnames = self.GetTrcNames()
        measnames = ['S11', 'S21', 'S12', 'S22']
        if trcnames == measnames:
            return
        self.ClearAll()
        self.write('DISP:WIND1 ON')
        tracenames = ['CH1_S11','CH1_S21','CH1_S12','CH1_S22']
        for i,(meas,trc) in enumerate(zip(measnames,tracenames)):
            self.write("CALC:PAR:DEF:EXT '%s', '%s'" % (trc,meas))
            self.write("DISP:WIND:TRAC%d:FEED '%s'" % (i+1,trc))
        self.write('DISP:WIND:TRAC2:MOVE 2')
        self.write('DISP:WIND:TRAC3:MOVE 2')
    def SetRange(self,start,end):
        self.SetStart(start)
        self.SetEnd(end)
    def SetCenterSpan(self,center,span):
        self.SetCenter(center)
        self.SetSpan(span)
    def SetStart(self,x):
        mystr = numtostr(x)
        mystr = 'SENS:FREQ:STAR '+mystr
        self.write(mystr)
    def SetEnd(self,x):
        mystr = numtostr(x)
        mystr = 'SENS:FREQ:STOP '+mystr
        self.write(mystr)
    def SetCenter(self,x):
        mystr = numtostr(x)
        mystr = 'SENS:FREQ:CENT '+mystr
        self.write(mystr)
    def SetSpan(self,x):
        mystr = numtostr(x)
        mystr = 'SENS:FREQ:SPAN '+mystr
        self.write(mystr)
    def SetIFBW(self,x):
        mystr = numtostr(x)
        mystr = 'SENS:BWID '+mystr
        self.write(mystr)
    def SetPower(self,x):
        mystr = numtostr(x)
        mystr = 'SOUR:POW '+mystr
        self.write(mystr)
    def GetPower(self):
        mystr = 'SOUR:POW?'
        pp = self.query(mystr)
        pp = float(pp)
        return pp
    def SetPoints(self,x):
        mystr = '%d' % x
        mystr = 'SENS:SWE:POIN '+mystr
        self.write(mystr)
    def Measure2ports(self,autoscale = True):
        self.TwoPortSetup()
        print((self.query('INIT;*OPC?'))) #Trigger single sweep and wait for response
        if autoscale:
            self.AutoScaleAll()
        return self.GetAllData()
    def Measure1port(self,autoscale = True):
        self.SinglePortSetup()
        print((self.query('INIT;*OPC?'))) #Trigger single sweep and wait for response
        if autoscale:
            self.AutoScaleAll()
        return self.GetAllData()
    def ClearAll(self): #Clears all traces and windows
        windows = self.query('DISP:CAT?')
        windows = windows.strip('\n')
        if windows != '"EMPTY"':
            windows = [int(x) for x in windows.strip('"').split(',')]
            for i in windows:
                self.write('DISP:WIND%d OFF' % i)
    def AutoScaleAll(self):
        self.write('DISP:WIND:TRAC:Y:COUP:METH WIND')
        windows = self.query('DISP:CAT?')
        windows = windows.strip('\n')
        if windows != '"EMPTY"':
            windows = [int(x) for x in windows.strip('"').split(',')]
            for i in windows:
                self.write('DISP:WIND%d:TRAC:Y:AUTO' % i)
    def GetFrequency(self):
        freq = self.query('CALC:X?')
        freq = np.asarray([float(xx) for xx in freq.split(',')])
        return freq
    def GetAllData(self):
        pars = self.query('CALC:PAR:CAT:EXT?')
        pars = pars.strip('\n').strip('"').split(',')
        parnames = pars[1::2]
        pars = pars[::2]
        names = ['Frequency (Hz)']
        alltrc = [self.GetFrequency()]
        for pp in parnames:
            names.append('%sre ()' % pp)
            names.append('%sim ()' % pp)
        for par in pars:
            self.write("CALC:PAR:SEL '%s'" % par)
            yy = self.query("CALC:DATA? SDATA")
            yy = np.asarray([float(xx) for xx in yy.split(',')])
            yyre = yy[::2]
            yyim = yy[1::2]
            alltrc.append(yyre)
            alltrc.append(yyim)
        final = OrderedDict()
        for name,data in zip(names,alltrc):
            final[name]=data
        return final
    def GetTrcNames(self):
        pars = self.query('CALC:PAR:CAT:EXT?')
        pars = pars.strip('\n').strip('"').split(',')
        parnames = pars[1::2]
        return parnames
    def MeasureScreen(self):
        self.write('INIT:CONT 0')
        print((self.query('INIT;*OPC?'))) #Trigger single sweep and wait for response
        return self.GetAllData()
# DC source commands
    '''
    def EnableDCsource(self,reset=True):
        if reset:
            self.write('SYST:VVS:VOLT 1.00')
        self.write('SYST:VVS:ENAB 1')
        return
    def DisableDCsource(self):
        self.write('SYST:VVS:ENAB 0')
        return
    def SetDCvoltage(self,vv):
        mystr = numtostr(vv)
        mystr = 'SYST:VVS:VOLT '+mystr
        self.write(mystr)
        return
    def GetDCvoltage(self):
        mystr = 'SYST:VVS:VOLT?'
        vv = self.query(mystr)
        vv = float(vv)
        return vv
    def GetMDCvoltage(self):
        mystr = 'SYST:VVS:MVOL?'
        vv = self.query(mystr)
        vv = float(vv)
        return vv
    def GetDCcurrent(self):
        mystr = 'SYST:VVS:CURR?'
        vv = self.query(mystr)
        vv = float(vv)
        return vv  
    '''