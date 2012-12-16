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
This module implements the bulk of item generation for the Pathfinder Item
Generator.
'''

#
# Library imports

import locale
import os
import random
import re

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

def generate_generic(conn, strength, roller, base_value):
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
    kind = get_item_type(conn, strength, roll)

    return generate_specific_item(conn, full_strength, kind, roller)


def generate_item(conn, description, roller):
    # description is of the form: lesser/greater major/medium/minor <kind>
    parts = description.split(' ')
    strength = ' '.join(parts[0:2])
    kind = ' '.join(parts[2:])
    # Now we have the parts in a usable form.
    return generate_specific_item(conn, strength, kind, roller)


def generate_specific_item(conn, strength, kind, roller):
    # Create an object.
    item = create_item(kind)

    # Finish generating the item
    return item.generate(conn, strength, roller)


def create_item(kind):
    # Create the apropriate Item subclass.
    subclass = ITEM_SUBCLASSES[kind]
    result = subclass.__new__(subclass)
    result.__init__()
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



#
# Classes
#


class BadPrice(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class Price(object):

    def __init__(self, enhancement_type):
        self.enhancement_type = enhancement_type
        self.gold = 0.0
        self.enhancement = 0


    def add_part(self, price_str):
        if type(price_str) == int or type(price_str) == float:
            self.add_gold(price_str)
        elif price_str.endswith(' gp'):
            self.add_gold(price_str)
        elif price_str.endswith(' sp'):
            self.add_silver(price_str)
        elif price_str.endswith(' cp'):
            self.add_copper(price_str)
        elif price_str.endswith(' bonus'):
            self.add_enhancement(price_str)
        else:
            raise BadPrice('price string ' + price_str + ' does not end with " gp" or " bonus"')


    def add_copper(self, price_str):
        if type(price_str) == int or type(price_str) == float:
            self.gold += price_str * 0.01
        else:
            match = re.match('(\+)?(.*) cp', price_str)
            if match:
                self.gold += float(match.group(2).replace(',', '')) * 0.01
            else:
                raise BadPrice('cannot extract a gold price from ' + price_str)


    def add_silver(self, price_str):
        if type(price_str) == int or type(price_str) == float:
            self.gold += price_str * 0.1
        else:
            match = re.match('(\+)?(.*) sp', price_str)
            if match:
                self.gold += float(match.group(2).replace(',', '')) * 0.1
            else:
                raise BadPrice('cannot extract a gold price from ' + price_str)


    def add_gold(self, price_str):
        if type(price_str) == int or type(price_str) == float:
            self.gold += price_str
        else:
            match = re.match('(\+)?(.*) gp', price_str)
            if match:
                self.gold += float(match.group(2).replace(',', ''))
            else:
                raise BadPrice('cannot extract a gold price from ' + price_str)


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
        cost = self.gold
        if self.enhancement > 0:
             temp = (self.enhancement ** 2) * 1000
             if self.enhancement_type == 'weapon':
                 temp *= 2
             cost += temp
        return locale.format_string('%d', cost, grouping=True) + ' gp'


class Table(object):

    def __init__(self, table):
        self.table = table

    def find_roll(self, conn, roll, strength):
        cursor = conn.cursor()
        if strength == None:
            cursor.execute('''SELECT * FROM {0} WHERE (? >= Roll_low) AND
                    (? <= Roll_high);'''.format(self.table),
                    (roll, roll) )
        else:
            cursor.execute('''SELECT * FROM {0} WHERE (? >= Roll_low) AND
                    (? <= Roll_high) AND (? = Strength);'''.format(
                        self.table), (roll, roll, strength) )
        result = cursor.fetchone()
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
    def generate(self, conn, strength, roller):
        # Initialize generation parameters.
        self.strength = strength
        self.roller = roller
        # Call the subclass generation initializer.
        self.generate_init()

        self.lookup(conn)
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


    # Type of item
    def type(self):
        return 'unspecified item'


    # Default implementation of the generation initializer.
    # A generation initializer is necessary in case an item needs to be
    # rerolled using the same parameters.
    def generate_init(self):
        pass


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
        #self.armor_threshold = self.t_random.total_rolls('Type', 'armor')
        self.armor_trheshold = 10 # TODO
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
        self.armor_price = ''
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


    def __str__(self):
        result = ''
        # Armor or Shield
        if self.armor_type == 'armor':
            result += 'Armor: '
        else:
            result += 'Shield: '
        # Item specifics
        if self.is_generic:
            result += self.armor_base
            if self.enhancement > 0:
                result += ' +' + str(self.enhancement)
                for spec in self.specials.keys():
                    result += '/' + spec
        else:
            result += self.specific_name
        # Cost
        result += '; ' + self.get_cost()
        return result


    def type(self):
        return 'armor or shield'


    def get_cost(self):
        try:
            if self.is_generic:
                # Compose a price.
                price = Price(self.armor_type)
                # Start with the base cost.
                price.add_gold(self.armor_price)
                # Add magic costs.
                if self.enhancement:
                    # Masterwork component
                    price.add_gold(150)
                    # Initial enhancement bonus
                    price.add_enhancement(self.enhancement)
                    # Special costs
                    for spec in self.specials.keys():
                        price.add_part(self.specials[spec])
                return price.compute()
            else:
                return self.specific_price
        except BadPrice as ex:
            return 'error with price calculation'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        # Look up the roll.
        rolled_armor = self.t_random.find_roll(conn, roll, None)
        self.armor_base = rolled_armor['Result']
        self.armor_type = rolled_armor['Type']
        self.armor_price = rolled_armor['Price']
        self.enhancement = 0

        # Roll for the magic property.
        roll = self.roll('1d100')
        rolled_magic = self.t_magic.find_roll(conn, roll, self.strength)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific armor or shield'):
            self.make_specific(conn)
        else:
            self.make_generic(conn, magic_type)


    def make_generic(self, conn, specification):
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
            # Roll for a special
            roll = self.roll('1d100')
            # Look it up.
            result = None
            if self.armor_type == 'armor':
                result = self.t_specials_armor.find_roll(conn, roll,
                        special_strength)
            else:
                result = self.t_specials_shield.find_roll(conn, roll,
                        special_strength)
            special = result['Result']
            price = result['Price']
            # If we don't already have the special, add it.
            if special not in self.specials.keys():
                self.specials[special] = price
                special_count -= 1


    def make_specific(self, conn):
        # Specific
        self.is_generic = False
        # Roll for the specific armor.
        roll = self.roll('1d100')
        # Look it up.
        result = None
        if self.armor_type == 'armor':
            result = self.t_specific_armor.find_roll(conn, 
                    roll, self.strength)
        else:
            result = self.t_specific_shield.find_roll(conn, roll,
                    self.strength)
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
        self.weapon_price = ''
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


    def __str__(self):
        result = 'Weapon: '
        if self.is_generic:
            result += self.weapon_base
            if self.enhancement > 0:
                result += ' +' + str(self.enhancement)
                for spec in self.specials.keys():
                    result += '/' + spec
        else:
            result += self.specific_name
        # Cost
        result += '; ' + self.get_cost()
        return result


    def type(self):
        return 'weapon'


    def get_cost(self):
        try:
            if self.is_generic:
                # Compose a price.
                price = Price('weapon')
                # Start with the base cost.
                price.add_gold(self.weapon_price)
                # Add magic costs.
                if self.enhancement:
                    # Masterwork component
                    price.add_gold(300)
                    # Initial enhancement bonus
                    price.add_enhancement(self.enhancement)
                    # Special costs
                    for spec in self.specials.keys():
                        price.add_part(self.specials[spec])
                return price.compute()
            else:
                return self.specific_price
        except BadPrice as ex:
            return 'error with price calculation'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        # Look up the roll.
        rolled_weapon = self.t_random.find_roll(conn, roll, None)
        self.weapon_base = rolled_weapon['Result']
        self.weapon_type = rolled_weapon['Type']
        self.damage_type = rolled_weapon['Damage Type']
        self.wield_type = rolled_weapon['Wield Type']
        self.weapon_price = rolled_weapon['Price']
        self.enhancement = 0

        # Roll for the magic property.
        roll = self.roll('1d100')
        rolled_magic = self.t_magic.find_roll(conn, roll, self.strength)
        magic_type = rolled_magic['Result']

        # Handle it
        if magic_type.endswith('specific weapon'):
            self.make_specific(conn)
        else:
            self.make_generic(conn, magic_type)


    def make_generic(self, conn, specification):
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
        retries = 0
        while special_count > 0:
            # Generate a special.
            result = self.generate_special(conn, special_strength, properties)
            if result == None:
                # Retry
                retries += 1
                if retries > 100:
                    # TODO find something better
                    raise Exception('too many retries')
                continue
            special = result['Result']
            price = result['Price']
            # If we don't already have the special, add it.
            if special and special not in self.specials.keys():
                self.specials[special] = price
                special_count -= 1
        # This tracks the number of retries for the sake of information.
        #if retries > 0:
        #    rf = open('retries.txt', 'a')
        #    rf.write(str(retries))
        #    rf.close()


    def generate_special(self, conn, special_strength, properties):
        # Roll for a special.
        roll = self.roll('1d100')
        # Look it up.
        result = None
        if self.weapon_type == 'melee':
            result = self.t_specials_melee.find_roll(conn, roll,
                    special_strength)
        else:
            result = self.t_specials_ranged.find_roll(conn, roll,
                    special_strength)
        special = result['Result']
        price = result['Price']
        qualifiers = [x for x in set(result['Qualifiers'].split(','))
                if len(x) > 0]
        disqualifiers = [x for x in set(result['Disqualifiers'].split('.'))
                if len(x) > 0]
        # Check qualifications.
        if self.check_qualifiers(set(properties),
                set(qualifiers), set(disqualifiers)) == False:
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


    def make_specific(self, conn):
        # Specific
        self.is_generic = False
        # Roll for the specific weapon.
        roll = self.roll('1d100')
        # Look it up.
        result = self.t_specific_weapon.find_roll(conn, roll, self.strength)
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


    def __str__(self):
        result = 'Potion: ' + self.spell
        result += ' (' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        result += '; ' + self.price
        return result


    def type(self):
        return 'potion'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the potion level.
        roll = self.roll('1d100')
        result = self.t_random.find_roll(conn, roll, self.strength)
        self.spell_level = result['Spell Level']
        self.caster_level = result['Caster Level']
        # Determine common or uncommon
        commonness = 'Common' # default
        if self.spell_level != '0':
            # Roll for common/uncomon
            roll = self.roll('1d100')
            commonness = self.t_type.find_roll(conn, roll, None)['Result']
        commonness = commonness.lower()
        # Now roll for and look up the spell.
        roll = self.roll('1d100')
        result = None
        if self.spell_level == '0':
            result = self.t_potions_0.find_roll(conn, roll, commonness)
        elif self.spell_level == '1st':
            result = self.t_potions_1.find_roll(conn, roll, commonness)
        elif self.spell_level == '2nd':
            result = self.t_potions_2.find_roll(conn, roll, commonness)
        elif self.spell_level == '3rd':
            result = self.t_potions_3.find_roll(conn, roll, commonness)
        self.spell = result['Result']
        self.price = result['Price']


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


    def __str__(self):
        return 'Ring: ' + self.ring + '; ' + self.price


    def type(self):
        return 'ring'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the ring.
        roll = self.roll('1d100')
        # Look it up.
        ring = self.t_rings.find_roll(conn, roll, self.strength)
        self.ring = ring['Result']
        self.price = ring['Price']


class Rod(Item):

    def __init__(self):
        Item.__init__(self, KEY_ROD)
        # Load tables.
        self.t_rods = TABLE_RODS
        # Rod details.
        self.rod = ''
        self.price = ''


    def __repr__(self):
        result = '<Rod'
        result += '>'
        return result


    def __str__(self):
        return 'Rod: ' + self.rod + '; ' + self.price


    def type(self):
        return 'rod'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the rod.
        roll = self.roll('1d100')
        # Look it up.
        rod = self.t_rods.find_roll(conn, roll, self.strength)
        self.rod = rod['Result']
        self.price = rod['Price']


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


    def __str__(self):
        result = 'Scroll: ' + self.spell
        result += ' (' + self.arcaneness
        result += ', ' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        result += '; ' + self.price
        return result


    def type(self):
        return 'scroll'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll a random scroll level
        roll = self.roll('1d100')
        random_scroll = self.t_random.find_roll(conn, roll, self.strength)
        self.spell_level = random_scroll['Spell Level']
        self.caster_level = random_scroll['Caster Level']
        # Roll for the scroll type.
        roll = self.roll('1d100')
        scroll_type = self.t_type.find_roll(conn, roll, None)['Result']
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
                result = self.t_arcane_level_0.find_roll(conn, roll, commonness)
            elif self.spell_level == '1st':
                result = self.t_arcane_level_1.find_roll(conn, roll, commonness)
            elif self.spell_level == '2nd':
                result = self.t_arcane_level_2.find_roll(conn, roll, commonness)
            elif self.spell_level == '3rd':
                result = self.t_arcane_level_3.find_roll(conn, roll, commonness)
            elif self.spell_level == '4th':
                result = self.t_arcane_level_4.find_roll(conn, roll, commonness)
            elif self.spell_level == '5th':
                result = self.t_arcane_level_5.find_roll(conn, roll, commonness)
            elif self.spell_level == '6th':
                result = self.t_arcane_level_6.find_roll(conn, roll, commonness)
            elif self.spell_level == '7th':
                result = self.t_arcane_level_7.find_roll(conn, roll, commonness)
            elif self.spell_level == '8th':
                result = self.t_arcane_level_8.find_roll(conn, roll, commonness)
            elif self.spell_level == '9th':
                result = self.t_arcane_level_9.find_roll(conn, roll, commonness)
        elif self.arcaneness == 'divine':
            if self.spell_level == '0':
                result = self.t_divine_level_0.find_roll(conn, roll, commonness)
            elif self.spell_level == '1st':
                result = self.t_divine_level_1.find_roll(conn, roll, commonness)
            elif self.spell_level == '2nd':
                result = self.t_divine_level_2.find_roll(conn, roll, commonness)
            elif self.spell_level == '3rd':
                result = self.t_divine_level_3.find_roll(conn, roll, commonness)
            elif self.spell_level == '4th':
                result = self.t_divine_level_4.find_roll(conn, roll, commonness)
            elif self.spell_level == '5th':
                result = self.t_divine_level_5.find_roll(conn, roll, commonness)
            elif self.spell_level == '6th':
                result = self.t_divine_level_6.find_roll(conn, roll, commonness)
            elif self.spell_level == '7th':
                result = self.t_divine_level_7.find_roll(conn, roll, commonness)
            elif self.spell_level == '8th':
                result = self.t_divine_level_8.find_roll(conn, roll, commonness)
            elif self.spell_level == '9th':
                result = self.t_divine_level_9.find_roll(conn, roll, commonness)
        self.spell = result['Result']
        self.price = result['Price']


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


    def __str__(self):
        return 'Staff: ' + self.staff + '; ' + self.price


    def type(self):
        return 'staff'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for a staff.
        roll = self.roll('1d100')
        staff = self.t_staves.find_roll(conn, roll, self.strength)
        self.staff = staff['Result']
        self.price = staff['Price']


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


    def __str__(self):
        result = 'Wand: ' + self.spell
        result += ' (' + self.spell_level + ' Level'
        result += ', CL ' + self.caster_level + ')'
        result += '; ' + self.price
        return result


    def type(self):
        return 'wand'


    def lookup(self, conn):
        # We don't do 'least minor'
        if self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for spell level.
        roll = self.roll('1d100')
        wand_spell = self.t_random.find_roll(conn, roll, self.strength)
        self.spell_level = wand_spell['Spell Level']
        self.caster_level = wand_spell['Caster Level']
        # Roll for type.
        roll = self.roll('1d100')
        wand_type = self.t_type.find_roll(conn, roll, None)
        commonness = wand_type['Result'].lower()
        # Roll for the actual wand.
        roll = self.roll('1d100')
        result = None
        if self.spell_level == '0':
            result = self.t_wands_0.find_roll(conn, roll, commonness)
        elif self.spell_level == '1st':
            result = self.t_wands_1.find_roll(conn, roll, commonness)
        elif self.spell_level == '2nd':
            result = self.t_wands_2.find_roll(conn, roll, commonness)
        elif self.spell_level == '3rd':
            result = self.t_wands_3.find_roll(conn, roll, commonness)
        elif self.spell_level == '4th':
            result = self.t_wands_4.find_roll(conn, roll, commonness)
        self.spell = result['Result']
        self.price = result['Price']
        

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
        self.price = ''
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
        result += '; ' + self.price
        return result


    def type(self):
        return 'wondrous item'


    def lookup(self, conn):
        # Roll for slot.
        roll = self.roll('1d100')
        self.slot = self.t_random.find_roll(conn, roll, None)['Result']
        # Note that 'least minor' is only valid for slotless.
        if self.slot != 'Slotless' and self.strength == 'least minor':
            self.strength = 'lesser minor'
        # Roll for the item.
        roll = self.roll('1d100')
        result = None
        if self.slot == 'Belts':
            result = self.t_belt.find_roll(conn, roll, self.strength)
        elif self.slot == 'Body':
            result = self.t_body.find_roll(conn, roll, self.strength)
        elif self.slot == 'Chest':
            result = self.t_chest.find_roll(conn, roll, self.strength)
        elif self.slot == 'Eyes':
            result = self.t_eyes.find_roll(conn, roll, self.strength)
        elif self.slot == 'Feet':
            result = self.t_feet.find_roll(conn, roll, self.strength)
        elif self.slot == 'Hands':
            result = self.t_hands.find_roll(conn, roll, self.strength)
        elif self.slot == 'Head':
            result = self.t_head.find_roll(conn, roll, self.strength)
        elif self.slot == 'Headband':
            result = self.t_headband.find_roll(conn, roll, self.strength)
        elif self.slot == 'Neck':
            result = self.t_neck.find_roll(conn, roll, self.strength)
        elif self.slot == 'Shoulders':
            result = self.t_shoulders.find_roll(conn, roll, self.strength)
        elif self.slot == 'Wrists':
            result = self.t_wrists.find_roll(conn, roll, self.strength)
        elif self.slot == 'Slotless':
            result = self.t_slotless.find_roll(conn, roll, self.strength)
        # TODO Note that 'least' slotless items aren't accounted for.
        if result != None:
            self.item = result['Result']
            self.price = result['Price']

    
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

