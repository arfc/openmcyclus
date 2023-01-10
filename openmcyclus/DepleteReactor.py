from cyclus.agents import Facility 

class DepleteReactor(Facility):
    '''
    Sample facility to get things going
    '''
    def tick(self):
        print("Hello ")

    def tock(self):
        print("World \n")
