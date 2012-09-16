#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

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

# Ultimate Equipment Tables

FILE_MAGIC_ARMOR_AND_SHIELDS        = 'ue/Magic_Armor_and_Shields'
FILE_MAGIC_WEAPONS                  = 'ue/Magic_Weapons'
FILE_METAMAGIC_RODS_1               = 'ue/Metamagic_Rods_1'
FILE_METAMAGIC_RODS_2               = 'ue/Metamagic_Rods_2'
FILE_METAMAGIC_RODS_3               = 'ue/Metamagic_Rods_3'
FILE_POTION_OR_OIL_LEVEL_0          = 'ue/Potion_or_Oil_Level_0'
FILE_POTION_OR_OIL_LEVEL_1          = 'ue/Potion_or_Oil_Level_1'
FILE_POTION_OR_OIL_LEVEL_2          = 'ue/Potion_or_Oil_Level_2'
FILE_POTION_OR_OIL_LEVEL_3          = 'ue/Potion_or_Oil_Level_3'
FILE_POTION_OR_OIL_TYPE             = 'ue/Potion_or_Oil_Type'
FILE_RANDOM_ARMOR_OR_SHIELD         = 'ue/Random_Armor_or_Shield'
FILE_RANDOM_ART_OBJECTS             = 'ue/Random_Art_Objects'
FILE_RANDOM_GEMS                    = 'ue/Random_Gems'
FILE_RANDOM_POTIONS_AND_OILS        = 'ue/Random_Potions_and_Oils'
FILE_RANDOM_SCROLLS                 = 'ue/Random_Scrolls'
FILE_RANDOM_WANDS                   = 'ue/Random_Wands'
FILE_RANDOM_WEAPON                  = 'ue/Random_Weapon'
FILE_RINGS                          = 'ue/Rings'
FILE_RODS                           = 'ue/Rods'
FILE_SCROLLS_ARCANE_LEVEL_0         = 'ue/Scrolls_Arcane_Level_0'
FILE_SCROLLS_ARCANE_LEVEL_1         = 'ue/Scrolls_Arcane_Level_1'
FILE_SCROLLS_ARCANE_LEVEL_2         = 'ue/Scrolls_Arcane_Level_2'
FILE_SCROLLS_ARCANE_LEVEL_3         = 'ue/Scrolls_Arcane_Level_3'
FILE_SCROLLS_ARCANE_LEVEL_4         = 'ue/Scrolls_Arcane_Level_4'
FILE_SCROLLS_ARCANE_LEVEL_5         = 'ue/Scrolls_Arcane_Level_5'
FILE_SCROLLS_ARCANE_LEVEL_6         = 'ue/Scrolls_Arcane_Level_6'
FILE_SCROLLS_ARCANE_LEVEL_7         = 'ue/Scrolls_Arcane_Level_7'
FILE_SCROLLS_ARCANE_LEVEL_8         = 'ue/Scrolls_Arcane_Level_8'
FILE_SCROLLS_ARCANE_LEVEL_9         = 'ue/Scrolls_Arcane_Level_9'
FILE_SCROLLS_DIVINE_LEVEL_0         = 'ue/Scrolls_Divine_Level_0'
FILE_SCROLLS_DIVINE_LEVEL_1         = 'ue/Scrolls_Divine_Level_1'
FILE_SCROLLS_DIVINE_LEVEL_2         = 'ue/Scrolls_Divine_Level_2'
FILE_SCROLLS_DIVINE_LEVEL_3         = 'ue/Scrolls_Divine_Level_3'
FILE_SCROLLS_DIVINE_LEVEL_4         = 'ue/Scrolls_Divine_Level_4'
FILE_SCROLLS_DIVINE_LEVEL_5         = 'ue/Scrolls_Divine_Level_5'
FILE_SCROLLS_DIVINE_LEVEL_6         = 'ue/Scrolls_Divine_Level_6'
FILE_SCROLLS_DIVINE_LEVEL_7         = 'ue/Scrolls_Divine_Level_7'
FILE_SCROLLS_DIVINE_LEVEL_8         = 'ue/Scrolls_Divine_Level_8'
FILE_SCROLLS_DIVINE_LEVEL_9         = 'ue/Scrolls_Divine_Level_9'
FILE_SCROLL_TYPE                    = 'ue/Scroll_Type'
FILE_SPECIAL_ABILITIES_AMMUNITION   = 'ue/Special_Abilities_Ammunition'
FILE_SPECIAL_ABILITIES_ARMOR        = 'ue/Special_Abilities_Armor'
FILE_SPECIAL_ABILITIES_MELEE_WEAPON = 'ue/Special_Abilities_Melee_Weapon'
FILE_SPECIAL_ABILITIES_RANGED_WEAPON= 'ue/Special_Abilities_Ranged_Weapon'
FILE_SPECIAL_ABILITIES_SHIELD       = 'ue/Special_Abilities_Shield'
FILE_SPECIAL_BANE                   = 'ue/Special_Bane'
FILE_SPECIAL_SLAYING_ARROW          = 'ue/Special_Slaying_Arrow'
FILE_SPECIFIC_ARMOR                 = 'ue/Specific_Armor'
FILE_SPECIFIC_CURSED_ITEMS          = 'ue/Specific_Cursed_Items'
FILE_SPECIFIC_SHIELDS               = 'ue/Specific_Shields'
FILE_SPECIFIC_WEAPONS               = 'ue/Specific_Weapons'
FILE_STAVES                         = 'ue/Staves'
FILE_WAND_LEVEL_0                   = 'ue/Wand_Level_0'
FILE_WAND_LEVEL_1                   = 'ue/Wand_Level_1'
FILE_WAND_LEVEL_2                   = 'ue/Wand_Level_2'
FILE_WAND_LEVEL_3                   = 'ue/Wand_Level_3'
FILE_WAND_LEVEL_4                   = 'ue/Wand_Level_4'
FILE_WAND_TYPE                      = 'ue/Wand_Type'
FILE_WONDROUS_ITEMS                 = 'ue/Wondrous_Items'
FILE_WONDROUS_ITEMS_BELT            = 'ue/Wondrous_Items_Belt'
FILE_WONDROUS_ITEMS_BODY            = 'ue/Wondrous_Items_Body'
FILE_WONDROUS_ITEMS_CHEST           = 'ue/Wondrous_Items_Chest'
FILE_WONDROUS_ITEMS_EYES            = 'ue/Wondrous_Items_Eyes'
FILE_WONDROUS_ITEMS_FEET            = 'ue/Wondrous_Items_Feet'
FILE_WONDROUS_ITEMS_HANDS           = 'ue/Wondrous_Items_Hands'
FILE_WONDROUS_ITEMS_HEAD            = 'ue/Wondrous_Items_Head'
FILE_WONDROUS_ITEMS_HEADBAND        = 'ue/Wondrous_Items_Headband'
FILE_WONDROUS_ITEMS_NECK            = 'ue/Wondrous_Items_Neck'
FILE_WONDROUS_ITEMS_SHOULDERS       = 'ue/Wondrous_Items_Shoulders'
FILE_WONDROUS_ITEMS_SLOTLESS        = 'ue/Wondrous_Items_Slotless'
FILE_WONDROUS_ITEMS_WRISTS          = 'ue/Wondrous_Items_Wrists'


