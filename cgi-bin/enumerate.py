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

# Ultimate Equipment Tables

TABLE_MAGIC_ARMOR_AND_SHIELDS         = 'Magic_Armor_and_Shields'
TABLE_MAGIC_WEAPONS                   = 'Magic_Weapons'
TABLE_METAMAGIC_RODS_1                = 'Metamagic_Rods_1'
TABLE_METAMAGIC_RODS_2                = 'Metamagic_Rods_2'
TABLE_METAMAGIC_RODS_3                = 'Metamagic_Rods_3'
TABLE_POTION_OR_OIL_LEVEL_0           = 'Potion_or_Oil_Level_0'
TABLE_POTION_OR_OIL_LEVEL_1           = 'Potion_or_Oil_Level_1'
TABLE_POTION_OR_OIL_LEVEL_2           = 'Potion_or_Oil_Level_2'
TABLE_POTION_OR_OIL_LEVEL_3           = 'Potion_or_Oil_Level_3'
TABLE_POTION_OR_OIL_TYPE              = 'Potion_or_Oil_Type'
TABLE_RANDOM_ARMOR_OR_SHIELD          = 'Random_Armor_or_Shield'
TABLE_RANDOM_ART_OBJECTS              = 'Random_Art_Objects'
TABLE_RANDOM_GEMS                     = 'Random_Gems'
TABLE_RANDOM_POTIONS_AND_OILS         = 'Random_Potions_and_Oils'
TABLE_RANDOM_SCROLLS                  = 'Random_Scrolls'
TABLE_RANDOM_WANDS                    = 'Random_Wands'
TABLE_RANDOM_WEAPON                   = 'Random_Weapon'
TABLE_RINGS                           = 'Rings'
TABLE_RODS                            = 'Rods'
TABLE_SCROLLS_ARCANE_LEVEL_0          = 'Scrolls_Arcane_Level_0'
TABLE_SCROLLS_ARCANE_LEVEL_1          = 'Scrolls_Arcane_Level_1'
TABLE_SCROLLS_ARCANE_LEVEL_2          = 'Scrolls_Arcane_Level_2'
TABLE_SCROLLS_ARCANE_LEVEL_3          = 'Scrolls_Arcane_Level_3'
TABLE_SCROLLS_ARCANE_LEVEL_4          = 'Scrolls_Arcane_Level_4'
TABLE_SCROLLS_ARCANE_LEVEL_5          = 'Scrolls_Arcane_Level_5'
TABLE_SCROLLS_ARCANE_LEVEL_6          = 'Scrolls_Arcane_Level_6'
TABLE_SCROLLS_ARCANE_LEVEL_7          = 'Scrolls_Arcane_Level_7'
TABLE_SCROLLS_ARCANE_LEVEL_8          = 'Scrolls_Arcane_Level_8'
TABLE_SCROLLS_ARCANE_LEVEL_9          = 'Scrolls_Arcane_Level_9'
TABLE_SCROLLS_DIVINE_LEVEL_0          = 'Scrolls_Divine_Level_0'
TABLE_SCROLLS_DIVINE_LEVEL_1          = 'Scrolls_Divine_Level_1'
TABLE_SCROLLS_DIVINE_LEVEL_2          = 'Scrolls_Divine_Level_2'
TABLE_SCROLLS_DIVINE_LEVEL_3          = 'Scrolls_Divine_Level_3'
TABLE_SCROLLS_DIVINE_LEVEL_4          = 'Scrolls_Divine_Level_4'
TABLE_SCROLLS_DIVINE_LEVEL_5          = 'Scrolls_Divine_Level_5'
TABLE_SCROLLS_DIVINE_LEVEL_6          = 'Scrolls_Divine_Level_6'
TABLE_SCROLLS_DIVINE_LEVEL_7          = 'Scrolls_Divine_Level_7'
TABLE_SCROLLS_DIVINE_LEVEL_8          = 'Scrolls_Divine_Level_8'
TABLE_SCROLLS_DIVINE_LEVEL_9          = 'Scrolls_Divine_Level_9'
TABLE_SCROLL_TYPE                     = 'Scroll_Type'
TABLE_SPECIAL_ABILITIES_AMMUNITION    = 'Special_Abilities_Ammunition'
TABLE_SPECIAL_ABILITIES_ARMOR         = 'Special_Abilities_Armor'
TABLE_SPECIAL_ABILITIES_MELEE_WEAPON  = 'Special_Abilities_Melee_Weapon'
TABLE_SPECIAL_ABILITIES_RANGED_WEAPON = 'Special_Abilities_Ranged_Weapon'
TABLE_SPECIAL_ABILITIES_SHIELD        = 'Special_Abilities_Shield'
TABLE_SPECIAL_BANE                    = 'Special_Bane'
TABLE_SPECIAL_SLAYING_ARROW           = 'Special_Slaying_Arrow'
TABLE_SPECIFIC_ARMOR                  = 'Specific_Armor'
TABLE_SPECIFIC_CURSED_ITEMS           = 'Specific_Cursed_Items'
TABLE_SPECIFIC_SHIELDS                = 'Specific_Shields'
TABLE_SPECIFIC_WEAPONS                = 'Specific_Weapons'
TABLE_STAVES                          = 'Staves'
TABLE_WAND_LEVEL_0                    = 'Wand_Level_0'
TABLE_WAND_LEVEL_1                    = 'Wand_Level_1'
TABLE_WAND_LEVEL_2                    = 'Wand_Level_2'
TABLE_WAND_LEVEL_3                    = 'Wand_Level_3'
TABLE_WAND_LEVEL_4                    = 'Wand_Level_4'
TABLE_WAND_TYPE                       = 'Wand_Type'
TABLE_WONDROUS_ITEMS                  = 'Wondrous_Items'
TABLE_WONDROUS_ITEMS_BELT             = 'Wondrous_Items_Belt'
TABLE_WONDROUS_ITEMS_BODY             = 'Wondrous_Items_Body'
TABLE_WONDROUS_ITEMS_CHEST            = 'Wondrous_Items_Chest'
TABLE_WONDROUS_ITEMS_EYES             = 'Wondrous_Items_Eyes'
TABLE_WONDROUS_ITEMS_FEET             = 'Wondrous_Items_Feet'
TABLE_WONDROUS_ITEMS_HANDS            = 'Wondrous_Items_Hands'
TABLE_WONDROUS_ITEMS_HEAD             = 'Wondrous_Items_Head'
TABLE_WONDROUS_ITEMS_HEADBAND         = 'Wondrous_Items_Headband'
TABLE_WONDROUS_ITEMS_NECK             = 'Wondrous_Items_Neck'
TABLE_WONDROUS_ITEMS_SHOULDERS        = 'Wondrous_Items_Shoulders'
TABLE_WONDROUS_ITEMS_SLOTLESS         = 'Wondrous_Items_Slotless'
TABLE_WONDROUS_ITEMS_WRISTS           = 'Wondrous_Items_Wrists'

