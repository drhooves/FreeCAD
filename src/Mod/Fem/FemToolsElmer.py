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
import os.path
import sys
import subprocess
import shutil
from PySide import QtCore
from PySide import QtGui

import FreeCAD as App
from FreeCAD import Console
import FemTools
import FemInputWriterElmer


err_lookup = {
    "wd_non_existent" : "Working directory {} doesn't exist.",
    "wd_not_dir" : "Working directory {} is not a directory.",
    "wd_name_conflict" : "Working directory {} invalid",
    "cd_create_error" : "Error creating case directory: {}",
    "create_inp_failed" : "Failed to create input files: {}",
    "exec_solver_failed" : "Solver execution failed with exit code: {}",
    "mesh_missing" : "Mesh object missing.",
    "no_freetext" : "Analysis without FreeText not jet supported!",
    "freetext_empty" : "FreeText must not be empty.",
}


def runSolver(analysis, solver):
    fea = FemToolsElmer(analysis, solver)
    fea.finished.connect(_solverFinished)
    QtCore.QThreadPool.globalInstance().start(fea)


def _solverFinished(status):
    Console.PrintLog(status.meshLog)
    Console.PrintLog(status.solverLog)
    if not status.success:
        Console.PrintMessage("Solver execution failed.\n")
        status.printErrorList(err_lookup)


class _Status(object):

    def __init__(self):
        self._success = True
        self.meshLog = ""
        self.solverLog = ""
        self.errorList = []

    @property
    def success(self):
        return self._success

    def error(self, err, *args):
        self._success = False
        self.errorList.append((err, args))

    def printErrorList(self, lookup):
        for err_id, args in self.errorList:
            Console.PrintError(lookup[err_id].format(*args) + "\n")


class FemToolsElmer(FemTools.FemTools):

    finished = QtCore.Signal(object)
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
        status = _Status()
        binary = self._check_elmer_binary(status)
        working_dir = self._check_working_dir(status)
        self._check_analysis(status)

        delete_wd = False
        progress_bar = App.Base.ProgressIndicator()
        if status.success:
            progress_bar.start("Executing Simulation...", 0)
            if not working_dir:
                working_dir = tempfile.mkdtemp()
                delete_wd = True
            try: self.write_input_files(working_dir)
            except OSError as e:
                status.error("create_inp_failed", e.strerror)
            ret_code = self.start_elmer(binary, working_dir)
            if ret_code != 0:
                status.error("exec_solver_failed", e.strerror)

        progress_bar.stop()
        if delete_wd:
            shutil.rmtree(working_dir)
        self.finished.emit(status)

    def find_elmer_binary(self):
        return "ElmerSolver"

    def write_input_files(self, working_dir):
        writer = FemInputWriterElmer.Writer(
                self.analysis, self.solver, self.mesh, self.materials_linear,
                self.materials_nonlinear, self.fixed_constraints,
                self.displacement_constraints, self.contact_constraints,
                self.planerotation_constraints, self.transform_constraints,
                self.selfweight_constraints, self.force_constraints,
                self.pressure_constraints, self.temperature_constraints,
                self.heatflux_constraints, self.initialtemperature_constraints,
                self.beam_sections, self.shell_thicknesses, self.fluid_sections,
                self.elmer_free_text)
        writer.write_all(self.SIF_NAME, working_dir)

    def _check_analysis(self, status):
        if self.mesh is None:
            status.error("mesh_missing")
        if self.elmer_free_text is None:
            status.error("no_freetext")
        elif self.elmer_free_text.Text == "":
            status.error("freetext_empty")

    def _check_elmer_binary(self, status):
        binary = self.find_elmer_binary()
        if binary is None:
            status.failed("Couldn't find elmer binary.")
            return None
        return binary

    def _check_working_dir(self, status):
        working_dir = self.get_working_dir()
        if not os.path.exists(working_dir):
            status.error("wd_non_existent", working_dir)
            return None
        if not os.path.isdir(working_dir):
            status.error("wd_not_dir", working_dir)
            return None
        case_dir = os.path.join(working_dir, self.analysis.Label)
        if os.path.exists(case_dir) and not os.path.isdir(case_dir):
            status.error("wd_name_conflict", working_dir)
            return None
        if not os.path.exists(case_dir):
            try: os.mkdir(case_dir)
            except OSError as e:
                status.error("cd_create_error", e.strerror)
                return None
        return case_dir

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
