#!/usr/bin/env python3.3
# vim: set fileencoding=utf-8

# Pathfinder Item Generator
#
# Copyright 2012-2013, Steven Clark.
#
# This program is free software, and is provided "as is", without warranty of
# any kind, express or implied, to the extent permitted by applicable law.
# See the full license in the file 'LICENSE'.
#
# This software includes Open Game Content.  See the file 'OGL' for more
# information.
#
'''
This module reads the table-based item database, and constructs another
database, which enumerates all possible magic items, along with their
probabilities.  This method is very slow, but very rigorous, and exercises
the standard item generation methods, and can act as a test.
'''

#
# Standard imports

from __future__ import print_function

import argparse
import os
import sqlite3 as sqlite
import sys
import traceback


#
# Local imports

import item
import rollers


#
# Constants

STANDARD_STRENGTHS = ['lesser minor', 'greater minor', 'lesser medium',
        'greater medium', 'lesser major', 'greater major']
EXPANDED_STRENGTHS = ['least minor', 'lesser minor', 'greater minor',
        'lesser medium', 'greater medium', 'lesser major', 'greater major']


#
# Global Variables

ENABLE_SKIPPING = False
PRINT_ROLLS = False
OUTPUT_PREFIX = 'enum'


#
# Classes

class EnumerationsComplete(Exception):
    pass

# This roller does not roll random at all.  Instead, it gives out sequential
# values, so that everything can be enumerated.
class EnumeratingRoller(rollers.Roller):

    def __init__(self):
        self.current = {}
        self.purposes1 = []
        self.purposes2 = []
        self.stage = 1
        self.last_purpose = None
        self.rightmost_purpose = None
        self.rolls = {}

    def begin_item(self):
        self.rolls = {}

    def end_item(self):
        pass

    def item_rolled(self, purpose, range_low, range_high, strength):
        if purpose not in self.rolls or range_high > self.rolls[purpose][1]:
            self.rolls[purpose] = (range_low, range_high, strength)

    def do_skip(self):
        if not ENABLE_SKIPPING:
            return 1
        multiplier = 1
        for purpose in self.purposes1:
            try:
                low, high, strength = self.rolls[purpose]
                span = high - low + 1
                multiplier = multiplier * span
                self.current[purpose]['value'] = high
            except KeyError as ex:
                # Simply omit it from the calculation. If there was no value,
                # it's not important.
                pass
        self.rolls = {}
        return multiplier

    def roll(self, dice_expression, purpose):
        # If this purpose has not been used yet, set it up.
        if purpose not in self.current.keys():
            # Determine the maximum on the die.
            # If there is more than one die, probability-wise, the resulting
            # sequence won't generate a list of items in the probability they
            # would be generated with random rolls, but that'll be okay, since
            # we'll be using this for 1d100s.  If that ever turns out not to
            # be true, this idea will still work, but it'll have to be changed
            # to generate higher probability numbers multiple times.
            (number, sides) = rollers.parseDiceExpression(dice_expression)
            # Set the current value to 0, so we can increment then return.
            self.current[purpose] = {'max': number * sides,
                    'value': 1}

        # States:
        # Round 1: initial values
        # Round 2: confirmation pass
        # Round 3: clear and increment based on round 2 values

        # Check state transitions.
        if self.stage == 1:
            # We advance to state 2 when the purpose is an old one, but not
            # most recent one.
            if purpose in self.purposes1 and purpose != self.last_purpose:
                self.stage = 2
                self.rightmost_purpose = self.last_purpose
        elif self.stage == 2:
            # We advance to state 3 like 1 to 2.
            if purpose in self.purposes2 and purpose != self.last_purpose:
                self.stage = 3

        # If we're repeating the last request, increment it.
        if purpose == self.last_purpose:
            if self.increment():
                raise EnumerationsComplete

        # Note the last purpose.
        self.last_purpose = purpose

        # Handle the state.
        if self.stage == 1:
            # This is the first pass.
            if purpose not in self.purposes1:
                self.purposes1.append(purpose)
        elif self.stage >= 2 and purpose == self.last_purpose:
            # Increment
            if self.increment():
                raise EnumerationsComplete
            # Restart purposes not in the list.
            for key in self.current.keys():
                if key not in self.purposes1:
                    self.current[key]['value'] = 1
            # Clear the purpose tracking lists.
            self.purposes1 = []
            self.purposes2 = []
            # Since stage 3 is effectively a preemptive 1, make it look like
            # the first part of a new 1 occurred.
            self.purposes1.append(purpose)
            self.stage = 1
            self.last_purpose = None
        return self.current[purpose]['value']

    def increment(self):
        # Increment according to the reverse of the purpose lists.
        for digit in reversed(self.purposes1):
            # Increment the purpose current value.
            self.current[digit]['value'] += 1
            value = self.current[digit]['value']
            # If the purpose value rolls over
            if value > self.current[digit]['max']:
                # Start it over at zero and let the loop continue.
                self.current[digit]['value'] = 1
            else:
                # We were able to increment without carrying.
                # This needs to happen just once somewhere.
                return False
        # We incremeneted all the way past the end.
        return True

