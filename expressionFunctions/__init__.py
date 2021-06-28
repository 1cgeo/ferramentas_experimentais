import os
from qgis import gui, core

def getFunctionsFolderPath():
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'functions'
    )

def loadExpressionFunctions():
    functionsFolderPath = getFunctionsFolderPath()
    wd = gui.QgsExpressionBuilderWidget()
    for fileName in os.listdir( functionsFolderPath ):
        codeFilePath = os.path.join( functionsFolderPath, fileName )
        with open(codeFilePath, 'r') as f:
            code = f.read()
            wd.loadFunctionCode(  code )
        core.QgsPythonRunner.run( code )