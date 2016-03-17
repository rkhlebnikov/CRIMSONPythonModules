import sys

try:
    import PythonQt
except:
    import PythonQtMock as PythonQt
    sys.modules["PythonQt"] = PythonQt

from xml.etree import ElementTree as ET


import os
import shutil
import zipfile
import tempfile
import struct
import base64
import numpy

from xml.dom.minidom import parse, parseString

import CRIMSONCore
import CRIMSONSolver

def extractFaceIdentifiers(dom, bc):
    faceIdDomObjects = [child for child in dom.getElementsByTagName('_faces')[0].childNodes if child.nodeName == 'item']
    faceIdentifiers = []
    for faceIdDomObj in faceIdDomObjects:
        faceType = int(faceIdDomObj.getElementsByTagName('faceId.faceType')[0].childNodes[0].data)
        parentSolidIndices = tuple((x.childNodes[0].data for x in faceIdDomObj.getElementsByTagName('item')))
        faceIdentifiers.append(CRIMSONCore.FaceIdentifier.FaceIdentifier(faceType, parentSolidIndices))
    bc.faceIdentifiers = tuple(faceIdentifiers)


def extractProperties(dom, bc):
    propertiesDomObjects = dom.getElementsByTagName('properties')[0].getElementsByTagName('item')

    for propDomObj in propertiesDomObjects:
        propName = propDomObj.getElementsByTagName('first')[0].childNodes[0].data.replace('_', ' ')
        encodedPropValue = propDomObj.getElementsByTagName('base64EncodedVariant')[0].childNodes[0].data

        variantType = struct.unpack('>I', base64.b64decode(encodedPropValue)[:4])[0]

        value = None
        if variantType == 6:
            format = '>d'
        if variantType == 2:
            format = '>i'
        if variantType == 1:
            format = '>?'

        value = struct.unpack(format, base64.b64decode(encodedPropValue)[5:])[0]
        bc.getProperties()[propName] = value


def upgradeBoundaryConditionSet(path, filename):
    return CRIMSONSolver.BoundaryConditionSets.BoundaryConditionSet.BoundaryConditionSet()


def upgradeInitialPressureBC(path, filename):
    bc = CRIMSONSolver.BoundaryConditions.InitialPressure.InitialPressure()
    dom = parse(os.path.join(path, filename))
    extractProperties(dom, bc)
    return bc


def upgradeRCRBC(path, filename):
    bc = CRIMSONSolver.BoundaryConditions.RCR.RCR()
    dom = parse(os.path.join(path, filename))
    extractFaceIdentifiers(dom, bc)
    extractProperties(dom, bc)
    return bc


def upgradeNoSlipBC(path, filename):
    bc = CRIMSONSolver.BoundaryConditions.NoSlip.NoSlip()
    dom = parse(os.path.join(path, filename))
    extractFaceIdentifiers(dom, bc)
    return bc


def upgradeZeroPressureBC(path, filename):
    bc = CRIMSONSolver.BoundaryConditions.ZeroPressure.ZeroPressure()
    dom = parse(os.path.join(path, filename))
    extractFaceIdentifiers(dom, bc)
    return bc


def upgradeSolverSetup(path, filename):
    ss = CRIMSONSolver.SolverSetups.SolverSetup3D.SolverSetup3D()
    dom = parse(os.path.join(path, filename))
    extractProperties(dom, ss)
    return ss


def upgradeSolverStudy(path, filename):
    ss = CRIMSONSolver.SolverStudies.SolverStudy.SolverStudy()
    dom = parse(os.path.join(path, filename))
    ss.setMeshNodeUID(dom.getElementsByTagName('_meshNodeUID')[0].childNodes[0].data)
    ss.setBoundaryConditionSetNodeUIDs([dom.getElementsByTagName('_bcSetNodeUID')[0].childNodes[0].data])
    ss.setSolverSetupNodeUID(dom.getElementsByTagName('_solverSetupNodeUID')[0].childNodes[0].data)

    return ss