#
# Functions

def prep_table(cursor, table):
    # Create the table.
    sql = 'CREATE TABLE {0} (Count INTEGER, Kind TEXT, Subtype TEXT, Item TEXT, Price REAL);'.format(table)
    cursor.execute(sql)


def enumerate_item(conn_in, conn_out, strengths, item_key, file_prefix):
    # Roll up items
    for strength in strengths:
        print('Analyzing', strength, item_key)
        roller = EnumeratingRoller()

        # Set up the output file or table name.
        filename = file_prefix + '_' + strength
        filename = filename.replace(' ', '_')
        filepath = OUTPUT_PREFIX + '/' + filename
        f_rollfile = None

        if conn_out == None:
            f_rollfile = open(filepath + '.rolls', 'w')

        # Collect items to count.
        items = {}
        # Roll items
        while True:
            try:
                # Notify the roller it's about to roll a single item.
                roller.begin_item()
                # Roll the item.
                x = item.generate_specific_item(conn_in, strength, item_key,
                        roller, roller)
                # Done rolling an item.
                roller.end_item()
                # Allow the roller to increment based on its saved values.
                count = roller.do_skip()
                # Get the rolls.
                roll = item.rolls_str(x)
                if PRINT_ROLLS:
                    if f_rollfile:
                        print(      roll + '           \n', end='', file=f_rollfile)
                    print(' ' + roll + '           \r', end='')
                # Store the item quantity.
                item_str = item.item_str(x)
                if item_str in items.keys():
                    items[item_str]['count'] += count
                else:
                    items[item_str] = {'count': count, 'item': x}
            except EnumerationsComplete:
                # Done!
                break

        cursor = None
        f_out = None
        if conn_out:
            cursor = conn_out.cursor()
            # The filename serves as a table name.
            prep_table(cursor, filename)
        else:
            f_out = open(filepath + '.txt', 'w')

        # Output the results.
        total = 0
        sql = 'INSERT INTO {0} VALUES (?,?,?,?,?)'.format(filename)
        for item_str in items.keys():
            xdict = items[item_str]
            count = xdict['count']
            x = xdict['item']
            total += count

            if cursor:
                # Do not include bad items in the database file.
                if not x.is_bad():
                    # count, kind, subtype, label, cost
                    cursor.execute(sql, (count, x.kind, x.subtype, x.label, \
                        x.price.as_float()) )
            else:
                # Text mode is for inspection, so include bad items.
                if x.is_bad:
                    print(items[item_str], item_str, 'invalid', sep='\t', file=f_out)
                else:
                    print(items[item_str], item_str, 'valid', sep='\t', file=f_out)

        print('    contained', total, 'items')

        # Close files.
        if f_out:
            f_out.close();
        if f_rollfile:
            f_rollfile.close()
        if conn_out:
            conn_out.commit()


