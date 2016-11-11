#!/usr/bin/env python
# encoding: utf-8
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

"""Cálculo de la eficiencia energética de los edificios según ISO/DIS 52000-1:2005"""

import argparse
import sys
from .settings import K_EXP, K_RDEL, FACTORESDEPASOOFICIALES
from .energycalculations import weighted_energy
from .inputoutput import readenergyfile, readfactors, ep2string

def main():
    from .__init__ import __version__
    COPY = u"""\tversión: %s
\t(c) 2015-2016 Ministerio de Fomento
\t    2015-2016 Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC)
\tAutores: Daniel Jiménez González <danielj@ietcc.csic.es>
\t         Rafael Villar Burke <pachi@ietcc.csic.es>
""" % __version__
    parser = argparse.ArgumentParser(description=u'Cálculo de la eficiencia energética según ISO/DIS 52000-1:2015 y CTE DB-HE',
                                     usage=u"%(prog)s [-h] [-f [FPFILE]] [--krdel [KRDEL]] [--kexp [KEXP]] vecfile\n\n" + COPY,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(dest='vecfile', nargs='?',
                        type=argparse.FileType('r'),
                        help=u'archivo de datos de los vectores energéticos')
    parser.add_argument('-f', '--factores', dest='fpfile', nargs='?',
                        type=argparse.FileType('r'), default=None,
                        help=u'archivo de definición de los factores de paso')
    parser.add_argument('--krdel', nargs='?', default=None, type=float,
                        help=u'factor de resuministro (k_rdel)')
    parser.add_argument('--kexp', nargs='?', default=None, type=float,
                        help=u'factor de exportacion (k_exp)')
    parser.add_argument('-A', '--area', dest='area', nargs='?',
                        type=float, default=1.0,
                        help=u'superficie de referencia')
    parser.add_argument('-o', '--outfile', dest='outputfile', nargs='?',
                        type=argparse.FileType('w'), default=None,
                        help=u'archivo de salida de resultados')
    args = parser.parse_args()

    cadenasalida = []

    if not args.vecfile:
        parser.print_help()
        sys.exit(2)
    cadenasalida.append(u'%s' % args.vecfile.name)

    if args.krdel is None:
        cadenasalida.append(u'Usando factor de resuministro predeterminado (k_rdel = %.2f)' % K_RDEL)
    else:
        cadenasalida.append(u'Usando factor de resuministro krdel = %.2f' % args.krdel)
    k_rdel = K_RDEL if args.krdel is None else args.krdel

    if args.kexp is None:
        cadenasalida.append(u'Usando factor de exportación predeterminado (k_exp = %.2f)' % K_EXP)
    else:
        cadenasalida.append(u'Usando factor de exportación kexp = %.2f' % args.kexp)
    k_exp  = K_EXP if args.kexp is None else args.kexp

    if args.fpfile:
        fpdatafile = args.fpfile
        cadenasalida.append(u'Archivo de factores de paso: %s ' % fpdatafile.name)
    else:
        fpdatafile = None
        cadenasalida.append(u'Usando factores de paso predefinidos')
    fP = (FACTORESDEPASOOFICIALES if args.fpfile is None
          else readfactors(args.fpfile))

    cadenasalida.append(u'Superficie de referencia: %.2f' % args.area)

    meta, data = readenergyfile(args.vecfile.name)
    EP = weighted_energy(data, fP, k_rdel, k_exp)

    cadenasalida.append(ep2string(EP, args.area))
    cadenasalida = u'\n'.join(cadenasalida)
    print(cadenasalida)

    if args.outputfile:
        print(u'Guardando resultados en el archivo: %s' % args.outputfile.name)
        args.outputfile.write(cadenasalida.encode('utf-8'))

if __name__ == '__main__':
    main()