STANDARD_STRENGTHS = ['lesser minor', 'greater minor', 'lesser medium',
        'greater medium', 'lesser major', 'greater major']
EXPANDED_STRENGTHS = ['least minor', 'lesser minor', 'greater minor',
        'lesser medium', 'greater medium', 'lesser major', 'greater major']

#
# Variables

ENABLE_SKIPPING = False
PRINT_ROLLS = False
DIR_PREFIX = 'enum'

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
        #print(80*'-')
        self.rolls = {}

    def end_item(self):
        pass

    def item_rolled(self, purpose, range_low, range_high, strength):
        if purpose not in self.rolls or range_high > self.rolls[purpose][1]:
            self.rolls[purpose] = (range_low, range_high, strength)
            #print('roll', purpose, range_low, range_high, strength)

    def do_skip(self):
        if not ENABLE_SKIPPING:
            return 1
        multiplier = 1
        #print(self.rolls)
        for purpose in self.purposes1:
            try:
                (low, high, strength) = self.rolls[purpose]
                #print(purpose, low, high)
                span = high - low + 1
                multiplier = multiplier * span
                self.current[purpose]['value'] = high
            except KeyError as ex:
                # Simply omit it from the calculation. If there was no value,
                # it's not important.
                #print('### ERROR!!! ', ex, self.purposes1, self.purposes2, self.rolls)
                pass
        #print(self.rolls)
        self.rolls = {}
        return multiplier

    def roll(self, dice_expression, purpose):
        #print('roll requested for', purpose, end='')
        # If this purpose has not been used yet, set it up.
        if purpose not in self.current.keys():
            #print('New purpose', purpose)
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
                #print('increment 1 end')
                raise EnumerationsComplete

        # Note the last purpose.
        self.last_purpose = purpose

        # Handle the state.
        if self.stage == 1:
            #print('@1', end='')
            # This is the first pass.
            if purpose not in self.purposes1:
                self.purposes1.append(purpose)
            #elif self.stage == 2:
            #    #print('@2', end='')
            #    # This is the second pass.
            #    if purpose not in self.purposes2:
            #        self.purposes2.append(purpose)
            #elif self.stage == 3:
        elif self.stage >= 2 and purpose == self.last_purpose:
            #print('@3', end='')
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
        #print('[' + purpose + ':' + str(self.current[purpose]['value']) + ']', end='')
        #print('[' + str(self.current[purpose]['value']) + ']', end='')
        return self.current[purpose]['value']

    def increment(self):
        #print('Increment:', self.purposes1)
        # Increment according to the reverse of the purpose lists.
        for digit in reversed(self.purposes1):
            #print('incr', digit)
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

