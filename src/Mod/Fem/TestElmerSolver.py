# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Markus Hovorka <m.hovorka@live.de>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "Elmer Solver Object"
__author__ = "Markus Hovorka"
__url__ = "http://www.freecadweb.org"


import os.path
import unittest
import tempfile
import shutil

import FreeCAD as App
from PySide import QtCore
import ObjectsFem
import FemToolsElmer
import FemGmshTools

if App.GuiUp:
    import FreeCADGui as Gui


def GuiSuite():
    classes = [TestCantileverGui]
    return _loadFromClasses(classes)


def AppSuite():
    classes = [TestSolverObject, TestCantileverApp]
    return _loadFromClasses(classes)


def All():
    allSuite = unittest.TestSuite()
    allSuite.addTest(AppSuite())
    if App.GuiUp:
        allSuite.addTest(GuiSuite())
    return allSuite


def runGui():
    suite = GuiSuite()
    unittest.TextTestRunner().run(suite)


def runApp():
    suite = AppSuite()
    unittest.TextTestRunner().run(suite)


def runAll():
    suite = All()
    unittest.TextTestRunner().run(suite)


def _loadFromClasses(classes):
    allSuite = unittest.TestSuite()
    for c in classes:
        oneSuite = unittest.defaultTestLoader.loadTestsFromTestCase(c)
        allSuite.addTest(oneSuite)
    return allSuite


class TestSolverObject(unittest.TestCase):

    def setUp(self):
        self.doc = App.newDocument()
        self.analysis_name = "test_analysis"
        self.solver_name = "test_solver"
        self.analysis = ObjectsFem.makeAnalysis(self.analysis_name)
        self.solver = ObjectsFem.makeSolverElmer(self.solver_name)
        self.analysis.Member += [self.solver]

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def testSimpleSaveRestore(self):
        with tempfile.TemporaryFile() as docFile:
            self.doc.saveAs(docFile.name)
            App.closeDocument(self.doc.Name)
            self.doc = App.open(docFile.name)

        self.analysis = self.doc.getObject(self.analysis_name)
        self.solver = self.doc.getObject(self.solver_name)
        self.assertIsNotNone(self.analysis)
        self.assertIsNotNone(self.solver)
        self.assertEqual(self.solver.SolverType, "FemSolverElmer")


class TestCantileverApp(unittest.TestCase):

    def setUp(self):
        self.doc = App.newDocument()
        self.mesh = _makeCantileverMesh()
        self.solver = ObjectsFem.makeSolverElmer()
        self.freetext = ObjectsFem.makeElmerFreeText()
        self.analysis = ObjectsFem.makeAnalysis()
        self.analysis.Member += [self.mesh, self.solver, self.freetext]
        self.freetext.Text = sif_file

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def testSpecificDir(self):
        try:
            caseDir = tempfile.mkdtemp()
            FemToolsElmer.runSolver(self.analysis, self.solver, caseDir)
            QtCore.QThreadPool.globalInstance().waitForDone()
            self._checkResult(caseDir)
        finally:
            shutil.rmtree(caseDir)

    def _checkResult(self, caseDir):
        self.assertTrue(os.path.isdir(caseDir))
        result1 = os.path.join(caseDir, "case0001.vtu")
        result2 = os.path.join(caseDir, "case0002.vtu")
        self.assertTrue(os.path.isfile(result1))
        self.assertTrue(os.path.isfile(result2))
        self.assertGreater(os.path.getsize(result1), 10e3)
        self.assertGreater(os.path.getsize(result2), 10e3)


class TestCantileverGui(unittest.TestCase):

    ELMER_NAME = "Elmer"
    ANALYSIS_NAME = "Analysis"

    def setUp(self):
        self.doc = App.newDocument()
        self.prevSetting = (App.ParamGet(
                "User parameter:BaseApp/Preferences/Mod/Fem/General")
                .GetString("WorkingDir"))
        try:
            Gui.activateWorkbench("FemWorkbench")
            Gui.runCommand("FEM_Analysis")
            Gui.runCommand("FEM_SolverElmer")
            Gui.runCommand("FEM_ElmerFreeText")
            self.analysis = App.ActiveDocument.getObject(self.ANALYSIS_NAME)
            self.solver = App.ActiveDocument.getObject(self.ELMER_NAME)
            self.analysis.Member += [_makeCantileverMesh()]
        except:
            self.tearDown()
            raise

    def tearDown(self):
        (App.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
                .SetString("WorkingDir", self.prevSetting))
        App.closeDocument(self.doc.Name)

    def testWithSetting(self):
        try:
            workingDir = tempfile.mkdtemp()
            (App.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
                    .SetString("WorkingDir", workingDir))
            self._runTest()
            caseDir = os.path.join(workingDir, self.analysis.Label)
            self._checkResult(caseDir)
        finally:
            shutil.rmtree(caseDir)

    def _runTest(self):
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.solver)
        Gui.runCommand("FEM_SolverRun")
        QtCore.QThreadPool.globalInstance().waitForDone()

    def _checkResult(self, caseDir):
        self.assertTrue(os.path.isdir(caseDir))
        result1 = os.path.join(caseDir, "case0001.vtu")
        result2 = os.path.join(caseDir, "case0002.vtu")
        self.assertTrue(
                os.path.isfile(result1),
                "{} is not a file.".format(result1))
        self.assertTrue(
                os.path.isfile(result2),
                "{} is not a file.".format(result2))
        self.assertGreater(os.path.getsize(result1), 10e3)
        self.assertGreater(os.path.getsize(result2), 10e3)


