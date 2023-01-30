import numpy as np
import pytest 
from openmcyclus import depletion
import xml.etree.ElementTree as ET

def test_read_model():
    '''
    Test for when the files are found
    '''
    model = depletion.read_model("../")
    assert 2 == 2

def test_read_microxs():
    microxs = depletion.read_microxs("../")
    assert 2 == 2

def test_create_recipe():
    depletion.create_recipe("../", "uox", "./")
    output_recipe = "./uox.xml"
    tree = ET.parse(output_recipe)
    root = tree.getroot()
    assert root.tag == 'recipes'
    assert root[0].tag == 'recipe'
    assert root[0][0].tag == 'name'
    assert root[0][1].tag == 'basis'
    assert root[0][2].tag == 'nuclide'
    assert root[0][2][0].tag == 'id'
    assert root[0][2][1].tag == 'comp'
    
