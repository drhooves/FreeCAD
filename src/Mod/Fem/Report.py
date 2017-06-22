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

__title__ = "FemToolsElmer"
__author__ = "Markus Hovorka"
__url__ = "http://www.freecadweb.org"


from PySide import QtCore
from PySide import QtGui

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Console


ERROR_COLOR = "red"
WARNING_COLOR = "yellow"
INFO_COLOR = "blue"


MSG_LOOKUP = {
    "wd_not_existent": "Working directory {} doesn't exist.",
    "wd_not_directory": "Working directory {} is not a directory.",
    "cd_not_directory": "Case directory {} is not a directory.",
    "cd_not_created": "Failed to creade case directory {}: {}",
    "elmersolver_not_found": "ElmerSolver binary not found (required).",
    "elmergrid_not_found": "ElmerGrid binary not found (required).",
    "elmer_failed": "ElmerSolver failed with error code: ",

    "create_inp_failed": "Failed to create input files: {}",
    "exec_solver_failed": "Solver execution failed with exit code: {}",
    "mesh_missing": "Mesh object missing.",
    "no_freetext": "Analysis without FreeText not jet supported!",
    "freetext_empty": "FreeText must not be empty.",
}


def display(report):
    if App.GuiUp:
        displayGui(report)
    else:
        displayLog(report)


def displayGui(report):
    dialog = ReportDialog(report, None)
    dialog.exec_()


def displayLog(report):
    for i in report.infos:
        Console.PrintLog("%s\n" % i)
    for w in report.warnings:
        Console.PrintWarning("%s\n" % w)
    for e in report.errors:
        Console.PrintError("%s\n" % e)


class Data(object):

    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []

    def extend(report):
        self.infos.extend(report.infos)
        self.warnings.extend(report.warnings)
        self.errors.extend(report.errors)

    def isValid(self):
        return len(self.errors) == 0

    def isEmpty(self):
        return not (self.infos or self.warnings or self.errors)

    def appendInfo(self, info, *args):
        self._append(self.infos, info, args)

    def appendWarning(self, warning, *args):
        self._append(self.warnings, warning, args)

    def appendError(self, error, *args):
        self._append(self.errors, error, args)

    def _append(self, msgList, msgKey, args):
        if msgKey not in MSG_LOOKUP:
            raise ValueError("Unknown error: %s" % msgKey)
        textFormatStr = MSG_LOOKUP[msgKey]
        msgList.append(textFormatStr.format(*args))


class ReportDialog(QtGui.QDialog):

    def __init__(self, report, parent):
        super(ReportDialog, self).__init__(parent)
        msgLbl = QtGui.QLabel(self._getText(report))
        okBtt = QtGui.QPushButton("Ok")
        okBtt.clicked.connect(self.close)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(msgLbl)
        layout.addWidget(okBtt)
        self.setGeometry(250, 250, 0, 50)
        self.setWindowTitle("FreeCAD Report")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setLayout(layout)

    def _getText(self, report):
        text = ""
        for i in report.infos:
            text += self._getColoredLine(i, INFO_COLOR) + "\n"
        for w in report.warnings:
            text += self._getColoredLine(w, WARNING_COLOR) + "\n"
        for e in report.errors:
            text += self._getColoredLine(e, ERROR_COLOR) + "\n"
        return text

    def _getColoredLine(self, text, color):
        return '<font color="%s">%s</font>' % (color, text)
