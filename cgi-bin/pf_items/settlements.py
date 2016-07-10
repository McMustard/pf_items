#!/usr/bin/env python3.3
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
This module performs tasks related to settlement item generation.
'''


#
# Standard Imports

import sqlite3 as sqlite
import sys
import traceback


#
# Local imports

import item
import rollers


#
# Constants

# The keys in these dictionaries are lower case so that a case insensitive
# lookup can be done by calling tolower() before doing the lookup.  It's not a
# perfect case insensitive search according to high Unicode standards, but
# it's good enough for our needs.  The value string is compared against the
# settlement itemization table file, so the string must match exactly, case
# included.

# Maps the parameter specification of a settlement to its standardized value.

SETTLEMENT_MAP = {
        'thorp'     : 'Thorp',
        'hamlet'    : 'Hamlet',
        'village'   : 'Village',
        'small-town': 'Small Town',
        'small town': 'Small Town',
        'smalltown' : 'Small Town',
        'large-town': 'Large Town',
        'large town': 'Large Town',
        'largetown' : 'Large Town',
        'small-city': 'Small City',
        'small city': 'Small City',
        'smallcity' : 'Small City',
        'large-city': 'Large City',
        'large city': 'Large City',
        'largecity' : 'Large City',
        'metropolis': 'Metropolis' }


#
# Classes

#
# Functions

def get_keys():
    return sorted(SETTLEMENT_MAP.keys())


def generate_settlement_items(conn, settlement, roller, **kwargs):

    # Create a result in a type that can be serialized into JSON.
    result = {}

    list_rolls = kwargs.get('list_rolls', '')

    # Convert the command-line parameter to a dict key string.
    try:
        key = SETTLEMENT_MAP[settlement.lower()]
    except KeyError:
        raise Exception('no such settlement type: ' + settlement)

    # Start rolling!

    # Get the key settlement attributes from the DB.
    cursor = conn.execute('''SELECT * FROM Settlements WHERE (Size = ?);''',
            (key,))
    row = cursor.fetchone()
    if row == None:
        raise Exception('failed to acquire settlement details')

    # Collect details for generation.
    settlement_base = row['Base']
    expr_minor = row['Minor']
    expr_medium = row['Medium']
    expr_major = row['Major']

    # Set up the result
    result['base_value'] = settlement_base
    result['minor_heading'] = ""
    result['medium_heading'] = ""
    result['major_heading'] = ""
    result['minor_items'] = []
    result['medium_items'] = []
    result['major_items'] = []

    # It's easier on the user (if the user is rolling) to roll like-dice
    # first.  Go through the gauntlet.
    count_minor = 0
    if expr_minor != '*':
        count_minor = roller.roll(expr_minor, 'number of minor items')
    count_medium = roller.roll(expr_medium, 'number of medium items')
    count_major = roller.roll(expr_major, 'number of major items')

    # Generate the minor magic items.  Remember we can get a '*' in a
    # metropolis.
    if count_minor > 0 or expr_minor == '*':
        if expr_minor == '*':
            result['minor_heading'] = 'This ' + key.lower() + \
                    ' has virtually every minor magic item.'
        else:
            for i in range(count_minor):
                x = get_random_item(conn, 'minor', roller, settlement_base)
                result['minor_items'].append(x.get_dict())

    # Generate the medium magic items.
    if count_medium > 0:
        for i in range(count_medium):
            x = get_random_item(conn, 'medium', roller, settlement_base)
            result['medium_items'].append(x.get_dict())

    # Generate the major magic items.
    if count_major > 0:
        for i in range(count_major):
            x = get_random_item(conn, 'major', roller, settlement_base)
            result['major_items'].append(x.get_dict())

    # Return the resulting collection.
    return result


def generate_custom(conn, base_value, q_ls_min, q_gt_min, q_ls_med, q_gt_med, q_ls_maj, q_gt_maj):
    # Easy peasy.
    result = {}
    result['minor_heading'] = ''
    result['medium_heading'] = ''
    result['major_heading'] = ''
    result['minor_items'] = []
    result['medium_items'] = []
    result['major_items'] = []

    # Note: 'x' is not an Item, but a string.
    for i in range(rollers.roll_form(q_ls_min)):
        x = item.fast_generate(conn, 'lesser minor', base_value)
        result['minor_items'].append(x.get_dict())
    for i in range(rollers.roll_form(q_gt_min)):
        x = item.fast_generate(conn, 'greater minor', base_value)
        result['minor_items'].append(x.get_dict())
    for i in range(rollers.roll_form(q_ls_med)):
        x = item.fast_generate(conn, 'lesser medium', base_value)
        result['medium_items'].append(x.get_dict())
    for i in range(rollers.roll_form(q_gt_med)):
        x = item.fast_generate(conn, 'greater medium', base_value)
        result['medium_items'].append(x.get_dict())
    for i in range(rollers.roll_form(q_ls_maj)):
        x = item.fast_generate(conn, 'lesser major', base_value)
        result['major_items'].append(x.get_dict())
    for i in range(rollers.roll_form(q_gt_maj)):
        x = item.fast_generate(conn, 'greater major', base_value)
        result['major_items'].append(x.get_dict())

    # Return the resulting collection.
    return result


def get_random_item(conn, strength, roller, base_value):
    x = item.generate_generic(conn, strength, roller, base_value)
    return x


#
# Execution

if __name__ == '__main__':
    # TODO testing code
    pass
