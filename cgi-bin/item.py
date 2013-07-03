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
This module implements the bulk of item generation for the Pathfinder Item
Generator.
'''

#
# Library imports

import locale
import math
import os
import random
import re
import sys

#
# Local imports

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

# Constants

# Keys into the subclass map, also usable for displaying categories, if
# desired.

KEY_ARMOR         = 'Armor/Shield'
KEY_WEAPON        = 'Weapon'
KEY_POTION        = 'Potion'
KEY_RING          = 'Ring'
KEY_ROD           = 'Rod'
KEY_SCROLL        = 'Scroll'
KEY_STAFF         = 'Staff'
KEY_WAND          = 'Wand'
KEY_WONDROUS_ITEM = 'Wondrous Item'

# Roll 'redirections'

ROLL_LEAST_MINOR = "Roll on the Least Minor table"

# Option values for specifying magic items parameters.

# There is no official term for this, but I call them "degrees".
DEGREE_OPTIONS = ['least', 'lesser', 'greater']

# I use "strength" for minor, medium, or major, with an otional degree before
# it.
STRENGTH_OPTIONS = ['minor', 'medium', 'major']

# Comprehensive item types, including subtypes.
TYPE_OPTIONS = ['armor/shield', 'armor', 'shield', 'weapon', 'potion',
        'ring', 'rod', 'scroll', 'staff', 'wand', 'wondrous', 'belt', 'belts',
        'body', 'chest', 'eyes', 'feet', 'hand', 'hands', 'head', 'headband',
        'neck', 'shoulders', 'slotless', 'wrist', 'wrists']

# Maps the parameter specification of an item type to its standardized value.
# Use a key converted to lower case to perform the lookup.

ITEM_TYPE_MAP = {
        'armor'            : 'Armor/Shield',
        'armor/shield'     : 'Armor/Shield',
        'armor and shield' : 'Armor/Shield',
        'armor or shield'  : 'Armor/Shield',
        'weapon'           : 'Weapon',
        'potion'           : 'Potion',
        'ring'             : 'Ring',
        'rod'              : 'Rod',
        'scroll'           : 'Scroll',
        'staff'            : 'Staff',
        'wand'             : 'Wand',
        'wondrous item'    : 'Wondrous Item',
        'wondrous'         : 'Wondrous Item' }

# As above, but includes subtypes
ITEM_SUBTYPE_MAP = {
        'armor/shield'     : ('Armor/Shield', ''),
        'armor and shield' : ('Armor/Shield', ''),
        'armor or shield'  : ('Armor/Shield', ''),
        'weapon'           : ('Weapon', ''),
        'potion'           : ('Potion', ''),
        'ring'             : ('Ring', ''),
        'rod'              : ('Rod', ''),
        'scroll'           : ('Scroll', ''),
        'staff'            : ('Staff', ''),
        'wand'             : ('Wand', ''),
        'wondrous item'    : ('Wondrous Item', ''),
        'wondrous'         : ('Wondrous Item', ''),
        'belt'             : ('Wondrous Item', 'Belts'),
        'belts'            : ('Wondrous Item', 'Belts'),
        'body'             : ('Wondrous Item', 'Body'),
        'chest'            : ('Wondrous Item', 'Chest'),
        'eyes'             : ('Wondrous Item', 'Eyes'),
        'feet'             : ('Wondrous Item', 'Feet'),
        'hand'             : ('Wondrous Item', 'Hands'),
        'hands'            : ('Wondrous Item', 'Hands'),
        'head'             : ('Wondrous Item', 'Head'),
        'headband'         : ('Wondrous Item', 'Headband'),
        'neck'             : ('Wondrous Item', 'Neck'),
        'shoulders'        : ('Wondrous Item', 'Shoulders'),
        'slotless'         : ('Wondrous Item', 'Slotless'),
        'wrist'            : ('Wondrous Item', 'Wrists'),
        'wrists'           : ('Wondrous Item', 'Wrists')
        }


#
# Variables

ENABLE_CACHE = False
CACHE_TYPE = 0

# Indicates that bad items will not be discarded.
ENUMERATION_MODE = False


#
# Functions

def enable_caching(cache_type):
    global ENABLE_CACHE, CACHE_TYPE
    ENABLE_CACHE = True
    CACHE_TYPE = cache_type

def set_enumeration():
    global ENUMERATION_MODE
    ENUMERATION_MODE = True

def extract_keywords(sequence, keywords):
    '''Searches the specified sequence for the specified keywords, returns
    a set containing the matches, and eliminates the matching items from
    the sequence.'''
    sequence_as_set = set(sequence)
    keywords_as_set = set(keywords)
    intersect = sequence_as_set.intersection(keywords_as_set)
    for x in intersect: sequence.remove(x)
    return intersect


def generate_generic(conn, strength, roller, base_value, listener):
    # Here, strength is merely 'minor', 'medium', 'major', so we need to
    # further qualify it with 'lesser' or 'greater'.
    
    # This will account for specified and unspecified base values.
    min_price = Price(base_value)
    value = Price('0 gp')
    x = None
    count = 0
    while value < min_price:
        # We may decide to change this later, but at least for now, the choice
        # between them will be 50/50.  Because slotless wondrous item can also
        # be 'least minor', use least if the roll is less than 25.  Item types
        # without the 'least' level will simply treat it as 'lesser'.
        full_strength = 'greater '
        roll = roller.roll('1d100', 'degree')
        if roll <= 25 and strength == 'minor':
            full_strength = 'least '
        elif roll <= 50:
            full_strength = 'lesser '
        full_strength += strength

        # Now, select an item type.
        roll = roller.roll('1d100', 'item type')
        # This lookup only needs minor/medium/major.
        kind = get_item_type(conn, strength, roll)

        x = generate_specific_item(conn, full_strength, kind, roller, listener)
        try:
            value = x.price
        except BadPrice as ex:
            value = Price('')
        count += 1
        if count > 1000:
            return 'Error: gave up after 1000 tries; <error> gp'
    return x


def generate_item(conn, description, roller, listener):
    # 'description' contains keywords.
    keywords = description.split(' ')

    # least/lesser/greater
    degrees = extract_keywords(keywords, DEGREE_OPTIONS)
    if len(degrees) != 1:
        raise Exception('must specify exactly one of: ' +
                ', '.join(DEGREE_OPTIONS))

    # minor/medium/major
    strengths = extract_keywords(keywords, STRENGTH_OPTIONS)
    if len(strengths) != 1:
        raise Exception('must specify exactly one of: ' +
                ', '.join(STRENGTH_OPTIONs))

    # item types and subtypes
    types = extract_keywords(keywords, TYPE_OPTIONS)
    if len(types) != 1:
        raise Exception('must specify exactly one of: ' +
                ', '.join(TYPE_OPTIONS))

    # Look for leftover keywords.
    if len(keywords) > 0:
        raise Exception('ignoring keywords:', *keywords)

    # Get singular values.
    degree = degrees.pop()
    strength = strengths.pop()
    kind = types.pop() # avoiding 'type' reserved word

    # Now we have the parts in a usable form.
    return generate_specific_item(conn, degree + ' ' + strength, kind, roller, listener)


def generate_specific_item(conn, strength, kind, roller, listener):
    # Create an object.
    item = create_item(kind)
    # Finish generating the item
    item.generate(conn, strength, roller, listener)
    return item


def fast_generate(conn, strength, kind, base_value):
    # Quickly get an item from a table.
    table = (kind + '_' + strength).replace(' ', '_').lower()

    # Gather up the possible candidates.
    # Note: Use the syntactic sugar offered by sqlite that uses a temporary
    # cursor, otherwise, the results seem short by 1 row. Perhaps it has to do
    # with using a cursor twice? Not quite sure.
    # Anyway, just use the conn directly.

    sql_a1 = 'SELECT SUM(Count) '
    sql_a2 = 'SELECT * '
    sql_b = 'FROM {0} WHERE Price >= (?);'.format(table)

    try:
        result_sum = conn.execute(sql_a1 + sql_b, (base_value,))
        candidates = conn.execute(sql_a2 + sql_b, (base_value,))

        if candidates == None:
            return None

        # The number of items.
        total = result_sum.fetchone()[0]

        # Roll a random number in the total range.
        roll = random.randrange(total)
        #print('Rolled', roll)

        # Go through the candidates until an item is found.
        accum = 0
        for c in candidates:
            count = c['Count']
            accum += count
            #print('Checking', accum, c['Item'])
            if roll < accum:
                #odds = (count / total) * 100
                #print('Got it!')
                return [c['Item'], c['Price']]
        return None
    except:
        return None


def create_item(kind):
    # Look up the kind of item for its official name.
    (main_kind, subtype) = ITEM_SUBTYPE_MAP[kind.lower()]

    # Create the apropriate Item subclass.
    subclass = ITEM_SUBCLASSES[main_kind]
    result = subclass.__new__(subclass)
    result.__init__()
    # Set the subtype (applicable only sometimes)
    result.subtype = subtype
    return result


def get_item_type(conn, strength, roll):
    cursor = conn.cursor()
    columns = None
    if strength == 'minor':
        columns = ('Minor_low', 'Minor_high')
    elif strength == 'medium':
        columns = ('Minor_low', 'Minor_high')
    elif strength == 'major':
        columns = ('Major_low', 'Major_high')
    else:
        # TODO an exception would be nice
        return ''
    # Search the database.
    cursor.execute('''SELECT Item from Item_Types WHERE (? >= {0}) AND
            (? <= {1});'''.format(*columns), (roll, roll) )
    return cursor.fetchone()["Item"]


def item_str(x):
    # Convert the item to a string (it has a __str__ method).
    s = str(x)
    # Some characters cause problems in Windows' command prompt (sigh).
    # Replace problem characters with their equivalents.
    s = s.replace('\u2019', "'")
    return s


def print_item(x):
    '''Prints an item to standard out.  Parameter 'x' is already a string,
    but this function catches Unicode-related exceptions, which occur when
    standard out happens to be the Windows console, which is not Unicode .'''
    s = item_str(x)
    try:
        print(s)
    except:
        print('Error: Unable to print item ({0}).'.format(x.kind()))


def rolls_str(x):
    return '[' + ','.join([str(t[1]) for t in x.rolls])  + ']'


def print_rolls(x):
    '''Prints an item's roll history.'''
    print(rolls_str(x), sep='', end='')

