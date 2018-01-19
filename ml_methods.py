import numpy as np
from sklearn.naive_bayes import BernoulliNB
from sklearn.neural_network import MLPClassifier

class ml_methods(object):

    def __init__(self):
        pass

    def MLP(self, X, y) -> list:
        classify = MLPClassifier()
        classify.fit(X, y)
        return(classify.coefs_)

