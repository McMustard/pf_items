#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys

import rollers

#
# Constants

# File names

FILE_SETTLEMENTS = 't_settlements'
FILE_ITEMTYPES = 't_itemtypes'
FILE_CRB = 't_corerulebook'
FILE_APG = 't_advancedplayersguide'

# Tables

TABLE_SETTLEMENTS = {}
TABLE_TYPES_MINOR = []
TABLE_TYPES_MEDIUM = []
TABLE_TYPES_MAJOR = []
TABLE_CRB = {}
TABLE_APG = {}

# Maps the parameter specification of a settlement to its string for table
# lookups.
SETTLEMENT_MAP = {
        'thorp': 'Thorp',
        'hamlet': 'Hamlet',
        'village': 'Village',
        'small-town': 'Small Town',
        'large-town': 'Large Town',
        'small-city': 'Small City',
        'large-city': 'Large City',
        'metropolis': 'Metropolis' }

#
# Functions

def loadSettlements(filename):
    f = open(filename, 'r')
    # Throw away the first line, a header.
    f.readline()
    # Now read the remaining lines.
    for line in f:
        data = line[:-1].split('\t')
        TABLE_SETTLEMENTS[data[0]] = {
                'base': data[1],
                'minor': data[2],
                'medium': data[3],
                'major': data[4] }
    f.close()


def loadItemTypes(filename):
    f = open(filename, 'r')
    # Throw away the first line, a header.
    f.readline()
    # Now read the remaining lines.
    for line in f:
        data = line[:-1].split('\t')
        TABLE_TYPES_MINOR.append ({'min': int(data[1]), 'max': int(data[2]),
            'type': data[0]})
        TABLE_TYPES_MEDIUM.append({'min': int(data[3]), 'max': int(data[4]),
            'type': data[0]})
        TABLE_TYPES_MAJOR.append ({'min': int(data[5]), 'max': int(data[6]),
            'type': data[0]})
    f.close()


def loadItemFile(filename, table):
    f = open(filename, 'r')
    # Throw away the first line, a header.
    f.readline()
    # Now read the remaining lines.
    for line in f:
        data = line[:-1].split('\t')
        if data[0] not in table:
            table[data[0]] = []
        table[data[0]].append({'subtype': data[1], 'item': data[2],
            'minor_min' : int(data[3]), 'minor_max' : int(data[4]),
            'medium_min': int(data[5]), 'medium_max': int(data[6]),
            'major_min' : int(data[7]), 'major_max' : int(data[8])})


def lookupItem(table, strength, kind, roll):
    key_min = strength + '_min'
    key_max = strength + '_max'
    for row in table[kind]:
        if roll >= row[key_min] and roll <= row[key_max]:
                return (row['item'], row['subtype'])
    print('ERROR: No result for', strength, kind, str(roll))
    return (strength + ' ' + kind + '(' + str(roll) + ')', '')


def generateItems(settlement, roller):
    # Convert the command-line parameter to a dict key string.
    try:
        key = SETTLEMENT_MAP[settlement]
    except KeyError:
        print('Internal program error!')
        return
    # Print some information for reference.
    print('Generating magic items for a ' + key + ':')
    print('--------------------')

    # Start rolling!

    # It'll be useful to print the base value of the settlement.
    settlement_base = TABLE_SETTLEMENTS[key]['base']
    print('Base value: ' + settlement_base + ' gp')
    print()

    # Get the dice expressions.
    expr_minor = TABLE_SETTLEMENTS[key]['minor']
    expr_medium = TABLE_SETTLEMENTS[key]['medium']
    expr_major = TABLE_SETTLEMENTS[key]['major']

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
                printRandomItems('minor', roller)
        print()

    # Generate the medium magic items.
    if count_medium > 0:
        print('Medium Magic Items:')
        print('--------------------')
        for i in range(count_medium):
            printRandomItems('medium', roller)
        print()

    # Generate the major magic items.
    if count_major > 0:
        print('Major Magic Items:')
        print('--------------------')
        for i in range(count_major):
            printRandomItems('major', roller)


