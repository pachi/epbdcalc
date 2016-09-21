#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Ministerio de Fomento
#                    Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, sys

currpath = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(currpath, '..'))

from pyepbd import (weighted_energy,
                    readenergyfile,
                    readenergydata,
                    ep2string, readfactors)

def check(EPB, res):
    """Check that result is within valid range"""
    ep = EPB['EP']
    res = {'ren': ep['ren'] - res[0], 'nren': ep['nren'] - res[1]}
    if abs(res['ren'] + res['nren']) > 2.0:
        print('Resultado no coincidente: ', res['ren']+ res['nren'])
        print(ep2string(EPB))
        print('#####################################################')
        print('--------------------')
        return False
    else:
        return True

def epfromfile(filename, krdel, kexp, fp):
    """Compute primary energy (weighted energy) from data in filename"""
    datafile = os.path.join(currpath, filename)
    data = readenergyfile(datafile)
    return weighted_energy(data, krdel, fp, kexp)

def epfromdata(datalist, krdel, kexp, fp):
    """Compute primary energy (weighted energy) from datalist"""
    data = readenergydata(datalist)
    return weighted_energy(data, krdel, fp, kexp)

TESTFP = readfactors(os.path.join(currpath, '../examples/factores_paso_test.csv'))
TESTFP2 = readfactors(os.path.join(currpath, '../examples/factores_paso_20140203.csv'))
TESTKRDEL = 1.0
TESTKEXP = 1.0

def test_ejemplo1base():
    EP = epfromfile('../examples/ejemplo1base.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [50.0, 200.0])

def test_ejemplo1base_fail():
    EP = epfromfile('../examples/ejemplo1base.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert not check(EP, [53.0, 200.0])

def test_ejemplo1base_normativo():
    EP = epfromfile('../examples/ejemplo1base.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [34.1, 208.20])

def test_ejemplo1PV():
    EP = epfromfile('../examples/ejemplo1PV.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [75.0, 100.0])

def test_ejemplo1PV_normativo():
    EP = epfromfile('../examples/ejemplo1PV.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [67.1, 104.1])

def test_ejemplo1xPV():
    EP = epfromfile('../examples/ejemplo1xPV.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [120.0, -80.0])

def test_ejemplo1xPV_normativo():
    EP = epfromfile('../examples/ejemplo1xPV.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [120.0, -80.0])

def test_ejemplo1xPVk0():
    EP = epfromfile('../examples/ejemplo1xPV.csv', TESTKRDEL, 0.0, TESTFP)
    assert check(EP, [100.0, 0.0])

def test_ejemplo1xPVk0_normativo():
    EP = epfromfile('../examples/ejemplo1xPV.csv', TESTKRDEL, 0.0, TESTFP2)
    assert check(EP, [100.0, 0.0])

def test_ejemplo2xPVgas():
    EP = epfromfile('../examples/ejemplo2xPVgas.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [30.0, 169.0])

def test_ejemplo2xPVgas_normativo():
    EP = epfromfile('../examples/ejemplo2xPVgas.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [30.9, 186.1])

def test_ejemplo3PVBdC():
    EP = epfromfile('../examples/ejemplo3PVBdC.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [180.0, 38.0])

def test_ejemplo3PVBdC_normativo():
    EP = epfromfile('../examples/ejemplo3PVBdC.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [177.5, 39.6])

def test_ejemplo4cgnfosil():
    EP = epfromfile('../examples/ejemplo4cgnfosil.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [-14.0, 227.0])

def test_ejemplo4cgnfosil_normativo():
    EP = epfromfile('../examples/ejemplo4cgnfosil.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [-12.7, 251])

def test_ejemplo5cgnbiogas():
    EP = epfromfile('../examples/ejemplo5cgnbiogas.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [159.0, 69.0])

def test_ejemplo5cgnbiogas_normativo():
    EP = epfromfile('../examples/ejemplo5cgnbiogas.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [148.9, 76.4])

def test_ejemplo6K3():
    EP = epfromfile('../examples/ejemplo6K3.csv', TESTKRDEL, TESTKEXP, TESTFP)
    assert check(EP, [1385.5, -662])

def test_ejemplo6K3_normativo():
    EP = epfromfile('../examples/ejemplo6K3.csv', TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [1385.5, -662])

def test_fromdata():
    # data from ejemplo3PVBdC_normativo
    datalist = [
            {'values': [9.67, 7.74, 4.84, 4.35, 2.42, 2.9, 3.87, 3.39, 2.42, 3.87, 5.8, 7.74],
             'carrier': 'ELECTRICIDAD', 'ctype': 'CONSUMO', 'originoruse': 'EPB'},
            {'values': [1.13, 1.42, 1.99, 2.84, 4.82, 5.39, 5.67, 5.11, 4.54, 3.40, 2.27, 1.42],
             'carrier': 'ELECTRICIDAD', 'ctype': 'PRODUCCION', 'originoruse': 'INSITU'},
            {'values': [21.48, 17.18, 10.74, 9.66, 5.37, 6.44, 8.59, 7.52, 5.37, 8.59, 12.89, 17.18],
             'carrier': 'MEDIOAMBIENTE', 'ctype': 'CONSUMO', 'originoruse': 'EPB'},
            {'values': [21.48, 17.18, 10.74, 9.66, 5.37, 6.44, 8.59, 7.52, 5.37, 8.59, 12.89, 17.18],
             'carrier': 'MEDIOAMBIENTE', 'ctype': 'PRODUCCION', 'originoruse': 'INSITU'}
            ]
    EP = epfromdata(datalist, TESTKRDEL, TESTKEXP, TESTFP2)
    assert check(EP, [177.5, 39.6])