def _makeCantileverMesh():
    geo = App.ActiveDocument.addObject("Part::Box")
    geo.Length = 8000
    geo.Width = 1000
    geo.Height = 1000
    mesh = ObjectsFem.makeMeshGmsh()
    mesh.Part = geo

    fixedGroup = ObjectsFem.makeMeshGroup(mesh, name="Fixed")
    fixedGroup.References += [(geo, ('Face1',))]
    forceGroup = ObjectsFem.makeMeshGroup(mesh, name="Force")
    forceGroup.References += [(geo, ('Face2',))]
    bodyGroup = ObjectsFem.makeMeshGroup(mesh, name="Body")
    bodyGroup.References += [(geo, ('Solid1',))]

    tools = FemGmshTools.FemGmshTools(mesh)
    tools.create_mesh()

    return mesh


sif_file = """
Header
  CHECK KEYWORDS Warn
  Mesh DB "." "."
  Include Path ""
  Results Directory ""
End

Simulation
  Max Output Level = 5
  Coordinate System = Cartesian
  Coordinate Mapping(3) = 1 2 3
  Simulation Type = Steady state
  Steady State Max Iterations = 1
  Output Intervals = 1
  Timestepping Method = BDF
  BDF Order = 1
  Solver Input File = case.sif
  Post File = case.vtu
  Coordinate scaling = 0.001
  Use Mesh Names = Logical True
End

Constants
  Gravity(4) = 0 -1 0 9.82
  Stefan Boltzmann = 5.67e-08
  Permittivity of Vacuum = 8.8542e-12
  Boltzmann Constant = 1.3807e-23
  Unit Charge = 1.602e-19
End

Body 1
  Name = "Body"
  Equation = 1
  Material = 1
End

Solver 2
  Equation = Linear elasticity
Element=p:2
  Variable = -dofs 3 Displacement
  Procedure = "StressSolve" "StressSolver"
  Exec Solver = Always
  Stabilize = True
  Bubbles = False
  Lumped Mass Matrix = False
  Optimize Bandwidth = True
  Steady State Convergence Tolerance = 1.0e-5
  Nonlinear System Convergence Tolerance = 1.0e-7
  Nonlinear System Max Iterations = 20
  Nonlinear System Newton After Iterations = 3
  Nonlinear System Newton After Tolerance = 1.0e-3
  Nonlinear System Relaxation Factor = 1
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 500
  Linear System Convergence Tolerance = 1.0e-10
  BiCGstabl polynomial degree = 2
  Linear System Preconditioning = Diagonal
  Linear System ILUT Tolerance = 1.0e-3
  Linear System Abort Not Converged = False
  Linear System Residual Output = 1
  Linear System Precondition Recompute = 1
End

Solver 1
  Equation = Result Output
  Output Format = Vtu
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = case
  Exec Solver = After Simulation
End

Equation 1
  Name = "Equation 1"
  Active Solvers(2) = 2 1
End

Material 1
  Name = "Steel (alloy - generic)"
  Heat expansion Coefficient = 12.0e-6
  Electric Conductivity = 1.367e6
  Heat Conductivity = 37.2
  Sound speed = 5100.0
  Heat Capacity = 976.0
  Mesh Poisson ratio = 0.285
  Density = 7850.0
  Poisson ratio = 0.3
  Youngs modulus = 210.0e9
End

Boundary Condition 1
  Name = "Fixed"
  Displacement 3 = 0
  Displacement 2 = 0
  Displacement 1 = 0
End

Boundary Condition 2
  Name = "Force"
  Force 2 = 9000000
End
"""
