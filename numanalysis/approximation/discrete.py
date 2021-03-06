import numpy as np
from typing import Callable

from util import dot_discrete, square_root_method

class DiscreteApproximation:
    def __init__(self, a: float, b: float, f: Callable[[float], float]):
        self._a = a
        self._b = b
        self._f = f
        self._polynom = None
        self._min_nodes = 20

    def get_mean_quadratic_approximation(self, n: int = 20, verbose: bool = False):
        if n == 0 or n < self._min_nodes:
            n = self._min_nodes
        nodes = np.linspace(self._a, self._b, n)
        print(len(nodes))
        m = self._opt_power(n, nodes)
        matrix, v = self._make_system(m, nodes)
        c = square_root_method(matrix, v)

        def polynom(x):
            s = 0
            x_pow = 1
            for k in range(m + 1):
                s += c[k] * x_pow
                x_pow *= x
            return s

        def delta(x):
            return self._f(x) - polynom(x)

        sigma = (dot_discrete(delta, delta, nodes) / (n - m))
        print(f'm* = {m}, sigma* = {sigma}')
        self._polynom = polynom
        if verbose:
            print("Discrete delta: ", end='')
            self._delta_descrete(m)

        return self._polynom

    def _opt_power(self, n, nodes):
        costs = [np.inf for _ in range(n)]
        for m in range(1, n):
            matrix, v = self._make_system(m, nodes)

            c = square_root_method(matrix, v)

            def polynom(x: float):
                s = 0
                x_pow = 1
                for k in range(m + 1):
                    s += c[k] * x_pow
                    x_pow *= x
                return s

            def delta(x: float):
                return self._f(x) - polynom(x)

            costs[m] = (dot_discrete(delta, delta, nodes) / (n - m))
            print(f"m = {m}, sigma = {costs[m]}")
        opt_power = int(input("Analyze costs and input optimal power: "))
        return opt_power

    def _make_system(self, m, nodes):
        v = np.array([
            dot_discrete(self._f, lambda x: x ** i, nodes)
            for i in range(m + 1)])
        matrix = np.array([[dot_discrete(lambda x: x ** j, lambda x: x ** i, nodes)
                            for j in range(m + 1)]
                           for i in range(m + 1)])
        return matrix, v

    def _delta_descrete(self, n):
        nodes = np.linspace(self._a, self._b, n + 1)
        print("||f-Pm||^2 =", dot_discrete(lambda x: self._f(x) - self._polynom(x),
                                           lambda x: self._f(x) - self._polynom(x), nodes))
