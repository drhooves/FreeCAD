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
__author__ = "Bernd Hahnebach, Markus Hovorka"
__url__ = "http://www.freecadweb.org"


class Proxy(object):

    Type = "FemElmerFreeText"

    def __init__(self, obj):
        obj.Proxy = self

        # Prop_None     = 0
        # Prop_ReadOnly = 1
        # Prop_Transient= 2
        # Prop_Hidden   = 4
        # Prop_Output   = 8
        attr = 4
        obj.addProperty(
                "App::PropertyString", "Text",
                "Base", "Text to be used for the SIF-File.", attr)
        obj.Text = DEFAULT_SIF_TEXT

    def execute(self, obj):
        return True


DEFAULT_SIF_TEXT = """\
Header
  CHECK KEYWORDS Warn
  Mesh DB "." "."
  Include Path ""
  Results Directory ""
End

Simulation
  Max Output Level = 5
  Coordinate System = Cartesian
  Coordinate Mapping(3) = 1 2 3
  Simulation Type = Steady state
  Steady State Max Iterations = 1
  Output Intervals = 1
  Timestepping Method = BDF
  BDF Order = 1
  Solver Input File = case.sif
  Post File = case.vtu
  Coordinate scaling = 0.001
  Use Mesh Names = Logical True
End

Constants
  Gravity(4) = 0 -1 0 9.82
  Stefan Boltzmann = 5.67e-08
  Permittivity of Vacuum = 8.8542e-12
  Boltzmann Constant = 1.3807e-23
  Unit Charge = 1.602e-19
End

Body 1
  Name = "Body_Volumes"
  Equation = 1
  Material = 1
End

Solver 2
  Equation = Linear elasticity
Element=p:2
  Variable = -dofs 3 Displacement
  Procedure = "StressSolve" "StressSolver"
  Exec Solver = Always
  Stabilize = True
  Bubbles = False
  Lumped Mass Matrix = False
  Optimize Bandwidth = True
  Steady State Convergence Tolerance = 1.0e-5
  Nonlinear System Convergence Tolerance = 1.0e-7
  Nonlinear System Max Iterations = 20
  Nonlinear System Newton After Iterations = 3
  Nonlinear System Newton After Tolerance = 1.0e-3
  Nonlinear System Relaxation Factor = 1
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 500
  Linear System Convergence Tolerance = 1.0e-10
  BiCGstabl polynomial degree = 2
  Linear System Preconditioning = Diagonal
  Linear System ILUT Tolerance = 1.0e-3
  Linear System Abort Not Converged = False
  Linear System Residual Output = 1
  Linear System Precondition Recompute = 1
End

Solver 1
  Equation = Result Output
  Output Format = Vtu
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = case
  Exec Solver = After Simulation
End

Equation 1
  Name = "Equation 1"
  Active Solvers(2) = 2 1
End

Material 1
  Name = "Steel (alloy - generic)"
  Heat expansion Coefficient = 12.0e-6
  Electric Conductivity = 1.367e6
  Heat Conductivity = 37.2
  Sound speed = 5100.0
  Heat Capacity = 976.0
  Mesh Poisson ratio = 0.285
  Density = 7850.0
  Poisson ratio = 0.3
  Youngs modulus = 210.0e9
End

Boundary Condition 1
  Name = "Fixed_Faces"
  Displacement 3 = 0
  Displacement 2 = 0
  Displacement 1 = 0
End

Boundary Condition 2
  Name = "Force_Faces"
  Force 2 = 9000000
End\
"""
