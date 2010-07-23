#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
#
#   ChemPy - A chemistry toolkit for Python
#
#   Copyright (c) 2010 by Joshua W. Allen (jwallen@mit.edu)
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the 'Software'),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
This module provides functionality for automatic drawing of two-dimensional
molecules.
"""

import math
import numpy
import os.path
import re

import sys
sys.path.append(os.path.abspath('.'))
from chempy.molecule import *

################################################################################

def render(atoms, bonds, coordinates, symbols, fstr):
    """
    Uses the Cairo graphics library to create the drawing of the molecule.
    """

    try:
        import cairo
    except ImportError:
        print 'Cairo not found; potential energy surface will not be drawn.'
        return

    # Initialize Cairo surface and context
    width = 640; height = 480
    ext = os.path.splitext(fstr)[1].lower()
    if ext == '.svg':
        surface = cairo.SVGSurface(fstr, width, height)
    elif ext == '.pdf':
        surface = cairo.PDFSurface(fstr, width, height)
    elif ext == '.ps':
        surface = cairo.PSSurface(fstr, width, height)
    cr = cairo.Context(surface)

    bondLength = 32
    coordinates[:,1] *= -1
    coordinates = coordinates * bondLength + 160

    # Some global settings
    cr.select_font_face("sans")
    cr.set_font_size(10)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)

    # Draw bonds
    cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
    cr.set_line_width(1.0)
    for atom1 in bonds:
        for atom2, bond in bonds[atom1].iteritems():
            index1 = atoms.index(atom1)
            index2 = atoms.index(atom2)
            if index1 < index2:
                x1, y1 = coordinates[index1,:]
                x2, y2 = coordinates[index2,:]
                angle = math.atan2(y2 - y1, x2 - x1)

                dx = x2 - x1; dy = y2 - y1
                du = math.cos(angle + math.pi / 2)
                dv = math.sin(angle + math.pi / 2)
                if bond.isDouble() and (symbols[index1] != '' or symbols[index2] != ''):
                    # Draw double bond centered on bond axis
                    du *= 2; dv *= 2
                    cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
                    cr.move_to(x1 - du, y1 - dv); cr.line_to(x2 - du, y2 - dv)
                    cr.stroke()
                    cr.move_to(x1 + du, y1 + dv); cr.line_to(x2 + du, y2 + dv)
                    cr.stroke()
                elif bond.isTriple() and (symbols[index1] != '' or symbols[index2] != ''):
                    # Draw triple bond centered on bond axis
                    du *= 3; dv *= 3
                    cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
                    cr.move_to(x1 - du, y1 - dv); cr.line_to(x2 - du, y2 - dv)
                    cr.stroke()
                    cr.move_to(x1, y1); cr.line_to(x2, y2)
                    cr.stroke()
                    cr.move_to(x1 + du, y1 + dv); cr.line_to(x2 + du, y2 + dv)
                    cr.stroke()
                else:
                    # Draw bond on skeleton
                    cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
                    cr.move_to(x1, y1); cr.line_to(x2, y2)
                    cr.stroke()
                    # Draw other bonds
                    if bond.isDouble():
                        du *= 4; dv *= 4; dx = 2 * dx / bondLength; dy = 2 * dy / bondLength
                        cr.move_to(x1 + du + dx, y1 + dv + dy); cr.line_to(x2 + du - dx, y2 + dv - dy)
                        cr.stroke()
                    elif bond.isTriple():
                        du *= 3; dv *= 3; dx = 2 * dx / bondLength; dy = 2 * dy / bondLength
                        cr.move_to(x1 - du + dx, y1 - dv + dy); cr.line_to(x2 - du - dx, y2 - dv - dy)
                        cr.stroke()
                        cr.move_to(x1 + du + dx, y1 + dv + dy); cr.line_to(x2 + du - dx, y2 + dv - dy)
                        cr.stroke()

    # Draw atoms (for now)
    for i, atom in enumerate(atoms):
        symbol = symbols[i]
        index = atoms.index(atom)
        x0, y0 = coordinates[index,:]
        vector = numpy.zeros(2, numpy.float64)
        for atom2 in bonds[atom]:
            vector += coordinates[atoms.index(atom2),:] - coordinates[index,:]
        heavyFirst = vector[0] <= 0
        renderSymbol(symbol, atom, coordinates, atoms, bonds, x0, y0, cr, heavyFirst)

    # Finish Cairo drawing
    surface.finish()

def renderSymbol(symbol, atom, coordinates0, atoms, bonds, x0, y0, cr, heavyFirst=True):
    """
    Render the `label` for an atom centered around the coordinates (`x0`, `y0`)
    onto the Cairo context `cr`. If `heavyFirst` is ``False``, then the order
    of the atoms will be reversed in the symbol
    """

    if symbol != '':
        heavyAtom = symbol[0]

        # Split label by atoms
        labels = re.findall('[A-Z][0-9]*', symbol)
        if not heavyFirst: labels.reverse()
        symbol = ''.join(labels)

        # Determine positions of each character in the symbol
        coordinates = []

        y0 += max([cr.text_extents(char)[3] for char in symbol if char.isalpha()]) / 2

        for i, label in enumerate(labels):
            for j, char in enumerate(label):
                cr.set_font_size(6 if char.isdigit() else 10)
                xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(char)
                if i == 0 and j == 0:
                    # Center heavy atom at (x0, y0)
                    x = x0 - width / 2.0 - xbearing
                    y = y0
                else:
                    # Left-justify other atoms (for now)
                    x = x0
                    y = y0
                if char.isdigit(): y += height / 2.0
                coordinates.append((x,y))
                x0 = x + xadvance

        x = 1000000; y = 1000000; width = 0; height = 0
        startWidth = 0; endWidth = 0
        for i, char in enumerate(symbol):
            cr.set_font_size(6 if char.isdigit() else 10)
            extents = cr.text_extents(char)
            if coordinates[i][0] + extents[0] < x: x = coordinates[i][0] + extents[0]
            if coordinates[i][1] + extents[1] < y: y = coordinates[i][1] + extents[1]
            width += extents[4] if i < len(symbol) - 1 else extents[2]
            if extents[3] > height: height = extents[3]
            if i == 0: startWidth = extents[2]
            if i == len(symbol) - 1: endWidth = extents[2]

        if not heavyFirst:
            for i in range(len(coordinates)):
                coordinates[i] = (coordinates[i][0] - (width - startWidth / 2 - endWidth / 2), coordinates[i][1])
            x -= width - startWidth / 2 - endWidth / 2

        # Background
        x1 = x - 2; y1 = y - 2; x2 = x + width + 2; y2 = y + height + 2; r = 4
        cr.move_to(x1 + r, y1)
        cr.line_to(x2 - r, y1)
        cr.curve_to(x2 - r/2, y1, x2, y1 + r/2, x2, y1 + r)
        cr.line_to(x2, y2 - r)
        cr.curve_to(x2, y2 - r/2, x2 - r/2, y2, x2 - r, y2)
        cr.line_to(x1 + r, y2)
        cr.curve_to(x1 + r/2, y2, x1, y2 - r/2, x1, y2 - r)
        cr.line_to(x1, y1 + r)
        cr.curve_to(x1, y1 + r/2, x1 + r/2, y1, x1 + r, y1)
        cr.close_path()
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.fill()

        # Set color for text
        if heavyAtom == 'C':    cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        elif heavyAtom == 'N':  cr.set_source_rgba(0.0, 0.0, 1.0, 1.0)
        elif heavyAtom == 'O':  cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)
        elif heavyAtom == 'F':  cr.set_source_rgba(0.5, 0.75, 1.0, 1.0)
        elif heavyAtom == 'Si': cr.set_source_rgba(0.5, 0.5, 0.75, 1.0)
        elif heavyAtom == 'Al': cr.set_source_rgba(0.75, 0.5, 0.5, 1.0)
        elif heavyAtom == 'P':  cr.set_source_rgba(1.0, 0.5, 0.0, 1.0)
        elif heavyAtom == 'S':  cr.set_source_rgba(1.0, 0.75, 0.5, 1.0)
        elif heavyAtom == 'Cl': cr.set_source_rgba(0.0, 1.0, 0.0, 1.0)
        elif heavyAtom == 'Br': cr.set_source_rgba(0.6, 0.2, 0.2, 1.0)
        elif heavyAtom == 'I':  cr.set_source_rgba(0.5, 0.0, 0.5, 1.0)
        else:                   cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)

        # Text itself
        for i, char in enumerate(symbol):
            cr.set_font_size(6 if char.isdigit() else 10)
            xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(char)
            xi, yi = coordinates[i]
            cr.move_to(xi, yi)
            cr.show_text(char)

        x, y = coordinates[0] if heavyFirst else coordinates[-1]
            
    else:
        x = x0 + 2; y = y0; width = 0; height = 0
        heavyAtom = ''

    # Draw radical electrons and charges
    # These will be placed either horizontally along the top or bottom of the
    # atom or vertically along the left or right of the atom
    orientation = ' '
    if len(bonds[atom]) == 1:
        # Terminal atom - we require a horizontal arrangement if there are
        # more than just the heavy atom
        atom1 = bonds[atom].keys()[0]
        vector = coordinates0[atoms.index(atom),:] - coordinates0[atoms.index(atom1),:]
        if len(symbol) <= 1:
            angle = math.atan2(vector[1], vector[0])
            if 3 * math.pi / 4 <= angle or angle < -3 * math.pi / 4:  orientation = 'l'
            elif -3 * math.pi / 4 <= angle < -1 * math.pi / 4:        orientation = 'b'
            elif -1 * math.pi / 4 <= angle <  1 * math.pi / 4:        orientation = 'r'
            else:                                                     orientation = 't'
        else:
            if vector[1] <= 0:
                orientation = 'b'
            else:
                orientation = 't'
    else:
        # Internal atom
        # First try to see if there is a "preferred" side on which to place the
        # radical/charge data, i.e. if the bonds are unbalanced
        vector = numpy.zeros(2, numpy.float64)
        for atom1 in bonds[atom]:
            vector += coordinates0[atoms.index(atom),:] - coordinates0[atoms.index(atom1),:]
        if numpy.linalg.norm(vector) < 1e-4:
            # All of the bonds are balanced, so we'll need to be more shrewd
            angles = []
            for atom1 in bonds[atom]:
                vector = coordinates0[atoms.index(atom1),:] - coordinates0[atoms.index(atom),:]
                angles.append(math.atan2(vector[1], vector[0]))
            # Try one more time to see if we can use one of the four sides
            # (due to there being no bonds in that quadrant)
            # We don't even need a full 90 degrees open (using 60 degrees instead)
            if   all([ 1 * math.pi / 3 >= angle or angle >=  2 * math.pi / 3 for angle in angles]):  orientation = 't'
            elif all([-2 * math.pi / 3 >= angle or angle >= -1 * math.pi / 3 for angle in angles]):  orientation = 'b'
            elif all([-1 * math.pi / 6 >= angle or angle >=  1 * math.pi / 6 for angle in angles]):  orientation = 'r'
            elif all([ 5 * math.pi / 6 >= angle or angle >= -5 * math.pi / 6 for angle in angles]):  orientation = 'l'
            else:
                # If we still don't have it (e.g. when there are 4+ equally-
                # spaced bonds), just put everything in the top right for now
                orientation = 'tr'
        else:
            # There is an unbalanced side, so let's put the radical/charge data there
            angle = math.atan2(vector[1], vector[0])
            if 3 * math.pi / 4 <= angle or angle < -3 * math.pi / 4:  orientation = 'l'
            elif -3 * math.pi / 4 <= angle < -1 * math.pi / 4:        orientation = 'b'
            elif -1 * math.pi / 4 <= angle <  1 * math.pi / 4:        orientation = 'r'
            else:                                                     orientation = 't'
        
    cr.set_font_size(10)
    extents = cr.text_extents(heavyAtom)

    if len(orientation) > 1: xi += 4

    if orientation[0] == 'l':
        xi = x - 2
        yi = y
    elif orientation[0] == 'b':
        xi = x
        yi = y - extents[3] - 3
    elif orientation[0] == 'r':
        xi = x + extents[2] + 4
        yi = y
    elif orientation[0] == 't':
        xi = x
        yi = y + 3
    
    if (orientation[0] == 'b' or orientation[0] == 't') and len(symbol) > 0:
        xi += extents[0] + extents[2]/2.0 + 2.0
    elif (orientation[0] == 'l' or orientation[0] == 'r') and len(symbol) > 0:
        yi += extents[1] + extents[3]/2.0 + 2.0

    # Get width/height
    cr.set_font_size(6)
    if orientation[0] == 'b' or orientation[0] == 't':
        width = 0.0
        if atom.radicalElectrons > 0: width = atom.radicalElectrons * 3 + 1
        if atom.charge == 1:          width += cr.text_extents('+')[2] + 1
        elif atom.charge > 1:         width += cr.text_extents('%i+' % atom.charge)[2] + 1
        elif atom.charge == -1:       width += cr.text_extents(u'\u2013')[2] + 1
        elif atom.charge < -1:        width += cr.text_extents(u'%i\u2013' % abs(atom.charge))[2] + 1
        xi -= width / 2.0
    elif orientation[0] == 'l' or orientation[0] == 'r':
        height = 0.0
        if atom.radicalElectrons > 0: height = atom.radicalElectrons * 3 + 1
        if atom.charge == 1:          height += cr.text_extents('+')[3] + 1
        elif atom.charge > 1:         height += cr.text_extents('%i+' % atom.charge)[3] + 1
        elif atom.charge == -1:       width += cr.text_extents(u'\u2013')[3] + 1
        elif atom.charge < -1:        height += cr.text_extents(u'%i\u2013' % abs(atom.charge))[3] + 1
        yi -= height / 2.0

    if orientation[0] == 'b' or orientation[0] == 't':
        # Draw radical electrons first
        for i in range(atom.radicalElectrons):
            cr.new_sub_path()
            cr.arc(xi + 3 * i, yi, 1, 0, 2 * math.pi)
            cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            cr.fill()
        if atom.radicalElectrons > 0: xi += atom.radicalElectrons * 3
        # Draw charges second
        text = ''
        if atom.charge == 1:       text = '+'
        elif atom.charge > 1:      text = '%i+' % atom.charge
        elif atom.charge == -1:    text = u'\u2013'
        elif atom.charge < -1:     text = u'%i\u2013' % abs(atom.charge)
        if text != '':
            extents = cr.text_extents(text)
            cr.move_to(xi - extents[0], yi - extents[1] - extents[3]/2)
            cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            cr.show_text(text)
    elif orientation[0] == 'l' or orientation[0] == 'r':
        # Draw charges first
        text = ''
        if atom.charge == 1:       text = '+'
        elif atom.charge > 1:      text = '%i+' % atom.charge
        elif atom.charge == -1:    text = u'\u2013'
        elif atom.charge < -1:     text = u'%i\u2013' % abs(atom.charge)
        if text != '':
            extents = cr.text_extents(text)
            cr.move_to(xi - extents[0] - extents[2]/2, yi)
            cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            cr.show_text(text)
        if atom.charge != 0: yi += extents[3]
        # Draw radical electrons second
        for i in range(atom.radicalElectrons):
            cr.new_sub_path()
            cr.arc(xi, yi + 3 * i, 1, 0, 2 * math.pi)
            cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            cr.fill()

################################################################################

def findLongestPath(chemGraph, atoms0):
    """
    Finds the longest path containing the list of `atoms` in the `chemGraph`.
    The atoms are assumed to already be in a path, with ``atoms[0]`` being a
    terminal atom.
    """
    atom1 = atoms0[-1]
    paths = [atoms0]
    for atom2 in chemGraph.bonds[atom1]:
        if atom2 not in atoms0:
            atoms = atoms0[:]
            atoms.append(atom2)
            paths.append(findLongestPath(chemGraph, atoms))
    lengths = [len(path) for path in paths]
    index = lengths.index(max(lengths))
    return paths[index]

def getBackbone(chemGraph):
    """
    Return the atoms that make up the backbone of the molecule.
    """

    if chemGraph.isCyclic():

        cycles = []
        for atom in chemGraph.atoms:
            if chemGraph.isAtomInCycle(atom):
                cycles.extend(chemGraph.getAllCycles(atom))
        for cycle in cycles:
            print [chemGraph.atoms.index(a) for a in cycle]

        quit()

    else:
        # Make a shallow copy of the chemGraph so we don't modify the original
        chemGraph = chemGraph.copy()

        # Remove hydrogen atoms from consideration, as they cannot be part of
        # the backbone
        chemGraph.makeHydrogensImplicit()

        # If there are only one or two atoms remaining, these are the backbone
        if len(chemGraph.atoms) == 1 or len(chemGraph.atoms) == 2:
            return chemGraph.atoms[:]

        # Find the terminal atoms - those that only have one explicit bond
        terminalAtoms = []
        for atom in chemGraph.atoms:
            if len(chemGraph.bonds[atom]) == 1:
                terminalAtoms.append(atom)

        # Starting from each terminal atom, find the longest straight path to
        # another terminal; this defines the backbone
        backbone = []
        for atom in terminalAtoms:
            path = findLongestPath(chemGraph, [atom])
            if len(path) > len(backbone):
                backbone = path

        return backbone

################################################################################

def generateCoordinates(chemGraph, atoms, bonds):
    """
    Generate the 2D coordinates to be used when drawing the `chemGraph`, a
    :class:`ChemGraph` object. Use the `atoms` parameter to pass a list
    containing the atoms in the molecule for which coordinates are needed. If
    you don't specify this, all atoms in the molecule will be used.

    Because we are working in two dimensions, we call the horizontal direction
    :math:`u` and the vertical direction :math:`v`. The vertices are arranged
    based on a standard bond length of unity, and can be scaled later for
    longer bond lengths.

    This function ignores any previously-existing coordinate information.
    """

    # Initialize array of coordinates
    coordinates = numpy.zeros((len(atoms), 2), numpy.float64)

    # If there are only one or two atoms to draw, then determining the
    # coordinates is trivial
    if len(atoms) == 1:
        coordinates[0,:] = [0.0, 0.0]
        return coordinates
    elif len(atoms) == 2:
        coordinates[0,:] = [0.0, 0.0]
        coordinates[1,:] = [1.0, 0.0]
        return coordinates

    # Find the backbone of the molecule
    backbone = getBackbone(chemGraph)

    # Generate coordinates for atoms in backbone
    if chemGraph.isCyclic():
        raise NotImplementedError('Currently cannot find backbone of cyclic molecules!')
    else:
        # Straight chain backbone

        # First atom in backbone goes at origin
        index0 = atoms.index(backbone[0])
        coordinates[index0,:] = [0.0, 0.0]

        # Second atom in backbone goes on x-axis (for now; this could be improved!)
        index1 = atoms.index(backbone[1])
        vector = numpy.array([1.0, 0.0], numpy.float64)
        if bonds[backbone[0]][backbone[1]].isTriple():
            rotatePositive = False
        else:
            rotatePositive = True
            rot = numpy.array([[math.cos(-math.pi / 6), math.sin(-math.pi / 6)], [-math.sin(-math.pi / 6), math.cos(-math.pi / 6)]], numpy.float64)
            vector = numpy.array([1.0, 0.0], numpy.float64)
            vector = numpy.dot(rot, vector)
        coordinates[index1,:] = coordinates[index0,:] + vector

        # Other atoms in backbone
        for i in range(2, len(backbone)):
            atom1 = backbone[i-1]
            atom2 = backbone[i]
            index1 = atoms.index(atom1)
            index2 = atoms.index(atom2)
            bond0 = bonds[backbone[i-2]][atom1]
            bond = bonds[atom1][atom2]
            # Angle of next bond depends on the number of bonds to the start atom
            numBonds = len(bonds[atom1])
            if numBonds == 2:
                if (bond0.isTriple() or bond.isTriple()) or (bond0.isDouble() and bond.isDouble()):
                    # Rotate by 0 degrees towards horizontal axis (to get angle of 180)
                    angle = 0.0
                else:
                    # Rotate by 60 degrees towards horizontal axis (to get angle of 120)
                    angle = math.pi / 3
            elif numBonds == 3:
                # Rotate by 60 degrees towards horizontal axis (to get angle of 120)
                angle = math.pi / 3
            elif numBonds == 4:
                # Rotate by 0 degrees towards horizontal axis (to get angle of 90)
                angle = 0.0
            elif numBonds == 5:
                # Rotate by 36 degrees towards horizontal axis (to get angle of 144)
                angle = math.pi / 5
            elif numBonds == 6:
                # Rotate by 0 degrees towards horizontal axis (to get angle of 180)
                angle = 0.0
            # Determine coordinates for atom
            if angle != 0:
                if not rotatePositive: angle = -angle
                rot = numpy.array([[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]], numpy.float64)
                vector = numpy.dot(rot, vector)
                rotatePositive = not rotatePositive
            coordinates[index2,:] = coordinates[index1,:] + vector

    # If backbone is linear, then rotate so that the bond is parallel to the
    # horizontal axis
    vector0 = coordinates[atoms.index(backbone[1]),:] - coordinates[atoms.index(backbone[0]),:]
    linear = True
    for i in range(2, len(backbone)):
        vector = coordinates[atoms.index(backbone[i]),:] - coordinates[atoms.index(backbone[i-1]),:]
        if numpy.linalg.norm(vector - vector0) > 1e-4:
            linear = False
            break
    if linear:
        angle = math.atan2(vector0[0], vector0[1]) - math.pi / 2
        rot = numpy.array([[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]], numpy.float64)
        coordinates = numpy.dot(coordinates, rot)

    # Center backbone at origin
    origin = numpy.zeros(2, numpy.float64)
    for atom in backbone:
        index = atoms.index(atom)
        origin += coordinates[index,:]
    origin /= len(backbone)
    coordinates -= origin

    # We now proceed by calculating the coordinates of the functional groups
    # attached to the backbone
    # Each functional group is independent, although they may contain further
    # branching and cycles
    # In general substituents should try to grow away from the origin to
    # minimize likelihood of overlap

    # Don't need to do terminal atoms in backbone (if backbone is straight chain)
    for i in range(1, len(backbone)-1):
        atom0 = backbone[i]

        # Determine rotation angle and matrix
        angle = 2 * math.pi / len(bonds[atom0])
        rot = numpy.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]], numpy.float64)
        index0 = atoms.index(atom0)
        # Determine the vector of any currently-existing bond from this atom
        # (We use the bond to the previous atom in the backbone here)
        vector = coordinates[atoms.index(backbone[i-1]),:] - coordinates[index0,:]

        # Iterate through each neighboring atom to this backbone atom
        # If the neighbor is not in the backbone, then we need to determine
        # coordinates for it
        for atom1, bond in bonds[atom0].iteritems():
            if atom1 not in backbone:
                occupied = True; count = 0
                # Rotate vector until we find an unoccupied location
                while occupied and count < len(bonds[atom0]):
                    count += 1; occupied = False
                    vector = numpy.dot(rot, vector)
                    for atom2 in bonds[atom0]:
                        index2 = atoms.index(atom2)
                        if numpy.linalg.norm(coordinates[index2,:] - coordinates[index0,:] - vector) < 1e-4:
                            occupied = True
                coordinates[atoms.index(atom1),:] = coordinates[index0,:] + vector
                processFunctionalGroup(atom0, atom1, atoms, bonds, coordinates)

    return coordinates

################################################################################

def processFunctionalGroup(atom0, atom1, atoms, bonds, coordinates):
    """
    For the functional group starting with the bond from `atom0` to `atom1`,
    generate the coordinates of the rest of the functional group. `atom0` is
    treated as if a terminal atom. `atom0` and `atom1` must already have their
    coordinates determined. `atoms` is a list of the atoms to be drawn, `bonds`
    is a dictionary of the bonds to draw, and `coordinates` is an array of the
    coordinates for each atom to be drawn. This function is designed to be
    recursive.
    """

    # Assume for now that each functional group is acyclic

    index0 = atoms.index(atom0)
    index1 = atoms.index(atom1)

    # Determine the vector of any currently-existing bond from this atom
    # (We use the bond to the previous atom here)
    vector = coordinates[index0,:] - coordinates[index1,:]

    # Determine rotation angle and matrix
    numBonds = len(bonds[atom1])
    angle = 0.0
    if numBonds == 2:
        bond0, bond = bonds[atom1].values()
        if (bond0.isTriple() or bond.isTriple()) or (bond0.isDouble() and bond.isDouble()):
            angle = math.pi
        else:
            angle = 2 * math.pi / 3
            # Make sure we're rotating such that we move away from the origin,
            # to discourage overlap of functional groups
            rot1 = numpy.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]], numpy.float64)
            rot2 = numpy.array([[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]], numpy.float64)
            vector1 = coordinates[index1,:] + numpy.dot(rot1, vector)
            vector2 = coordinates[index1,:] + numpy.dot(rot2, vector)
            if numpy.linalg.norm(vector1) < numpy.linalg.norm(vector2):
                angle = -angle
    else:
        angle = 2 * math.pi / numBonds
    rot = numpy.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]], numpy.float64)

    # Iterate through each neighboring atom to this backbone atom
    # If the neighbor is not in the backbone, then we need to determine
    # coordinates for it
    for atom, bond in bonds[atom1].iteritems():
        if atom is not atom0:
            occupied = True; count = 0
            # Rotate vector until we find an unoccupied location
            while occupied and count < len(bonds[atom1]):
                count += 1; occupied = False
                vector = numpy.dot(rot, vector)
                for atom2 in bonds[atom1]:
                    index2 = atoms.index(atom2)
                    if numpy.linalg.norm(coordinates[index2,:] - coordinates[index1,:] - vector) < 1e-4:
                        occupied = True
            coordinates[atoms.index(atom),:] = coordinates[index1,:] + vector

            # Recursively continue with functional group
            processFunctionalGroup(atom1, atom, atoms, bonds, coordinates)

################################################################################

def drawMolecule(chemGraph, fstr=''):
    """
    Primary function for generating a drawing of a :class:`ChemGraph` object
    `chemGraph`. The parameter `fstr` is the name of a file to save the drawing
    to; valid file extensions are ``.pdf``, ``.svg``, and ``.ps``.
    """

    atoms = chemGraph.atoms[:]
    bonds = chemGraph.bonds.copy()

    # Special cases: H, H2, anything with one heavy atom

    # Remove all unlabeled hydrogen atoms from the molecule, as they are not drawn
    atomsToRemove = []
    for atom in atoms:
        if atom.isHydrogen() and atom.label == '': atomsToRemove.append(atom)
    for atom in atomsToRemove:
        atoms.remove(atom)
    for atom in bonds:
        if atom not in atoms: del bonds[atom]
        for atom2 in bonds[atom]:
            if atom2 not in atoms: del bonds[atom][atom2]

    # Generate the coordinates to use to draw the molecule
    coordinates = generateCoordinates(chemGraph, atoms, bonds)

    # Generate labels to use
    symbols = [atom.symbol for atom in atoms]
    for i in range(len(symbols)):
        # Don't label carbon atoms
        if symbols[i] == 'C':
            if len(bonds[atoms[i]]) > 1 or (atoms[i].radicalElectrons == 0 and atoms[i].charge == 0):
                symbols[i] = ''
    # Do label atoms that have only double bonds to one or more labeled atoms
    changed = True
    while changed:
        changed = False
        for i in range(len(symbols)):
            if symbols[i] == '' and all([(bond.isDouble() or bond.isTriple()) for bond in bonds[atoms[i]].values()]) and any([symbols[atoms.index(atom)] != '' for atom in bonds[atoms[i]]]):
                symbols[i] = atoms[i].symbol
                changed = True
    # Add implicit hydrogens
    for i in range(len(symbols)):
        if symbols[i] != '':
            if atoms[i].implicitHydrogens == 1: symbols[i] = symbols[i] + 'H'
            elif atoms[i].implicitHydrogens > 1: symbols[i] = symbols[i] + 'H%i' % (atoms[i].implicitHydrogens)

    # Render using Cairo
    render(atoms, bonds, coordinates, symbols, fstr)

################################################################################

if __name__ == '__main__':

    molecule = Molecule()

    # Test #1: Straight chain backbone, no functional groups
    #molecule.fromSMILES('C=CC=CCC') # 1,3-hexadiene

    # Test #2: Straight chain backbone, small functional groups
    #molecule.fromSMILES('OCC(O)C(O)C(O)C(O)C(=O)') # glucose

    # Test #3: Straight chain backbone, large functional groups
    #molecule.fromSMILES('CCCCCCCCC(CCCC(CCC)(CCC)CCC)CCCCCCCCC')

    # Test #4: For improved rendering
    # Double bond test #1
    #molecule.fromSMILES('C=CCC=CC(=C)C(=C)C(=O)CC')
    # Double bond test #2
    #molecule.fromSMILES('C=C=O')
    # Radicals
    molecule.fromSMILES('[O][CH][C]([O])[C]([O])[CH][O]')
    
    # Test #5: Cyclic backbone, no functional groups
    #molecule.fromSMILES('c1ccc2ccccc2c1') # naphthalene

    #molecule.fromSMILES('C=CC(C)(C)CCC')
    #molecule.fromSMILES('CCC(C)CCC(CCC)C')
    #molecule.fromSMILES('C=CC(C)=CCC')
    #molecule.fromSMILES('COC(C)(C)C(C)(C)N(C)C')
    #molecule.fromSMILES('CCC=C=CCCC')
    #molecule.fromSMILES('C1CCCCC1CCC2CCCC2')

    drawMolecule(molecule.resonanceForms[0], 'molecule.svg')

