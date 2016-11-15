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
#
# Author(s): Rafael Villar Burke <pachi@ietcc.csic.es>,
#            Daniel Jiménez González <dani@ietcc.csic.es>
#
""" Calcula la eficiencia energética como balance entre la energía usada y la ahorrada a la red.

El proceso de calculo de la eficiencia energética se calcula en dos pasos:

- En un primer paso se consideran las producciones y consumos de cada combustible,
  que se equilibran mediante el suministro de la red correspondiente.

- Después se aplican los pasos A, de importación, y B, de exportación y ahorro,
  para obtener la eficiencia energética del caso considerado.

La red proporciona la cantidad suficiente de cada tipo de combustible para
equilibrar el balance entre producción y consumo. Además, es necesario obtener qué
parte de la demanda energética no ha podido ser satisfecha instantáneamente pero
podría serlo con la energía producida en otros pasos de cálculo. Esto se regula
mediante el parámetro normativo de resuministro ($k_{rdel}$).

Realizado el calculo del balance, los valores energéticos se agrupan en unos pocos
conceptos con valores anuales de los que se obtendrá el indicador de eficiencia
energética según indica la norma \textit{ISO/DIS 52000-1:2015} aplicando los pasos A y B.

Estos indicadores tienen una parte renovable y otra no renovable, lo que permite
calcular el valor de consumo energético total, además del porcentaje de uso de
energías renovables.


Las funciones devuelven un diccionario con la parte renovable y no renovable
de los indicadores, que aportan en base anual, aunque el cálculo se realice
en pasos temporales menores.

El cálculo está organizado por:
    - vectores energéticos
    - fuentes de energía
    - destino o uso de la energía.
"""

from .utils import *

# origin for produced energy must be either 'INSITU' or 'COGENERACION'
VALIDORIGINS = ['INSITU', 'COGENERACION']