# Functions

def generate_generic(strength, roller, base_value):
    # Here, strength is merely 'minor', 'medium', 'major', so we need to
    # further qualify it with 'lesser' or 'greater'.
    
    # We don't want to use the roller mechanism, since this is not a table
    # choice, but rather an artifact of the new item system not having
    # provision for linkage with the settlement item generation system.

    # We may decide to change this later, but at least for now, the choice
    # between them will be 50/50.
    full_strength = random.choice(['lesser ', 'greater ']) + strength

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
    # Throw away the first and second lines, headers.
    # Eventually, we can read them in for metadata.
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
    if strength == 'minor':
        table = TABLE_TYPES_MINOR
    elif strength == 'medium':
        table = TABLE_TYPES_MEDIUM
    elif strength == 'major':
        table = TABLE_TYPES_MAJOR
    # Look for the roll among the mins and maxes.
    if table != None:
        for row in table:
            if in_range(roll, row['range']): return row['type']
    return ''


def split_range(range_str):
    span = (0,0)
    if '-' in range_str:
        span = tuple(range_str.split('-'))
    elif '–' in range_str:
        # Note: the character mentioned here is hex 2013, not a simple dash
        span = tuple(range_str.split('–'))
    else:
        span = (range_str, range_str)
    return (int(span[0]), int(span[1]))


