# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

__title__ = "FemToolsElmer"
__author__ = "Bernd Hahnebach, Markus Hovorka"
__url__ = "http://www.freecadweb.org"

## \addtogroup FEM
#  @{

import os
import sys
import subprocess
import shutil
from PySide import QtCore
from PySide import QtGui

import FreeCAD as App
import FemTools
import FemInputWriterElmer


class FemToolsElmer(FemTools.FemTools):

    finished = QtCore.Signal(int)
    SIF_NAME = "case.sif"

    def __init__(self, analysis, solver):
        if analysis is None: raise Exception("Analysis must not be None.")
        if solver is None: raise Exception("Solver must not be None.")
        QtCore.QRunnable.__init__(self)
        QtCore.QObject.__init__(self)
        self.analysis = analysis
        self.solver = solver
        self.update_objects()

    def start_elmer(self, binary, working_dir):
        return subprocess.Popen([binary], cwd=working_dir).wait()

    def run(self):
        binary = self.find_elmer_binary()
        if binary is None:
            print("Error: Couldn't find elmer binary.")
            return
        if self.is_analysis_valid():
            working_dir = self.get_working_dir()
            is_temp = False
            if not working_dir:
                working_dir = tempfile.mkdtemp()
                is_temp = True
            self.prepare_case_dir(working_dir)
            progress_bar = App.Base.ProgressIndicator()
            progress_bar.start("Running ElmerSolver...", 0)
            ret_code = self.start_elmer(binary, working_dir)
            self.finished.emit(ret_code)
            if is_temp:
                shutil.rmtree(working_dir)
            progress_bar.stop()

    def find_elmer_binary(self):
        return "ElmerSolver"

    def prepare_case_dir(self, working_dir):
        writer = FemInputWriterElmer.Writer(
                self.analysis, self.solver, self.mesh, self.materials_linear,
                self.materials_nonlinear, self.fixed_constraints,
                self.displacement_constraints, self.contact_constraints,
                self.planerotation_constraints, self.transform_constraints,
                self.selfweight_constraints, self.force_constraints,
                self.pressure_constraints, self.temperature_constraints,
                self.heatflux_constraints, self.initialtemperature_constraints,
                self.beam_sections, self.shell_thicknesses, self.fluid_sections)
        writer.write_all(self.SIF_NAME, working_dir)

    def is_analysis_valid(self):
        if self.mesh is None:
            print "Mesh object missing."
            return False
        return True

    def get_working_dir(self):
        fem_prefs = App.ParamGet(
                "User parameter:BaseApp/Preferences/Mod/Fem/General")
        wd_setting = fem_prefs.GetString("WorkingDir")
        if wd_setting:
            return wd_setting
        return tempfile.mkdtemp()

    def load_results(self):
        self.results_present = False
        print('Result loading for Elmer not implemented yet!')