def build_enum_table(conn_in, conn_out):

    # Create the output directory.
    try:
        os.mkdir(OUTPUT_PREFIX)
    except FileExistsError:
        pass
    
    # Enumerate items for each class.
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'armor/shield', 'armor')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'weapon', 'weapon')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'potion', 'potion')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'ring', 'ring')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'rod', 'rod')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'scroll', 'scroll')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'staff', 'staff')
    enumerate_item(conn_in, conn_out,
            STANDARD_STRENGTHS, 'wand', 'wand')
    enumerate_item(conn_in, conn_out,
            EXPANDED_STRENGTHS, 'wondrous', 'wondrous')

    # If database, commit.
    if conn_out:
        conn_out.commit()


def initialize_database(database_file):
    conn = None
    successful = False
    try:
        # Open the database file.
        conn = sqlite.connect(database_file)
        conn.row_factory = sqlite.Row
        successful = True
    except sqlite.Error as e:
        # Print an error and exit.
        print('Error: %s' % e.message)
        sys.exit(1)
    finally:
        if not successful and conn:
            conn.close()
    return conn


def run_program(args):
    '''Does the "real" work of __main__.'''

    # Put the item generator in enumeration mode.
    item.set_enumeration()

    # Flags for the file/directory string.
    n_cache = 0
    n_skip = 0
    n_print_rolls = 0

    # Set the options.
    if args.cache:
        item.enable_caching(args.cache)
        n_cache = args.cache
    if args.skip:
        global ENABLE_SKIPPING
        ENABLE_SKIPPING = True
        n_skip = 1
    if args.print_rolls:
        global PRINT_ROLLS
        PRINT_ROLLS = True
        n_print_rolls = 1

    # Set the prefix.
    global OUTPUT_PREFIX
    if args.prefix:
        OUTPUT_PREFIX = args.prefix
    OUTPUT_PREFIX = OUTPUT_PREFIX + '_c{0}_s{1}_r{2}'.format(n_cache, n_skip, n_print_rolls)

    # If the output is a database, set it up.
    conn_out = None
    if args.database:
        # Remove the existing database file.
        db_filename = OUTPUT_PREFIX + '.db'
        if os.path.isfile(db_filename):
            os.remove(db_filename)
        conn_out = initialize_database(db_filename)
        if not conn_out:
            print("Unable to initialize output database!")
            sys.exit(1)

    # Initialize the INPUT database.
    conn_in = initialize_database(args.database_in)

    # Build the enumeration table!
    build_enum_table(conn_in, conn_out)


#
# Main

if __name__ == '__main__':

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(
            description='Initializes databases from text files')

    # Positional Arguments:
    
    # Item database name.
    parser.add_argument('database_in', metavar='INPUT_DATABASE',
            help='The database name')

    # Optional Arguments:

    # Specifies a different file or directory prefix, rather than 'enum'.
    parser.add_argument('--prefix', '-p',
            help='Output file or directory prefix (default "enum")')

    # Specifies to output to a database file rather than a directory.
    parser.add_argument('--database', '-d', action='store_true',
            help='Output to a database file instead of a directory')

    # Whether to use a cache, and the type (a number).
    # The number is meaningful in item.py.
    parser.add_argument('--cache', type=int,
            help='The type of cache to use')

    # Whether to save time by skipping rolls according to a heuristic.
    parser.add_argument('--skip', action='store_true',
            help='Skip rolls that would repeat previous return')

    # Whether to print the rolls as items are generated (as a kind of progress
    # report.
    parser.add_argument('--print-rolls', '-r', action='store_true',
            help='Prints rolls')

    # Go.
    args = parser.parse_args()
    run_program(args)

