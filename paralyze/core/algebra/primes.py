import math
import numpy as np


def is_prime(number):
    """Checks if given ``number`` is a prime.
    """
    assert isinstance(number, int), "is_prime only handles integers"

    if number == 0 or number == 1:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False
    else:
        sqrtN = math.floor(math.sqrt(number))
        for i in range(3, sqrtN+1, 2):
            if number % i == 0:
                return False
        return True


def primes(number):
    assert isinstance(number, int)

    if number < 2:
        return []

    markers = [False for i in range(number+1)]
    ps = []

    p = 2
    while p <= number//2:
        ps.append(p)
        for i in range(p+p, number+1, p):
            markers[i] = True

        p += 1
        while p <= number//2 and markers[p]:
            p += 1

    for i in range(number//2+1, number+1):
        if not markers[i]:
            ps.append(i)

    return np.array(ps)


def prime_factors(number):
    """
    """
    assert isinstance(number, int)
    assert number != 0

    ps = primes(number)
    factors = []
    nRest = number

    for p in ps:
        if p*p > number:
            break
        while nRest % p == 0:
            nRest /= p
            factors.append(p)

    if nRest != 1:
        factors.append(nRest)

    return np.array(factors)
