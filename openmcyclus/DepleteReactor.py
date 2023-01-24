from cyclus.agents import Facility 

class DepleteReactor(Facility):
    '''
    Archetype class to model a reactor facility that is 
    coupled to the stand alone depletion solver in OpenMC.
    With the exception of the depletion solver, this 
    archetype has the same functionality as the 
    cycamore:Reactor archetype.
    '''
    def tick(self):
        print("Hello ")

    def tock(self):
        print("World \n")