def components_t_forcarrier(carrierdata, k_rdel):
    """Calculate timestep energy balance for carrier data

    carrierdata: { 'CONSUMO': { 'EPB': [vi1, ..., vin],
                                'NEPB': [vj1, ..., vjn] },
                   'PRODUCCION': { 'INSITU': [vk1, ..., vkn]},
                                   'COGENERACION' : [vl1, ..., vln] }
                 } // n: number of timesteps

    k_rdel: redelivery factor [0, 1]

    This follows the EN15603 procedure for calculation of delivered and
    exported energy components.

    Returns:

    components = { 'grid':
                       { 'input': value },
                   'INSITU':
                       { 'input': [ va1, ..., van ],
                         'to_nEPB': [ vb1, ..., vbn ],
                         'to_grid': [ vc1, ..., vcn ] },
                   'COGENERACION':
                       { 'input': [ va1, ..., van ],
                         'to_nEPB': [ vb1, ..., vbn ],
                         'to_grid': [ vc1, ..., vcn ] },
                 }
    """
    # Energy used by technical systems for EPB services, for each time step
    E_EPus_t = carrierdata['CONSUMO']['EPB']
    # Energy used by technical systems for non-EPB services, for each time step
    E_nEPus_t = carrierdata['CONSUMO']['NEPB']
    numsteps = len(E_EPus_t)

    # (Electricity) produced on-site and inside the assessment boundary, by origin
    E_pr_t_byorigin = carrierdata['PRODUCCION']
    # (Electric) energy produced on-site and inside the assessment boundary, for each time step (formula 23)
    E_pr_t = veclistsum([E_pr_t_byorigin[origin] for origin in VALIDORIGINS])

    # Produced energy from all origins for EPB services for each time step (formula 24)
    E_pr_used_EPus_t = vecvecmin(E_EPus_t, E_pr_t)

    ## Exported energy for each time step (produced energy not consumed in EPB uses) (formula 25)
    E_exp_t = vecvecdif(E_pr_t, E_pr_used_EPus_t)

    # Exported energy by production origin for each time step, weigthing done by produced energy
    F_exp_t = [E_exp_t[i] / E_pr_ti if E_pr_ti != 0 else 0 for (i, E_pr_ti) in enumerate(E_pr_t)]
    E_exp_t_byorigin = {origin: vecvecmul(E_pr_t_byorigin[origin], F_exp_t) for origin in VALIDORIGINS}

    # Exported (electric) energy used for non-EPB uses for each time step (formula 26)
    E_exp_used_nEPus_t = vecvecmin(E_exp_t, E_nEPus_t)
    # Exported energy used for non-EPB services for each time step, by origin, weighting done by exported energy
    F_exp_used_nEPus_t = [E_exp_used_nEPus_t[i] / E_exp_ti if E_exp_ti !=0 else 0 for (i, E_exp_ti) in enumerate(E_exp_t)]
    E_exp_used_nEPus_t_byorigin = {origin: vecvecmul(E_exp_t_byorigin[origin], F_exp_used_nEPus_t) for origin in VALIDORIGINS}

    # Exported energy not used for any service for each time step (formula 27)
    # Note: this is later affected by k_rdel for redelivery and k_exp for exporting
    E_exp_nused_t = vecvecdif(E_exp_t, E_exp_used_nEPus_t)
    # Exported energy not used for any service for each time step, by origin, weighting done by exported energy
    F_exp_nused_t = [E_exp_nused_t[i] / E_exp_ti if E_exp_ti !=0 else 0 for (i, E_exp_ti) in enumerate(E_exp_t)]
    E_exp_nused_t_byorigin = {origin: vecvecmul(E_exp_t_byorigin[origin], F_exp_nused_t) for origin in VALIDORIGINS}

    # Annual exported energy not used for any service (formula 28)
    E_exp_nused_an = sum(E_exp_nused_t)

    # Delivered (electric) energy for each time step (formula 29)
    E_del_t = vecvecdif(E_EPus_t, E_pr_used_EPus_t)
    # Annual delivered (electric) energy for EPB uses (formula 30)
    E_del_an = sum(E_del_t)

    # Annual temporary exported (electric) energy (formula 31)
    E_exp_tmp_an = min(E_exp_nused_an, E_del_an)

    # Temporary exported energy for each time step (formula 32)
    # E_exp_tmp_t = np.zeros(numsteps) if (E_exp_nused_an == 0) else E_exp_tmp_an * E_exp_nused_t / E_exp_nused_an # not used

    # Redelivered energy for each time step (formula 33)
    if E_del_an == 0:
        E_del_rdel_t = [0.0] * numsteps
    else:
        E_del_rdel_t = [E_exp_tmp_an * E_del_ti / E_del_an for E_del_ti in E_del_t]
    # Annual redelivered energy
    # E_del_rdel_an = sum(E_del_rdel_t) # not used

    # Exported (electric) energy to the grid for each time step (formula 34)
    # E_exp_grid_t = vecdif(E_exp_nused_t, E_exp_tmp_t) # not used

    # Annual exported (electric) energy to the grid (formula 35)
    E_exp_grid_an = E_exp_nused_an - E_exp_tmp_an
    # Energy exported to grid, by origin, weighting done by exported and not used energy
    F_exp_grid_an = E_exp_grid_an / E_exp_nused_an if E_exp_nused_an != 0 else 0
    E_exp_grid_t_byorigin = {origin: veckmul(E_exp_nused_t_byorigin[origin], F_exp_grid_an) for origin in VALIDORIGINS}

    # (Electric) energy delivered by the grid for each time step (formula 36)
    # E_del_grid_t = vecdif(E_del_t, E_del_rdel_t)  # not used

    # Annual (electric) energy delivered by the grid (formula 37)
    # E_del_grid_an = E_del_an - E_del_rdel_an # not used

    # Corrected delivered energy for each time step (formula 38)
    E_del_t_corr = [E_del_ti - k_rdel * E_del_rdel_t[i] for (i, E_del_ti) in enumerate(E_del_t)]

    # Corrected temporary exported energy (formula 39)
    # E_exp_tmp_t_corr = [E_exp_tmp_ti * (1 - k_rdel) for E_exp_tmp_ti in E_exp_tmp_t] # not used

    components_t = {'grid': {'input': sum(E_del_t_corr)}} # Scalar

    components_t.update({origin: {'input': E_pr_t_byorigin[origin],
                                  'to_nEPB': E_exp_used_nEPus_t_byorigin[origin],
                                  'to_grid': E_exp_grid_t_byorigin[origin]} for origin in VALIDORIGINS})
    return components_t

def components_an_forcarrier(components_t):
    """Calculate annual energy balance for carrier from timestep balance

    Returns:

        { 'grid': value1,
          'INSITU': value2,
          'COGENERACION': value3
        }
    """
    components_an = {}
    for origin in components_t: # This is grid + VALIDORIGINS
        components_an[origin] = {}
        components_t_byorigin = components_t[origin]
        for use in components_t_byorigin:
            if origin == 'grid' and use == 'input': # we have a scalar
                sumforuse = components_t_byorigin[use]
            else: # we have a list
                sumforuse = sum(components_t_byorigin[use])
            if abs(sumforuse) > 0.01: # exclude smallish values
                components_an[origin][use] = sumforuse
    return components_an