def in_range(roll, range_str):
    (rmin, rmax) = split_range(range_str)
    return roll >= rmin and roll <= rmax


def total_range(range_str):
    (rmin, rmax) = split_range(range_str)
    return rmax - rmin + 1


def parse_price(price_str):
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
        self.metadata = []
        self.columns = []
        self.rows = []
        self.filename = filename
        self.load_file(filename)


    def load_file(self, filename):
        # Open the file.
        f = open(filename, 'r')
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
            print('Error: The rows in table', self.filename, 'do not total ' +
                    'up to a multiple of 100; a row is probably missing.')


    def find_roll(self, roll, strength):
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
        if col_strength:
            raise TableRowMissingError('Table ' + self.filename + ': ' +
                    'There is no row for strength: ' + strength +
                    ', roll: ' + str(roll) )
        else:
            raise TableRowMissingError('Table ' + self.filename + ': ' +
                    'There is no row for strength: <none>, ' +
                    'roll: ' + str(roll))


    def total_rolls(self, column_name, column_value):
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
        # Strength: major, medium, minor
        self.strength = ''
        # Roller
        self.roller = None

    # Remembers a roll for traceability
    def log_roll(self, roll):
        self.rolls.append(roll)

    # Generates the item, referring to the subclass, following the Template
    # Method design pattern.
    def generate(self, strength, roller):
        # Initialize generation parameters.
        self.strength = strength
        self.roller = roller
        # Call the subclass generation initializer.
        self.generate_init()

        return self.lookup(strength, roller)


    # TODO Just a placeholder until I figure out how this will work.
    def generateSpecials(strength, kind, roller, rolls):
        # If the weapon special ability is not specific enough, pick something.
        if kind == 'Weapon Special Ability':
            roll = roller.roll('1d100')
            rolls.append(roll)
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
            rolls.append(roll)
            special = special[:-1] + ':' + \
                    lookupItem(TABLE_CRB, strength, kind, roll)[0]

        # Generate more as needed.
        if special == 'ROLL TWICE':
            specials.extend(generateSpecials(strength, kind, roller, rolls))
            specials.extend(generateSpecials(strength, kind, roller, rolls))
        else:
            specials.append(special)

        # Put everything in one string and return it.
        return specials


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
        self.t_random          = Table(FILE_RANDOM_ARMOR_OR_SHIELD)
        self.t_magic           = Table(FILE_MAGIC_ARMOR_AND_SHIELDS)
        self.t_specific_armor  = Table(FILE_SPECIFIC_ARMOR)
        self.t_specials_armor  = Table(FILE_SPECIAL_ABILITIES_ARMOR)
        self.t_specific_shield = Table(FILE_SPECIFIC_SHIELDS)
        self.t_specials_shield = Table(FILE_SPECIAL_ABILITIES_SHIELD)
        self.armor_threshold = self.t_random.total_rolls('Type', 'armor')
        self.re_enhancement = re.compile('\+(\d+) armor or shield')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')


    def __repr__(self):
        result = '<Armor'
        result += '>'
        return result


    def __str__(self):
        return ''


    def lookup(self, strength, roller):
        # Roll for the item.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        # Look up the roll.
        mundane = self.t_random.find_roll(roll, None)
        armor_base = mundane['Result']
        armor_type = mundane['Type']

        # Roll for the magic property.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        magic = self.t_magic.find_roll(roll, strength)
        magic_type = magic['Result']

        # Handle it
        if magic_type.endswith('specific armor or shield'):
            return self.get_specific_item(roller, strength, armor_type)
        else:
            return armor_base + ' ' + self.get_magic_bonuses(roller,
                    strength, armor_type, magic_type)


    def get_magic_bonuses(self, roller, strength, armor_type, specification):
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
            roll = roller.roll('1d100')
            self.rolls.append(roll)
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
                cost_static += parse_price(price)
            elif price.endswith(' bonus'):
                cost_enhancement += parse_enhancement_price(price)
            else:
                print('Error: this item cannot be priced.')
            # Add it to the string.
            specials += '/' + special
        return specials


    def get_specific_item(self, roller, strength, armor_type):
        # Roll for the specific armor.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        # Look it up.
        if armor_type == 'armor':
            result = self.t_specific_armor.find_roll(roll, strength)
        else:
            result = self.t_specific_shield.find_roll(roll, strength)
        return result['Result']


