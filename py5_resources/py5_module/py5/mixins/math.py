from typing import overload

import numpy as np
from numpy.random import MT19937
from numpy.random import RandomState, SeedSequence

class MathMixin:

    _rs = RandomState(MT19937(SeedSequence()))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # *** BEGIN METHODS ***

    @classmethod
    def sin(cls, angle: float) -> float:
        """$class_Sketch_sin"""
        return np.sin(angle)

    @classmethod
    def cos(cls, angle: float) -> float:
        """$class_Sketch_cos"""
        return np.cos(angle)

    @classmethod
    def tan(cls, angle: float) -> float:
        """$class_Sketch_tan"""
        return np.tan(angle)

    @classmethod
    def asin(cls, value: float) -> float:
        """$class_Sketch_asin"""
        return np.arcsin(value)

    @classmethod
    def acos(cls, value: float) -> float:
        """$class_Sketch_acos"""
        return np.arccos(value)

    @classmethod
    def atan(cls, value: float) -> float:
        """$class_Sketch_atan"""
        return np.arctan(value)

    @classmethod
    def atan2(cls, y: float, x: float) -> float:
        """$class_Sketch_atan2"""
        return np.arctan2(y, x)

    @classmethod
    def degrees(cls, radians: float) -> float:
        """$class_Sketch_degrees"""
        return np.degrees(radians)

    @classmethod
    def radians(cls, degrees: float) -> float:
        """$class_Sketch_radians"""
        return np.radians(degrees)

    @classmethod
    def constrain(cls, amt: float, low: float, high: float) -> float:
        """$class_Sketch_constrain"""
        return np.where(amt < low, low, np.where(amt > high, high, amt))

    @classmethod
    def dist(cls, *args: float) -> float:
        """$class_Sketch_dist"""
        p1 = args[:(len(args) // 2)]
        p2 = args[(len(args) // 2):]
        assert len(p1) == len(p2)
        return sum([(a - b)**2 for a, b in zip(p1, p2)])**0.5

    @classmethod
    def lerp(cls, start: float, stop: float, amt: float) -> float:
        """$class_Sketch_lerp"""
        return amt * (stop - start) + start

    @classmethod
    def mag(cls, *args: float) -> float:
        """$class_Sketch_mag"""
        return sum([x * x for x in args])**0.5

    @classmethod
    def norm(cls, value: float, start: float, stop: float) -> float:
        """$class_Sketch_norm"""
        return (value - start) / (stop - start)

    @classmethod
    def sq(cls, n: float) -> float:
        """$class_Sketch_sq"""
        return n * n

    @overload
    def random(cls, high: float) -> float:
        """$class_Sketch_random"""
        pass

    @overload
    def random(cls, low: float, high: float) -> float:
        """$class_Sketch_random"""
        pass

    @classmethod
    def random_seed(cls, seed: int) -> None:
        cls._rs = RandomState(MT19937(SeedSequence(seed)))

    @classmethod
    def random(cls, *args: float) -> float:
        """$class_Sketch_random"""
        if len(args) == 1:
            high = args[0]
            if isinstance(high, (int, float)):
                return high * cls._rs.rand()
        elif len(args) == 2:
            low, high = args
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                return low + (high - low) * cls._rs.rand()

        types = ','.join([type(a).__name__ for a in args])
        raise TypeError(f'No matching overloads found for Sketch.random({types})')

    @classmethod
    def random_gaussian(cls) -> float:
        return cls._rs.randn()
