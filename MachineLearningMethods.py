import numpy as np
import pandas as pd
import xgboost as xbg
from sklearn.naive_bayes import BernoulliNB
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import SGDClassifier, LassoLars, LinearRegression

class MachineLearningMethods(object):

    def __init__(self):
        pass

    def multi_layer_percep(self, X, y) -> list:
        classify = MLPClassifier()
        classify.fit(X, y)
        return(classify.coefs_)
    
    def gradient_boost_classif(self, X, y):
        classify = GradientBoostingClassifier()
        classify.fit(X, y)
        return(classify.feature_importances_)

    def stand_gradient_desc(self, X, y):
        classify = SGDClassifier()
        classify.fit(X, y)
        return(classify.coef_[0])

    def lasso_lars(self, X, y):
        classify = LassoLars()
        classify.fit(X, y)
        return(classify.coef_)

    def gradient_boost(self, X, y, param, num_round):
        real_X = xgb.DMatrix(npymat, X)
        real_y = xgb.DMatrix(y)
        param = {'max_depth': 2, 'eta': 1, 'silent': 1, 'objective': 'binary:logistic'}
        bst = xgb.train(param, real_X)

    def linear_regr(self, X, y):
        classify = LinearRegression()
        classify.fit(X, y)
        return(classify.coef_)
