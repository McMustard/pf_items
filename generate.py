#!/usr/bin/env python
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
This module acts as the command line interface for the Pathfinder Item
Generator.
'''

from __future__ import print_function

import argparse
import re
import sqlite3 as sqlite
import sys

# Local imports

import item
import rollers
import settlements


#
# Functions

def test(conn, roller):
    strengths = ['least minor', 'lesser minor', 'greater minor',
            'lesser medium', 'greater medium', 'lesser major',
            'greater major']
    items = ['Armor/Shield', 'Weapon', 'Potion', 'Ring', 'Rod', 'Scroll',
            'Staff', 'Wand', 'Wondrous Item']
    for s in strengths:
        for i in items:
            print(s + ' ' + i)
            print('-' * 78)
            for c in range(1000):
                print(item.generate_item(s + ' ' + i, roller),end=', ')
            print()


def make_series(sequence):
    if len(sequence) == 0: return ''
    quoted = ['"' + value + '"' for value in sequence]
    quoted[-1] = 'and ' + quoted[-1]
    return ', '.join(quoted)


#
# Execution

# Parser subcommands

def run_generate_settlement(conn, args):
    # Set up the roller.
    if args.manual:
        roller = rollers.ManualDiceRoller()
    else:
        roller = rollers.PseudorandomRoller()
    # Generate items.
    settlements.generate_settlement_items(conn,
            ' '.join(args.settlement_type), roller)


def run_generate_item(conn, args):
    # Set up the roller.
    if args.manual:
        roller = rollers.ManualDiceRoller()
    else:
        roller = rollers.PseudorandomRoller()
    # Generate an item.
    #item.generate_item(conn, args.strength + ' TYPE', roller)
    # TODO type, parameters


def run_test(conn, args):
    print("run_test")
    # Use an automatic dice roller.
    roller = rollers.PseudorandomRoller()
    # Run a test.
    test(conn, roller)


if __name__ == '__main__':

    # Undocumented subcommmand.
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        run_test()
        sys.exit(0)

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(
            description='Generates magic items for Pathfinder')

    # Error-checking
    #parser.add_argument('--check-errors', action='store_true',
    #        help='Instructs the program to check for errors in the item ' +
    #        'tables')

    # Subcommands: type of generation
    subparsers = parser.add_subparsers()

    # Subcommand: settlement

    # Generate items for a settlement
    parser_settlement = subparsers.add_parser('settlement',
            help='Generates magic items for a settlement.')

    parser_settlement.add_argument('settlement_type',
            metavar='SETTLEMENT_TYPE', nargs='+',
            help='The settlement size: ' +
            make_series(settlements.get_keys()) )
    parser_settlement.set_defaults(func=run_generate_settlement)

    # Subcommand: one for each item type

    # Generate a specific class of item
    #parser_item = subparsers.add_parser('item')

    # Item type

    parser_item = subparsers.add_parser('item',
            help='Generate a random magic item')
    parser_item.set_defaults(func=run_generate_item)

    ## Item strength
    #parser_item.add_argument('--strength',
    #        required=True,
    #        help='The strength of the magic item: "lesser" or "greater", ' +
    #        'followed by "minor", "medium", or "major".  Slotless wondrous ' +
    #        'items can also be "least minor".')

    #parser_item.set_defaults(func=run_generate_item)

    ## Perform a simple die roll
    #parser_roll = subparsers.add_parser('roll',
    #        help='Performs a die roll according to a simple die expression,' +
    #        ' e.g. 2d4.')

    ## Test mode: dump out a whole bunch of items.
    #parser_test = subparsers.add_parser('test',
    #        help='Runs a test by generating many items.')

    ### More of an indicator that the group is finished than anything.
    ##group = None


    # Options common to several subparsers

    for sub in [parser_settlement, parser_item]:
        # By default, the program will roll automatically.  This option will
        # cause it to prompt, so dice rolls can be entered manually.
        sub.add_argument('--manual', '-m', action='store_true',
                help='Prompts for rolls rather than using the built-in ' +
                'roller')

    # Go.
    args = parser.parse_args()

    # Open the database.
    conn = None
    try:
        conn = sqlite.connect('data\\data.db')
        conn.row_factory = sqlite.Row
        args.func(conn, args)
    except sqlite.Error, e:
        print('Error: %s' % e.message)
        sys.exit(1)
    finally:
        if conn: conn.close()

