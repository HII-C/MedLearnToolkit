def doLearning(self):      
        C = [10**(k) for k in xrange(-4,4)]
        params = [{'C':C, 'penalty':['l1'],}]
        print "learning!"
        print >> self.backend.parent.logfile, str(time.time())+' learning' , self.name
        self.backend.parent.logfile.flush()
        s = time.time()

        if self.online:
            #Learner=SGDClassifier(loss='log', alpha=0.0001)
            Learner=GridSearchCV(LogisticRegression(), params, cv=3, scoring='log_loss')
        else:
            Learner=GridSearchCV(LogisticRegression(), params, cv=3, scoring='log_loss')

        X = self.sparse_X_csr
        while X == None:
            time.sleep(1)
            print 'waiting for sparse csr'
            X = self.sparse_X_csr

        print 'transform', time.time() -s
        print 'pos examples', sum(self.Y)
        print 'pos features', X.sum()
        try:
            Learner.fit(X, self.Y)
            print 'best params', Learner.best_params_
            print 'grid scores', Learner.grid_scores_
            Learner = Learner.best_estimator_
            
        except:
            print "could not learn!"
        
        self.estimator = Learner
        self.dumpDecisionRule()
        print 'fit', time.time() -s
        self.predictions = self.sparse_X_csr * Learner.coef_.T + Learner.intercept_
        print 'predict', time.time() -s
        self.predictions = np.exp(self.predictions) / (1+np.exp(self.predictions))
        print 'scale', time.time() -s
        

        self.eval_predictions = self.sparse_X_csr_eval * Learner.coef_.T + Learner.intercept_
        self.eval_predictions = np.exp(self.eval_predictions) / (1+np.exp(self.eval_predictions))


        self.ranking = zip([pat['index'] for pat in self.patient_list], np.ravel(self.predictions).tolist())
        self.ranking += zip(self.backend.validate_patient_ids, np.ravel(self.eval_predictions).tolist())
        self.ranking = dict(self.ranking)


        print 'rank', time.time() -s
        print "done"

        try:
            self.do_evaluation()
            print 'evaluating new model'
        except:
            pass