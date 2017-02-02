
class MacroscopicValues(object):

    def __init__(self, stencil):
        self.stencil = stencil

    def __call__(self, pdfs):

        h = 0.0
        u = self.stencil.Vector()

        for alpha in self.stencil.Q:
            pdf = pdfs[alpha]
            h += pdf
            u += self.stencil.e[alpha] * pdf

        return h, u / h