def computebalance(carrierlist, k_rdel):
    """Calculate timestep and annual energy composition by carrier

    carrierlist: list of energy components

        [ {'carrier': carrier1, 'ctype': ctype1, 'originoruse': originoruse1, 'values': values1},
          {'carrier': carrier2, 'ctype': ctype2, 'originoruse': originoruse2, 'values': values2},
          ... ]

        where:

            * carrier is an energy carrier
            * ctype is either 'PRODUCCION' or 'CONSUMO' por produced or used energy
            * originoruse defines:
              - the energy origin for produced energy (INSITU or COGENERACION)
              - the energy end use (EPB or NEPB) for delivered energy
            * values is a list of energy values, one for each timestep
            * comment is a comment string for the vector

    k_rdel: redelivery factor [0, 1]


    Returns:
        components[carrier] = { 'timestep': [vt1, ..., vtn]
                                'annual': vannual }
        where timestep and annual are the timestep and annual
        balanced values for carrier.
    """
    # Add all values of vectors with the same carrier ctype and originoruse
    # datadict[carrier][ctype][originoruse] -> values as np.array with length=numsteps
    datadict = {}
    numsteps = max(len(datum['values']) for datum in carrierlist)
    for datum in carrierlist:
        carrier = datum['carrier']
        ctype = datum['ctype']
        originoruse = datum['originoruse']
        values = datum['values']
        if carrier not in datadict:
            datadict[carrier] = {'CONSUMO': {'EPB': [0.0] * numsteps,
                                             'NEPB': [0.0] * numsteps},
                                 'PRODUCCION': {'INSITU': [0.0] * numsteps,
                                                'COGENERACION': [0.0] * numsteps}}
        datadict[carrier][ctype][originoruse] = vecvecsum(datadict[carrier][ctype][originoruse], values)

    # Compute timestep and annual balance
    components = {}
    for carrier in datadict:
        bal_t = components_t_forcarrier(datadict[carrier], k_rdel)
        bal_an = components_an_forcarrier(bal_t)
        components[carrier] = {'timestep': bal_t,
                               'annual': bal_an}
    return components

####################################################

def delivered_weighted_energy_stepA(components, fp):
    """Total delivered (or produced) weighted energy entering the assessment boundary in step A

    Energy is weighted depending on its origin (by source or grid).

    This function returns a data structure with keys 'ren' and 'nren' corresponding
    to the renewable and not renewable share of this weighted energy (step A).
    """

    delivered_wenergy_stepA = {'ren': 0.0, 'nren': 0.0}
    fpA = [fpi for fpi in fp if fpi['uso']=='input' and fpi['step']=='A']
    for source in components:
        origins = components[source]
        if 'input' in origins:
            factor_paso_A = [fpi for fpi in fpA if fpi['fuente']==source][0]
            delivered_wenergy_stepA = {'ren': delivered_wenergy_stepA['ren'] + factor_paso_A['ren'] * origins['input'],
                                       'nren': delivered_wenergy_stepA['nren'] + factor_paso_A['nren'] * origins['input'] }
    return delivered_wenergy_stepA

def exported_weighted_energy_stepA(components, fpA):
    """Total exported weighted energy going outside the assessment boundary in step A

    Energy is weighted depending on its destination (non-EPB uses or grid).

    This function returns a data structure with keys 'ren' and 'nren' corresponding
    to the renewable and not renewable share of this weighted energy (step A).
    """

    to_nEPB = {'ren': 0.0, 'nren': 0.0}
    to_grid = {'ren': 0.0, 'nren': 0.0}
    fpAnEPB = [fpi for fpi in fpA if fpi['uso']=='to_nEPB']
    fpAgrid = [fpi for fpi in fpA if fpi['uso']=='to_grid']
    for source in components:
        destinations = components[source]
        if 'to_nEPB' in destinations:
            fp_tmp = [fpi for fpi in fpAnEPB if fpi['fuente']==source][0] # TODO: check whether there's data
            to_nEPB = { 'ren': to_nEPB['ren'] + fp_tmp['ren'] * destinations['to_nEPB'],
                        'nren': to_nEPB['nren'] + fp_tmp['nren'] * destinations['to_nEPB'] }

        if 'to_grid' in destinations:
            fp_tmp = [fpi for fpi in fpAgrid if fpi['fuente']==source][0] # TODO: check whether there's data
            to_grid = { 'ren': to_grid['ren'] + fp_tmp['ren'] * destinations['to_grid'],
                        'nren': to_grid['nren'] + fp_tmp['nren'] * destinations['to_grid'] }

    exported_energy_stepA = { 'ren': to_nEPB['ren'] + to_grid['ren'],
                              'nren': to_nEPB['nren'] + to_grid['nren'] }
    return exported_energy_stepA

