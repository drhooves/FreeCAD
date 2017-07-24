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


__title__ = "FemElmerTasks"
__author__ = "Markus Hovorka, Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"


## \addtogroup FEM
#  @{


import subprocess
import os.path

import FreeCAD as App
import FemElmerWriter
import FemSolve
import FemSettings
import FemMisc


class Check(FemSolve.Check):

    def run(self):
        if (self.checkMesh()):
            self.checkMeshType()
        self.checkMaterial()
        self.checkSupported(FemElmerWriter.SUPPORTED)

    def checkMeshType(self):
        mesh = FemMisc.getSingleMember(self.analysis, "Fem::FemMeshObject")
        if not FemMisc.isOfType(mesh, "Fem::FemMeshObject", "FemMeshGmsh"):
            self.report.appendError(
                "Unsupported type of mesh. "
                "Mesh must be created with gmsh.")
            self.fail()
            return False
        return True


class Prepare(FemSolve.Prepare):

    def run(self):
        writer = FemElmerWriter.Writer(
                self.analysis, self.solver, self.directory)
        writer.writeInputFiles(self.report)


class Solve(FemSolve.Solve):

    def run(self):
        binary = FemSettings.getBinary("ElmerSolver")
        self._process = subprocess.Popen(
            [binary], cwd=self.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.signalAbort.add(self._process.terminate)
        output = self._observeSolver(self._process)
        self._process.communicate()
        self.signalAbort.remove(self._process.terminate)
        if not self.aborted:
            self._updateOutput(output)

    def _observeSolver(self, process):
        output = ""
        line = process.stdout.readline()
        self.pushStatus(line)
        output += line
        line = process.stdout.readline()
        while line:
            line = "\n%s" % line.rstrip()
            self.pushStatus(line)
            output += line
            line = process.stdout.readline()
        return output

    def _updateOutput(self, output):
        if self.solver.ElmerOutput is None:
            self._createOutput()
        self.solver.ElmerOutput.Text = output

    def _createOutput(self):
        self.solver.ElmerOutput = self.analysis.Document.addObject(
                "App::TextDocument", self.solver.Name + "Output")
        self.solver.ElmerOutput.Label = self.solver.Label + "Output"
        self.solver.ElmerOutput.ReadOnly = True
        self.analysis.Member += [self.solver.ElmerOutput]


class Results(FemSolve.Results):

    def run(self):
        if self.solver.ElmerResult is None:
            self._createResults()
        postPath = os.path.join(self.directory, "case0001.vtu")
        self.solver.ElmerResult.read(postPath)
        self.solver.ElmerResult.getLastPostObject().recompute()

    def _createResults(self):
        self.solver.ElmerResult = self.analysis.Document.addObject(
                "Fem::FemPostPipeline", self.solver.Name + "Result")
        self.solver.ElmerResult.Label = self.solver.Label + "Result"
        self.analysis.Member += [self.solver.ElmerResult]
