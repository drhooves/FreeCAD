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


from pivy import coin


class Proxy(object):

    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        vobj.addDisplayMode(coin.SoGroup(), self.getDefaultDisplayMode());

    def getDefaultDisplayMode(self):
        return "Default"

    def getDisplayModes(self, vobj):
        """Override to provide actual display modes.

        One display mode (e.g. Dummy) is always required by FreeCAD.
        DocumentObjects with the TypeId "App::FeaturePython" don't
        provide one by default.
        """
        return ["Default"]
