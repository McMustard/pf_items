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
This module implements the bulk of item generation for the Pathfinder Item
Generator.
'''

from __future__ import print_function
import random
import re

# Local imports
import rollers
import generate

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

# Data file names
FILE_ITEMTYPES = 't_itemtypes'

# Tables
# Filled in on first use

TABLE_TYPES_LOADED = False
TABLE_TYPES_MINOR = []
TABLE_TYPES_MEDIUM = []
TABLE_TYPES_MAJOR = []

# Maps the parameter specification of an item type to its standardized value.
# Use a key converted to lower case to perform the lookup.

ITEM_TYPE_MAP = {
        'armor'            : 'Armor/Shield',
        'armor/shield'     : 'Armor/Shield',
        'armor and shield' : 'Armor/Shield',
        'armor or shield' : 'Armor/Shield',
        'weapon'           : 'Weapon',
        'potion'           : 'Potion',
        'ring'             : 'Ring',
        'rod'              : 'Rod',
        'scroll'           : 'Scroll',
        'staff'            : 'Staff',
        'wand'             : 'Wand',
        'wondrous item'    : 'Wondrous Item',
        'wondrous'         : 'Wondrous Item' }


#
# Functions

def generate_generic(strength, roller, base_value):
    # Here, strength is merely 'minor', 'medium', 'major', so we need to
    # further qualify it with 'lesser' or 'greater'.
    
    # We may decide to change this later, but at least for now, the choice
    # between them will be 50/50.  Because slotless wondrous item can also
    # be 'least minor', use least if the roll is less than 25.  Item types
    # without the 'least' level will simply treat it as 'lesser'.
    full_strength = 'greater '
    roll = roller.roll('1d100')
    if roll <= 25 and strength == 'minor':
        full_strength = 'least '
    elif roll <= 50:
        full_strength = 'lesser '
    full_strength += strength

    # Now, select an item type.
    roll = roller.roll('1d100')
    # This lookup only needs minor/medium/major.
    kind = get_item_type(strength, roll)

    return generate_specific_item(full_strength, kind, roller)


def generate_item(description, roller):
    # description is of the form: lesser/greater major/medium/minor <kind>
    parts = description.split(' ')
    strength = ' '.join(parts[0:2])
    kind = ' '.join(parts[2:])
    # Now we have the parts in a usable form.
    return generate_specific_item(strength, kind, roller)


def generate_specific_item(strength, kind, roller):
    # Create an object.
    item = create_item(kind)

    # Finish generating the item
    return item.generate(strength, roller)


def create_item(kind):
    # Create the apropriate Item subclass.
    subclass = ITEM_SUBCLASSES[kind]
    result = subclass.__new__(subclass)
    result.__init__()
    return result


def load_item_types(filename):
    global TABLE_TYPES_LOADED
    global TABLE_TYPES_MINOR
    global TABLE_TYPES_MEDIUM
    global TABLE_TYPES_MAJOR
    if TABLE_TYPES_LOADED:
        return
    f = open(filename, 'r')
    # Throw away the first through third lines, headers.
    # Eventually, we can read them in for metadata.
    f.readline()
    f.readline()
    f.readline()
    # Now read the remaining lines.
    for line in f:
        data = line[:-1].split('\t')
        TABLE_TYPES_MINOR.append ({'type': data[0], 'range': data[1]})
        TABLE_TYPES_MEDIUM.append({'type': data[0], 'range': data[2]})
        TABLE_TYPES_MAJOR.append ({'type': data[0], 'range': data[3]})
    f.close()
    TABLE_TYPES_LOADED = True


def get_item_type(strength, roll):
    # Load Item Types
    load_item_types(FILE_ITEMTYPES)
    # Select the appropriate table.
    global TABLE_TYPES_MINOR
    global TABLE_TYPES_MEDIUM
    global TABLE_TYPES_MAJOR
    table = None
    # Look for the roll among the mins and maxes.
    if strength == 'minor':
        for row in TABLE_TYPES_MINOR:
            if in_range(roll, row['range']): return row['type']
    elif strength == 'medium':
        for row in TABLE_TYPES_MEDIUM:
            if in_range(roll, row['range']): return row['type']
    elif strength == 'major':
        for row in TABLE_TYPES_MAJOR:
            if in_range(roll, row['range']): return row['type']
    return ''


def split_range(range_str):
    span = (0,0)
    if '-' in range_str:
        span = tuple(range_str.split('-'))
    elif '–' in range_str:
        # Note: the character mentioned here is hex 2013, not a simple dash
        span = tuple(range_str.split('–'))
    elif '—' in range_str:
        # Note: the character mentioned here is hex 2014, not a simple dash
        span = tuple(range_str.split('—'))
    else:
        span = (range_str, range_str)
    return (int(span[0]), int(span[1]))


def in_range(roll, range_str):
    (rmin, rmax) = split_range(range_str)
    return roll >= rmin and roll <= rmax


def total_range(range_str):
    (rmin, rmax) = split_range(range_str)
    return rmax - rmin + 1


def parse_gold_price(price_str):
    match = re.match('\+(.*) gp', price_str)
    if match:
        return int(match.group(1).replace(',', ''))
    else:
        print('Error: cannot extract a price from', price_str)
    return 0


def parse_enhancement_price(price_str):
    match = re.match('\+(\d+) bonus', price_str)
    if match:
        return int(match.group(1))
    else:
        print('Error: cannot extract enhancement bonus from', price_str)
    return 0


#
# Classes
#


class TableRowMissingError(Exception):

    def __init__(self, message):
        # Base class init.
        Exception.__init__(self, message)


class Table(object):

    def __init__(self, filename):
        self.loaded = False
        self.metadata = []
        self.columns = []
        self.rows = []
        self.filename = filename


    def load(self):
        if self.loaded: return
        # Open the file.
        f = open(self.filename, 'r')
        self.header = f.readline()[:-1]
        if not self.header.startswith('#'):
            print('Error in table file', self.filename)
        self.metadata = f.readline()[:-1].split('\t')
        self.columns = f.readline()[:-1].split('\t')
        col_roll = None
        col_count = len(self.columns)
        try:
            col_roll = self.columns.index('Roll')
        except ValueError:
            print('Error finding Roll column in table', self.filename)
            raise
        # Total up all the roll ranges
        total_rolls = 0
        row_number = 0
        # Read entries as tab-separated values.
        for line in f:
            if line.startswith('#'): continue
            row = line[:-1].split('\t')
            if len(row) < col_count:
                print('Error: row', row_number, 'does not have enough columns')
            total_rolls += total_range(row[col_roll])
            self.rows.append(row)
            row_number += 1
        if total_rolls % 100 != 0:
            # This does not seem to work for slotless wondrous items.
            # It may be due to the single-digit numbers?
            #print('Error: The rows in table', self.filename, 'do not total ' +
            #        'up to a multiple of 100; a row is probably missing.')
            pass
        self.loaded = True


    def find_roll(self, roll, strength):
        self.load()
        # Indices of commonly used columns
        col_roll = None
        col_strength = None
        try:
            col_roll = self.columns.index('Roll')
        except ValueError:
            print('Error finding Roll column in table', self.filename)
            raise
        try:
            col_strength = self.columns.index('Strength')
        except ValueError:
            # No Strength column is not necessarily an error.
            pass
        for row in self.rows:
            check_range = in_range(roll, row[col_roll])
            check_str = False
            if col_strength is not None:
                check_str = row[col_strength] == strength
            else:
                check_str = True
            if check_range and check_str:
                # Return a dictionary of the resulting data
                return dict(zip(self.columns, row))
        raise TableRowMissingError('Table ' + self.filename + ': ' +
                'There is no row for strength: ' + str(strength) +
                ', roll: ' + str(roll) )


    def total_rolls(self, column_name, column_value):
        self.load()
        col_roll = None
        col_search = None
        try:
            col_roll = self.columns.index('Roll')
        except ValueError:
            print('Error finding Roll column in table', self.filename)
            raise
        try:
            col_search = self.columns.index(column_name)
        except ValueError:
            print('Error finding',column_name ,'column in table',
                    self.filename)
            raise
        total = 0
        for row in self.rows:
            if row[col_search] == column_value:
                total += total_range(row[col_roll])
        return total
            

# Ultimate Equipment Tables

TABLE_MAGIC_ARMOR_AND_SHIELDS         = Table('ue/Magic_Armor_and_Shields')
TABLE_MAGIC_WEAPONS                   = Table('ue/Magic_Weapons')
TABLE_METAMAGIC_RODS_1                = Table('ue/Metamagic_Rods_1')
TABLE_METAMAGIC_RODS_2                = Table('ue/Metamagic_Rods_2')
TABLE_METAMAGIC_RODS_3                = Table('ue/Metamagic_Rods_3')
TABLE_POTION_OR_OIL_LEVEL_0           = Table('ue/Potion_or_Oil_Level_0')
TABLE_POTION_OR_OIL_LEVEL_1           = Table('ue/Potion_or_Oil_Level_1')
TABLE_POTION_OR_OIL_LEVEL_2           = Table('ue/Potion_or_Oil_Level_2')
TABLE_POTION_OR_OIL_LEVEL_3           = Table('ue/Potion_or_Oil_Level_3')
TABLE_POTION_OR_OIL_TYPE              = Table('ue/Potion_or_Oil_Type')
TABLE_RANDOM_ARMOR_OR_SHIELD          = Table('ue/Random_Armor_or_Shield')
TABLE_RANDOM_ART_OBJECTS              = Table('ue/Random_Art_Objects')
TABLE_RANDOM_GEMS                     = Table('ue/Random_Gems')
TABLE_RANDOM_POTIONS_AND_OILS         = Table('ue/Random_Potions_and_Oils')
TABLE_RANDOM_SCROLLS                  = Table('ue/Random_Scrolls')
TABLE_RANDOM_WANDS                    = Table('ue/Random_Wands')
TABLE_RANDOM_WEAPON                   = Table('ue/Random_Weapon')
TABLE_RINGS                           = Table('ue/Rings')
TABLE_RODS                            = Table('ue/Rods')
TABLE_SCROLLS_ARCANE_LEVEL_0          = Table('ue/Scrolls_Arcane_Level_0')
TABLE_SCROLLS_ARCANE_LEVEL_1          = Table('ue/Scrolls_Arcane_Level_1')
TABLE_SCROLLS_ARCANE_LEVEL_2          = Table('ue/Scrolls_Arcane_Level_2')
TABLE_SCROLLS_ARCANE_LEVEL_3          = Table('ue/Scrolls_Arcane_Level_3')
TABLE_SCROLLS_ARCANE_LEVEL_4          = Table('ue/Scrolls_Arcane_Level_4')
TABLE_SCROLLS_ARCANE_LEVEL_5          = Table('ue/Scrolls_Arcane_Level_5')
TABLE_SCROLLS_ARCANE_LEVEL_6          = Table('ue/Scrolls_Arcane_Level_6')
TABLE_SCROLLS_ARCANE_LEVEL_7          = Table('ue/Scrolls_Arcane_Level_7')
TABLE_SCROLLS_ARCANE_LEVEL_8          = Table('ue/Scrolls_Arcane_Level_8')
TABLE_SCROLLS_ARCANE_LEVEL_9          = Table('ue/Scrolls_Arcane_Level_9')
TABLE_SCROLLS_DIVINE_LEVEL_0          = Table('ue/Scrolls_Divine_Level_0')
TABLE_SCROLLS_DIVINE_LEVEL_1          = Table('ue/Scrolls_Divine_Level_1')
TABLE_SCROLLS_DIVINE_LEVEL_2          = Table('ue/Scrolls_Divine_Level_2')
TABLE_SCROLLS_DIVINE_LEVEL_3          = Table('ue/Scrolls_Divine_Level_3')
TABLE_SCROLLS_DIVINE_LEVEL_4          = Table('ue/Scrolls_Divine_Level_4')
TABLE_SCROLLS_DIVINE_LEVEL_5          = Table('ue/Scrolls_Divine_Level_5')
TABLE_SCROLLS_DIVINE_LEVEL_6          = Table('ue/Scrolls_Divine_Level_6')
TABLE_SCROLLS_DIVINE_LEVEL_7          = Table('ue/Scrolls_Divine_Level_7')
TABLE_SCROLLS_DIVINE_LEVEL_8          = Table('ue/Scrolls_Divine_Level_8')
TABLE_SCROLLS_DIVINE_LEVEL_9          = Table('ue/Scrolls_Divine_Level_9')
TABLE_SCROLL_TYPE                     = Table('ue/Scroll_Type')
TABLE_SPECIAL_ABILITIES_AMMUNITION    = Table('ue/Special_Abilities_Ammunition')
TABLE_SPECIAL_ABILITIES_ARMOR         = Table('ue/Special_Abilities_Armor')
TABLE_SPECIAL_ABILITIES_MELEE_WEAPON  = Table('ue/Special_Abilities_Melee_Weapon')
TABLE_SPECIAL_ABILITIES_RANGED_WEAPON = Table('ue/Special_Abilities_Ranged_Weapon')
TABLE_SPECIAL_ABILITIES_SHIELD        = Table('ue/Special_Abilities_Shield')
TABLE_SPECIAL_BANE                    = Table('ue/Special_Bane')
TABLE_SPECIAL_SLAYING_ARROW           = Table('ue/Special_Slaying_Arrow')
TABLE_SPECIFIC_ARMOR                  = Table('ue/Specific_Armor')
TABLE_SPECIFIC_CURSED_ITEMS           = Table('ue/Specific_Cursed_Items')
TABLE_SPECIFIC_SHIELDS                = Table('ue/Specific_Shields')
TABLE_SPECIFIC_WEAPONS                = Table('ue/Specific_Weapons')
TABLE_STAVES                          = Table('ue/Staves')
TABLE_WAND_LEVEL_0                    = Table('ue/Wand_Level_0')
TABLE_WAND_LEVEL_1                    = Table('ue/Wand_Level_1')
TABLE_WAND_LEVEL_2                    = Table('ue/Wand_Level_2')
TABLE_WAND_LEVEL_3                    = Table('ue/Wand_Level_3')
TABLE_WAND_LEVEL_4                    = Table('ue/Wand_Level_4')
TABLE_WAND_TYPE                       = Table('ue/Wand_Type')
TABLE_WONDROUS_ITEMS                  = Table('ue/Wondrous_Items')
TABLE_WONDROUS_ITEMS_BELT             = Table('ue/Wondrous_Items_Belt')
TABLE_WONDROUS_ITEMS_BODY             = Table('ue/Wondrous_Items_Body')
TABLE_WONDROUS_ITEMS_CHEST            = Table('ue/Wondrous_Items_Chest')
TABLE_WONDROUS_ITEMS_EYES             = Table('ue/Wondrous_Items_Eyes')
TABLE_WONDROUS_ITEMS_FEET             = Table('ue/Wondrous_Items_Feet')
TABLE_WONDROUS_ITEMS_HANDS            = Table('ue/Wondrous_Items_Hands')
TABLE_WONDROUS_ITEMS_HEAD             = Table('ue/Wondrous_Items_Head')
TABLE_WONDROUS_ITEMS_HEADBAND         = Table('ue/Wondrous_Items_Headband')
TABLE_WONDROUS_ITEMS_NECK             = Table('ue/Wondrous_Items_Neck')
TABLE_WONDROUS_ITEMS_SHOULDERS        = Table('ue/Wondrous_Items_Shoulders')
TABLE_WONDROUS_ITEMS_SLOTLESS         = Table('ue/Wondrous_Items_Slotless')
TABLE_WONDROUS_ITEMS_WRISTS           = Table('ue/Wondrous_Items_Wrists')


class Item(object):

    #
    # Methods that are not meant to be overridden

    # Initializes object variables
    def __init__(self, kind):
        #print('Item.__init__')
        # The kind of item, stored mainly so a subclass doesn't need to know
        # its own name.
        self.kind = kind
        # All the rolls that led to the selection of the item
        self.rolls = []
        # The base cost of an item, if any
        self.base_cost = 0
        # The item label, before any additions, which subclasses track on
        # their own.
        self.label = ''
        # Generation parameters
        # Strength: lesser/greater + major/medium/minor
        self.strength = ''
        # Roller
        self.roller = None


    # Generates the item, referring to the subclass, following the Template
    # Method design pattern.
    def generate(self, strength, roller):
        # Initialize generation parameters.
        self.strength = strength
        self.roller = roller
        # Call the subclass generation initializer.
        self.generate_init()

        self.lookup()
        return self


    # Rolls and keeps a log of the rolled values.
    def roll(self, roll_expr):
        roll = self.roller.roll(roll_expr)
        self.rolls.append((roll_expr, roll))
        return roll


    #
    # Methods that are meant to be overridden

    # The standard __repr__ method
    def __repr__(self):
        result = '<Item '
        result += 'rolls:{} '.format(self.rolls)
        result += 'base_cost:{} '.format(self.base_cost)
        result += 'label:{}'.format(self.label)
        result += '>'
        return result


    # The standard __str__ method
    def __str__(self):
        return 'generic item'


    # Default implementation of the generation initializer.
    # A generation initializer is necessary in case an item needs to be
    # rerolled using the same parameters.
    def generate_init(self):
        pass


class Armor(Item):

    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        #print("Armor.__init__")
        # Load tables
        self.t_random          = TABLE_RANDOM_ARMOR_OR_SHIELD
        self.t_magic           = TABLE_MAGIC_ARMOR_AND_SHIELDS
        self.t_specific_armor  = TABLE_SPECIFIC_ARMOR
        self.t_specials_armor  = TABLE_SPECIAL_ABILITIES_ARMOR
        self.t_specific_shield = TABLE_SPECIFIC_SHIELDS
        self.t_specials_shield = TABLE_SPECIAL_ABILITIES_SHIELD
        self.armor_threshold = self.t_random.total_rolls('Type', 'armor')
        self.re_enhancement = re.compile('\+(\d+) armor or shield')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')
        # Placeholder for armor details
        self.placeholder = ''


    def __repr__(self):
        result = '<Armor'
        result += '>'
        return result


    def __str__(self):
        # TODO Armor: or Shield:, not both
        result = 'Armor/Shield: ' + self.placeholder
        return result


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        # Look up the roll.
        rolled_armor = self.t_random.find_roll(roll, None)
        armor_base = rolled_armor['Result']
        armor_type = rolled_armor['Type']

        # Roll for the magic property.
        roll = self.roll('1d100')
        rolled_magic = self.t_magic.find_roll(roll, self.strength)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific armor or shield'):
            self.placeholder = self.get_specific_item(armor_type)
        else:
            self.placeholder = armor_base + ' ' + self.get_magic_bonuses(
                    armor_type, magic_type)


    def get_magic_bonuses(self, armor_type, specification):
        # "Regular" magic item, with an assortment of bonuses.
        # We already rolled, and know what we need: specification param.
        enhancement_bonus = 0
        special_count = 0
        special_strength = 0
        # This part is always at the beginning
        match = self.re_enhancement.match(specification)
        if match:
            enhancement_bonus = int(match.group(1))
        # This might be in the middle of the string
        match = self.re_specials.search(specification)
        if match:
            special_count = {'one': 1, 'two': 2}[match.group(1)]
            special_strength = '+' + match.group(2)
        # Construct a string listing the specials.  The enhancement goes first.
        specials = '+' + str(enhancement_bonus)
        # Also keep totals for cost calculation.
        cost_enhancement = enhancement_bonus
        cost_static = 0
        # Add specials!
        for i in range(special_count):
            # Roll for a special
            roll = self.roll('1d100')
            # Look it up.
            result = None
            if armor_type == 'armor':
                result = self.t_specials_armor.find_roll(roll,
                        special_strength)
            else:
                result = self.t_specials_shield.find_roll(roll,
                        special_strength)
            special = result['Result']
            price = result['Price']
            if price.endswith(' gp'):
                cost_static += parse_gold_price(price)
            elif price.endswith(' bonus'):
                cost_enhancement += parse_enhancement_price(price)
            else:
                print('Error: this item cannot be priced.')
            # Add it to the string.
            specials += '/' + special
        return specials


    def get_specific_item(self, armor_type):
        # Roll for the specific armor.
        roll = self.roll('1d100')
        # Look it up.
        if armor_type == 'armor':
            result = self.t_specific_armor.find_roll(roll, self.strength)
        else:
            result = self.t_specific_shield.find_roll(roll, self.strength)
        return result['Result']


class Weapon(Item):

    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        #print("Weapon.__init__")
        # Load tables
        self.t_random          = TABLE_RANDOM_WEAPON
        self.t_magic           = TABLE_MAGIC_WEAPONS
        self.t_specific_weapon = TABLE_SPECIFIC_WEAPONS
        self.t_specials_melee  = TABLE_SPECIAL_ABILITIES_MELEE_WEAPON
        self.t_specials_ranged = TABLE_SPECIAL_ABILITIES_RANGED_WEAPON
        self.re_enhancement = re.compile('\+(\d+) weapon')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')
        # Item details
        self.weapon_base = ''
        self.weapon_type = ''
        self.wield_type = ''
        self.weapon_properties = set()
        # Base weapon price, or price if specific weapon.
        self.weapon_base_cost = 0
        # Weapon enhancement bonus
        self.magic_enhancement = 0
        # Tuple: (special name, enhancement cost, static cost)
        self.magic_specials = []
        # Enhancement cost of specials
        self.magic_specials_enhancement_cost = 0
        # Gold cost of specials
        self.magic_specials_gold_cost = 0


    def __repr__(self):
        result = '<Weapon'
        result += '>'
        return result


    def __str__(self):
        result = 'Weapon: ' + self.weapon_base
        if self.magic_enhancement:
            result += ' +' + str(self.magic_enhancement)
        if self.magic_specials:
            result += '/' + '/'.join([x for (x,y,z) in self.magic_specials])
        return result


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        rolled_weapon = self.t_random.find_roll(roll, None)
        # Fill out weapon details.
        self.weapon_base = rolled_weapon['Result']
        self.weapon_type = rolled_weapon['Type']
        self.damage_type = rolled_weapon['Damage Type']
        self.wield_type = rolled_weapon['Wield Type']
        self.weapon_properties = []
        self.magic_specials = []
        # Roll for the magic property.
        roll = self.roll('1d100')
        rolled_magic = self.t_magic.find_roll(roll, self.strength)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific weapon'):
            self.get_specific_item()
        else:
            self.get_magic_bonuses(magic_type)


    def get_magic_bonuses(self, specification):
        # The weapon properties determine what kinds of enchantments can be
        # applied.  We don't do this in 'lookup' because it becomes invalid if
        # it needs to be replaced with a specific weapon.
        if 'B' in self.damage_type: self.weapon_properties.append('bludgeoning')
        if 'P' in self.damage_type: self.weapon_properties.append('piercing')
        if 'S' in self.damage_type: self.weapon_properties.append('slashing')
        self.weapon_properties.extend(
                [x for x in self.wield_type.split(',') if len(x) > 0])
        # TODO track cost to bound it
        cost_enhancement = 0
        # This part is always at the beginning
        match = self.re_enhancement.match(specification)
        if match:
            self.magic_enhancement = int(match.group(1))
            cost_enhancement += self.magic_enhancement
        # This might be present, multiple times
        match = self.re_specials.findall(specification)
        for part in match:
            special_count = {'one': 1, 'two': 2}[part[0]]
            special_strength = '+' + str(part[1])
            # Add specials!
            for i in range(special_count):
                # Don't stop until we find a valid special
                while True:
                    # Generate a special.
                    special = self.generate_special(special_strength)
                    if special:
                        # Note costs.
                        #cost_static += parse_gold_price(special[2])
                        #cost_enhancement += parse_enhancement_price(special[1])
                        # Add it to the list.
                        self.magic_specials.append(special)
                        # Found one
                        break


    def get_specific_item(self):
        # Roll for the specific weapon.
        roll = self.roll('1d100')
        result = self.t_specific_weapon.find_roll(roll, self.strength)
        self.weapon_base = result['Result']
        self.price = result['Price']


    def generate_special(self, special_strength):
        # Roll for a special
        roll = self.roll('1d100')
        self.rolls.append(roll)
        # Look it up.
        result = None
        if self.weapon_type == 'melee':
            result = self.t_specials_melee.find_roll(roll,
                    special_strength)
        else:
            result = self.t_specials_ranged.find_roll(roll,
                    special_strength)
        special = result['Result']
        price = result['Price']
        qualifiers = [x for x in set(result['Qualifiers'].split(','))
                if len(x) > 0]
        disqualifiers = [x for x in set(result['Disqualifiers'].split('.'))
                if len(x) > 0]
        # Check qualifications.
        if self.check_qualifiers(set(self.weapon_properties),
                set(qualifiers), set(disqualifiers)) == False:
            return None
        if price.endswith(' gp'):
            return (special, '', price)
        elif price.endswith(' bonus'):
            return (special, price, '')
        return (special, '', '')


    def check_qualifiers(self, properties, qualifiers, disqualifiers):
        if len(properties) > 0:
            if len(qualifiers) > 0:
                if len(properties.intersection(qualifiers)) == 0:
                    return False
            if len(disqualifiers) > 0:
                if len(properties.intersection( disqualifiers)) != 0:
                    return False
        return True


class Potion(Item):

    def __init__(self):
        Item.__init__(self, KEY_POTION)
        #print("Potion.__init__")
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


    def __repr__(self):
        result = '<Potion'
        result += '>'
        return result


    def __str__(self):
        result = 'Potion: ' + self.spell
        result += ' (' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        return result


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the potion level.
        roll = self.roll('1d100')
        result = self.t_random.find_roll(roll, self.strength)
        self.spell_level = result['Spell Level']
        self.caster_level = result['Caster Level']
        # Determine common or uncommon
        commonness = 'Common' # default
        if self.spell_level != '0':
            # Roll for common/uncomon
            roll = self.roll('1d100')
            commonness = self.t_type.find_roll(roll, '')['Result']
        commonness = commonness.lower()
        # Now roll for and look up the spell.
        roll = self.roll('1d100')
        result = None
        if self.spell_level == '0':
            result = self.t_potions_0.find_roll(roll, commonness)
        elif self.spell_level == '1st':
            result = self.t_potions_1.find_roll(roll, commonness)
        elif self.spell_level == '2nd':
            result = self.t_potions_2.find_roll(roll, commonness)
        elif self.spell_level == '3rd':
            result = self.t_potions_3.find_roll(roll, commonness)
        self.spell = result['Result']


class Ring(Item):

    def __init__(self):
        Item.__init__(self, KEY_RING)
        #print("Ring.__init__")
        # Load tables.
        self.t_rings = TABLE_RINGS
        # Ring details.
        self.ring = ''


    def __repr__(self):
        result = '<Ring'
        result += '>'
        return result


    def __str__(self):
        return 'Ring: ' + self.ring


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the ring.
        roll = self.roll('1d100')
        # Look it up.
        ring = self.t_rings.find_roll(roll, self.strength)
        self.ring = ring['Result']


class Rod(Item):

    def __init__(self):
        Item.__init__(self, KEY_ROD)
        #print("Rod.__init__")
        # Load tables.
        self.t_rods = TABLE_RODS
        # Rod details.
        self.rod = ''


    def __repr__(self):
        result = '<Rod'
        result += '>'
        return result


    def __str__(self):
        return 'Rod: ' + self.rod


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the rod.
        roll = self.roll('1d100')
        # Look it up.
        rod = self.t_rods.find_roll(roll, self.strength)
        self.rod = rod['Result']


class Scroll(Item):

    def __init__(self):
        Item.__init__(self, KEY_SCROLL)
        #print("Scroll.__init__")
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


    def __repr__(self):
        result = '<Scroll'
        result += '>'
        return result


    def __str__(self):
        result = 'Scroll: ' + self.spell
        result += ' (' + self.arcaneness
        result += ', ' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        return result


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll a random scroll level
        roll = self.roll('1d100')
        random_scroll = self.t_random.find_roll(roll, self.strength)
        self.spell_level = random_scroll['Spell Level']
        self.caster_level = random_scroll['Caster Level']
        # Roll for the scroll type.
        roll = self.roll('1d100')
        scroll_type = self.t_type.find_roll(roll, '')['Result']
        # Roll for the spell.
        roll = self.roll('1d100')
        # Now get the exact scroll.
        words = scroll_type.split(' ')
        commonness = words[0].lower()
        self.arcaneness = words[1].lower()
        # Note that unlike potions, there are uncommon level 0 scrolls.
        result = None
        if self.arcaneness == 'arcane':
            if self.spell_level == '0':
                result = self.t_arcane_level_0.find_roll(roll, commonness)
            elif self.spell_level == '1st':
                result = self.t_arcane_level_1.find_roll(roll, commonness)
            elif self.spell_level == '2nd':
                result = self.t_arcane_level_2.find_roll(roll, commonness)
            elif self.spell_level == '3rd':
                result = self.t_arcane_level_3.find_roll(roll, commonness)
            elif self.spell_level == '4th':
                result = self.t_arcane_level_4.find_roll(roll, commonness)
            elif self.spell_level == '5th':
                result = self.t_arcane_level_5.find_roll(roll, commonness)
            elif self.spell_level == '6th':
                result = self.t_arcane_level_6.find_roll(roll, commonness)
            elif self.spell_level == '7th':
                result = self.t_arcane_level_7.find_roll(roll, commonness)
            elif self.spell_level == '8th':
                result = self.t_arcane_level_8.find_roll(roll, commonness)
            elif self.spell_level == '9th':
                result = self.t_arcane_level_9.find_roll(roll, commonness)
        elif self.arcaneness == 'divine':
            if self.spell_level == '0':
                result = self.t_divine_level_0.find_roll(roll, commonness)
            elif self.spell_level == '1st':
                result = self.t_divine_level_1.find_roll(roll, commonness)
            elif self.spell_level == '2nd':
                result = self.t_divine_level_2.find_roll(roll, commonness)
            elif self.spell_level == '3rd':
                result = self.t_divine_level_3.find_roll(roll, commonness)
            elif self.spell_level == '4th':
                result = self.t_divine_level_4.find_roll(roll, commonness)
            elif self.spell_level == '5th':
                result = self.t_divine_level_5.find_roll(roll, commonness)
            elif self.spell_level == '6th':
                result = self.t_divine_level_6.find_roll(roll, commonness)
            elif self.spell_level == '7th':
                result = self.t_divine_level_7.find_roll(roll, commonness)
            elif self.spell_level == '8th':
                result = self.t_divine_level_8.find_roll(roll, commonness)
            elif self.spell_level == '9th':
                result = self.t_divine_level_9.find_roll(roll, commonness)
        self.spell = result['Result']


class Staff(Item):

    def __init__(self):
        Item.__init__(self, KEY_STAFF)
        #print("Staff.__init__")
        # Load tables.
        self.t_staves = TABLE_STAVES
        # Staff details.
        self.staff = ''


    def __repr__(self):
        result = '<Staff'
        result += '>'
        return result


    def __str__(self):
        return 'Staff: ' + self.staff


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for a staff.
        roll = self.roll('1d100')
        staff = self.t_staves.find_roll(roll, self.strength)
        self.staff = staff['Result']


class Wand(Item):

    def __init__(self):
        Item.__init__(self, KEY_WAND)
        #print("Wand.__init__")
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


    def __repr__(self):
        result = '<Wand'
        result += '>'
        return result


    def __str__(self):
        result = 'Wand: ' + self.spell
        result += ' (' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        return result


    def lookup(self):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for spell level.
        roll = self.roll('1d100')
        wand_spell = self.t_random.find_roll(roll, self.strength)
        self.spell_level = wand_spell['Spell Level']
        self.caster_level = wand_spell['Caster Level']
        # Roll for type.
        roll = self.roll('1d100')
        wand_type = self.t_type.find_roll(roll, '')
        commonness = wand_type['Result'].lower()
        # Roll for the actual wand.
        roll = self.roll('1d100')
        result = None
        if self.spell_level == '0':
            result = self.t_wands_0.find_roll(roll, commonness)
        elif self.spell_level == '1st':
            result = self.t_wands_1.find_roll(roll, commonness)
        elif self.spell_level == '2nd':
            result = self.t_wands_2.find_roll(roll, commonness)
        elif self.spell_level == '3rd':
            result = self.t_wands_3.find_roll(roll, commonness)
        elif self.spell_level == '4th':
            result = self.t_wands_4.find_roll(roll, commonness)
        self.spell = result['Result']
        

class WondrousItem(Item):

    def __init__(self):
        Item.__init__(self, KEY_WONDROUS_ITEM)
        #print("WondrousItem.__init__")
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
        # Unlike the other classes, we may do least minor.
        # So, don't modify self.strength to "fix" that.


    def __repr__(self):
        result = '<WondrousItem'
        result += '>'
        return result


    def __str__(self):
        result = 'Wondrous Item: '
        result += self.item
        result += ' (' + self.slot + ')'
        return result


    def lookup(self):
        # Roll for slot.
        roll = self.roll('1d100')
        self.slot = self.t_random.find_roll(roll, '')['Result']
        # Note that 'least minor' is only valid for slotless.
        if self.slot != 'Slotless' and self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        result = None
        if self.slot == 'Belts':
            result = self.t_belt.find_roll(roll, self.strength)
        elif self.slot == 'Body':
            result = self.t_body.find_roll(roll, self.strength)
        elif self.slot == 'Chest':
            result = self.t_chest.find_roll(roll, self.strength)
        elif self.slot == 'Eyes':
            result = self.t_eyes.find_roll(roll, self.strength)
        elif self.slot == 'Feet':
            result = self.t_feet.find_roll(roll, self.strength)
        elif self.slot == 'Hands':
            result = self.t_hands.find_roll(roll, self.strength)
        elif self.slot == 'Head':
            result = self.t_head.find_roll(roll, self.strength)
        elif self.slot == 'Headband':
            result = self.t_headband.find_roll(roll, self.strength)
        elif self.slot == 'Neck':
            result = self.t_neck.find_roll(roll, self.strength)
        elif self.slot == 'Shoulders':
            result = self.t_shoulders.find_roll(roll, self.strength)
        elif self.slot == 'Wrists':
            result = self.t_wrists.find_roll(roll, self.strength)
        elif self.slot == 'Slotless':
            result = self.t_slotless.find_roll(roll, self.strength)
        # TODO Note that 'least' slotless items aren't accounted for.
        self.item = result['Result']

    
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


# Test routine

if __name__ == '__main__':
    # Assert that the string to subclass dictionary works.
    for key in ITEM_SUBCLASSES:
        assert Item.factory(key) != None

    # Generate a few items
    print('Generating ---------')
    item = Armor()
    item.generate('minor', rollers.PseudorandomRoller())
    print(item)
    

# Some old code for reference

# # Now, generate an item of that type.
# (item, rolls, cost) = generateItem(strength, kind, roller, rolls)
# #return '[' + str(roll).rjust(3, ' ') + '] ' + kind + ': ' + item
# print('[', ', '.join([str(x).rjust(3, ' ') for x in rolls]), ']',
#         sep='')
# print('\t', kind, ', ', item, '; ', cost, ' gp', sep='')
