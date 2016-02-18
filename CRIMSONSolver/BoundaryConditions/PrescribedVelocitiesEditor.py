try:
    import os
    import math

    import PythonQt

    PythonQt.QtCore.QObject = PythonQt.private.QObject

    from PythonQt import QtGui, QtCore, QtUiTools
    from PythonQt.CRIMSON import Utils

    import numpy
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
    from matplotlib.figure import Figure

    from matplotlib import rc
except:
    class PrescribedVelocitiesEditor(object):
        pass

else:
    rc('font', **{'family': 'serif', 'serif': ['Palatino']})

    class PrescribedVelocitiesFigure(FigureCanvas):
        """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

        def __init__(self, parent=None, width=5, height=4, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111)
            self._setupAxes()

            #
            FigureCanvas.__init__(self, fig)
            self.setParent(parent)

            FigureCanvas.setSizePolicy(self,
                                       QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
            FigureCanvas.updateGeometry(self)

            self.originalWaveform = numpy.array([])
            self.originalWaveformPlot = None
            self.smoothedWaveform = numpy.array([])
            self.smoothedWaveformPlot = None

            self.mpl_connect('motion_notify_event', self._showPointTooltip)

        def setOriginalWaveform(self, waveform):
            self.originalWaveform = waveform
            self.smoothedWaveform = waveform

            self.axes.clear()
            self._setupAxes()

            if len(waveform) > 0:
                self._createOriginalWaveformPlot(waveform)
                self._createSmoothedWaveformPlot(waveform)

            self.draw()

        def setSmoothedWaveform(self, waveform):
            self.smoothedWaveform = waveform
            if self.smoothedWaveformPlot is not None:
                self.axes.lines.remove(self.smoothedWaveformPlot)
            self._createSmoothedWaveformPlot(waveform)
            self.draw()

        # Private stuff
        def _setupAxes(self):
            self.axes.grid(b=True, linestyle='-', color='0.9')
            self.axes.set_xlabel('Time $(s)$')
            self.axes.set_ylabel('Flow rate')

        def _createOriginalWaveformPlot(self, waveform):
            self.originalWaveformPlot, = self.axes.plot(waveform[:, 0], waveform[:, 1], 'lightskyblue', zorder=3)

        def _createSmoothedWaveformPlot(self, waveform):
            self.smoothedWaveformPlot, = self.axes.plot(waveform[:, 0], waveform[:, 1], 'midnightblue', zorder=4)

        def resizeEvent(self, evt):
            FigureCanvas.resizeEvent(self, evt)
            self.figure.tight_layout()

        def _showPointTooltip(self, event):
            if event.inaxes is not self.axes:  # mouse is inside our axes
                return

            if len(self.smoothedWaveform) == 0:
                QtGui.QToolTip.hideText()
                return

            dataToDisplayTransform = self.axes.transData

            closestPoint = None
            closestDist = 0
            for dataCoords in self.smoothedWaveform:
                displayCoords = dataToDisplayTransform.transform(dataCoords)

                dist = math.sqrt((event.x - displayCoords[0]) ** 2 + (event.y - displayCoords[1]) ** 2)
                if closestPoint is None or dist < closestDist:
                    closestPoint = dataCoords
                    closestDist = dist

            maxDistInPixels = 5
            if closestDist < maxDistInPixels:
                QtGui.QToolTip.showText(QtGui.QCursor.pos(), '({0[0]}, {0[1]})'.format(closestPoint))
            else:
                QtGui.QToolTip.hideText()


    class PrescribedVelocitiesEditor(object):
        def __init__(self, prescribedVelocitiesBC):
            self.prescribedVelocitiesBC = prescribedVelocitiesBC

            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "PrescribedVelocitiesBoundaryConditionEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))

            self.figure = PrescribedVelocitiesFigure()
            plotLayout = self.ui.findChild(PythonQt.QtCore.QObject, "plotLayout")
            plotFrame = self.ui.findChild(PythonQt.QtCore.QObject, "plotFrame")
            self.navigationToolbar = NavigationToolbar(self.figure, plotFrame)
            plotLayout.addWidget(self.navigationToolbar)
            plotLayout.addWidget(self.figure)

            loadWaveformButton = self.ui.findChild(PythonQt.QtCore.QObject, "loadWaveformButton")
            loadWaveformButton.connect('clicked(bool)', self.loadWaveform)

            self.numberOfSamplesSpinBox = self.ui.findChild(PythonQt.QtCore.QObject, "numberOfSamplesSpinBox")
            self.numberOfSamplesSpinBox.connect('valueChanged(int)', self._computeSmoothedWaveform)

            self.smoothnessSlider = self.ui.findChild(PythonQt.QtCore.QObject, "smoothnessSlider")
            self.smoothnessSlider.connect('valueChanged(int)', self._computeSmoothedWaveform)

            if self.prescribedVelocitiesBC.firstFilteredCoef < 0:
                # Support for converted old mitk scenes
                self.prescribedVelocitiesBC.firstFilteredCoef = int(
                    self._findLastNonZeroCoef()[0] * (self.prescribedVelocitiesBC.firstFilteredCoef / -100.0))

            self._updatePlot(self.prescribedVelocitiesBC.numberOfSamples, self.prescribedVelocitiesBC.firstFilteredCoef)

        def getEditorWidget(self):
            return self.ui

        def loadWaveform(self):
            fileName = PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load waveform", "",
                                                                  "Waveform file (*.flow);; All files (*.*)")
            if not fileName:
                return

            self.loadWaveformFromFile(fileName)

        def loadWaveformFromFile(self, fileName):
            loadedWaveform = numpy.loadtxt(fileName)
            if loadedWaveform is None:
                Utils.logError("Error: Failed to load waveform from file " + fileName)

            self.prescribedVelocitiesBC.originalWaveform = loadedWaveform
            self._updatePlot(loadedWaveform.shape[0], 0)

        # Private stuff
        def _updatePlot(self, nSamples, firstFilteredCoef):
            self._resetPlot()
            self.figure.setOriginalWaveform(self.prescribedVelocitiesBC.originalWaveform)
            self.numberOfSamplesSpinBox.value = nSamples
            self.smoothnessSlider.maximum = self._findLastNonZeroCoef()[0]
            self.smoothnessSlider.value = firstFilteredCoef

        def _computeSmoothedWaveform(self):
            self.prescribedVelocitiesBC.firstFilteredCoef = self.smoothnessSlider.value
            self.prescribedVelocitiesBC.numberOfSamples = self.numberOfSamplesSpinBox.value

            originalWaveform = self.prescribedVelocitiesBC.originalWaveform
            firstFilteredCoef = self.prescribedVelocitiesBC.firstFilteredCoef
            nSamples = self.prescribedVelocitiesBC.numberOfSamples

            if len(originalWaveform) == 0:
                return

            lastNonZeroCoef, fft = self._findLastNonZeroCoef()
            fft[lastNonZeroCoef - firstFilteredCoef + 1:] = 0

            smoothedWaveform = numpy.empty((nSamples, 2))
            smoothedWaveform[:, 0] = numpy.linspace(originalWaveform[0, 0], originalWaveform[-1, 0], nSamples)
            smoothedWaveform[:-1, 1] = numpy.fft.irfft(fft, nSamples - 1) * (nSamples - 1) / float(
                originalWaveform.shape[0] - 1)
            smoothedWaveform[-1, 1] = smoothedWaveform[0, 1]
            self.prescribedVelocitiesBC.smoothedWaveform = smoothedWaveform

            self.figure.setSmoothedWaveform(self.prescribedVelocitiesBC.smoothedWaveform)

        def _findLastNonZeroCoef(self):
            if len(self.prescribedVelocitiesBC.originalWaveform) == 0:
                return 1, numpy.zeros((1))

            fft = numpy.fft.rfft(self.prescribedVelocitiesBC.originalWaveform[:-1, 1])
            maxAbsoluteValue = numpy.absolute(fft).max()
            lastNonZeroCoef = 0
            for i in xrange(len(fft) - 1, 0, -1):
                if numpy.absolute(fft[i]) > 1e-4 * maxAbsoluteValue:
                    lastNonZeroCoef = i
                    break
            return lastNonZeroCoef, fft

        def _resetPlot(self):
            self.navigationToolbar._views.clear()
            self.navigationToolbar._positions.clear()
