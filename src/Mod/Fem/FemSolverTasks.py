# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Markus Hovorka <m.hovorka@live.de>          *
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


import FemTask
import FemSignal
import FemMisc


class Base(FemTask.Thread):

    def __init__(self, solver, directory):
        super(Base, self).__init__()
        self.solver = solver
        self.directory = directory

    @property
    def analysis(self):
        return FemMisc.findAnalysisOfMember(self.solver)


class Check(Base):

    def checkMesh(self):
        meshes = FemMisc.getMember(
            self.analysis, "Fem::FemMeshObject")
        if len(meshes) == 0:
            self.report.appendError("Missing a mesh object.")
            self.fail()
            return False
        elif len(meshes) > 1:
            self.report.appendError(
                "Too many meshes. "
                "More than one mesh is not supported.")
            self.fail()
            return False
        return True

    def checkMaterial(self):
        matObjs = FemMisc.getMember(
            self.analysis, "App::MaterialObjectPython")
        if len(matObjs) == 0:
            self.report.appendError(
                "No material object found. "
                "At least one material is required.")
            self.fail()
            return False
        return True

    def checkSupported(self, allSupported):
        for m in self.analysis.Member:
            if FemMisc.isOfType(m, "Fem::Constraint"):
                supported = False
                for sc in allSupported:
                    if FemMisc.isOfType(m, *sc):
                        supported = True
                if not supported:
                    self.report.appendWarning(
                        "Ignored unsupported constraint: %s" % m.Label)
        return True


class Solve(Base):

    def __init__(self, solver, directory):
        super(Solve, self).__init__(solver, directory)
        self.signalOutput = set()
        self.signalLine = set()
        self._output = []

    def start(self):
        super(Solve, self).start()
        self._output = []

    def appendOutput(self, line):
        self._output.append(line)
        FemSignal.notify(self.signalLine, line)

    @property
    def output(self):
        return "".join(self._output)

    @output.setter
    def output(self, value):
        self._output = [value]
        FemSignal.notify(self.signalOutput)


class Prepare(Base):
    pass


class Results(Base):
    pass
