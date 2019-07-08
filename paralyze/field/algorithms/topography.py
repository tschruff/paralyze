import numpy as np

def find_local_extrema(a, stencil, comparator):
    shape = a.shape
    extrema = [[] for k in range(len(shape))]

    it = np.nditer(a, flags=['multi_index'], op_flags=['readonly'])
    while not it.finished:

        v = it[0]
        i = it.multi_index
        is_peak = True

        for d in stencil:
            j = tuple([sum(x) for x in zip(i, d)])
            try:
                if comparator(a[j], v):
                    is_peak = False
                    break
            except IndexError:
                pass

        if is_peak:
            for k in range(len(i)):
                extrema[k].append(i[k])

        it.iternext()

    return tuple([np.array(k) for k in extrema])
