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
import tempfile
import shutil

import FreeCAD as App
import FemSolverTasks
import FemSettings
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
_dirTypes = {}


def getMachine(solver, path=None):
    _DocObserver.attach()
    m = _machines.get(solver)
    if m is None or not _isPathValid(m, path):
        m = _createMachine(solver, path)
    return m


def _isPathValid(m, path):
    t = _dirTypes[m.directory]
    setting = FemSettings.getDirSetting()
    if path is not None:
        return t == None and m.directory == path
    if setting == FemSettings.BESIDE:
        if t == FemSettings.BESIDE:
            base = os.path.split(m.directory.rstrip("/"))[0]
            return base == _getBesideBase(m.solver)
        return False
    if setting == FemSettings.TEMPORARY:
        return t == FemSettings.TEMPORARY
    if setting == FemSettings.CUSTOM:
        if t == FemSettings.CUSTOM:
            firstBase = os.path.split(m.directory.rstrip("/"))[0]
            customBase = os.path.split(firstBase)[0]
            return customBase == _getCustomBase(m.solver)
        return False


def _createMachine(solver, path):
    global _dirTypes
    setting = FemSettings.getDirSetting()
    if path is not None:
        _dirTypes[path] = None
    elif setting == FemSettings.BESIDE:
        path = _getBesideDir(solver)
        _dirTypes[path] = FemSettings.BESIDE
    elif setting == FemSettings.TEMPORARY:
        path = _getTempDir(solver)
        _dirTypes[path] = FemSettings.TEMPORARY
    elif setting == FemSettings.CUSTOM:
        path = _getCustomDir(solver)
        _dirTypes[path] = FemSettings.CUSTOM
    m = solver.Proxy.buildMachine(solver, path)
    _machines[solver] = m
    return m


def _getTempDir(solver):
    return tempfile.mkdtemp(prefix="fem")


def _getBesideDir(solver):
    base = _getBesideBase(solver)
    specificPath = os.path.join(base, solver.Label)
    specificPath = _getUniquePath(specificPath)
    if not os.path.isdir(specificPath):
        os.makedirs(specificPath)
    return specificPath


def _getBesideBase(solver):
    fcstdPath = solver.Document.FileName
    if fcstdPath == "":
        raise ValueError("must save")
    return os.path.splitext(fcstdPath)[0]


def _getCustomDir(solver):
    base = _getCustomBase(solver)
    specificPath = os.path.join(
            base, solver.Document.Name, solver.Label)
    specificPath = _getUniquePath(specificPath)
    if not os.path.isdir(specificPath):
        os.makedirs(specificPath)
    return specificPath


def _getCustomBase(solver):
    path = FemSettings.getCustomDir()
    if not os.path.isdir(path):
        raise ValueError("Invalid path")
    return path


def _getUniquePath(path):
    postfix = 1
    if path in _dirTypes:
        path += "_%03d" % postfix
    while path in _dirTypes:
        postfix += 1
        path = path[:-4] + "_%03d" % postfix
    return path


class Machine(FemSolverTasks.Base):

    def __init__(self, solver, directory, target=SOLVE):
        super(Machine, self).__init__(solver, directory)
        self.name = self.solver
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
        "ElmerOutput",
        "ElmerResult"
    ]

    @classmethod
    def attach(cls):
        if cls._instance is None:
            cls._instance = cls()
            App.addDocumentObserver(cls._instance)

    def slotNewObject(self, obj):
        self._checkModel(obj)

    def slotDeletedObject(self, obj):
        self._checkModel(obj)
        if obj in _machines:
            self._deleteMachine(obj)

    def slotChangedObject(self, obj, prop):
        if prop not in self._BLACKLIST_PROPS:
            self._checkSolver(obj)
            self._checkModel(obj)

    def slotDeletedDocument(self, doc):
        for obj in doc.Objects:
            if obj in _machines:
                self._deleteMachine(obj)

    def _deleteMachine(self, obj):
        m = _machines[obj]
        t = _dirTypes[m.directory]
        if t == FemSettings.TEMPORARY:
            shutil.rmtree(m.directory)
        del _dirTypes[m.directory]
        del _machines[obj]

    def _checkSolver(self, obj):
        analysis = FemMisc.findAnalysisOfMember(obj)
        for m in _machines.itervalues():
            if analysis == m.analysis and obj == m.solver:
                m.reset()

    def _checkModel(self, obj):
        if self._partOfModel(obj):
            analysis = FemMisc.findAnalysisOfMember(obj)
            for m in _machines.itervalues():
                if analysis == m.analysis:
                    m.reset()

    def _partOfModel(self, obj):
        for t in self._WHITELIST:
            if obj.isDerivedFrom(t):
                return True
        return False
