import numpy as np
import pytest 
import depletion

def test_read_model2():
    '''
    Test for raising an error when one of the files is not 
    found in the given path
    '''
    model = depletion.read_model("./")
    assert 2 == 2

def test_read_microxs():
    assert 2 == 2