def gridsavings_stepB(components, fp, k_exp):
    """Avoided weighted energy resources in the grid due to exported electricity

    The computation is done for a single energy carrier, considering the
    exported energy used for non-EPB uses (to_nEPB) and the energy exported
    to the grid (to_grid), each with its own weigting factors and k_exp.

    This function returns a data structure with keys 'ren' and 'nren' corresponding
    to the renewable and not renewable share of this weighted energy (step B).
    """

    to_nEPB = {'ren': 0.0, 'nren': 0.0}
    to_grid = {'ren': 0.0, 'nren': 0.0}
    fpA = [fpi for fpi in fp if fpi['step']=='A']
    fpB = [fpi for fpi in fp if fpi['step']=='B']
    fpAnEPB = [fpi for fpi in fpA if fpi['uso']=='to_nEPB']
    fpAgrid = [fpi for fpi in fpA if fpi['uso']=='to_grid']
    fpBnEPB = [fpi for fpi in fpB if fpi['uso']=='to_nEPB']
    fpBgrid = [fpi for fpi in fpB if fpi['uso']=='to_grid']

    for source in components:
        destinations = components[source]
        if 'to_nEPB' in destinations:
            fpA_tmp = [fpi for fpi in fpAnEPB if fpi['fuente']==source][0] # TODO: check whether there's data
            fpB_tmp = [fpi for fpi in fpBnEPB if fpi['fuente']==source][0] # TODO: check whether there's data
            to_nEPB = { 'ren': to_nEPB['ren'] + (fpB_tmp['ren'] - fpA_tmp['ren']) * destinations['to_nEPB'],
                        'nren': to_nEPB['nren'] + (fpB_tmp['nren'] - fpA_tmp['nren']) * destinations['to_nEPB'] }
        if 'to_grid' in destinations:
            fpA_tmp = [fpi for fpi in fpAgrid if fpi['fuente']==source][0] # TODO: check whether there's data
            fpB_tmp = [fpi for fpi in fpBgrid if fpi['fuente']==source][0] # TODO: check whether there's data
            to_grid = { 'ren': to_grid['ren'] + (fpB_tmp['ren'] - fpA_tmp['ren']) * destinations['to_grid'],
                        'nren': to_grid['nren'] + (fpB_tmp['nren'] - fpA_tmp['nren']) * destinations['to_grid'] }

    gridsavings = {'ren': k_exp * (to_nEPB['ren'] + to_grid['ren']), 'nren': k_exp * (to_nEPB['nren'] + to_grid['nren'])}
    return gridsavings

def weighted_energy(data, fp, k_rdel, k_exp):
    """Total weighted energy (step A + B) = used energy (step A) - saved energy (step B)

    The energy saved to the grid due to exportation (step B) is substracted
    from the the energy balance in the asessment boundary AB (step A).
    This is  computed for all energy carrier and all energy sources.

    This function returns a data structure with keys 'ren' and 'nren'
    corresponding to the renewable and not renewable parts of the balance.

    In the context of the CTE regulation weighted energy corresponds to
    primary energy.

    data is a list of energy vectors:

    fp is a dictionary of weighting factors
    k_rdel is the redelivery energy factor [0, 1]
    k_exp is the exported energy factor [0, 1]
    """
    balance = computebalance(data, k_rdel)
    EPA = {'ren': 0.0, 'nren': 0.0}
    EPB = {'ren': 0.0, 'nren': 0.0}

    for carrier in balance:
        fp_cr = [fpi for fpi in fp if fpi['vector'] == carrier]
        cr_balance_an = balance[carrier]['annual']

        delivered_wenergy_stepA = delivered_weighted_energy_stepA(cr_balance_an, fp_cr)
        exported_wenergy_stepA = exported_weighted_energy_stepA(cr_balance_an, fp_cr)
        weighted_energy_stepA = { 'ren': delivered_wenergy_stepA['ren'] - exported_wenergy_stepA['ren'],
                                  'nren': delivered_wenergy_stepA['nren'] - exported_wenergy_stepA['nren'] }

        gsavings_stepB = gridsavings_stepB(cr_balance_an, fp_cr, k_exp)
        weighted_energy_stepAB = { 'ren': weighted_energy_stepA['ren'] - gsavings_stepB['ren'],
                                   'nren': weighted_energy_stepA['nren'] - gsavings_stepB['nren'] }

        EPA = {'ren': EPA['ren'] + weighted_energy_stepA['ren'], 'nren': EPA['nren'] + weighted_energy_stepA['nren']}
        EPB = {'ren': EPB['ren'] + weighted_energy_stepAB['ren'], 'nren': EPB['nren'] + weighted_energy_stepAB['nren']}

    return {'EP': EPB, 'EPpasoA': EPA}
