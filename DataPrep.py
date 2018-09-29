import numpy as np

class PatientObject:

    def __init__(self, concept_code_list, has_target):
        # LeftData is a list of strings of concept codes (the codes being concepts attached to each patient)
        # HasTarget is an int, 0 if the patient doesn't have the target condition and 1 if the patient does
        self.LeftData = concept_code_list
        self.HasTarget = has_target

    def getLeftData(self):
        return self.LeftData

    def getHasTarget(self):
        return self.HasTarget

class XGInput:

    def __init__(self, numPatients, numConcepts):
        #LeftMatrix has patients as rows and the universe of concepts as columns, with value 1 when the patient in that row has the code in that column
        #RightMatrix is the same as binary vector HasTarget
        self.LeftMatrix = np.zeros((numPatients, numConcepts))
        self.RightMatrix = np.zeros((numPatients, 1))

    def formLeft(self, list_PatientObject, universe_list):
        #universe_list is a list of universe of codes
        #generates LeftMatrix
        for row in range(0, len(list_PatientObject)):
            for column in range(0, len(universe_list)):
                if universe_list[column] in list_PatientObject[row]:
                    self.LeftMatrix[row][column] = 1

    def formRight(self, list_PatientObject):
        #generates RightMatrix
        for element in range(0, len(list_PatientObject)): #assign every value of RightMatrix
            patient = list_PatientObject[element]
            self.RightMatrix[element] = patient.getHasTarget()