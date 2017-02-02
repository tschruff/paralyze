
class Zhou(object):

    def __call__(self, alpha, h, u):
        if alpha == 0:
            return 0
        feq = 0.0
        if alpha % 2 == 0:
            return feq / 4.0
        else:
            return feq
