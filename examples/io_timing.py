import cProfile
import os
import pstats

here = os.path.abspath(os.path.dirname(__file__))

CSB = os.path.join(here, '../data/uniform-8.csv')
NPY = os.path.join(here, '../data/uniform-8.npy')


def cprofile(func):
    def profiled_func(*args, **kwargs):
        pr = cProfile.Profile()
        try:
            pr.enable()
            result = func(*args, **kwargs)
            pr.disable()
            return result
        finally:
            ps = pstats.Stats(pr)
            ps.strip_dirs()
            ps.sort_stats('cumtime').print_stats(20)
    return profiled_func


@cprofile
def load_csb():
    return CSBFile.load(CSB)


@cprofile
def load_npy():
    return load_spheres(NPY)


def main():
    bodies = load_csb()
    if not os.path.exists(NPY):
        save_spheres(bodies, NPY)
    load_npy()


if __name__ == '__main__':
    main()
