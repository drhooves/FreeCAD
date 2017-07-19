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


import os.path
import shutil


def findAnalysisOfMember(member):
    if member is None:
        raise ValueError("Member must not be None")
    for obj in member.Document.Objects:
        if obj.isDerivedFrom("Fem::FemAnalysis"):
            if member in obj.Member:
                return obj
    return None


def getMember(analysis, baseType, pyType=None):
    if analysis is None:
        raise ValueError("Analysis must not be None")
    matching = []
    for m in analysis.Member:
        if isOfType(m, baseType, pyType):
            matching.append(m)
    return matching


def getSingleMember(analysis, baseType, pyType=None):
    objs = getMember(analysis, baseType, pyType)
    return objs[0] if objs else None


def wipeDir(directory):
    for node in os.listdir(directory):
        path = os.path.join(directory, node)
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)


def isOfType(obj, baseType, pyType=None):
    if obj.isDerivedFrom(baseType):
        if pyType is None:
            return True
        if hasattr(obj, "Proxy") and obj.Proxy.Type == pyType:
            return True
    return False


def getUniqueName(obj):
    name = obj.Name
    if hasattr(obj, "Document"):
        name = "%s.%s" % (obj.Document.Name, name)
    return name
