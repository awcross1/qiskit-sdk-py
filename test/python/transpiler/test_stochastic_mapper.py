# -*- coding: utf-8 -*-

# Copyright 2018, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""Test the Stochastic Mapper pass"""

import unittest
from qiskit.transpiler.passes import StochasticMapper
from qiskit.mapper import Coupling
from qiskit.converters import circuit_to_dag
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from ..common import QiskitTestCase


class TestStochasticMapper(QiskitTestCase):
    """
    Tests the StochasticMapper pass.
    
    All of the tests use a fixed seed since the results
    may depend on it.
    """

    def test_trivial_case(self):
        """
         q0:--(+)-[U]-(+)-
               |       |
         q1:---.-------|--
                       |
         q2:-----------.--

         Coupling map: [1]--[0]--[2]
        """
        coupling = Coupling({0: [1, 2]})

        qr = QuantumRegister(3, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[0], qr[1])
        circuit.h(qr[0])
        circuit.cx(qr[0], qr[2])

        dag = circuit_to_dag(circuit)
        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(dag, after)

    def test_trivial_in_same_layer(self):
        """
         q0:--(+)--
               |
         q1:---.---

         q2:--(+)--
               |
         q3:---.---

         Coupling map: [0]--[1]--[2]--[3]
        """
        coupling = Coupling({0: [1], 1: [2], 2: [3]})

        qr = QuantumRegister(4, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[2], qr[3])
        circuit.cx(qr[0], qr[1])

        dag = circuit_to_dag(circuit)
        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(dag, after)

    def test_permute_wires_1(self):
        """All of the test_permute_wires tests are derived
        from the basic mapper tests. In this case, the
        stochastic mapper handles a single
        layer by qubit label permutations so as not to
        introduce additional swap gates.
         q0:-------

         q1:--(+)--
               |
         q2:---.---

         Coupling map: [1]--[0]--[2]

         q0:-(+)--
              |
         q1:--.---

         q2:------

        """
        coupling = Coupling({0: [1, 2]})

        qr = QuantumRegister(3, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[1], qr[2])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.cx(qr[1], qr[0])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_permute_wires_2(self):
        """
         qr0:---.---[H]--
                |
         qr1:---|--------
                |
         qr2:--(+)-------

         Coupling map: [0]--[1]--[2]

         qr0:---.--[H]--
                |
         qr1:--(+)------

         qr2:--------------
        """
        coupling = Coupling({1: [0, 2]})

        qr = QuantumRegister(3, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[0], qr[2])
        circuit.h(qr[0])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.cx(qr[0], qr[1])
        expected.h(qr[0])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_permute_wires_3(self):
        """
         qr0:--(+)---.--
                |    |
         qr1:---|----|--
                |    |
         qr2:---|----|--
                |    |
         qr3:---.---(+)-

         Coupling map: [0]--[1]--[2]--[3]
         For this seed,  we get the (1,2) edge.

         qr0:-----------

         qr1:---.---(+)-
                |    |
         qr2:--(+)---.--

         qr3:-----------
        """
        coupling = Coupling({0: [1], 1: [2], 2: [3]})

        qr = QuantumRegister(4, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[0], qr[3])
        circuit.cx(qr[3], qr[0])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.cx(qr[1], qr[2])
        expected.cx(qr[2], qr[1])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_permute_wires_4(self):
        """No qubit label permutation occurs if the first
        layer has only single-qubit gates. This is suboptimal but is
        the current behavior.
         qr0:------(+)--
                    |
         qr1:-------|---
                    |
         qr2:-------|---
                    |
         qr3:--[H]--.---

         Coupling map: [0]--[1]--[2]--[3]

         qr0:------X---------
                   |
         qr1:------X-(+)-----
                      |
         qr2:------X--.------
                   |
         qr3:-[H]--X---------

        """
        coupling = Coupling({0: [1], 1: [2], 2: [3]})

        qr = QuantumRegister(4, 'q')
        circuit = QuantumCircuit(qr)
        circuit.h(qr[3])
        circuit.cx(qr[3], qr[0])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.h(qr[3])
        expected.swap(qr[2], qr[3])
        expected.swap(qr[0], qr[1])
        expected.cx(qr[2], qr[1])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_permute_wires_5(self):
        """
         qr0:--(+)------
                |
         qr1:---|-------
                |
         qr2:---|-------
                |
         qr3:---.--[H]--

         Coupling map: [0]--[1]--[2]--[3]
         For this seed, the mapper permutes these labels
         onto the (1,2) edge.

         qr0:------------

         qr1:---(+)------
                 |
         qr2:----.--[H]--

         qr3:------------

        """
        coupling = Coupling({0: [1], 1: [2], 2: [3]})

        qr = QuantumRegister(4, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[3], qr[0])
        circuit.h(qr[3])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.cx(qr[2], qr[1])
        expected.h(qr[2])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_permute_wires_6(self):
        """
         qr0:--(+)-------.--
                |        |
         qr1:---|--------|--
                |
         qr2:---|--------|--
                |        |
         qr3:---.--[H]--(+)-

         Coupling map: [0]--[1]--[2]--[3]
         For this seed, the mapper permutes these labels
         onto the (1,2) edge.

         qr0:---------------------

         qr1:-------(+)-------.---
                     |        |
         qr2:--------.--[H]--(+)--

         qr3:---------------------

        """
        coupling = Coupling({0: [1], 1: [2], 2: [3]})

        qr = QuantumRegister(4, 'q')
        circuit = QuantumCircuit(qr)
        circuit.cx(qr[3], qr[0])
        circuit.h(qr[3])
        circuit.cx(qr[0], qr[3])
        dag = circuit_to_dag(circuit)

        expected = QuantumCircuit(qr)
        expected.cx(qr[2], qr[1])
        expected.h(qr[2])
        expected.cx(qr[1], qr[2])

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)

        self.assertEqual(circuit_to_dag(expected), after)

    def test_overoptimization_case(self):
        """Check mapper overoptimization.

        The mapper should not change the semantics of the input.
        An overoptimization introduced issue #81:
        https://github.com/Qiskit/qiskit-terra/issues/81
        """
        coupling = Coupling({0: [2], 1: [2], 2: [3]})
        '''
                                    ┌───┐     ┌─┐                
q_0: |0>────────────────────────────┤ X ├──■──┤M├────────────────
                               ┌───┐└───┘┌─┴─┐└╥┘┌───┐        ┌─┐
q_1: |0>───────────────────────┤ Y ├─────┤ X ├─╫─┤ S ├──■─────┤M├
        ┌───┐             ┌───┐└───┘     └───┘ ║ └───┘┌─┴─┐┌─┐└╥┘
q_2: |0>┤ Z ├──■──────────┤ T ├────────────────╫──────┤ X ├┤M├─╫─
        └───┘┌─┴─┐┌───┐┌─┐└───┘                ║      └───┘└╥┘ ║ 
q_3: |0>─────┤ X ├┤ H ├┤M├─────────────────────╫────────────╫──╫─
             └───┘└───┘└╥┘                     ║            ║  ║ 
 c_0: 0 ════════════════╬══════════════════════╩════════════╬══╬═
                        ║                                   ║  ║ 
 c_1: 0 ════════════════╬═══════════════════════════════════╬══╩═
                        ║                                   ║    
 c_2: 0 ════════════════╬═══════════════════════════════════╩════
                        ║                                        
 c_3: 0 ════════════════╩════════════════════════════════════════
        '''
        qr = QuantumRegister(4, 'q')
        cr = ClassicalRegister(4, 'c')
        circuit = QuantumCircuit(qr, cr)
        circuit.x(qr[0])
        circuit.y(qr[1])
        circuit.z(qr[2])
        circuit.cx(qr[0], qr[1])
        circuit.cx(qr[2], qr[3])
        circuit.s(qr[1])
        circuit.t(qr[2])
        circuit.h(qr[3])
        circuit.cx(qr[1], qr[2])
        circuit.measure(qr[0], cr[0])
        circuit.measure(qr[1], cr[1])
        circuit.measure(qr[2], cr[2])
        circuit.measure(qr[3], cr[3])
        dag = circuit_to_dag(circuit)
        '''
                               ┌───┐   ┌───┐        ┌─┐
q_0: |0>───────────────────────┤ X ├─X─┤ T ├──────X─┤M├────────────────
                          ┌───┐└───┘ │ └───┘┌───┐ │ └╥┘┌───┐        ┌─┐
q_1: |0>──────────────────┤ Y ├──────┼──────┤ X ├─┼──╫─┤ S ├──■─────┤M├
        ┌───┐             └───┘      │      └─┬─┘ │  ║ └───┘┌─┴─┐┌─┐└╥┘
q_2: |0>┤ Z ├──■─────────────────────X────────■───X──╫──────┤ X ├┤M├─╫─
        └───┘┌─┴─┐┌───┐┌─┐                           ║      └───┘└╥┘ ║
q_3: |0>─────┤ X ├┤ H ├┤M├───────────────────────────╫────────────╫──╫─
             └───┘└───┘└╥┘                           ║            ║  ║
 c_0: 0 ════════════════╬════════════════════════════╩════════════╬══╬═
                        ║                                         ║  ║
 c_1: 0 ════════════════╬═════════════════════════════════════════╬══╩═
                        ║                                         ║
 c_2: 0 ════════════════╬═════════════════════════════════════════╩════
                        ║
 c_3: 0 ════════════════╩══════════════════════════════════════════════
        '''
        expected = QuantumCircuit(qr, cr)
        expected.x(qr[0])
        expected.y(qr[1])
        expected.z(qr[2])
        expected.cx(qr[2], qr[3])
        expected.h(qr[3])
        expected.measure(qr[3], cr[3])
        expected.swap(qr[0], qr[2])
        expected.cx(qr[2], qr[1])
        expected.s(qr[1])
        expected.t(qr[0])
        expected.swap(qr[0], qr[2])
        expected.cx(qr[1], qr[2])
        expected.measure(qr[0], cr[0])
        expected.measure(qr[1], cr[1])
        expected.measure(qr[2], cr[2])
        expected_dag = circuit_to_dag(expected)

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)
        self.assertEqual(expected_dag, after)

    def test_already_mapped(self):
        """Circuit not remapped if matches topology.

        See: https://github.com/Qiskit/qiskit-terra/issues/342
        """
        coupling = Coupling({1: [0, 2], 2: [3], 3: [4, 14], 5: [4],
                             6: [5, 7, 11], 7: [10], 8: [7], 9: [8, 10],
                             11: [10], 12: [5, 11, 13], 13: [4, 14],
                             15: [0, 2, 14]})
        qr = QuantumRegister(16, 'q')
        cr = ClassicalRegister(16, 'c')
        circ = QuantumCircuit(qr, cr)
        circ.cx(qr[3], qr[14])
        circ.cx(qr[5], qr[4])
        circ.h(qr[9])
        circ.cx(qr[9], qr[8])
        circ.x(qr[11])
        circ.cx(qr[3], qr[4])
        circ.cx(qr[12], qr[11])
        circ.cx(qr[13], qr[4])
        for j in range(16):
            circ.measure(qr[j], cr[j])

        dag = circuit_to_dag(circ)

        pass_ = StochasticMapper(coupling, None, 20, 13)
        after = pass_.run(dag)
        self.assertEqual(circuit_to_dag(circ), after)

# TODO: Port over the other mapper tests


if __name__ == '__main__':
    unittest.main()