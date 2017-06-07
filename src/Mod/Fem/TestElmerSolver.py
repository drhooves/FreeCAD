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

import unittest
import tempfile

import FreeCAD as App
import ObjectsFem


if App.GuiUp:
    import FreeCADGui as Gui


def GuiSuite():
    classes = []
    return _loadFromClasses(classes)


def AppSuite():
    classes = [TestSolverObject]
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
