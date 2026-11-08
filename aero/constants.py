"""
constants.py
Physical constants and unit helpers. Everything in the engine uses SI units
(metres, seconds, kilograms, newtons, pascals) except angles, which the
user-facing API takes in degrees.
"""

RHO_SEA_LEVEL = 1.225      # kg/m^3, ISA sea-level air density
GRAVITY = 9.80665          # m/s^2
MS_TO_KMH = 3.6            # multiply m/s by this to get km/h