#
# Classes
#


class BadPrice(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class Price(object):

    def __init__(self, initial_value, enhancement_type=''):
        self.enhancement_type = enhancement_type
        self.gold = 0.0
        self.enhancement = 0
        self.piece_expr = re.compile('(((\d{1,3},)*\d+) *(pp|gp|sp|cp)[, ]*)', re.I)
        # Initialize with the provided string
        self.add(initial_value)


    def __lt__(self, other):
        return self.gold < other.gold


    def __le__(self, other):
        return self.gold <= other.gold


    def __str__(self):
        return self.compute()


    def as_float(self):
        return self.gold


    def add(self, price_str):
        # If the value provided is int or float, add it directly.
        if type(price_str) == int or type(price_str) == float:
            self.gold += float(price_str)
        # If it's a bonus, the price depends on the sum, so it defers.
        elif price_str.endswith(' bonus'):
            self.add_enhancement(price_str)
        # Empty string is non-value.
        elif price_str == None or price_str == '':
            self.gold = float('nan')
        # Otherwise, it might be a pp/gp/sp/cp string.
        else:
            self.add_expression(price_str)


    def add_expression(self, expr):
        for piece in self.piece_expr.finditer(expr):
            # Group 2 is the count, group 4 is the type.
            scale = 0.0
            count = float(piece.group(2).replace(',',''))
            coin_type = piece.group(4)
            if   coin_type == 'pp': scale = 10.0
            elif coin_type == 'gp': scale =  1.0
            elif coin_type == 'sp': scale = 0.10
            elif coin_type == 'cp': scale = 0.01
            self.gold += (count * scale)


    def add_enhancement(self, price_str):
        if type(price_str) == int:
            self.enhancement += price_str
            return
        match = re.match('\+(\d+) bonus', price_str)
        if match:
            self.enhancement += int(match.group(1))
        else:
            raise BadPrice('cannot extract enhancement bonus from ' +
                    price_str)

 
    def compute(self):
        if math.isnan(self.gold):
            return '<error> gp'
        cost = self.gold
        if self.enhancement > 0:
             temp = (self.enhancement ** 2) * 1000
             if self.enhancement_type == 'weapon':
                 temp *= 2
             cost += temp
        return locale.format_string('%.2f', cost, grouping=True) + ' gp'


class Table(object):

    def __init__(self, table):
        self.table = table
        self.cache = {}
        self.cache_style = CACHE_TYPE
        self.query_nostrength = '''SELECT * FROM {0} WHERE (? >= Roll_low) AND
            (? <= Roll_high);'''.format(self.table)
        self.query_strength = '''SELECT * FROM {0} WHERE (? >= Roll_low) AND
            (? <= Roll_high) AND (? = Strength);'''.format(self.table)
        

    def find_roll(self, conn, roll, strength, purpose, listener):
        # If caching is enabled, go for it
        if ENABLE_CACHE:
            if self.cache_style == 1:
                if strength not in self.cache:
                    self.cache[strength] = []
                for line in self.cache[strength]:
                    if roll >= line['low'] and roll <= line['high']:
                        return line['result']
            elif self.cache_style == 2:
                if strength not in self.cache:
                    self.cache[strength] = {}
                if strength in self.cache:
                    a = self.cache[strength]
                    if roll in a:
                        return a[roll]
        
        cursor = conn.cursor()
        if strength == None:
            cursor.execute(self.query_nostrength, (roll, roll))
        else:
            cursor.execute(self.query_strength, (roll, roll, strength))
        result = cursor.fetchone()
        if result:
            try:
                roll_low = result['Roll_low']
                roll_high = result['Roll_high']
                listener.item_rolled(purpose, result['Roll_low'], result['Roll_high'], strength)
            except IndexError as ex:
                return None
        else:
            #print('No result for roll', roll)
            return None

        if ENABLE_CACHE:
            if self.cache_style == 1:
                line = {}
                line['low'] = result['Roll_low']
                line['high'] = result['Roll_high']
                line['result'] = result
                self.cache[strength].append(line)
            elif self.cache_style == 2:
                for i in range(int(result['Roll_low']), int(result['Roll_high']) + 1):
                    self.cache[strength][i] = result
        return result


# Ultimate Equipment Tables

TABLE_MAGIC_ARMOR_AND_SHIELDS         = Table('Magic_Armor_and_Shields')
TABLE_MAGIC_WEAPONS                   = Table('Magic_Weapons')
TABLE_METAMAGIC_RODS_1                = Table('Metamagic_Rods_1')
TABLE_METAMAGIC_RODS_2                = Table('Metamagic_Rods_2')
TABLE_METAMAGIC_RODS_3                = Table('Metamagic_Rods_3')
TABLE_POTION_OR_OIL_LEVEL_0           = Table('Potion_or_Oil_Level_0')
TABLE_POTION_OR_OIL_LEVEL_1           = Table('Potion_or_Oil_Level_1')
TABLE_POTION_OR_OIL_LEVEL_2           = Table('Potion_or_Oil_Level_2')
TABLE_POTION_OR_OIL_LEVEL_3           = Table('Potion_or_Oil_Level_3')
TABLE_POTION_OR_OIL_TYPE              = Table('Potion_or_Oil_Type')
TABLE_RANDOM_ARMOR_OR_SHIELD          = Table('Random_Armor_or_Shield')
TABLE_RANDOM_ART_OBJECTS              = Table('Random_Art_Objects')
TABLE_RANDOM_GEMS                     = Table('Random_Gems')
TABLE_RANDOM_POTIONS_AND_OILS         = Table('Random_Potions_and_Oils')
TABLE_RANDOM_SCROLLS                  = Table('Random_Scrolls')
TABLE_RANDOM_WANDS                    = Table('Random_Wands')
TABLE_RANDOM_WEAPON                   = Table('Random_Weapon')
TABLE_RINGS                           = Table('Rings')
TABLE_RODS                            = Table('Rods')
TABLE_SCROLLS_ARCANE_LEVEL_0          = Table('Scrolls_Arcane_Level_0')
TABLE_SCROLLS_ARCANE_LEVEL_1          = Table('Scrolls_Arcane_Level_1')
TABLE_SCROLLS_ARCANE_LEVEL_2          = Table('Scrolls_Arcane_Level_2')
TABLE_SCROLLS_ARCANE_LEVEL_3          = Table('Scrolls_Arcane_Level_3')
TABLE_SCROLLS_ARCANE_LEVEL_4          = Table('Scrolls_Arcane_Level_4')
TABLE_SCROLLS_ARCANE_LEVEL_5          = Table('Scrolls_Arcane_Level_5')
TABLE_SCROLLS_ARCANE_LEVEL_6          = Table('Scrolls_Arcane_Level_6')
TABLE_SCROLLS_ARCANE_LEVEL_7          = Table('Scrolls_Arcane_Level_7')
TABLE_SCROLLS_ARCANE_LEVEL_8          = Table('Scrolls_Arcane_Level_8')
TABLE_SCROLLS_ARCANE_LEVEL_9          = Table('Scrolls_Arcane_Level_9')
TABLE_SCROLLS_DIVINE_LEVEL_0          = Table('Scrolls_Divine_Level_0')
TABLE_SCROLLS_DIVINE_LEVEL_1          = Table('Scrolls_Divine_Level_1')
TABLE_SCROLLS_DIVINE_LEVEL_2          = Table('Scrolls_Divine_Level_2')
TABLE_SCROLLS_DIVINE_LEVEL_3          = Table('Scrolls_Divine_Level_3')
TABLE_SCROLLS_DIVINE_LEVEL_4          = Table('Scrolls_Divine_Level_4')
TABLE_SCROLLS_DIVINE_LEVEL_5          = Table('Scrolls_Divine_Level_5')
TABLE_SCROLLS_DIVINE_LEVEL_6          = Table('Scrolls_Divine_Level_6')
TABLE_SCROLLS_DIVINE_LEVEL_7          = Table('Scrolls_Divine_Level_7')
TABLE_SCROLLS_DIVINE_LEVEL_8          = Table('Scrolls_Divine_Level_8')
TABLE_SCROLLS_DIVINE_LEVEL_9          = Table('Scrolls_Divine_Level_9')
TABLE_SCROLL_TYPE                     = Table('Scroll_Type')
TABLE_SPECIAL_ABILITIES_AMMUNITION    = Table('Special_Abilities_Ammunition')
TABLE_SPECIAL_ABILITIES_ARMOR         = Table('Special_Abilities_Armor')
TABLE_SPECIAL_ABILITIES_MELEE_WEAPON  = Table('Special_Abilities_Melee_Weapon')
TABLE_SPECIAL_ABILITIES_RANGED_WEAPON = Table('Special_Abilities_Ranged_Weapon')
TABLE_SPECIAL_ABILITIES_SHIELD        = Table('Special_Abilities_Shield')
TABLE_SPECIAL_BANE                    = Table('Special_Bane')
TABLE_SPECIAL_SLAYING_ARROW           = Table('Special_Slaying_Arrow')
TABLE_SPECIFIC_ARMOR                  = Table('Specific_Armor')
TABLE_SPECIFIC_CURSED_ITEMS           = Table('Specific_Cursed_Items')
TABLE_SPECIFIC_SHIELDS                = Table('Specific_Shields')
TABLE_SPECIFIC_WEAPONS                = Table('Specific_Weapons')
TABLE_STAVES                          = Table('Staves')
TABLE_WAND_LEVEL_0                    = Table('Wand_Level_0')
TABLE_WAND_LEVEL_1                    = Table('Wand_Level_1')
TABLE_WAND_LEVEL_2                    = Table('Wand_Level_2')
TABLE_WAND_LEVEL_3                    = Table('Wand_Level_3')
TABLE_WAND_LEVEL_4                    = Table('Wand_Level_4')
TABLE_WAND_TYPE                       = Table('Wand_Type')
TABLE_WONDROUS_ITEMS                  = Table('Wondrous_Items')
TABLE_WONDROUS_ITEMS_BELT             = Table('Wondrous_Items_Belt')
TABLE_WONDROUS_ITEMS_BODY             = Table('Wondrous_Items_Body')
TABLE_WONDROUS_ITEMS_CHEST            = Table('Wondrous_Items_Chest')
TABLE_WONDROUS_ITEMS_EYES             = Table('Wondrous_Items_Eyes')
TABLE_WONDROUS_ITEMS_FEET             = Table('Wondrous_Items_Feet')
TABLE_WONDROUS_ITEMS_HANDS            = Table('Wondrous_Items_Hands')
TABLE_WONDROUS_ITEMS_HEAD             = Table('Wondrous_Items_Head')
TABLE_WONDROUS_ITEMS_HEADBAND         = Table('Wondrous_Items_Headband')
TABLE_WONDROUS_ITEMS_NECK             = Table('Wondrous_Items_Neck')
TABLE_WONDROUS_ITEMS_SHOULDERS        = Table('Wondrous_Items_Shoulders')
TABLE_WONDROUS_ITEMS_SLOTLESS         = Table('Wondrous_Items_Slotless')
TABLE_WONDROUS_ITEMS_WRISTS           = Table('Wondrous_Items_Wrists')


class Item(object):

    #
    # Methods that are not meant to be overridden

    # Initializes object variables
    def __init__(self, kind):
        # The kind of item, stored mainly so a subclass doesn't need to know
        # its own name.
        self.kind = kind
        # All the rolls that led to the selection of the item
        self.rolls = []
        # The item label, before any additions, which subclasses track on
        # their own.
        self.label = ''
        # Generation parameters
        # Strength: lesser/greater + major/medium/minor
        self.strength = ''
        # Roller
        self.roller = None
        # Subtype (when Wondrous)
        self.subtype = ''
        # Validity flag (used in enumeration mode)
        self.bad_item = False
        # Price
        self.price = None


    # Generates the item, referring to the subclass, following the Template
    # Method design pattern.
    def generate(self, conn, strength, roller, listener):
        # Initialize generation parameters.
        self.strength = strength
        self.roller = roller
        # Look up the item
        self.lookup(conn, listener)


    # The standard __str__ method
    def __str__(self):
        #s = self.subtype + ': ' + self.label
        s = self.label
        try:
            s += '; ' + str(self.price)
        except BadPrice as ex:
            s += '; pricing error'
        if self.bad_item:
            s += " [invalid]"
        return s


    #
    # Information on the finished item


    def is_bad(self):
        return self.bad_item


    #
    # Consider these "private"


    # Rolls and keeps a log of the rolled values.
    def roll(self, roll_expr, purpose):
        roll = self.roller.roll(roll_expr, purpose)
        self.rolls.append((roll_expr, roll))
        return roll


    # Removes the last roll from the log.
    def unroll(self):
        if len(self.rolls) > 0:
            self.rolls.pop()


    #
    # Methods that are meant to be overridden


    # The standard __repr__ method
    def __repr__(self):
        result = '<Item '
        result += 'rolls:{} '.format(self.rolls)
        result += 'label:{}'.format(self.label)
        result += '>'
        return result


class Armor(Item):

    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        # Load tables
        self.t_random          = TABLE_RANDOM_ARMOR_OR_SHIELD
        self.t_magic           = TABLE_MAGIC_ARMOR_AND_SHIELDS
        self.t_specific_armor  = TABLE_SPECIFIC_ARMOR
        self.t_specials_armor  = TABLE_SPECIAL_ABILITIES_ARMOR
        self.t_specific_shield = TABLE_SPECIFIC_SHIELDS
        self.t_specials_shield = TABLE_SPECIAL_ABILITIES_SHIELD
        self.re_enhancement = re.compile('\+(\d+) armor or shield')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')
        # Armor details
        # Generic item or specific
        self.is_generic = True
        # Armor piece
        self.armor_base = ''
        # Armor or shield
        self.armor_type = ''
        # Mundane item price
        self.armor_price = '0 gp'
        # Raw enhancement bonus
        self.enhancement = 0
        # Dict of specials to costs
        self.specials = {}
        # Specific item name
        self.specific_name = ''
        # Specific item cost
        self.specific_price = 'error looking up price'


    def __repr__(self):
        result = '<Armor'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        purpose = 'armor type'
        roll = self.roll('1d100', purpose)
        # Look up the roll.
        rolled_armor = self.t_random.find_roll(conn, roll, None, purpose, listener)
        self.armor_base = rolled_armor['Result']
        self.armor_type = rolled_armor['Type']
        self.armor_price = rolled_armor['Price']
        self.enhancement = 0

        # Roll for the magic property.
        purpose = 'armor magic property'
        roll = self.roll('1d100', purpose)
        rolled_magic = self.t_magic.find_roll(conn, roll, self.strength, purpose, listener)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific armor or shield'):
            self.make_specific(conn, listener)
        else:
            self.make_generic(conn, magic_type, listener)

        # Subtype
        self.subtype = ''
        if self.armor_type == 'armor':
            self.subtype = 'Armor'
        elif self.subtype == 'shield':
            self.subtype = 'Shield'

        # Item specifics
        if self.is_generic:
            # Compose the label.
            self.label = self.armor_base
            if self.enhancement > 0:
                self.label += ' +' + str(self.enhancement)
                for spec in sorted(self.specials.keys()):
                    self.label += '/' + spec
            # Compose a price.
            # Start with the base cost.
            self.price = Price(self.armor_price, self.armor_type)
            # Add magic costs.
            if self.enhancement:
                # Masterwork component
                self.price.add(150)
                # Initial enhancement bonus
                self.price.add_enhancement(self.enhancement)
                # Special costs
                for spec in self.specials.keys():
                    self.price.add(self.specials[spec])
        else:
            # Specific magic armor. Just copy the details.
            self.label += self.specific_name
            self.price = Price(self.specific_price)


    def make_generic(self, conn, specification, listener):
        self.is_generic = True
        # "Regular" magic item, with an assortment of bonuses.  We already
        # know what we need in the specification param.
        special_count = 0
        special_strength = 0
        # This part is always at the beginning
        match = self.re_enhancement.match(specification)
        if match:
            self.enhancement = int(match.group(1))
        # This might be in the middle of the string
        match = self.re_specials.search(specification)
        if match:
            special_count = {'one': 1, 'two': 2}[match.group(1)]
            special_strength = '+' + match.group(2)
        # Add specials!
        while special_count > 0:
            # Generate a special.
            result = self.generate_special(conn, special_strength, listener)
            if result == None:
                # Mark as bad item.
                self.bad_item = True
                return
            special = result['Result']
            price = result['Price']
            # If in enumeration.
            if ENUMERATION_MODE:
                # If we already have this special, just note it as a bad item.
                if special in self.specials.keys():
                    self.bad_item = True
                # In enumeration mode, always accept specials.
                self.specials[special] = price
                special_count -= 1
            else:
                # If we don't already have the special, add it.
                if special not in self.specials.keys():
                    self.specials[special] = price
                    special_count -= 1
                else:
                    # Do not note that we made this roll.
                    self.unroll()


    def generate_special(self, conn, special_strength, listener):
        # Roll for a special.
        purpose = 'armor special ability ' + str(len(self.specials.keys()) + 1)
        roll = self.roll('1d100', purpose)
        # Look it up.
        result = None
        if self.armor_type == 'armor':
            result = self.t_specials_armor.find_roll(conn, roll,
                    special_strength, purpose, listener)
        else:
            result = self.t_specials_shield.find_roll(conn, roll,
                    special_strength, purpose, listener)
        special = result['Result']
        price = result['Price']
        return result


    def make_specific(self, conn, listener):
        # Specific
        self.is_generic = False
        # Roll for the specific armor.
        purpose = 'specific magic armor'
        roll = self.roll('1d100', purpose)
        # Look it up.
        result = None
        if self.armor_type == 'armor':
            result = self.t_specific_armor.find_roll(conn, roll,
                    self.strength, purpose, listener)
        else:
            result = self.t_specific_shield.find_roll(conn, roll,
                    self.strength, purpose, listener)
        self.specific_name = result['Result']
        self.specific_price = result['Price']


class Weapon(Item):

    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        # Load tables
        self.t_random          = TABLE_RANDOM_WEAPON
        self.t_magic           = TABLE_MAGIC_WEAPONS
        self.t_specific_weapon = TABLE_SPECIFIC_WEAPONS
        self.t_specials_melee  = TABLE_SPECIAL_ABILITIES_MELEE_WEAPON
        self.t_specials_ranged = TABLE_SPECIAL_ABILITIES_RANGED_WEAPON
        self.re_enhancement = re.compile('\+(\d+) weapon')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')
        # Weapon details
        # Generic item or specific
        self.is_generic = True
        # Weapon type
        self.weapon_base = ''
        # Melee, ranged, ammunition
        self.weapon_type = ''
        # Light, one-hand, or two-hand
        self.wield_type = ''
        # Mundane item price
        self.weapon_price = '0 gp'
        # Raw enhancement bonus
        self.enhancement = 0
        # Dict of specials to costs
        self.specials = {}
        # Specific item name
        self.specific_name = ''
        # Specific item cost
        self.specific_price = 'error looking up price'


    def __repr__(self):
        result = '<Weapon'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        purpose = 'weapon type'
        roll = self.roll('1d100', purpose)
        # Look up the roll.
        rolled_weapon = self.t_random.find_roll(conn, roll, None, purpose, listener)
        self.weapon_base = rolled_weapon['Result']
        self.weapon_type = rolled_weapon['Type']
        self.damage_type = rolled_weapon['Damage Type']
        self.wield_type = rolled_weapon['Wield Type']
        self.weapon_price = rolled_weapon['Price']
        self.enhancement = 0

        # Roll for the magic property.
        purpose = 'weapon magic property'
        roll = self.roll('1d100', purpose)
        rolled_magic = self.t_magic.find_roll(conn, roll, self.strength, purpose, listener)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific weapon'):
            self.make_specific(conn, purpose, listener)
        else:
            self.make_generic(conn, magic_type, purpose, listener)

        # Subtype
        self.subtype = ''
        if self.weapon_type == 'melee':
            self.subtype = 'Melee'
        elif self.weapon_type == 'ranged':
            self.subtype = 'Ranged'

        # Item specifics
        if self.is_generic:
            # Compose the label.
            self.label = self.weapon_base
            if self.enhancement > 0:
                self.label += ' +' + str(self.enhancement)
                for spec in self.specials.keys():
                    self.label += '/' + spec
            # Compose a price.
            # Start with the base cost.
            self.price = Price(self.weapon_price, 'weapon')
            # Add magic costs.
            if self.enhancement:
                # Masterwork component
                self.price.add(300)
                # Initial enhancement bonus
                self.price.add_enhancement(self.enhancement)
                # Special costs
                for spec in self.specials.keys():
                    self.price.add(self.specials[spec])
        else:
            # Specific magic weapon. Just copy the details.
            self.label = self.specific_name
            self.price = Price(self.specific_price)


    def make_generic(self, conn, specification, purpose, listener):
        self.is_generic = True
        # The weapon properties determine what kinds of enchantments can be
        # applied.  We don't do this in 'lookup' because it becomes invalid if
        # it needs to be replaced with a specific weapon.
        properties = []
        if 'B' in self.damage_type: properties.append('bludgeoning')
        if 'P' in self.damage_type: properties.append('piercing')
        if 'S' in self.damage_type: properties.append('slashing')
        properties.extend(
                [x for x in self.wield_type.split(',') if len(x) > 0])
        special_count = 0
        special_strength = 0
        # This part is always at the beginning.
        match = self.re_enhancement.match(specification)
        if match:
            self.enhancement = int(match.group(1))
        # This might be present, multiple times
        match = self.re_specials.findall(specification)
        for part in match:
            special_count = {'one': 1, 'two': 2}[part[0]]
            special_strength = '+' + str(part[1])
        # Add specials!
        while special_count > 0:
            # Generate a special.
            result = self.generate_special(conn, special_strength, properties, purpose, listener)
            if result == None:
                # Mark as bad item.
                self.bad_item = True
                return
            special = result['Result']
            price = result['Price']
            # If in enumeration.
            if ENUMERATION_MODE:
                # If we already have this special, just note it as a bad item.
                if special in self.specials.keys():
                    self.bad_item = True
                # In enumeration mode, always accept specials.
                self.specials[special] = price
                special_count -= 1
            else:
                # If we don't already have the special, add it.
                if special not in self.specials.keys():
                    self.specials[special] = price
                    special_count -= 1
                else:
                    # Do not note that we made this roll.
                    self.unroll()


    def generate_special(self, conn, special_strength, properties, purpose, listener):
        # Look it up.
        result = None
        # Roll for a special.
        purpose = 'weapon special ability ' + str(len(self.specials.keys()) + 1)
        roll = self.roll('1d100', purpose)
        if self.weapon_type == 'melee':
            result = self.t_specials_melee.find_roll(conn, roll,
                    special_strength, purpose, listener)
        else:
            result = self.t_specials_ranged.find_roll(conn, roll,
                    special_strength, purpose, listener)
        special = result['Result']
        price = result['Price']
        qualifiers = [x for x in set(result['Qualifiers'].split(','))
                if len(x) > 0]
        disqualifiers = [x for x in set(result['Disqualifiers'].split('.'))
                if len(x) > 0]
        # Check qualifications.
        qualifies = self.check_qualifiers(set(properties),
                set(qualifiers), set(disqualifiers))
        if ENUMERATION_MODE:
            self.bad_item = (not qualifies)
        if qualifiers == False:
            return None
        return result


    def check_qualifiers(self, properties, qualifiers, disqualifiers):
        if len(properties) > 0:
            if len(qualifiers) > 0:
                if len(properties.intersection(qualifiers)) == 0:
                    return False
            if len(disqualifiers) > 0:
                if len(properties.intersection( disqualifiers)) != 0:
                    return False
        return True


    def make_specific(self, conn, purpose, listener):
        # Specific
        self.is_generic = False
        # Roll for the specific weapon.
        purpose = 'specific magic weapon'
        roll = self.roll('1d100', purpose)
        # Look it up.
        result = self.t_specific_weapon.find_roll(conn, roll, self.strength, purpose, listener)
        self.specific_name = result['Result']
        self.specific_price = result['Price']


class Potion(Item):

    def __init__(self):
        Item.__init__(self, KEY_POTION)
        # Load tables.
        self.t_random = TABLE_RANDOM_POTIONS_AND_OILS
        self.t_type = TABLE_POTION_OR_OIL_TYPE
        self.t_potions_0 = TABLE_POTION_OR_OIL_LEVEL_0
        self.t_potions_1 = TABLE_POTION_OR_OIL_LEVEL_1
        self.t_potions_2 = TABLE_POTION_OR_OIL_LEVEL_2
        self.t_potions_3 = TABLE_POTION_OR_OIL_LEVEL_3
        # Potion details
        self.spell = ''
        self.spell_level = ''
        self.caster_level = ''
        self.price = ''


    def __repr__(self):
        result = '<Potion'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the potion level.
        purpose = 'potion level'
        roll = self.roll('1d100', purpose)
        result = self.t_random.find_roll(conn, roll, self.strength, purpose, listener)
        self.spell_level = result['Spell Level']
        self.caster_level = result['Caster Level']
        # Determine common or uncommon
        commonness = 'Common' # default
        if self.spell_level != '0':
            # Roll for common/uncomon
            purpose = 'potion rarity'
            roll = self.roll('1d100', purpose)
            commonness = self.t_type.find_roll(conn, roll, None, purpose, listener)['Result']
        commonness = commonness.lower()
        # Now roll for and look up the spell.
        result = None
        purpose = 'potion spell'
        roll = self.roll('1d100', purpose)
        if self.spell_level == '0':
            result = self.t_potions_0.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '1st':
            result = self.t_potions_1.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '2nd':
            result = self.t_potions_2.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '3rd':
            result = self.t_potions_3.find_roll(conn, roll, commonness, purpose, listener)
        self.spell = result['Result']
        self.price = result['Price']

        # Subtype
        self.subtype = 'Potion'

        # Item specifics
        self.label = 'Potion of ' + self.spell
        self.label += ' (' + self.spell_level + ' Level'
        self.label += ', CL ' + self.caster_level + ')'
        # Cost
        self.price = Price(result['Price'])


class Ring(Item):

    def __init__(self):
        Item.__init__(self, KEY_RING)
        # Load tables.
        self.t_rings = TABLE_RINGS
        # Ring details.
        self.ring = ''
        self.price = ''


    def __repr__(self):
        result = '<Ring'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the ring.
        purpose = 'specific ring'
        roll = self.roll('1d100', purpose)
        # Look it up.
        ring = self.t_rings.find_roll(conn, roll, self.strength, purpose, listener)
        
        # Subtype
        self.subtype = 'Ring'

        # Item specifics
        self.label = ring['Result']
        self.price = Price(ring['Price'])


class Rod(Item):

    def __init__(self):
        Item.__init__(self, KEY_ROD)
        # Load tables.
        self.t_rods = TABLE_RODS


    def __repr__(self):
        result = '<Rod'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the rod.
        purpose = 'specific rod'
        roll = self.roll('1d100', purpose)
        # Look it up.
        rod = self.t_rods.find_roll(conn, roll, self.strength, purpose, listener)

        # Subtype
        self.subtype = 'Rod'

        # Item specifics
        self.label = rod['Result']
        self.price = Price(rod['Price'])


class Scroll(Item):

    def __init__(self):
        Item.__init__(self, KEY_SCROLL)
        # Load tables.
        self.t_random = TABLE_RANDOM_SCROLLS
        self.t_type = TABLE_SCROLL_TYPE
        self.t_arcane_level_0 = TABLE_SCROLLS_ARCANE_LEVEL_0
        self.t_arcane_level_1 = TABLE_SCROLLS_ARCANE_LEVEL_1
        self.t_arcane_level_2 = TABLE_SCROLLS_ARCANE_LEVEL_2
        self.t_arcane_level_3 = TABLE_SCROLLS_ARCANE_LEVEL_3
        self.t_arcane_level_4 = TABLE_SCROLLS_ARCANE_LEVEL_4
        self.t_arcane_level_5 = TABLE_SCROLLS_ARCANE_LEVEL_5
        self.t_arcane_level_6 = TABLE_SCROLLS_ARCANE_LEVEL_6
        self.t_arcane_level_7 = TABLE_SCROLLS_ARCANE_LEVEL_7
        self.t_arcane_level_8 = TABLE_SCROLLS_ARCANE_LEVEL_8
        self.t_arcane_level_9 = TABLE_SCROLLS_ARCANE_LEVEL_9
        self.t_divine_level_0 = TABLE_SCROLLS_DIVINE_LEVEL_0
        self.t_divine_level_1 = TABLE_SCROLLS_DIVINE_LEVEL_1
        self.t_divine_level_2 = TABLE_SCROLLS_DIVINE_LEVEL_2
        self.t_divine_level_3 = TABLE_SCROLLS_DIVINE_LEVEL_3
        self.t_divine_level_4 = TABLE_SCROLLS_DIVINE_LEVEL_4
        self.t_divine_level_5 = TABLE_SCROLLS_DIVINE_LEVEL_5
        self.t_divine_level_6 = TABLE_SCROLLS_DIVINE_LEVEL_6
        self.t_divine_level_7 = TABLE_SCROLLS_DIVINE_LEVEL_7
        self.t_divine_level_8 = TABLE_SCROLLS_DIVINE_LEVEL_8
        self.t_divine_level_9 = TABLE_SCROLLS_DIVINE_LEVEL_9
        # Scroll details
        self.spell = ''
        self.arcaneness = ''
        self.spell_level = ''
        self.caster_level = ''
        self.price = ''


    def __repr__(self):
        result = '<Scroll'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll a random scroll level
        purpose = 'scroll level'
        roll = self.roll('1d100', purpose)
        random_scroll = self.t_random.find_roll(conn, roll, self.strength, purpose, listener)
        self.spell_level = random_scroll['Spell Level']
        self.caster_level = random_scroll['Caster Level']
        # Roll for the scroll type.
        purpose = 'scroll type'
        roll = self.roll('1d100', purpose)
        scroll_type = self.t_type.find_roll(conn, roll, None, purpose, listener)['Result']
        # Now get the exact scroll.
        words = scroll_type.split(' ')
        commonness = words[0].lower()
        self.arcaneness = words[1].lower()
        # Roll for the spell.
        purpose = 'scroll spell'
        roll = self.roll('1d100', purpose)
        # Note that unlike potions, there are uncommon level 0 scrolls.
        result = None
        if self.arcaneness == 'arcane':
            if self.spell_level == '0':
                result = self.t_arcane_level_0.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '1st':
                result = self.t_arcane_level_1.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '2nd':
                result = self.t_arcane_level_2.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '3rd':
                result = self.t_arcane_level_3.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '4th':
                result = self.t_arcane_level_4.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '5th':
                result = self.t_arcane_level_5.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '6th':
                result = self.t_arcane_level_6.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '7th':
                result = self.t_arcane_level_7.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '8th':
                result = self.t_arcane_level_8.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '9th':
                result = self.t_arcane_level_9.find_roll(conn, roll, commonness, purpose, listener)
        elif self.arcaneness == 'divine':
            if self.spell_level == '0':
                result = self.t_divine_level_0.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '1st':
                result = self.t_divine_level_1.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '2nd':
                result = self.t_divine_level_2.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '3rd':
                result = self.t_divine_level_3.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '4th':
                result = self.t_divine_level_4.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '5th':
                result = self.t_divine_level_5.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '6th':
                result = self.t_divine_level_6.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '7th':
                result = self.t_divine_level_7.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '8th':
                result = self.t_divine_level_8.find_roll(conn, roll, commonness, purpose, listener)
            elif self.spell_level == '9th':
                result = self.t_divine_level_9.find_roll(conn, roll, commonness, purpose, listener)
        self.spell = result['Result']

        # Subtype
        self.subtype = 'Scroll'

        # Item specifics
        self.label = 'Scroll of ' + self.spell
        self.label += ' (' + self.arcaneness
        self.label += ', ' + self.spell_level + ' Level'
        self.label += ', CL ' + self.caster_level + ')'
        self.price = Price(result['Price'])


class Staff(Item):

    def __init__(self):
        Item.__init__(self, KEY_STAFF)
        # Load tables.
        self.t_staves = TABLE_STAVES
        # Staff details.
        self.staff = ''
        self.price = ''


    def __repr__(self):
        result = '<Staff'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for a staff.
        purpose = 'specific staff'
        roll = self.roll('1d100', purpose)
        staff = self.t_staves.find_roll(conn, roll, self.strength, purpose, listener)

        # Subtype
        self.subtype = 'Staff'

        # Item specifics
        self.label = staff['Result']
        self.price = Price(staff['Price'])


class Wand(Item):

    def __init__(self):
        Item.__init__(self, KEY_WAND)
        # Load tables.
        self.t_random = TABLE_RANDOM_WANDS
        self.t_type = TABLE_WAND_TYPE
        self.t_wands_0 = TABLE_WAND_LEVEL_0
        self.t_wands_1 = TABLE_WAND_LEVEL_1
        self.t_wands_2 = TABLE_WAND_LEVEL_2
        self.t_wands_3 = TABLE_WAND_LEVEL_3
        self.t_wands_4 = TABLE_WAND_LEVEL_4
        # Wand details.
        self.spell = ''
        self.spell_level = ''
        self.caster_level = ''
        self.price = ''


    def __repr__(self):
        result = '<Wand'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for spell level.
        purpose = 'wand level'
        roll = self.roll('1d100', purpose)
        wand_spell = self.t_random.find_roll(conn, roll, self.strength, purpose, listener)
        self.spell_level = wand_spell['Spell Level']
        self.caster_level = wand_spell['Caster Level']
        # Roll for type.
        purpose = 'wand type'
        roll = self.roll('1d100', purpose)
        wand_type = self.t_type.find_roll(conn, roll, None, purpose, listener)
        commonness = wand_type['Result'].lower()
        # Roll for the actual wand.
        purpose = 'wand spell'
        roll = self.roll('1d100', purpose)
        result = None
        if self.spell_level == '0':
            result = self.t_wands_0.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '1st':
            result = self.t_wands_1.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '2nd':
            result = self.t_wands_2.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '3rd':
            result = self.t_wands_3.find_roll(conn, roll, commonness, purpose, listener)
        elif self.spell_level == '4th':
            result = self.t_wands_4.find_roll(conn, roll, commonness, purpose, listener)
        self.spell = result['Result']

        # Subtype
        self.subtype = 'Wand'

        # Item specifics
        self.label = 'Wand of ' + self.spell
        self.label += ' (' + self.spell_level + ' Level'
        self.label += ', CL ' + self.caster_level + ')'
        self.price = Price(result['Price'])
        

class WondrousItem(Item):

    def __init__(self):
        Item.__init__(self, KEY_WONDROUS_ITEM)
        # Load tables.
        self.t_random = TABLE_WONDROUS_ITEMS
        self.t_belt = TABLE_WONDROUS_ITEMS_BELT
        self.t_body = TABLE_WONDROUS_ITEMS_BODY
        self.t_chest = TABLE_WONDROUS_ITEMS_CHEST
        self.t_eyes = TABLE_WONDROUS_ITEMS_EYES
        self.t_feet = TABLE_WONDROUS_ITEMS_FEET
        self.t_hands = TABLE_WONDROUS_ITEMS_HANDS
        self.t_head = TABLE_WONDROUS_ITEMS_HEAD
        self.t_headband = TABLE_WONDROUS_ITEMS_HEADBAND
        self.t_neck = TABLE_WONDROUS_ITEMS_NECK
        self.t_shoulders = TABLE_WONDROUS_ITEMS_SHOULDERS
        self.t_slotless = TABLE_WONDROUS_ITEMS_SLOTLESS
        self.t_wrists = TABLE_WONDROUS_ITEMS_WRISTS
        # Wondrous item details
        self.slot = ''
        self.item = ''
        self.price = '0 gp'
        # Unlike the other classes, we may do least minor.
        # So, don't modify self.strength to "fix" that.


    def __repr__(self):
        result = '<WondrousItem'
        result += '>'
        return result


    def lookup(self, conn, listener):
        # If we don't have a subtype, roll for one.
        if self.subtype in [None, '']:
            # Roll for subtype.
            purpose = 'wondrous item slot'
            roll = self.roll('1d100', purpose)
            self.subtype = self.t_random.find_roll(conn, roll, None, purpose, listener)['Result']
        # Note that 'least minor' is only valid for slotless.
        if self.subtype != 'Slotless' and self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        purpose = 'specific wondrous item'
        roll = self.roll('1d100', purpose)
        result = None
        if self.subtype == 'Belts':
            result = self.t_belt.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Body':
            result = self.t_body.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Chest':
            result = self.t_chest.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Eyes':
            result = self.t_eyes.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Feet':
            result = self.t_feet.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Hands':
            result = self.t_hands.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Head':
            result = self.t_head.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Headband':
            result = self.t_headband.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Neck':
            result = self.t_neck.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Shoulders':
            result = self.t_shoulders.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Wrists':
            result = self.t_wrists.find_roll(conn, roll, self.strength, purpose, listener)
        elif self.subtype == 'Slotless':
            result = self.t_slotless.find_roll(conn, roll, self.strength, purpose, listener)
        # The table might be directing us to roll on another table.
        if result != None and result['Result'] == ROLL_LEAST_MINOR:
            purpose = 'least minor wondrous item'
            roll = self.roll('1d100', purpose)
            result = None
            # This special result only happens on the slotless table.
            result = self.t_slotless.find_roll(conn, roll, 'least minor', purpose, listener)
        # Perform a final check on the rolled item.
        if result == None:
            return

        # Subtype
        # (already taken care of)

        # Item specifics
        self.label = result['Result']
        self.price = Price(result['Price'])

    
# A dictionary that maps from an item type string to an Item subclass
# We won't do any fancy registration stuff, just use a fixed table.
ITEM_SUBCLASSES = {
        KEY_ARMOR         : Armor,
        KEY_WEAPON        : Weapon,
        KEY_POTION        : Potion,
        KEY_RING          : Ring,
        KEY_ROD           : Rod,
        KEY_SCROLL        : Scroll,
        KEY_STAFF         : Staff,
        KEY_WAND          : Wand,
        KEY_WONDROUS_ITEM : WondrousItem
    }

# Tester
if __name__ == '__main__':

    def test(price, expected_str):
        p = Price(price)
        print('Test: "', price, '" --> ', p, ' = ', expected_str, sep='')
        assert(p.compute() == expected_str)

    # These tests don't work in European locales, but I'm not too concerned
    # at the moment.
    test(0  , '0.00 gp')
    test(0.5, '0.50 gp')
    test(1.5, '1.50 gp')
    test(1000, '1,000.00 gp')
    test('' , '<error> gp')
    test('0 cp', '0.00 gp')
    test('10 cp', '0.10 gp')
    test('1 sp', '0.10 gp')
    test('10 sp', '1.00 gp')
    # Some of these strings are really strange, and perhaps _shouldn't_ be
    # considered valid, but we'll let it slide.
    test('1sp1cp', '0.11 gp')
    test('1sp1 cp', '0.11 gp')
    test('1sp 1cp', '0.11 gp')
    test('1sp 1 cp', '0.11 gp')
    test('1 sp1cp', '0.11 gp')
    test('1 sp1 cp', '0.11 gp')
    test('1 sp 1cp', '0.11 gp')
    test('1 sp 1 cp', '0.11 gp')
    test('1sp,1cp', '0.11 gp')
    test('1sp,1 cp', '0.11 gp')
    test('1sp, 1cp', '0.11 gp')
    test('1sp ,1cp', '0.11 gp')
    test('1sp , 1cp', '0.11 gp')
    test('1sp, 1 cp', '0.11 gp')
    test('1sp ,1 cp', '0.11 gp')
    test('1sp , 1 cp', '0.11 gp')
    test('1 sp,1cp', '0.11 gp')
    test('1 sp,1 cp', '0.11 gp')
    test('1 sp, 1cp', '0.11 gp')
    test('1 sp ,1cp', '0.11 gp')
    test('1 sp , 1cp', '0.11 gp')
    test('1 sp, 1 cp', '0.11 gp')
    test('1 sp ,1 cp', '0.11 gp')
    test('1 sp , 1 cp', '0.11 gp')
    test('1gp1sp1cp', '1.11 gp')
    test('1 gp 1sp1 cp', '1.11 gp')
    test('1gp,1sp 1cp', '1.11 gp')
    test('1 gp1sp 1 cp', '1.11 gp')
    test('1gp 1 sp1cp', '1.11 gp')
    test('1 gp,1 sp1 cp', '1.11 gp')
    test('1gp1 sp 1cp', '1.11 gp')
    test('1 gp 1 sp 1 cp', '1.11 gp')
    test('1gp,1sp,1cp', '1.11 gp')
    test('1 gp1sp,1 cp', '1.11 gp')
    test('1gp 1sp, 1cp', '1.11 gp')
    test('1 gp,1sp ,1cp', '1.11 gp')
    test('1gp1sp , 1cp', '1.11 gp')
    test('1 gp 1sp, 1 cp', '1.11 gp')
    test('1gp,1sp ,1 cp', '1.11 gp')
    test('1 gp1sp , 1 cp', '1.11 gp')
    test('1gp 1 sp,1cp', '1.11 gp')
    test('1 gp,1 sp,1 cp', '1.11 gp')
    test('1gp1 sp, 1cp', '1.11 gp')
    test('1 gp 1 sp ,1cp', '1.11 gp')
    test('1gp,1 sp , 1cp', '1.11 gp')
    test('1 gp1 sp, 1 cp', '1.11 gp')
    test('1gp 1 sp ,1 cp', '1.11 gp')
    test('1 gp,1 sp , 1 cp', '1.11 gp')
