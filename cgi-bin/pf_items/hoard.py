#!/usr/bin/env python2
# vim: set fileencoding=utf-8

# Pathfinder Item Generator
#
# Copyright 2012-2014, Steven Clark.
#
# This program is free software, and is provided "as is", without warranty of
# any kind, express or implied, to the extent permitted by applicable law.
# See the full license in the file 'LICENSE'.
#
# This software includes Open Game Content.  See the file 'OGL' for more
# information.
#
'''
This module implements the various calculation stages of treasure hoard
generation.
'''

#
# Library imports

from __future__ import print_function

import locale
import math
import os
import random
import re
import sys
import traceback

#
# Local imports

import item
import rollers

#
# Module initialization

if os.name == 'posix':
    # An extremely recognizable locale string.
    locale.setlocale(locale.LC_ALL, 'en_US')
elif os.name == 'nt':
    # Windows doesn't use the sensible value.
    locale.setlocale(locale.LC_ALL, 'enu')
else:
    # My best guess for other OSes.
    try: locale.setlocale(locale.LC_ALL, 'en_US')
    except: pass


#
# Constants

# Lowest APL, inclusive, involved in UE formulas.
APL_LOW = 1

# Highest APL, inclusive, involved in UI formulas.
APL_HIGH = 20

# Rate of XP/treasure progression
RATES = {
        'slow': 'Slow',
        'medium': 'Medium',
        'fast': 'Fast'}


# Some monsters have more treasure than others. "None" is not in this list
# because the generator wouldn't be used if there was no treasure, and "NPC
# gear" isn't a simple multiplier, so it needs special treatment.
MAGNITUDES = {
        'incidental': 0.5,
        'standard': 1.0,
        'double': 2.0,
        'triple': 3.0,
        }


#
# Variables


#
# Functions

def calculate_budget_custom(conn, gp_in):
    # A simple reflection
    price = item.Price(gp_in)
    return {'budget': str(price), 'as_int': int(price.as_float())}


def calculate_budget_encounter(conn, apl, rate, magnitude):
    # Convert the parameters to usable values.
    try:
        rate = RATES[rate]
        magnitude = MAGNITUDES[magnitude]
    except:
        # Return an empty dict
        return {}

    # Look up the encounter.
    sql = 'SELECT {0} FROM {1} WHERE ("Average Party Level" = ?)'.format(
            rate, 'Treasure_Values_Per_Encounter')
    result = conn.execute(sql, (apl,))
    budget = result.fetchone()[0]
    price = item.Price(budget)
    price.multiply(magnitude)

    return {'budget': str(price), 'as_int': int(price.as_float())}


def calculate_budget_npc_gear(conn, npc_level, is_heroic):
    level = 0
    try:
        level = int(npc_level)
        if is_heroic: level += 1
    except:
        # Return an empty dict
        return {}

    # Look up the NPC info.
    sql = 'SELECT {0} FROM {1} WHERE ("Level" = ?)'.format(
            '"Treasure Value"', 'NPC_Gear')
    result = conn.execute(sql, (level,))
    budget = result.fetchone()[0]
    price = item.Price(budget)

    return {'budget': str(price), 'as_int': int(price.as_float())}


def lookup_treasure_type(conn, type_code, result):
    result[type_code] = []
    # Draft the entire table.
    sql = 'SELECT * FROM {0}'.format('Type_' + type_code.upper() + '_Treasure')
    i = 0
    for row in conn.execute(sql):
        cost = item.Price(row[0])
        result[type_code].append({
            'index': i, 'cost': int(cost.as_float()),
            'item': row[0], 'description': row[1],
            'count': 0})
        i += 1


def get_treasure_list(conn, types):
    result = {}
    for t in types:
        lookup_treasure_type(conn, t, result)
    return result


def generate_treasure_lot(conn, description, roller, listener):
    results = []
    exprs = [x.strip().lower() for x in description.split(', ')]
    for expr in exprs:
        x = item.generate_treasure_item(conn, expr, roller, listener)
        if x: results.extend(x)
    return results


def generate_treasure_type(conn, subspec, roller, listener):
    result = []
    for item in subspec:
        for i in range(item['count']):
            x = generate_treasure_lot(conn, item['description'],
                    roller, listener)
            if x: result.extend(x)
    return result


def generate_treasure(conn, requests, roller, listener):
    types = "abcdefghi"
    accum = []
    for tt in types:
        if tt not in requests: continue
        # Get proper descriptions from the database.
        table = {}
        lookup_treasure_type(conn, tt, table)
        descriptions = table[tt]
        # Stop at 100 items
        remaining = 100
        # Get the submitted counts.
        for item in requests[tt]:
            i = item['index']
            c = item['count']
            c = min(remaining, c)
            remaining -= c
            descriptions[i]['count'] = c
            if c <= 0: break
        treas = generate_treasure_type(conn, descriptions, roller, listener)
        accum.extend(treas)
    return accum

#
# Main Function

if __name__ == '__main__':
    pass