def enumerate_item(conn_in, strengths, item_key, file_prefix):

    # Roll up items
    for strength in strengths:
        print('Analyzing', strength, item_key)
        # Set up the output file.
        outfile = DIR_PREFIX + '/' + file_prefix + '_' + strength
        outfile = outfile.replace(' ', '_')
        f = open(outfile + '.txt', 'w')
        rollfile = open(outfile + '.rolls', 'w')
        roller = EnumeratingRoller()

        # Collect items to count.
        items = {}
        # Note the last roll so we can filter out duplicates.
        #last_roll = None
        # Roll items
        while True:
            try:
                # Notify the roller it's about to roll a single item.
                roller.begin_item()
                # Roll the item.
                x = item.generate_specific_item(conn_in, strength, item_key, roller, roller)
                # Done rolling an item.
                roller.end_item()
                # Allow the roller to increment based on its saved values.
                count = roller.do_skip()
                # Get the rolls.
                roll = item.rolls_str(x)
                if PRINT_ROLLS:
                    print(roll + '        \n', end='', file=rollfile)
                    print(' ' + roll + '        \r', end='')
                #if roll == last_roll:
                #    print('Repeat roll!')
                #last_roll = roll
                item_str = item.item_str(x)
                if item_str in items.keys():
                    items[item_str] += count
                else:
                    #print('New item', item_str)
                    items[item_str] = count
            except EnumerationsComplete:
                break
        total = 0
        for item_str in items.keys():
            count = items[item_str]
            total += count
            print(items[item_str], item_str, sep='\t', file=f)
        f.close();
        rollfile.close()
        print('    contained', total, 'items')


def build_enum_table(conn_in, cursor_out):

    try:
        os.mkdir(DIR_PREFIX)
    except FileExistsError:
        pass
    
    ## Temporarily limit the choices to test optimizations.
    #global STANDARD_STRENGTHS
    #STANDARD_STRENGTHS = ["lesser minor"]
    #global EXPANDED_STRENGTHS
    #EXPANDED_STRENGTHS = ["lesser minor"]

    enumerate_item(conn_in, STANDARD_STRENGTHS, 'armor/shield', 'armor')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'weapon', 'weapon')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'potion', 'potion')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'ring', 'ring')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'rod', 'rod')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'scroll', 'scroll')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'staff', 'staff')
    enumerate_item(conn_in, STANDARD_STRENGTHS, 'wand', 'wand')
    enumerate_item(conn_in, EXPANDED_STRENGTHS, 'wondrous', 'wondrous')


#def initialize_database(database_in, database_out):
def initialize_database(database_in):
    con_in = None
    con_out = None
    try:
        # We're starting over, so erase the file.
        #if os.path.isfile(database_out):
        #    os.remove(database_out)

        # Open the database files.
        con_in = sqlite.connect(database_in)
        con_in.row_factory = sqlite.Row

        #con_out = sqlite.connect(database_out)

        # Build the enumeration table!
        #build_enum_table(con_in, con_out.cursor())
        build_enum_table(con_in, None)

        # Commit
        #con_out.commit()

    except sqlite.Error as e:
        print('Error: %s' % e.message)
        sys.exit(1)
    finally:
        if con_in:
            con_in.close()
        if con_out:
            con_out.close()

def run_program(args):
    n_cache = 0
    n_skip = 0
    n_print_rolls = 0

    item.set_enumeration()

    # Set the caching options.
    if args.cache:
        item.enable_caching(args.cache)
        n_cache = args.cache
    if args.skip:
        print("skip enabled")
        global ENABLE_SKIPPING
        ENABLE_SKIPPING = True
        n_skip = 1
    if args.print_rolls:
        print("printing rolls")
        global PRINT_ROLLS
        PRINT_ROLLS = True
        n_print_rolls = 1
    if args.dir:
        global DIR_PREFIX
        DIR_PREFIX = args.dir

    global DIR_PREFIX
    DIR_PREFIX = DIR_PREFIX + '_c{0}_s{1}_r{2}'.format(n_cache, n_skip, n_print_rolls)

    #initialize_database(args.database_in, args.database_out)
    initialize_database(args.database_in)

#
# Main

if __name__ == '__main__':

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(
            description='Initializes databases from text files')

    # Positional arguments: database name
    parser.add_argument('database_in', metavar='INPUT_DATABASE',
            help='The database name')
    #parser.add_argument('database_out', metavar='OUTPUT_DATABASE',
    #        help='The database name')
    parser.add_argument('--cache', type=int,
            help='The type of cache to use')
    parser.add_argument('--skip', action='store_true',
            help='Skip rolls that would repeat previous return')
    parser.add_argument('--print-rolls', action='store_true',
            help='Prints rolls')
    parser.add_argument('--dir', '-d',
            help='Output directory override')

    # Go.
    args = parser.parse_args()
    run_program(args)

