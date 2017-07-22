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
import FemSolverTasks
import FemSettings
import FemMisc


class Check(FemSolverTasks.Check):

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


class Prepare(FemSolverTasks.Prepare):

    def run(self):
        writer = FemElmerWriter.Writer(
                self.analysis, self.solver, self.directory)
        writer.writeInputFiles(self.report)


class Solve(FemSolverTasks.Solve):

    def run(self):
        binary = FemSettings.getBinary("ElmerSolver")
        self._process = subprocess.Popen(
            [binary], cwd=self.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.signalAbort.add(self._process.terminate)
        line = self._process.stdout.readline()
        self.appendOutput(line)
        line = self._process.stdout.readline()
        while line:
            self.appendOutput("\n%s" % line.rstrip())
            line = self._process.stdout.readline()
        self._updateOutput()

    def _updateOutput(self):
        if self.solver.ElmerOutput is None:
            self.solver.ElmerOutput = self.analysis.Document.addObject(
                    "App::TextDocument", self.solver.Name + "Output")
            self.solver.ElmerOutput.Label = self.solver.Label + "Output"
            self.solver.ElmerOutput.ReadOnly = True
            self.analysis.Member += [self.solver.ElmerOutput]
        self.solver.ElmerOutput.Text = self.output


class Results(FemSolverTasks.Results):

    def run(self):
        if self.solver.ElmerResult is None:
            self.solver.ElmerResult = self.analysis.Document.addObject(
                    "Fem::FemPostPipeline", self.solver.Name + "Result")
            self.solver.ElmerResult.Label = self.solver.Label + "Result"
            self.analysis.Member += [self.solver.ElmerResult]
        postPath = os.path.join(self.directory, "case0001.vtu")
        self.solver.ElmerResult.read(postPath)
        self.solver.ElmerResult.getLastPostObject().recompute()