def printRandomItems(strength, roller):
    # First, determine the type of item.
    roll = roller.roll('1d100')
    kind = getItemType(strength, roll)
    # Now, generate an item of that type.
    print(generateItem(strength, kind, roller))


def getItemType(strength, roll):
    # Select the appropriate table.
    table = None
    if strength == 'minor':
        table = TABLE_TYPES_MINOR
    elif strength == 'medium':
        table = TABLE_TYPES_MEDIUM
    elif strength == 'major':
        table = TABLE_TYPES_MAJOR
    # Look for the roll among the mins and maxes.
    if table != None:
        for row in table:
            if roll >= row['min'] and roll <= row['max']:
                return row['type']
    return ''


def generateItem(strength, kind, roller):
    # Roll for the item.
    roll = roller.roll('1d100')
    # Look up an item
    # TODO incorporate APG by looking up a weight and another d100
    (item, subtype) = lookupItem(TABLE_CRB, strength, kind, roll)
    specials = ''

    # Check for starred items.  This requires another check.
    if item[-1] == '*':
        # The item name tells us what we need to roll.
        nextKind = item[:-1]
        roll = roller.roll('1d100')
        (item, subtype) = lookupItem(TABLE_CRB, strength, nextKind, roll)

    while item == 'ADD SPECIAL, ROLL AGAIN':
        # Look up a new item so we know what subtype to seek out.
        roll = roller.roll('1d100')
        (item, subtype) = lookupItem(TABLE_CRB, strength, kind, roll)
        if item != 'ADD SPECIAL, ROLL AGAIN':
            if subtype == '':
                print('ERROR!  No subtype for ' + item)
                return ''
            # Roll up a special.
            roll = roller.roll('1d100')
            specials = generateSpecials(strength,
                subtype + ' Special Ability', roller)
    # TODO Spells in Potions, Scrolls, Wands
    if len(specials) > 0:
        item = item + ', ' + specials
    return item


def generateSpecials(strength, kind, roller):
    # If the weapon special ability is not specific enough, pick something.
    if kind == 'Weapon Special Ability':
        roll = roller.roll('1d100')
        if roll <= 50:
            kind = 'Melee ' + kind
        else:
            kind = 'Ranged ' + kind
    # Collect some specials.
    specials = []
    # Go.
    roll = roller.roll('1d100')
    special = lookupItem(TABLE_CRB, strength, kind, roll)[0]
    if special[-1] == '*':
        # Roll for the specific special.
        roll = roller.roll('1d100')
        special = special[:-1] + ':' + \
                lookupItem(TABLE_CRB, strength, kind, roll)[0]

    # Generate more as needed.
    if special == 'ROLL TWICE':
        specials.extend(generateSpecials(strength, kind, roller))
        specials.extend(generateSpecials(strength, kind, roller))
    else:
        specials.append(special)

    # Put everything in one string and return it.
    return '/'.join(specials)


#
# Execution

if __name__ == '__main__':

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(description='Generates magic items for' +
            ' Pathfinder')

    # The only mandatory argument is settlement type.
    parser.add_argument('settlement', metavar='SETTLEMENT', 
            choices=SETTLEMENT_MAP.keys(), type=str,
            help='Settlement type (' + ', '.join(SETTLEMENT_MAP.keys()) + ')')

    # By default, the program will ask for manual roll results.  This
    # result configures automatic rolls.
    parser.add_argument('--auto', '-a', action='store_true',
            help='Uses built-in rolling instead of prompting for rolls')

    # Error-checking
    parser.add_argument('--check-errors', action='store_true',
            help='Instructs the program to check for errors in the item ' +
            'tables')

    # Go.
    args = parser.parse_args()

    # Load data files.
    loadSettlements(FILE_SETTLEMENTS)
    loadItemTypes(FILE_ITEMTYPES)
    loadItemFile(FILE_CRB, TABLE_CRB)
    loadItemFile(FILE_APG, TABLE_APG)

    # Set up the roller.
    if args.auto:
        roller = rollers.PseudorandomRoller()
    else:
        roller = rollers.ManualDiceRoller()

    # Check data for errors.
    if args.check_errors:
        print('Checking for errors')

    # Process.
    generateItems(args.settlement, roller)
