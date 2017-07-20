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

import os
import os.path

import FreeCAD as App
import FemSolverTasks
import FemSettings
import FemTempfile
import FemMisc
import FemSignal
import FemTask
import FemReport


CHECK = 0
PREPARE = 1
SOLVE = 2
RESULTS = 3
DONE = 4


_machines = {}
_solverDirs = {}


def getMachine(solver, path=None):
    _DocObserver.attach()
    name = FemMisc.getUniqueName(solver)
    task = FemTask.running.get(name)
    if task is not None and task.running:
        return task
    if path is None:
        path = getDefaultDir(solver)
    if path not in _machines:
        _machines[path] = solver.Proxy.buildMachine(solver, path)
    return _machines[path]


def getDefaultDir(solver):
    setting = FemSettings.getDirSetting()
    if setting == FemSettings.BESIDE:
        if solver.Document.FileName != "":
            return _getBesideDir(solver)
    if setting == FemSettings.TEMPORARY:
        return _getSolverDir(solver)
    if setting == FemSettings.CUSTOM:
        path = FemSettings.getCustomDir()
        return _getCustomDir(path, solver)


def _getSolverDir(solver):
    global _solverDirs
    name = FemMisc.getUniqueName(solver)
    if name not in _solverDirs:
        _solverDirs[name] = FemTempfile.createDir(solver)
    return _solverDirs[name]


def _getBesideDir(solver):
    fcstdPath = solver.Document.FileName
    if fcstdPath == "":
        raise ValueError("must save")
    basePath = os.path.splitext(fcstdPath)[0]
    specificPath = os.path.join(basePath, solver.Label)
    if not os.path.isdir(specificPath):
        os.makedirs(specificPath)
    return specificPath


def _getCustomDir(path, solver):
    if not os.path.isdir(path):
        raise ValueError("Invalid path")
    specificPath = os.path.join(
            path, solver.Document.Name, solver.Label)
    if not os.path.isdir(specificPath):
        os.makedirs(specificPath)
    return specificPath


class Machine(FemSolverTasks.Base):

    def __init__(self, solver, directory, target=SOLVE):
        super(Machine, self).__init__(solver, directory)
        self.name = FemMisc.getUniqueName(self.solver)
        self.signalState = set()
        self.check = None
        self.prepare = None
        self.solve = None
        self.results = None
        self.target = target
        self._state = CHECK
        self._pendingState = CHECK
        self._isReset = False

    @property
    def state(self):
        return self._state

    def run(self):
        self._isReset = False
        self._pendingState = self.state
        while (not self.aborted and not self.failed
                and self._pendingState <= self.target):
            task = self._getTask(self._pendingState)
            self._runTask(task)
            self.report.extend(task.report)
            if task.failed:
                self.fail()
            elif task.aborted:
                self.abort()
            else:
                self._pendingState += 1
        self._applyPending()

    def reset(self, newState=CHECK):
        if newState < self._pendingState:
            self._isReset = True
            self._state = newState
            FemSignal.notify(self.signalState)

    def _applyPending(self):
        if not self._isReset:
            self._state = self._pendingState
            FemSignal.notify(self.signalState)
        self._isReset = False

    def _runTask(self, task):
        def killer():
            task.abort()
        self.signalAbort.add(killer)
        task.start()
        task.join()
        self.signalAbort.remove(killer)

    def _getTask(self, state):
        if state == CHECK:
            return self.check
        elif state == PREPARE:
            return self.prepare
        elif state == SOLVE:
            return self.solve
        elif state == RESULTS:
            return self.results
        return None


class _DocObserver(object):

    _instance = None
    _WHITELIST = [
        "Fem::Constraint",
        "App::MaterialObject",
    ]
    _BLACKLIST_PROPS = [
        "Label",
    ]

    @classmethod
    def attach(cls):
        if cls._instance is None:
            cls._instance = cls()
            App.addDocumentObserver(cls._instance)

    def slotNewObject(self, obj):
        self._docChanged(obj)

    def slotDeleteObject(self, obj):
        self._docChanged(obj)

    def slotChangedObject(self, obj, prop):
        if prop not in self._BLACKLIST_PROPS:
            analysis = FemMisc.findAnalysisOfMember(obj)
            for m in _machines.itervalues():
                if analysis == m.analysis and obj == m.solver:
                    print "Reset because of: %s.%s" % (obj.Label, prop)
                    m.reset()
        self._docChanged(obj, prop)

    def _docChanged(self, obj, prop=None):
        if self._partOfModel(obj, prop):
            analysis = FemMisc.findAnalysisOfMember(obj)
            for m in _machines.itervalues():
                if analysis == m.analysis:
                    print "Reset because of: %s" % obj.Label
                    m.reset()

    def _partOfModel(self, obj, prop):
        if prop in self._BLACKLIST_PROPS:
            return False
        for t in self._WHITELIST:
            if obj.isDerivedFrom(t):
                return True
        return False