class Weapon(Item):

    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        #print("Weapon.__init__")
        # Load tables
        self.t_random          = Table(FILE_RANDOM_WEAPON)
        self.t_magic           = Table(FILE_MAGIC_WEAPONS)
        self.t_specific_weapon = Table(FILE_SPECIFIC_WEAPONS)
        self.t_specials_melee  = Table(FILE_SPECIAL_ABILITIES_MELEE_WEAPON)
        self.t_specials_ranged = Table(FILE_SPECIAL_ABILITIES_RANGED_WEAPON)
        self.re_enhancement = re.compile('\+(\d+) weapon')
        self.re_specials = re.compile('with (\w+) \+(\d+) special')


    def __repr__(self):
        result = '<Weapon'
        result += '>'
        return result


    def __str__(self):
        return ''


    def lookup(self, strength, roller):
        # Roll for the item.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        # Look up the roll.
        mundane = self.t_random.find_roll(roll, None)
        weapon_base = mundane['Result']
        weapon_type = mundane['Type']

        # Roll for the magic property.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        magic = self.t_magic.find_roll(roll, strength)
        magic_type = magic['Result']

        # Handle it
        if magic_type.endswith('specific weapon'):
            return self.get_specific_item(roller, strength, weapon_type)
        else:
            return weapon_base + ' ' + self.get_magic_bonuses(roller,
                    strength, weapon_type, magic_type)


    def get_magic_bonuses(self, roller, strength, weapon_type, specification):
        # Construct a 'specials' string
        specials = ''
        # Also keep totals for cost calculation.
        cost_enhancement = 0
        cost_static = 0
        # "Regular" magic item, with an assortment of bonuses.
        # We already rolled, and know what we need: specification param.
        enhancement_bonus = 0
        # This part is always at the beginning
        match = self.re_enhancement.match(specification)
        if match:
            enhancement_bonus = int(match.group(1))
            cost_enhancement += enhancement_bonus
            specials += '+' + str(enhancement_bonus)
        # This might be present, multiple times
        match = self.re_specials.findall(specification)
        for part in match:
            special_count = {'one': 1, 'two': 2}[part[0]]
            special_strength = '+' + str(part[1])
            # Add specials!
            for i in range(special_count):
                # Roll for a special
                roll = roller.roll('1d100')
                self.rolls.append(roll)
                # Look it up.
                result = None
                if weapon_type == 'melee':
                    result = self.t_specials_melee.find_roll(roll,
                            special_strength)
                else:
                    result = self.t_specials_ranged.find_roll(roll,
                            special_strength)
                special = result['Result']
                price = result['Price']
                if price.endswith(' gp'):
                    cost_static += parse_price(price)
                elif price.endswith(' bonus'):
                    cost_enhancement += parse_enhancement_price(price)
                else:
                    print('Error: this item cannot be priced.')
                # Add it to the string.
                specials += '/' + special
        return specials


    def get_specific_item(self, roller, strength, weapon_type):
        # Roll for the specific armor.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        # Look it up.
        result = self.t_specific_weapon.find_roll(roll, strength)
        return result['Result']


class Potion(Item):
    def __init__(self):
        Item.__init__(self, KEY_POTION)
        #print("Potion.__init__")

    def __repr__(self):
        result = '<Potion'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class Ring(Item):
    def __init__(self):
        Item.__init__(self, KEY_RING)
        #print("Ring.__init__")

    def __repr__(self):
        result = '<Ring'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class Rod(Item):
    def __init__(self):
        Item.__init__(self, KEY_ROD)
        #print("Rod.__init__")

    def __repr__(self):
        result = '<Rod'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class Scroll(Item):
    def __init__(self):
        Item.__init__(self, KEY_SCROLL)
        #print("Scroll.__init__")

    def __repr__(self):
        result = '<Scroll'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class Staff(Item):
    def __init__(self):
        Item.__init__(self, KEY_STAFF)
        #print("Staff.__init__")

    def __repr__(self):
        result = '<Staff'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class Wand(Item):
    def __init__(self):
        Item.__init__(self, KEY_WAND)
        #print("Wand.__init__")

    def __repr__(self):
        result = '<Wand'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


class WondrousItem(Item):
    def __init__(self):
        Item.__init__(self, KEY_WONDROUS_ITEM)
        #print("WondrousItem.__init__")

    def __repr__(self):
        result = '<WondrousItem'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass

    
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