def extractArray(arrayDomObject):
    array = numpy.empty([int(arrayDomObject.getElementsByTagName('count')[0].childNodes[0].data), 2])

    for index, valuePairDomObj in enumerate(arrayDomObject.getElementsByTagName('item')):
        array[index, 0] = float(valuePairDomObj.getElementsByTagName('first')[0].childNodes[0].data)
        array[index, 1] = float(valuePairDomObj.getElementsByTagName('second')[0].childNodes[0].data)

    return array


def upgradePrescribedVelocitiesBC(path, filename):
    bc = CRIMSONSolver.BoundaryConditions.PrescribedVelocities.PrescribedVelocities()
    dom = parse(os.path.join(path, filename))
    extractFaceIdentifiers(dom, bc)
    extractProperties(dom, bc)

    bc.originalWaveform = extractArray(dom.getElementsByTagName('_waveform')[0])
    bc.smoothedWaveform = extractArray(dom.getElementsByTagName('_smoothedWaveform')[0])
    bc.numberOfSamples = bc.smoothedWaveform.shape[0]
    bc.firstFilteredCoef = -int(dom.getElementsByTagName('_smoothingValue')[0].childNodes[0].data)
    return bc


def writeUpgradedObject(obj, path, filename, newExt, indexXML):
    newfilename = os.path.splitext(filename)[0] + newExt
    CRIMSONCore.IO.saveToFile(obj, os.path.join(path, newfilename))
    os.remove(os.path.join(path, filename))
    node = indexXML.find(".//*[@file='{0}']".format(filename))
    node.set('file', newfilename)


def createMeshFaceInfo(tempDir, filename, allFiles, indexXML):
    baseName = os.path.splitext(os.path.splitext(filename)[0])[0]
    baseName = str(baseName[44:]) + '_Meshed'

    try:
        baseName = (x for x in allFiles if baseName in x and x.endswith('.sms')).next()
        newFileName = baseName + '.faceinfo'
    except:
        return

    with open(os.path.join(tempDir, filename), 'rt') as inFile, open(os.path.join(tempDir, newFileName),
                                                                     'wt') as outFile:
        for l in inFile:
            if 'inflowFaceId' not in l and 'outflowFaceId' not in l:
                outFile.writelines(l.replace('data._', 'faceIdMap._'))

        meshNode = indexXML.find(".//*data[@type='MeshSimMeshData'][@file='{0}']".format(filename))
        if meshNode:
            meshNode.append(ET.Element('additionalFile', {'file': baseName + '.faceinfo'}))


