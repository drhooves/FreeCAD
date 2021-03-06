# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Markus Hovorka <m.hovorka@live.de>               *
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


__title__ = "_Base"
__author__ = "Markus Hovorka"
__url__ = "http://www.freecadweb.org"


from pivy import coin


class BaseProxy(object):

    BaseType = "App::FeaturePython"

    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLinkSubList", "References",
            "Base", "")

    def execute(self, obj):
        return True


class BaseViewProxy(object):

    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        default = coin.SoGroup()
        vobj.addDisplayMode(default, "Default")

    def getDisplayModes(self, obj):
        "Return a list of display modes."
        modes = ["Default"]
        return modes

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode


class HeatProxy(BaseProxy):
    pass


class HeatViewProxy(BaseViewProxy):

    def getIcon(self):
        return ":/icons/fem-equation-heat.svg"


class ElasticityProxy(BaseProxy):
    pass


class ElasticityViewProxy(BaseViewProxy):

    def getIcon(self):
        return ":/icons/fem-equation-elasticity.svg"


class FlowProxy(BaseProxy):
    pass


class FlowViewProxy(BaseViewProxy):

    def getIcon(self):
        return ":/icons/fem-equation-flow.svg"
