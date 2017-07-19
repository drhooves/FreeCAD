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
import tempfile
import shutil

import FreeCAD as App
import FemMisc


_directories = {}
_files = {}


def createDir(obj):
    path = tempfile.mkdtemp()
    _register(obj, path, _directories)
    return path


def createFile(obj):
    path = tempfile.mkstemp()
    _register(obj, path, _files)
    return path


def removeDirs(obj, *path):
    if name in _directories:
        if len(path) == 0:
            path = _directories[name]
        for p in path:
            shutil.rmtree(p)


def removeFiles(obj, *path):
    name = FemMisc.getUniqueName(obj)
    if name in _files:
        if len(path) == 0:
            path = _files[name]
        for p in path:
            os.remove(p)


def _register(obj, path, store):
    _DocObserver.attach()
    name = FemMisc.getUniqueName(obj)
    resSet = store.get(name, set())
    resSet.add(path)
    store[name] = resSet


class _DocObserver(object):

    _instance = None

    @classmethod
    def attach(cls):
        if cls._instance is None:
            cls._instance = cls()
            App.addDocumentObserver(cls._instance)

    def slotDeleteObject(self, obj):
        removeDirs(obj)
        removeFiles(obj)

    def slotDeleteDocument(self, doc):
        for obj in doc.Objects:
            removeDirs(obj)
            removeFiles(obj)
        removeDirs(doc)
        removeFiles(doc)
