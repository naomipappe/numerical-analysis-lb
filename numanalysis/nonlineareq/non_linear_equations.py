from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class NonLinearEquationResult:
    calculation_result: float = 0
    log: list = field(default_factory=list)

    def __str__(self):
        return f'\n'.join(self.log)

    def __repr__(self):
        return f'res = {self.calculation_result}'


@dataclass
class NonLinearEquation:
    lhs: Callable[[float or np.ndarray], float]
    left_border: float
    right_border: float
    initial_root_candidate: float = None
    lhs_derivative: Callable[[float or np.ndarray], float] = None
    lhs_derivative2: Callable[[float or np.ndarray], float] = None
    delta: float = 1e-6

    def __post_init__(self):
        self.__input_check()

    def __input_check(self):
        if self.left_border >= self.right_border:
            raise ValueError(
                f'Invalid boundaries, left border ={self.left_border} >= right border ={self.right_border}'
            )
        if self.initial_root_candidate < self.left_border or self.initial_root_candidate > self.right_border:
            raise ValueError(
                f'Invalid starting approximation, initial root candidate={self.initial_root_candidate} '
                f'is out of boundaries[{self.left_border}, {self.right_border}] '
            )
        if self.lhs(self.left_border) * self.lhs(self.right_border) > 0:
            raise ValueError(
                f'No root can be found on the segment [{self.left_border}, {self.right_border}]'
            )

    def initial_approximation_fault(self):
        return abs(self.closest_border() - self.initial_root_candidate)

    def closest_border(self):
        if self.lhs(self.initial_root_candidate) * self.lhs(self.right_border) < 0:
            return self.right_border
        return self.left_border


class NonLinearEquationMethod:
    @classmethod
    def solve(cls, equation: NonLinearEquation) -> NonLinearEquationResult:
        raise NotImplementedError()

    @classmethod
    def __initial_root(cls, equation: NonLinearEquation):
        raise NotImplementedError()


class Newton(NonLinearEquationMethod):
    @classmethod
    def solve(cls, equation: NonLinearEquation) -> NonLinearEquationResult:
        """
        lhs: Left-hand side of the equation\n
        lhs_der: Derivative of the left - hand side of the equation\n
        initial_root_candidate: Initial root approximation\n
        left_border: Left border of the search interval\n
        right_border: Right border of the search interval\n
        delta: Tolerated method error\n
        returns Approximated root of the lhs in the interval
        """
        cls.__initial_root(equation)

        def step(root_candidate):
            return root_candidate - equation.lhs(root_candidate) / equation.lhs_derivative(root_candidate)

        root = equation.initial_root_candidate
        i = 0
        result = NonLinearEquationResult()
        while abs(step(root) - root) > equation.delta or equation.lhs(step(root)) > equation.delta:
            result.log.append(
                f'Iteration number = {i}, current approximation = {root}, error = {equation.lhs(root)}'
            )
            i += 1
            root = step(root)

        result.calculation_result = root

        return result

    @classmethod
    def __initial_root(cls, equation: NonLinearEquation):
        if equation.initial_root_candidate is None:
            if equation.lhs(equation.left_border) * equation.lhs_derivative2(equation.left_border) > 0:
                equation.initial_root_candidate = equation.left_border
            elif equation.lhs(equation.right_border) * equation.lhs_derivative2(equation.right_border) > 0:
                equation.initial_root_candidate = equation.right_border
            else:
                equation.initial_root_candidate = (equation.left_border + equation.right_border) / 2


class Secant(NonLinearEquationMethod):
    @classmethod
    def solve(cls, equation: NonLinearEquation) -> NonLinearEquationResult:
        """
        Solve a non-linear equation using the secant method
        Parameters
        ----------
        equation : NonLinearEquation
        NonLinearEquation object, with equation left-hand side derivative initialised

        Returns
        -------
        result : NonLinearEquationResult
        NonLinearEquationResult object, containing the resulting root approximation
        as well as calculation logs

        Examples
        --------
        Solve the equation sin(x+2)-x**2+2*x-1 = 0
        from numanalysis.nonlineareq.non_linear_equations import Secant, NonLinearEquation, NonLinearEquationResult

        def lhs(x: float) -> float:
            return sin(x+2)-x**2+2*x-1

        left_border, right_border = 1, 2
        initial_root_candidate = 1

        equation = NonLinearEquation(lhs, left_border, right_border, initial_root_candidate, lhs_derr)
        result = Secant.solve(equation)
        """

        x_values = np.linspace(equation.left_border, equation.right_border, min(
            int(1. / equation.delta), 10 ** 5))
        min_val, max_val = round(np.min(np.abs(equation.lhs_derivative(x_values))), 6), round(
            np.max(np.abs(equation.lhs_derivative(x_values))), 6)
        tau = 2. / (min_val + max_val)

        def step(root_candidate):
            return root_candidate - np.sign(equation.lhs_derivative(root_candidate)) * tau * equation.lhs(
                root_candidate)

        i = 0
        root = equation.initial_root_candidate
        result = NonLinearEquationResult()
        while abs(step(root) - root) > equation.delta or equation.lhs(step(root)) > equation.delta:
            result.log.append(
                f'Iteration number = {i}, current approximation = {root}, error = {equation.lhs(root)}'
            )
            i += 1
            root = step(root)
        result.calculation_result = root

        return result

    @classmethod
    def __initial_root(cls, equation: NonLinearEquation):
        if equation.initial_root_candidate is None:
            middle_point = (equation.left_border + equation.right_border) / 2
            equation.initial_root_candidate = (equation.closest_border() + middle_point) / 2


class Relaxation(NonLinearEquationMethod):
    @classmethod
    def solve(cls, equation: NonLinearEquation) -> NonLinearEquationResult:
        """
        lhs: Left-hand side of the equation\n
        initial_root_candidate: Initial root approximation\n
        left_border: Left border of the search interval\n
        right_border: Right border of the search interval\n
        delta: Tolerated method error\n
        returns Approximated root of the lhs in the interval
        """

        root = (equation.closest_border() + equation.initial_root_candidate) / 2
        previous_root = equation.initial_root_candidate

        def step(cur, prev):
            cur, prev = cur - \
                        equation.lhs(cur) * (cur - prev) / \
                        (equation.lhs(cur) - equation.lhs(prev)), cur
            return cur, prev

        i = 0
        result = NonLinearEquationResult()
        while abs(root - previous_root) > equation.delta or abs(equation.lhs(root)) > equation.delta:
            result.log.append(
                f'Iteration number = {i}, current approximation = {root}, error = {equation.lhs(root)}'
            )
            i += 1
            root, previous_root = step(root, previous_root)
        result.calculation_result = root
        return result

    @classmethod
    def __initial_root(cls, equation: NonLinearEquation):
        if equation.initial_root_candidate is None:
            middle_point = (equation.left_border + equation.right_border) / 2
            equation.initial_root_candidate = (equation.closest_border() + middle_point) / 2
