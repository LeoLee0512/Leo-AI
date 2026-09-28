"""Opt-in CPU/float64 autodiff component tests; no installed-Torch skip.

Execute with an explicitly inspected Python that already has Torch:
    python tests/pinn/torch_derivative_sanity.py

This module deliberately does not match pytest's test_*.py discovery pattern.
Missing Torch is a failing explicit command, never a skipped acceptance test.
The functions tested here are independent controls, not a nonexistent PINN runner.
"""

import math
import unittest

import torch


def derivatives(output, coordinates):
    first = torch.autograd.grad(output, coordinates, torch.ones_like(output), create_graph=True)[0]
    second = torch.autograd.grad(first, coordinates, torch.ones_like(first), create_graph=True)[0]
    return first, second


class TorchDerivativeSanity(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        self.x = torch.linspace(0.0, 1.0, 129, dtype=torch.float64, device="cpu").reshape(-1, 1)
        self.x.requires_grad_(True)

    def test_sine_first_second_and_forcing(self):
        output = torch.sin(math.pi * self.x)
        first, second = derivatives(output, self.x)
        self.assertLess((first - math.pi * torch.cos(math.pi * self.x)).abs().max().item(), 1e-14)
        self.assertLess((second + math.pi**2 * torch.sin(math.pi * self.x)).abs().max().item(), 1e-12)
        self.assertLess(output[[0, -1]].abs().max().item(), 1e-14)
        self.assertEqual(first.dtype, torch.float64)
        self.assertEqual(second.device.type, "cpu")

    def test_polynomial_derivatives(self):
        first, second = derivatives(self.x**4 - 3.0 * self.x**2 + 2.0 * self.x, self.x)
        self.assertLess((first - (4.0 * self.x**3 - 6.0 * self.x + 2.0)).abs().max().item(), 1e-14)
        self.assertLess((second - (12.0 * self.x**2 - 6.0)).abs().max().item(), 1e-14)

    def test_coordinate_mapping_chain_rule(self):
        # Explicit z=2x-1 mapping; losing the factors 2 and 4 must be visible.
        z = 2.0 * self.x - 1.0
        first, second = derivatives(z**3, self.x)
        self.assertLess((first - 6.0 * z**2).abs().max().item(), 1e-14)
        self.assertLess((second - 24.0 * z).abs().max().item(), 1e-14)

    def test_embedded_boundary_product_rule(self):
        first, second = derivatives(self.x * (1.0 - self.x) * torch.sin(math.pi * self.x), self.x)
        expected_first = ((1.0 - 2.0 * self.x) * torch.sin(math.pi * self.x)
                          + self.x * (1.0 - self.x) * math.pi * torch.cos(math.pi * self.x))
        expected_second = (-2.0 * torch.sin(math.pi * self.x)
                           + 2.0 * (1.0 - 2.0 * self.x) * math.pi * torch.cos(math.pi * self.x)
                           - self.x * (1.0 - self.x) * math.pi**2 * torch.sin(math.pi * self.x))
        self.assertLess((first - expected_first).abs().max().item(), 1e-14)
        self.assertLess((second - expected_second).abs().max().item(), 1e-12)

    def test_detached_output_is_an_error(self):
        with self.assertRaises(RuntimeError):
            derivatives(torch.sin(math.pi * self.x).detach(), self.x)

    def test_accidental_no_grad_is_an_error(self):
        with torch.no_grad():
            output = torch.sin(math.pi * self.x)
        with self.assertRaises(RuntimeError):
            derivatives(output, self.x)

    def test_missing_derivative_graph_is_an_error(self):
        output = torch.sin(math.pi * self.x)
        first = torch.autograd.grad(output, self.x, torch.ones_like(output), create_graph=False)[0]
        with self.assertRaises(RuntimeError):
            torch.autograd.grad(first, self.x, torch.ones_like(first))

    def test_fixed_seed_initialization_and_derivatives_repeat_exactly(self):
        def evaluate(seed):
            torch.manual_seed(seed)
            network = torch.nn.Sequential(torch.nn.Linear(1, 8), torch.nn.Tanh(), torch.nn.Linear(8, 1))
            network.to(device="cpu", dtype=torch.float64)
            output = network(self.x)
            first, second = derivatives(output, self.x)
            self.assertTrue(all(parameter.dtype == torch.float64 for parameter in network.parameters()))
            return tuple(value.detach().clone() for value in (output, first, second))
        left, right = evaluate(20260904), evaluate(20260904)
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(left, right)))
        self.assertFalse(torch.equal(left[0], evaluate(20260905)[0]))


if __name__ == "__main__":
    print(f"VALIDATOR_COMPONENT; Torch={torch.__version__}; device=cpu; dtype=float64; trainingApplicable=false", flush=True)
    unittest.main(verbosity=2)
