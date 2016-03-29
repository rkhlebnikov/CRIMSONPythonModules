import sys

try:
    import PythonQt
except:
    import PythonQtMock as PythonQt
    sys.modules["PythonQt"] = PythonQt

import os
import shutil
import zipfile
import tempfile

def upgradeScene2(filename):
    print("Opening " + filename + "...")
    zin = zipfile.ZipFile(filename, 'r')

    newfilename = os.path.splitext(filename)[0] + '_new' + os.path.splitext(filename)[1]
    print("Saving to " + newfilename + "...")

    zout = zipfile.ZipFile(newfilename, mode='w', compression=zipfile.ZIP_STORED, allowZip64=True)
    for zipInfo in zin.infolist():
        buffer = zin.read(zipInfo)
        if zipInfo.filename.endswith('pyssd'):
            buffer = buffer.replace('SolverSetups', 'SolverParameters').replace('SolverSetup3D', 'SolverParameters3D')
                
        zout.writestr(zipInfo, buffer)

    zout.close()
    zin.close()

    print("Done.")

try:
    from PythonQt import QtGui

    def upgradeScenes2():
        filenames = PythonQt.QtGui.QFileDialog.getOpenFileNames(None, "Select scenes to upgrade", "", "*.mitk")
        for filename in filenames:
            upgradeScene2(filename)
except:
    pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: upgradeScene2 filefame [filename...]")
        sys.exit(1)


    for filename in sys.argv[1:]:
        try:
            upgradeScene2(filename)
        except Exception as e:
            print("Upgrading {0} failed: {1}".format(filename, str(e)))
            raise
