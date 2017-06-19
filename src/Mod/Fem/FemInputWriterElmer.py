# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Markus Hovorka <m.hovorka@live.de                *
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

__title__ = "FemInputWriterElmer"
__author__ = "Markus Hovorka, Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## \addtogroup FEM
#  @{

from FreeCAD import Console
import os.path
import io
import tempfile
import subprocess

import Fem
import ObjectsFem
import FemInputWriter
import sifio


_STARTINFO_NAME = "ELMERSOLVER_STARTINFO"
_ELMERGRID_IFORMAT = "8"
_ELMERGRID_OFORMAT = "2"


class Writer(FemInputWriter.FemInputWriter):

    # The first parameter defines the input file format:
    #   1)  .grd      : Elmergrid file format
    #   2)  .mesh.*   : Elmer input format
    #   3)  .ep       : Elmer output format
    #   4)  .ansys    : Ansys input format
    #   5)  .inp      : Abaqus input format by Ideas
    #   6)  .fil      : Abaqus output format
    #   7)  .FDNEUT   : Gambit (Fidap) neutral file
    #   8)  .unv      : Universal mesh file format
    #   9)  .mphtxt   : Comsol Multiphysics mesh format
    #   10) .dat      : Fieldview format
    #   11) .node,.ele: Triangle 2D mesh format
    #   12) .mesh     : Medit mesh format
    #   13) .msh      : GID mesh format
    #   14) .msh      : Gmsh mesh format
    #   15) .ep.i     : Partitioned ElmerPost format
    #
    # The second parameter defines the output file format:
    #   1)  .grd      : ElmerGrid file format
    #   2)  .mesh.*   : ElmerSolver format (also partitioned .part format)
    #   3)  .ep       : ElmerPost format
    #   4)  .msh      : Gmsh mesh format
    #   5)  .vtu      : VTK ascii XML format
    #
    # The third parameter is the name of the input file.
    # If the file does not exist, an example with the same name is created.
    # The default output file name is the same with a different suffix.

    def __init__(
            self, analysis_obj, solver_obj, mesh_obj, matlin_obj,
            matnonlin_obj, fixed_obj, displacement_obj, contact_obj,
            planerotation_obj, transform_obj, selfweight_obj, force_obj,
            pressure_obj, temperature_obj, heatflux_obj,
            initialtemperature_obj, beamsection_obj, shellthickness_obj,
            fluid_section_obj, elmer_free_text_obj, analysis_type=None,
            dir_name=None):

        FemInputWriter.FemInputWriter.__init__(
            self, analysis_obj, solver_obj, mesh_obj, matlin_obj,
            matnonlin_obj, fixed_obj, displacement_obj, contact_obj,
            planerotation_obj, transform_obj, selfweight_obj, force_obj,
            pressure_obj, temperature_obj, heatflux_obj,
            initialtemperature_obj, beamsection_obj, shellthickness_obj,
            fluid_section_obj, analysis_type, dir_name)
        self.elmer_free_text = elmer_free_text_obj

    def write_all(self, sif_name, working_dir):
        sif_path = os.path.join(working_dir, sif_name)
        Console.PrintLog(
                "Write Elmer input files to {}...\n"
                .format(working_dir))
        self.write_sif(sif_path)
        self.write_startinfo(sif_name, working_dir)
        mesh_ret = self.write_mesh(working_dir)
        return mesh_ret

    def write_sif(self, sif_path):
        header = self.get_header()
        simulation = self.get_simulation()
        constants = self.get_constants()
        body_forces = self.get_body_forces()
        initial_conditions = self.get_body_forces()
        material = self.get_material()
        solver = self.get_solver()
        equation = self.get_equation(solver)
        body = self.get_body(
                material, body_forces, equation, initial_conditions)

        sections = []
        sections.append(header)
        sections.append(simulation)
        sections.append(constants)
        sections.extend(body_forces)
        sections.extend(initial_conditions)
        sections.append(material)
        sections.append(solver)
        sections.append(equation)
        sections.append(body)

        with io.FileIO(sif_path, 'w') as fstream:
            sifio.write(sections, fstream)

    def get_header(self):
        section = sifio.Section(sifio.HEADER)
        section["Mesh DB"] = "."
        section["Include Path"] = ""
        section["Results Directory"] = ""
        return section

    def get_simulation(self):
        section = sifio.Section(sifio.SIMULATION)
        section["Coordinate System"] = "Cartesian"
        section["Coordinate Mapping"] = (1, 2, 3)
        section["Simulation Type"] = "Steady state"
        section["Steady State Max Iterations"] = 1
        section["Output Intervals"] = 1
        section["Timestepping Method"] = "BDF"
        section["BDF Order"] = 1
        section["Post File"] = "case.vtu"
        section["Coordinate scaling"] = 0.001
        section["Use Mesh Names"] = True
        return section

    def get_constants(self):
        section = sifio.Section(sifio.CONSTANTS)
        section["Gravity"] = (0, -1, 0, 9.82)
        section["Stefan Boltzmann"] = 5.67e-12
        section["Permittivity of Vacuum"] = 8.8542e-12
        section["Boltzmann Constant"] = 1.3807e-23
        section["Unit Charge"] = 1.602e-19
        return section

    def get_body_forces(self):
        pass

    def get_initial_conditions(self):
        pass

    def get_material(self):
        pass

    def get_solver(self):
        pass

    def get_equation(self):
        pass

    def get_body(self):
        pass

    def write_startinfo(self, sif_name, working_dir):
        startinfo_path = os.path.join(working_dir, _STARTINFO_NAME)
        Console.PrintLog(
                "Write ELMERFEM_STARTINFO to {}.\n"
                .format(startinfo_path))
        with open(startinfo_path, 'w') as f:
            f.write(sif_name)

    def write_mesh(self, working_dir):
        with tempfile.NamedTemporaryFile(suffix=".unv") as meshFile:
            Fem.export([self.mesh_object], meshFile.name)
            args = [self._find_elmergrid_binary(),
                    _ELMERGRID_IFORMAT,
                    _ELMERGRID_OFORMAT,
                    meshFile.name,
                    "-out", working_dir]
            p = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return p.communicate()

    def _find_elmergrid_binary(self):
        return "ElmerGrid"
