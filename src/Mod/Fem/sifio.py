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


import collections


HEADER              = "Header"
SIMULATION          = "Simulation"
CONSTANTS           = "Constants"
BODY                = "Body"
MATERIAL            = "Material"
BODY_FORCE          = "Body Force"
EQUATION            = "Equation"
SOLVER              = "Solver"
BOUNDARY_CONDITION  = "Boundary Condition"
INITIAL_CONDITION   = "Initial Condition"
COMPONENT           = "Component"


_VALID_SECTIONS = (
        HEADER,
        SIMULATION,
        CONSTANTS,
        BODY,
        MATERIAL,
        BODY_FORCE,
        EQUATION,
        SOLVER,
        BOUNDARY_CONDITION,
        INITIAL_CONDITION,
        COMPONENT,
)


_NUMBERED_SECTIONS = (
        BODY,
        MATERIAL,
        BODY_FORCE,
        EQUATION,
        SOLVER,
        BOUNDARY_CONDITION,
        INITIAL_CONDITION,
        COMPONENT,
)

_SECTION_DELIM  = "End"
_WHITESPACE     = " "
_NEWLINE        = "\n"

_TYPE_REAL      = "Real"
_TYPE_INTEGER   = "Integer"
_TYPE_LOGICAL   = "Logical"
_TYPE_STRING    = "String"
_TYPE_FILE      = "File"


def write(sections, stream):
    ids = _IDManager()
    _Writer(ids, sections, stream).write()


def isNumbered(section):
    return section in _NUMBERED_SECTIONS


class Section(object):

    def __init__(self, name):
        self.name = name
        if name not in _VALID_SECTIONS:
            raise ValueError("Invalid section name: %s" % name)
        self._attrs = dict()

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def __getitem__(self, key):
        return self._attrs[key]

    def __delitem__(self, key):
        del self._attrs[key]

    def __iter__(self):
        return iter(self._attrs)


class PathAttr(str):
    pass


class _Writer(object):

    def __init__(self, idManager, sections, stream):
        self._ids = idManager
        self._sections = sections
        self._stream = stream

    def write(self):
        for s in self.sections:
            self._writeSection(s)
            self.stream.write(_NEWLINE)

    def _writeSection(self):
        self._writeSectionHeader(s)
        self.stream.write(_NEWLINE)
        self._writeSectionBody(s)
        self.stream.write(_NEWLINE)
        self._writeSectionFooter(s)

    def _writeSectionHeader(self, s):
        self.stream.write(s.name)
        self.stream.write(_WHITESPACE)
        if section.isNumbered(s):
            self.stream.write(self._ids.getId(s))

    def _writeSectionFooter(self, s):
        self.stream.write(_SECTION_DELIM)

    def _writeSectionBody(self, s):
        for key, data in s:
            self._writeAttribute(key, data))
            self.stream.write(_NEWLINE)

    def _writeAttribute(key, data):
        if isinstance(data, section.Section):
            self._writeSectionAttr(key, data)
        elif self._isCollection(data):
            self._writeArrAttr(key, data)
        else:
            self._writeScalarAttr(key, data)

    def _isCollection(data):
        return (not isinstance(data, basestring)
                and isinstance(data, collections.Iterable))

    def _checkScalar(dataType):
        if issubclass(dataType, int):
            return self._genIntAttr
        if issubclass(dataType, float):
            return self._genFloatAttr
        if issubclass(dataType, bool):
            return self._genBoolAttr
        if issubclass(dataType, basestring):
            return self._genStrAttr
        return None

    def _writeScalarAttr(self, key, data):
        attrType = self._getAttrTypeScalar(data)
        if attrType is None:
            raise ValueError("Unsupported data type: %s" % type(data))
        self.stream.write(key)
        self.stream.write(_WHITESPACE)
        self.stream.write("=")
        self.stream.write(_WHITESPACE)
        self.stream.write(attrType)
        self.stream.write(_WHITESPACE)
        self.stream.write(self._preprocess(data, type(data)))

    def _writeArrAttr(self, key, data):
        attrType = self._getAttrTypeArr(data)
        self.stream.write(key)
        self.stream.write("(" + len(data) + ")")
        self.stream.write(_WHITESPACE)
        self.stream.write("=")
        self.stream.write(_WHITESPACE)
        self.stream.write(attrType)
        for val in data:
            self.stream.write(_WHITESPACE)
            self.stream.write(self._preprocess(val, type(data)))

    def _getSifDataType(dataType):
        if issubclass(dataType, section.Section):
            return _TYPE_INTEGER
        if issubclass(dataType, int):
            return _TYPE_INTEGER
        if issubclass(dataType, float):
            return _TYPE_REAL
        if issubclass(dataType, bool):
            return _TYPE_LOGICAL
        if issubclass(dataType, section.Path):
            return _TYPE_FILE
        if issubclass(dataType, basestring):
            return _TYPE_STRING
        raise ValueError("Unsupported data type: %s" % type(data))

    def _preprocess(data, dataType):
        if issubclass(dataType, section.Section):
            return str(self.ids.getId(data))
        if issubclass(dataType, section.Path):
            return '"{}"'.format(data)
        if issubclass(dataType, basestring):
            return '"{}"'.format(data)
        return str(data)

    def _getAttrTypeScalar(data):
        return self._getSifDataType(type(data))

    def _getAttrTypeArr(data):
        if not data:
            raise ValueError("Collections must not be empty.")
        it = iter(data)
        dataType = type(it.next())
        for entry in it:
            if not isinstance(entry, dataType):
                raise ValueError("Collection must be homogenueous")
        return self._getSifDataType(dataType)


class _IdManager(object):

    def __init__(self, sections, stream, firstId=1):
        self._pool = dict()
        self._ids = dict()
        self.firstId = firstId

    def _setId(self, section):
        if section.name not in self._pool:
            self._pool[section.name] = self.firstId
        self._ids[section] = self._pool[section.name]
        self._pool[section.name] += 1

    def _getId(self, section):
        if section not in self._ids:
            self.setId(section)
        return self._ids[section]
