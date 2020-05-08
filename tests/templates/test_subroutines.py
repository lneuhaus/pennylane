# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the :mod:`pennylane.template.subroutines` module.
Integration tests should be placed into ``test_templates.py``.
"""
# pylint: disable=protected-access,cell-var-from-loop
import pytest
import pennylane as qml
from pennylane import numpy as np

from pennylane.templates.subroutines import (
	Interferometer, 
	ArbitraryUnitary,
	SingleExcitationUnitary
)
from pennylane.templates.subroutines.arbitrary_unitary import (
    _all_pauli_words_but_identity,
    _tuple_to_word,
    _n_k_gray_code,
)

# fmt: off
PAULI_WORD_TEST_DATA = [
    (1, ["X", "Y", "Z"]),
    (
        2,
        ["XI", "YI", "ZI", "ZX", "IX", "XX", "YX", "YY", "ZY", "IY", "XY", "XZ", "YZ", "ZZ", "IZ"],
    ),
    (
        3,
        [
            "XII", "YII", "ZII", "ZXI", "IXI", "XXI", "YXI", "YYI", "ZYI", "IYI", "XYI", "XZI", "YZI",
            "ZZI", "IZI", "IZX", "XZX", "YZX", "ZZX", "ZIX", "IIX", "XIX", "YIX", "YXX", "ZXX", "IXX",
            "XXX", "XYX", "YYX", "ZYX", "IYX", "IYY", "XYY", "YYY", "ZYY", "ZZY", "IZY", "XZY", "YZY",
            "YIY", "ZIY", "IIY", "XIY", "XXY", "YXY", "ZXY", "IXY", "IXZ", "XXZ", "YXZ", "ZXZ", "ZYZ",
            "IYZ", "XYZ", "YYZ", "YZZ", "ZZZ", "IZZ", "XZZ", "XIZ", "YIZ", "ZIZ", "IIZ",
        ]
    ),
]

GRAY_CODE_TEST_DATA = [
    (2, 2, [[0, 0], [1, 0], [1, 1], [0, 1]]),
    (2, 3, [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 1, 1], [1, 1, 1], [1, 0, 1], [0, 0, 1]]),
    (4, 2, [
        [0, 0], [1, 0], [2, 0], [3, 0], [3, 1], [0, 1], [1, 1], [2, 1], 
        [2, 2], [3, 2], [0, 2], [1, 2], [1, 3], [2, 3], [3, 3], [0, 3]
    ]),
    (3, 3, [
        [0, 0, 0], [1, 0, 0], [2, 0, 0], [2, 1, 0], [0, 1, 0], [1, 1, 0], [1, 2, 0], [2, 2, 0], [0, 2, 0], 
        [0, 2, 1], [1, 2, 1], [2, 2, 1], [2, 0, 1], [0, 0, 1], [1, 0, 1], [1, 1, 1], [2, 1, 1], [0, 1, 1], 
        [0, 1, 2], [1, 1, 2], [2, 1, 2], [2, 2, 2], [0, 2, 2], [1, 2, 2], [1, 0, 2], [2, 0, 2], [0, 0, 2]
    ]),
]
# fmt: on


class TestHelperFunctions:
    """Test the helper functions used in the layers."""

    @pytest.mark.parametrize("n,k,expected_code", GRAY_CODE_TEST_DATA)
    def test_n_k_gray_code(self, n, k, expected_code):
        """Test that _n_k_gray_code produces the Gray code correctly."""
        for expected_word, word in zip(expected_code, _n_k_gray_code(n, k)):
            assert expected_word == word

    @pytest.mark.parametrize("num_wires,expected_pauli_words", PAULI_WORD_TEST_DATA)
    def test_all_pauli_words_but_identity(self, num_wires, expected_pauli_words):
        """Test that the correct Pauli words are returned."""
        for expected_pauli_word, pauli_word in zip(expected_pauli_words, _all_pauli_words_but_identity(num_wires)):
            assert expected_pauli_word == pauli_word

    @pytest.mark.parametrize("tuple,expected_word", [
        ((0,), "I"),
        ((1,), "X"),
        ((2,), "Y"),
        ((3,), "Z"),
        ((0, 0, 0), "III"),
        ((1, 2, 3), "XYZ"),
        ((1, 2, 3, 0, 0, 3, 2, 1), "XYZIIZYX"),
    ])
    def test_tuple_to_word(self, tuple, expected_word):
        assert _tuple_to_word(tuple) == expected_word

class TestInterferometer:
    """Tests for the Interferometer from the pennylane.template.layers module."""

    def test_invalid_mesh_exception(self):
        """Test that Interferometer() raises correct exception when mesh not recognized."""
        dev = qml.device('default.gaussian', wires=1)
        varphi = [0.42342]

        @qml.qnode(dev)
        def circuit(varphi, mesh=None):
            Interferometer(theta=[], phi=[], varphi=varphi, mesh=mesh, wires=0)
            return qml.expval(qml.NumberOperator(0))

        with pytest.raises(ValueError, match="Mesh option"):
            circuit(varphi, mesh='a')

    def test_invalid_mesh_exception(self):
        """Test that Interferometer() raises correct exception when beamsplitter not recognized."""
        dev = qml.device('default.gaussian', wires=1)
        varphi = [0.42342]

        @qml.qnode(dev)
        def circuit(varphi, bs=None):
            Interferometer(theta=[], phi=[], varphi=varphi, beamsplitter=bs, wires=0)
            return qml.expval(qml.NumberOperator(0))

        with pytest.raises(ValueError, match="did not recognize option"):
            circuit(varphi, bs='a')

    def test_clements_beamsplitter_convention(self, tol):
        """test the beamsplitter convention"""
        N = 2
        wires = range(N)

        theta = [0.321]
        phi = [0.234]
        varphi = [0.42342, 0.1121]

        with qml.utils.OperationRecorder() as rec_rect:
            Interferometer(theta, phi, varphi, mesh='rectangular', beamsplitter='clements', wires=wires)

        with qml.utils.OperationRecorder() as rec_tria:
            Interferometer(theta, phi, varphi, mesh='triangular', beamsplitter='clements', wires=wires)

        for rec in [rec_rect, rec_tria]:

            assert len(rec.queue) == 4

            assert isinstance(rec.queue[0], qml.Rotation)
            assert rec.queue[0].parameters == phi

            assert isinstance(rec.queue[1], qml.Beamsplitter)
            assert rec.queue[1].parameters == [theta[0], 0]

            assert isinstance(rec.queue[2], qml.Rotation)
            assert rec.queue[2].parameters == [varphi[0]]

            assert isinstance(rec.queue[3], qml.Rotation)
            assert rec.queue[3].parameters == [varphi[1]]

    def test_one_mode(self, tol):
        """Test that a one mode interferometer correctly gives a rotation gate"""
        varphi = [0.42342]

        with qml.utils.OperationRecorder() as rec:
            Interferometer(theta=[], phi=[], varphi=varphi, wires=0)

        assert len(rec.queue) == 1
        assert isinstance(rec.queue[0], qml.Rotation)
        assert np.allclose(rec.queue[0].parameters, varphi, atol=tol)

    def test_two_mode_rect(self, tol):
        """Test that a two mode interferometer using the rectangular mesh
        correctly gives a beamsplitter+rotation gate"""
        N = 2
        wires = range(N)

        theta = [0.321]
        phi = [0.234]
        varphi = [0.42342, 0.1121]

        with qml.utils.OperationRecorder() as rec:
            Interferometer(theta, phi, varphi, wires=wires)

        isinstance(rec.queue[0], qml.Beamsplitter)
        assert rec.queue[0].parameters == theta+phi

        assert isinstance(rec.queue[1], qml.Rotation)
        assert rec.queue[1].parameters == [varphi[0]]

        assert isinstance(rec.queue[2], qml.Rotation)
        assert rec.queue[2].parameters == [varphi[1]]

    def test_two_mode_triangular(self, tol):
        """Test that a two mode interferometer using the triangular mesh
        correctly gives a beamsplitter+rotation gate"""
        N = 2
        wires = range(N)

        theta = [0.321]
        phi = [0.234]
        varphi = [0.42342, 0.1121]

        with qml.utils.OperationRecorder() as rec:
            Interferometer(theta, phi, varphi, mesh='triangular', wires=wires)

        assert len(rec.queue) == 3

        assert isinstance(rec.queue[0], qml.Beamsplitter)
        assert rec.queue[0].parameters == theta+phi

        assert isinstance(rec.queue[1], qml.Rotation)
        assert rec.queue[1].parameters == [varphi[0]]

        assert isinstance(rec.queue[2], qml.Rotation)
        assert rec.queue[2].parameters == [varphi[1]]

    def test_three_mode(self, tol):
        """Test that a three mode interferometer using either mesh gives the correct gates"""
        N = 3
        wires = range(N)

        theta = [0.321, 0.4523, 0.21321]
        phi = [0.234, 0.324, 0.234]
        varphi = [0.42342, 0.234, 0.1121]

        with qml.utils.OperationRecorder() as rec_rect:
            Interferometer(theta, phi, varphi, wires=wires)

        with qml.utils.OperationRecorder() as rec_tria:
            Interferometer(theta, phi, varphi, wires=wires)

        for rec in [rec_rect, rec_tria]:
            # test both meshes (both give identical results for the 3 mode case).
            assert len(rec.queue) == 6

            expected_bs_wires = [[0, 1], [1, 2], [0, 1]]

            for idx, op in enumerate(rec_rect.queue[:3]):
                assert isinstance(op, qml.Beamsplitter)
                assert op.parameters == [theta[idx], phi[idx]]
                assert op.wires == expected_bs_wires[idx]

            for idx, op in enumerate(rec.queue[3:]):
                assert isinstance(op, qml.Rotation)
                assert op.parameters == [varphi[idx]]
                assert op.wires == [idx]

    def test_four_mode_rect(self, tol):
        """Test that a 4 mode interferometer using rectangular mesh gives the correct gates"""
        N = 4
        wires = range(N)

        theta = [0.321, 0.4523, 0.21321, 0.123, 0.5234, 1.23]
        phi = [0.234, 0.324, 0.234, 1.453, 1.42341, -0.534]
        varphi = [0.42342, 0.234, 0.4523, 0.1121]

        with qml.utils.OperationRecorder() as rec:
            Interferometer(theta, phi, varphi, wires=wires)

        assert len(rec.queue) == 10

        expected_bs_wires = [[0, 1], [2, 3], [1, 2], [0, 1], [2, 3], [1, 2]]

        for idx, op in enumerate(rec.queue[:6]):
            assert isinstance(op, qml.Beamsplitter)
            assert op.parameters == [theta[idx], phi[idx]]
            assert op.wires == expected_bs_wires[idx]

        for idx, op in enumerate(rec.queue[6:]):
            assert isinstance(op, qml.Rotation)
            assert op.parameters == [varphi[idx]]
            assert op.wires == [idx]

    def test_four_mode_triangular(self, tol):
        """Test that a 4 mode interferometer using triangular mesh gives the correct gates"""
        N = 4
        wires = range(N)

        theta = [0.321, 0.4523, 0.21321, 0.123, 0.5234, 1.23]
        phi = [0.234, 0.324, 0.234, 1.453, 1.42341, -0.534]
        varphi = [0.42342, 0.234, 0.4523, 0.1121]

        with qml.utils.OperationRecorder() as rec:
            Interferometer(theta, phi, varphi, mesh='triangular', wires=wires)

        assert len(rec.queue) == 10

        expected_bs_wires = [[2, 3], [1, 2], [0, 1], [2, 3], [1, 2], [2, 3]]

        for idx, op in enumerate(rec.queue[:6]):
            assert isinstance(op, qml.Beamsplitter)
            assert op.parameters == [theta[idx], phi[idx]]
            assert op.wires == expected_bs_wires[idx]

        for idx, op in enumerate(rec.queue[6:]):
            assert isinstance(op, qml.Rotation)
            assert op.parameters == [varphi[idx]]
            assert op.wires == [idx]

    def test_integration(self, tol):
        """test integration with PennyLane and gradient calculations"""
        N = 4
        wires = range(N)
        dev = qml.device('default.gaussian', wires=N)

        sq = np.array([[0.8734294, 0.96854066],
                       [0.86919454, 0.53085569],
                       [0.23272833, 0.0113988 ],
                       [0.43046882, 0.40235136]])

        theta = np.array([3.28406182, 3.0058243, 3.48940764, 3.41419504, 4.7808479, 4.47598146])
        phi = np.array([3.89357744, 2.67721355, 1.81631197, 6.11891294, 2.09716418, 1.37476761])
        varphi = np.array([0.4134863, 6.17555778, 0.80334114, 2.02400747])

        @qml.qnode(dev)
        def circuit(theta, phi, varphi):
            for w in wires:
                qml.Squeezing(sq[w][0], sq[w][1], wires=w)

            Interferometer(theta=theta, phi=phi, varphi=varphi, wires=wires)
            return [qml.expval(qml.NumberOperator(w)) for w in wires]

        res = circuit(theta, phi, varphi)
        expected = np.array([0.96852694, 0.23878521, 0.82310606, 0.16547786])
        assert np.allclose(res, expected, atol=tol)

        # compare the two methods of computing the Jacobian
        jac_A = circuit.jacobian((theta, phi, varphi), method="A")
        jac_F = circuit.jacobian((theta, phi, varphi), method="F")
        assert jac_A == pytest.approx(jac_F, abs=tol)


class TestSingleExcitationUnitary:
    """Tests for the SingleExcitationUnitary template from the pennylane.templates.subroutine module."""

    @pytest.mark.parametrize(
        ("ph", "ref_gates"),
        [
        ([0,2],   [[0 , qml.RX      , [0]  , [-np.pi/2]] , [1 , qml.Hadamard, [2], []],
                   [7 , qml.RX      , [0]  , [ np.pi/2]] , [8 , qml.Hadamard, [2], []],
                   [9 , qml.Hadamard, [0]  , []]         , [10, qml.RX      , [2], [-np.pi/2]],
                   [16, qml.Hadamard, [0]  , []]         , [17, qml.RX      , [2], [ np.pi/2]],
                   [4 , qml.RZ      , [2]  , [np.pi/6]]  , [13, qml.RZ      , [2], [-np.pi/6]]]
                   ),

        ([10,11], [[0 , qml.RX      , [10]  , [-np.pi/2]] , [1 , qml.Hadamard, [11], []],
                   [12, qml.Hadamard, [10]  , []]         , [13, qml.RX      , [11], [ np.pi/2]],
                   [3 , qml.RZ      , [11], [np.pi/6]]    , [10, qml.RZ      , [11], [-np.pi/6]]]
                   ),        

        ([1,4],   [[2 , qml.CNOT, [1,2], []], [3 , qml.CNOT, [2,3], []], [4 , qml.CNOT, [3,4], []],
                   [6 , qml.CNOT, [3,4], []], [7 , qml.CNOT, [2,3], []], [8 , qml.CNOT, [1,2], []],
                   [13, qml.CNOT, [1,2], []], [14, qml.CNOT, [2,3], []], [15, qml.CNOT, [3,4], []],
                   [17, qml.CNOT, [3,4], []], [18, qml.CNOT, [2,3], []], [19, qml.CNOT, [1,2], []]]
                   ),

        ([10,11], [[2 , qml.CNOT, [10,11] , []], [4  , qml.CNOT, [10,11], []],
                   [9 , qml.CNOT, [10,11] , []], [11 , qml.CNOT, [10,11], []]]
                   )        
        ]
    )
    def test_single_ex_unitary_operations(self, ph, ref_gates):
        """Test the correctness of the SingleExcitationUnitary template including the gate count
        and order, the wires each operation acts on and the correct use of parameters 
        in the circuit."""

        sqg = 10
        cnots = 4*(ph[1]-ph[0])
        weight = np.pi/3
        with qml.utils.OperationRecorder() as rec:
            SingleExcitationUnitary(weight, wires_rp=ph)

        idx = ref_gates[0][0]

        exp_gate = ref_gates[0][1]
        res_gate = rec.queue[idx]

        exp_wires = ref_gates[0][2]
        res_wires = rec.queue[idx]._wires

        exp_weight = ref_gates[0][3]
        res_weight = rec.queue[idx].parameters        

        assert len(rec.queue) == sqg + cnots
        assert isinstance(res_gate, exp_gate) 
        assert res_wires == exp_wires
        assert res_weight == exp_weight

    @pytest.mark.parametrize(
        ("weight", "ph", "msg_match"),
        [
            ( 0.2      , [0]         , "'wires_rp' must be of shape"),
            ( 0.2      , []          , "'wires_rp' must be of shape"),
            ([0.2, 1.1], [0,2]       , "'weight' must be of shape"),
            ( 0.2      , None        , "wires must be a positive integer"),
            ( 0.2      , ["a", "b"]  , "wires must be a positive integer"),
            ( 0.2      , [1.13, 5.23], "wires must be a positive integer"),
            ( 0.2      , [3, 3]      , "wires_rp_1 must be > wires_rp_0"),
            ( 0.2      , [3, 1]      , "wires_rp_1 must be > wires_rp_0")
        ]
    )
    def test_single_excitation_unitary_exceptions(self, weight, ph, msg_match):
        """Test that SingleExcitationUnitary throws an exception if ``weight`` or 
        ``ph`` parameter has illegal shapes, types or values."""
        dev = qml.device("default.qubit", wires=5)

        def circuit(weight=weight, wires_rp=ph):
            SingleExcitationUnitary(weight=weight, wires_rp=ph)
            return qml.expval(qml.PauliZ(0))

        qnode = qml.QNode(circuit, dev)

        with pytest.raises(ValueError, match=msg_match):
            qnode(weight=weight, wires_rp=ph)

    @pytest.mark.parametrize(
        ("weight", "ph", "expected"),
        [
            ( 2.21375586 , [0, 2], [-0.59956665, 1.        , 0.59956665, -1.]),
            ( -5.93892805, [1, 3], [ 1.        , 0.94132639, -1.       , -0.94132639])
        ]
    )
    def test_integration(self, weight, ph, expected, tol):
        """Test integration with PennyLane and gradient calculations"""

        N = 4
        wires = range(N)
        dev = qml.device('default.qubit', wires=N)

        @qml.qnode(dev)
        def circuit(weight):
            init_state = np.flip(np.array([1,1,0,0]))
            qml.BasisState(init_state, wires=wires)
            SingleExcitationUnitary(weight, wires_rp=ph)

        return [qml.expval(qml.PauliZ(w)) for w in range(N)]

        res = circuit(weight)
        assert np.allclose(res, np.array(expected), atol=tol)

        # compare the two methods of computing the Jacobian
        jac_A = circuit.jacobian((weight), method="A")
        jac_F = circuit.jacobian((weight), method="F")
        assert jac_A == pytest.approx(jac_F, abs=tol)


class TestArbitraryUnitary:
    """Test the ArbitraryUnitary template."""

    def test_correct_gates_single_wire(self):
        """Test that the correct gates are applied on a single wire."""
        weights = np.arange(3, dtype=float)

        with qml.utils.OperationRecorder() as rec:
            ArbitraryUnitary(weights, wires=[0])

        assert all(op.name == "PauliRot" and op.wires == [0] for op in rec.queue)

        pauli_words = ["X", "Y", "Z"]

        for i, op in enumerate(rec.queue):
            assert op.params[0] == weights[i]
            assert op.params[1] == pauli_words[i]

    def test_correct_gates_two_wires(self):
        """Test that the correct gates are applied on two wires."""
        weights = np.arange(15, dtype=float)

        with qml.utils.OperationRecorder() as rec:
            ArbitraryUnitary(weights, wires=[0, 1])

        assert all(op.name == "PauliRot" and op.wires == [0, 1] for op in rec.queue)

        pauli_words = ["XI", "YI", "ZI", "ZX", "IX", "XX", "YX", "YY", "ZY", "IY", "XY", "XZ", "YZ", "ZZ", "IZ"]

        for i, op in enumerate(rec.queue):
            assert op.params[0] == weights[i]
            assert op.params[1] == pauli_words[i]
