#!/usr/bin/env python

from __future__ import print_function

import argparse
import re
import sys

# Local imports

import item
import rollers

#
# Constants

# File names

FILE_SETTLEMENTS = 't_settlements'

# Tables

TABLE_SETTLEMENTS = {}

# Maps the parameter specification of a settlement to its string for table
# lookups.  The keys are lower case so that a case insensitive lookup can be
# done by calling tolower() before doing the lookup.  It's not a perfect
# case insensitive search according to high Unicode standards, but it's good
# enough for our needs.  The value string is compared against the settlement
# itemization table file, so the string must match exactly, case included.
SETTLEMENT_MAP = {
        'thorp': 'Thorp',
        'hamlet': 'Hamlet',
        'village': 'Village',
        'small-town': 'Small Town',
        'small town': 'Small Town',
        'smalltown': 'Small Town',
        'large-town': 'Large Town',
        'large town': 'Large Town',
        'largetown': 'Large Town',
        'small-city': 'Small City',
        'small city': 'Small City',
        'smallcity': 'Small City',
        'large-city': 'Large City',
        'large city': 'Large City',
        'largecity': 'Large City',
        'metropolis': 'Metropolis' }


#
# Functions

def load_settlements(filename):
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


def generate_settlement_items(settlement, roller):
    # Convert the command-line parameter to a dict key string.
    try:
        key = SETTLEMENT_MAP[settlement.lower()]
    except KeyError:
        print('Internal program error!')
        return
    # Print some information for reference.
    print('Generating magic items for a ' + key + ':')
    print('-' * 78)

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
                print_random_items('minor', roller, settlement_base)
        print()

    # Generate the medium magic items.
    if count_medium > 0:
        print('Medium Magic Items:')
        print('--------------------')
        for i in range(count_medium):
            print_random_items('medium', roller, settlement_base)
        print()

    # Generate the major magic items.
    if count_major > 0:
        print('Major Magic Items:')
        print('--------------------')
        for i in range(count_major):
            print_random_items('major', roller, settlement_base)


def generate_item(description, roller):
    print('Random ' + description + ':')
    # Generate an item
    # TODO Note: This is for debugging.  Remove the loop!
    for i in range(10):
        x = item.generate_item(description, roller)
        print(x)


def print_random_items(strength, roller, base_value):
    # Generate a generic item
    x = item.generate_generic(strength, roller, base_value)
    print(x)


#
# Execution

if __name__ == '__main__':

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(description='Generates magic items ' +
            ' for Pathfinder')

    # Type of generation
    group = parser.add_mutually_exclusive_group(required=True)

    # Generate items for a settlement
    group.add_argument('--settlement', '-s',
            choices=SETTLEMENT_MAP.keys(), type=str,
            help='The settlement size, using the values from the core ' +
            'rulebook')

    # Generate a specific class of item
    group.add_argument('--item', '-i',
            help='Item strength [lesser|greater] (minor|medium|major) ' +
            'and type of item (armor-and-shield, weapon, etc.).  Ex: ' +
            '--item="lesser minor Armor or Shield"')

    # By default, the program will ask for manual roll results.  This
    # result configures automatic rolls.
    parser.add_argument('--auto', '-a', action='store_true',
            help='Uses built-in rolling instead of prompting for rolls')

    # Error-checking
    #parser.add_argument('--check-errors', action='store_true',
    #        help='Instructs the program to check for errors in the item ' +
    #        'tables')

    # Go.
    args = parser.parse_args()

    # Load data files.
    load_settlements(FILE_SETTLEMENTS)

    # Set up the roller.
    if args.auto:
        roller = rollers.PseudorandomRoller()
    else:
        roller = rollers.ManualDiceRoller()

    # Check data for errors.
    #if args.check_errors:
    #    print('Checking for errors')

    # Process.
    if args.settlement:
        generate_settlement_items(args.settlement, roller)
    elif args.item:
        generate_item(args.item, roller)
