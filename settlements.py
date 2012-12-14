#!/usr/bin/env python3
# vim: set fileencoding=utf-8

# Pathfinder Item Generator
#
# Copyright 2012, Steven Clark.
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

import re
import sqlite3 as sqlite
import sys
import traceback

#
# Local imports

import item
import rollers

#
# Constants

# File names

FILE_SETTLEMENTS = 't_settlements'

# Tables

# Table as a dictionary from settlement type to attributes of that settlement
# type for magic item generation.

TABLE_SETTLEMENTS = {}

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
# Functions

def get_keys():
    return sorted(SETTLEMENT_MAP.keys())


def load_settlements():
    f = open(FILE_SETTLEMENTS, 'r')
    # Throw away the first two lines, headers.
    f.readline()
    f.readline()
    # Now read the remaining lines.
    for line in f:
        if line.startswith('#'): continue
        data = line[:-1].split('\t')
        TABLE_SETTLEMENTS[data[0]] = {
                'base': data[1],
                'minor': data[2],
                'medium': data[3],
                'major': data[4] }
    f.close()


def parse_range(value):
    if value == '-':
        return (0, 0)
    if '-' in value:
        strs = value.split('-')
        return (int(strs[0]), int(strs[1]))
    return (int(value), int(value))


def lookup_item(table, strength, kind, roll):
    for row in table[kind]:
        if roll >= row[strength][0] and roll <= row[strength][1]:
                return (row['item'], row['subtype'])
    print('ERROR: No result for', strength, kind, str(roll))
    return (strength + ' ' + kind + '(' + str(roll) + ')', '')


def generate_settlement_items(conn, settlement, roller):
    # Convert the command-line parameter to a dict key string.
    try:
        key = SETTLEMENT_MAP[settlement.lower()]
    except KeyError:
        print('No such settlement type:', settlement)
        return
    # Print some information for reference.
    print('Generating magic items for a ' + key + ':')
    print('-' * 78)

    # Start rolling!

    # Get the key settlement attributes from the DB.
    cursor = conn.execute('''SELECT * FROM Settlements WHERE (Size = ?);''',
            (key,))
    result = cursor.fetchone()
    if result == None:
        raise Exception('failed to acquire settlement details')
    settlement_base = result['Base']
    expr_minor = result['Minor']
    expr_medium = result['Medium']
    expr_major = result['Major']

    print('Base value:', settlement_base, ' gp')
    print()

    # It's easier on the user (if the user is rolling) to roll like-dice
    # first.  Go through the gauntlet.
    count_minor = 0
    if expr_minor != '*':
        count_minor = roller.roll(expr_minor)
    count_medium = roller.roll(expr_medium)
    count_major = roller.roll(expr_major)

    # Generate the minor magic items.  Remember we can get a '*' in a
    # metropolis.
    if count_minor > 0 or expr_minor == '*':
        print('Minor Magic Items:')
        print('--------------------')
        if expr_minor == '*':
            print('This ' + key + ' has virtually every minor magic item.')
        else:
            for i in range(count_minor):
                print_random_item(conn, 'minor', roller, settlement_base)
        print()

    # Generate the medium magic items.
    if count_medium > 0:
        print('Medium Magic Items:')
        print('--------------------')
        for i in range(count_medium):
            print_random_item(conn, 'medium', roller, settlement_base)
        print()

    # Generate the major magic items.
    if count_major > 0:
        print('Major Magic Items:')
        print('--------------------')
        for i in range(count_major):
            print_random_item(conn, 'major', roller, settlement_base)


def print_random_item(conn, strength, roller, base_value):
    # Generate a generic item
    try:
        # This should simplify the nesting and logic a little, for retries.
        retry = False
        # Get an item.
        x = item.generate_generic(conn, strength, roller, base_value)
        # We may need to try some substitutions. A known issue is with the
        # Windows console, which uses CP437, not UTF-8.
        try:
            print(x)
        except UnicodeEncodeError as ex:
            retry = True

        if retry:
            s = str(x)
            s = s.replace('\u2019', "'")
            try:
                print(s)
            except:
                print('Error: Unable to print item ({0}).'.format(x.type()))
                traceback.print_exc(file=sys.stdout)
    except:
        traceback.print_exc(file=sys.stdout)

#
# Execution

if __name__ == '__main__':
    # TODO testing code
    pass