def upgradeScene(filename):
    tempdir = tempfile.mkdtemp()
    try:
        print("Opening " + filename + "...")
        zipfile.ZipFile(filename, mode='r').extractall(tempdir)

        indexFileName = os.path.join(tempdir, 'index.xml')
        with open(indexFileName, 'rt') as f:
            indexXMLContents = ''
            for i, l in enumerate(f):
                indexXMLContents += l
                if i == 0:
                    indexXMLContents += '<v>'

            indexXMLContents += '</v>'

        indexXML = ET.fromstring(indexXMLContents)

        derivedNodes = {}
        for node in indexXML:
            if node.find(".//*[@type='CRIMSONSolverSolverSetupData']") is not None or \
                    node.find(".//*[@type='CRIMSONSolverSolverStudyData']") is not None or \
                    node.find(".//*[@type='CRIMSONSolverBoundaryConditionSet']") is not None:
                derivedNodes.setdefault(node[0].get('UID'), []).append(node)

        newSourceNodeUIDs = {}
        for i, sourceNodeUID in enumerate(derivedNodes.keys()):
            newUID = "OBJECT_{0}".format(i)
            newElement = ET.Element('node', {"UID": newUID})
            newElement.append(ET.Element('properties', {'file': newUID}))
            newElement.append(ET.Element('source', {'UID': sourceNodeUID}))
            with open(os.path.join(tempdir, newUID), 'wt') as f:
                f.write('''<?xml version="1.0" ?>
<Version Writer="T:\MITK\Modules\SceneSerializationBase\src\mitkPropertyListSerializer.cpp" Revision="$Revision: 17055 $" FileVersion="1" />
<property key="SolverSetup.SolverType" type="StringProperty">
    <string value="CRIMSON Solver" />
</property>
<property key="name" type="StringProperty">
    <string value="CRIMSON Solver" />
</property>
<property key="show empty data" type="BoolProperty">
    <bool value="true" />
</property>
<property key="layer" type="IntProperty">
    <int value="4096" />
</property>
''')
            indexXML.append(newElement)
            newSourceNodeUIDs[sourceNodeUID] = newUID

        for sourceNodeUID, derivedNodeList in derivedNodes.iteritems():
            for node in derivedNodeList:
                node.find("source").set('UID', newSourceNodeUIDs[sourceNodeUID])

        allFiles = os.listdir(tempdir)
        for savedfilename in allFiles:

            result = None
            if os.path.splitext(savedfilename)[1] == '.csbcs':
                result = upgradeBoundaryConditionSet(tempdir, savedfilename)
                newExt = '.pybcs'
            elif os.path.splitext(savedfilename)[1] == '.csnsbc':
                result = upgradeNoSlipBC(tempdir, savedfilename)
                newExt = '.pybc'
            elif os.path.splitext(savedfilename)[1] == '.cspic':
                result = upgradeInitialPressureBC(tempdir, savedfilename)
                newExt = '.pybc'
            elif os.path.splitext(savedfilename)[1] == '.csrcrbc':
                result = upgradeRCRBC(tempdir, savedfilename)
                newExt = '.pybc'
            elif os.path.splitext(savedfilename)[1] == '.cspvbc':
                result = upgradePrescribedVelocitiesBC(tempdir, savedfilename)
                newExt = '.pybc'
            elif os.path.splitext(savedfilename)[1] == '.cszpbc':
                result = upgradeZeroPressureBC(tempdir, savedfilename)
                newExt = '.pybc'

            elif os.path.splitext(savedfilename)[1] == '.csssd':
                result = upgradeSolverSetup(tempdir, savedfilename)
                newExt = '.pyssd'

            elif os.path.splitext(savedfilename)[1] == '.csstudy':
                result = upgradeSolverStudy(tempdir, savedfilename)
                newExt = '.pystudy'

            elif os.path.splitext(savedfilename)[1] == '.faceinfo':
                createMeshFaceInfo(tempdir, savedfilename, allFiles, indexXML)

            if result is not None:
                writeUpgradedObject(result, tempdir, savedfilename, newExt, indexXML)

        with open(indexFileName, 'wt') as f:
            f.write(ET.tostring(indexXML).replace('<v>', '').replace('</v>', ''))

        newfilename = os.path.splitext(filename)[0] + '_new' + os.path.splitext(filename)[1]
        print("Saving to " + newfilename + "...")

        newzipfile = zipfile.ZipFile(newfilename, mode='w', compression=zipfile.ZIP_STORED, allowZip64=True)
        for savedfilename in os.listdir(tempdir):
            newzipfile.write(os.path.join(tempdir, savedfilename), savedfilename)

        print("Done.")
    finally:
        shutil.rmtree(tempdir)


try:
    from PythonQt import QtGui

    def upgradeScenes():
        filenames = PythonQt.QtGui.QFileDialog.getOpenFileNames(None, "Select scenes to upgrade", "", "*.mitk")
        for filename in filenames:
            upgradeScene(filename)
except:
    pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: upgradeScene filefame [filename...]")
        sys.exit(1)


    for filename in sys.argv[1:]:
        try:
            upgradeScene(filename)
        except Exception as e:
            print("Upgrading {0} failed: {1}".format(filename, str(e)))
            raise
