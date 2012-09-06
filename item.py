#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from __future__ import print_function
import re

# Local imports
import rollers
import generate

# Constants

# Keys into the subclass map, also usable for displaying categories, if
# desired.

KEY_ARMOR         = 'Armor and Shield'
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


# Regular Expressions

RE_SPELL_LEVEL = re.compile('Spell Level (\d+)')


# Functions

# these will actually become methods, but are here for now

def calculatePotionCost(item):
    match = re.match(RE_SPELL_LEVEL, item)
    try:
        spell_level = int(match.group(1))
        caster_level = 2 * spell_level - 1     
        if spell_level == 0:
            spell_level = 0.5
            caster_level = 1
        return 50 * spell_level * caster_level
    except:
        print('Program error when trying to cost a potion:', item)
        return None
    return None

def calculateScrollCost(item):
    match = re.match(RE_SPELL_LEVEL, item)
    try:
        spell_level = int(match.group(1))
        caster_level = 2 * spell_level - 1     
        if spell_level == 0:
            spell_level = 0.5
            caster_level = 1
        return 25 * spell_level * caster_level
    except:
        print('Program error when trying to cost a scroll:', item)
        return None
    return None

def calculateWandCost(item):
    match = re.match(RE_SPELL_LEVEL, item)
    try:
        spell_level = int(match.group(1))
        caster_level = 2 * spell_level - 1     
        if spell_level == 0:
            spell_level = 0.5
            caster_level = 1
        return 750 * spell_level * caster_level
    except:
        print('Program error when trying to cost a wand:', item)
        return None
    return None


def loadItemTypes(filename):
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
        TABLE_TYPES_MINOR.append ({'min': int(data[1]), 'max': int(data[2]),
            'type': data[0]})
        TABLE_TYPES_MEDIUM.append({'min': int(data[3]), 'max': int(data[4]),
            'type': data[0]})
        TABLE_TYPES_MAJOR.append ({'min': int(data[5]), 'max': int(data[6]),
            'type': data[0]})
    f.close()
    TABLE_TYPES_LOADED = True


def getItemType(strength, roll):
    # Load Item Types
    loadItemTypes(FILE_ITEMTYPES)
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
            if roll >= row['min'] and roll <= row['max']:
                return row['type']
    return ''


def inRange(roll, range_str):
    span = (0,0)
    if '-' in range_str:
        span = tuple(range_str.split('-'))
    elif '–' in range_str:
        # Note: the character mentioned here is hex 2013, not a simple dash
        span = tuple(range_str.split('–'))
    else:
        span = (range_str, range_str)
    rmin = int(span[0])
    rmax = int(span[1])
    return roll >= rmin and roll <= rmax
        

#
# Classes
#


class Table(object):

    def __init__(self, filename):
        self.metadata = []
        self.columns = []
        self.rows = []
        self.loadFile(filename)


    def loadFile(self, filename):
        # Open the file.
        f = open(filename, 'r')
        self.metadata = f.readline()[:-1].split('\t')
        self.columns = f.readline()[:-1].split('\t')
        # Read entries as tab-separated values.
        for line in f:
            self.rows.append(line[:-1].split('\t'))


    def findRoll(self, roll, strength):
        # Indices of commonly used columns
        col_roll = None
        col_strength = None
        try:
            col_roll = self.columns.index('Roll')
        except:
            print('Error finding Roll column in table', self.metadata[0])
        try:
            col_strength = self.columns.index('Strength')
        except:
            # No Strength column is not necessarily an error.
            pass
        for row in self.rows:
            check_range = inRange(roll, row[col_roll])
            check_str = False
            if col_strength is not None:
                check_str = row[col_strength] == strength
            else:
                check_str = True
            if check_range and check_str:
                # Return a dictionary of the resulting data
                return dict(zip(self.columns, row))
        return None



class Item(object):

    # Factory constructor
    # kind: the type of item
    #def __new__(cls, kind):
    #    # If being invoked directly, look for an appropriate subclass.
    #    if cls is Item:
    #        # Look up the subclass in the fixed dict.
    #        subclass = ITEM_SUBCLASSES[kind]
    #        # Return a new instance of the subclass.  That, in turn, will call
    #        # this method, which the initial 'if' covers.
    #        return ITEM_SUBCLASSES[kind].__new__(subclass)
    #    # Default implementation
    #    return super(Item, cls).__new__(cls)

    # A class method that implements an Item subclass factory
    @classmethod
    def factory(cls, kind):
        # Create the apropriate Item subclass.
        subclass = ITEM_SUBCLASSES[kind]
        result = subclass.__new__(subclass)
        result.__init__()
        return result

    # A class method that randomly selects an item type, then uses the factory
    # __new__ to create a subclass, which further refines itself with rolls.
    @classmethod
    def select(cls, strength, roller, base_value):
        # First, determine the kind of item to generate.
        roll = roller.roll('1d100')
        kind = getItemType(strength, roll)
        # Create an object.
        item = Item.factory(kind)
        # Add the initial roll to its rolls list
        item.log_roll(roll)
        # Finish generating the item
        return item.generate(strength, roller)

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

        # LEFT OFF HERE ***********************************

        ## Look up an item
        #(item, subtype) = lookupItem(TABLE_CRB, strength, kind, roll)

        ## Check for starred items.  This requires another check.
        #if item[-1] == '*':
        #    # The item name tells us what we need to roll.
        #    nextKind = item[:-1]
        #    roll = roller.roll('1d100')
        #    rolls.append(roll)
        #    (item, subtype) = lookupItem(TABLE_CRB, strength, nextKind, roll)

        #while item == 'ADD SPECIAL, ROLL AGAIN':
        #    # Look up a new item so we know what subtype to seek out.
        #    roll = roller.roll('1d100')
        #    rolls.append(roll)
        #    (item, subtype) = lookupItem(TABLE_CRB, strength, kind, roll)
        #    if item != 'ADD SPECIAL, ROLL AGAIN':
        #        if subtype == '':
        #            print('ERROR!  No subtype for ' + item)
        #            return ''
        #        # Roll up a special.
        #        roll = roller.roll('1d100')
        #        rolls.append(roll)
        #        specials = generateSpecials(strength,
        #            subtype + ' Special Ability', roller, rolls)

        ## Determine the cost of the item, as it might need to be rerolled.
        #cost = pricing.calculateCost(kind, item, specials)

        ## TODO Spells in Potions, Scrolls, Wands
        #if len(specials) > 0:
        #    item = item + ', ' + '/'.join(specials)
        #return (item, rolls, cost)

        return 'Placeholder'


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

    # Default implementation if the generation initializer.
    # A generation initializer is necessary in case an item needs to be
    # rerolled using the same parameters.
    def generate_init(self):
        pass


class Armor(Item):
    def __init__(self):
        Item.__init__(self, KEY_ARMOR)
        # Armor and Shield special abilities
        self.specials = []
        #print("Armor.__init__")
        # Load tables
        self.t_random          = Table(FILE_RANDOM_ARMOR_OR_SHIELD)
        self.t_magic           = Table(FILE_MAGIC_ARMOR_AND_SHIELDS)
        self.t_specific_armor  = Table(FILE_SPECIFIC_ARMOR)
        self.t_specials_armor  = Table(FILE_SPECIAL_ABILITIES_ARMOR)
        self.t_specific_shield = Table(FILE_SPECIFIC_SHIELDS)
        self.t_specials_shield = Table(FILE_SPECIAL_ABILITIES_SHIELD)

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
        # Lookup an item.
        mundane = self.t_random.findRoll(roll, None)
        print('Armor/Shield:', mundane['Result'], '('+mundane['Type']+')')
        # Lookup a magic property.
        roll = roller.roll('1d100')
        self.rolls.append(roll)
        magic = None
        if mundane['Type'] == 'armor':
            magic = self.t_magic.findRoll(roll, strength)
        # TODO LEFT OFF HERE: NEED TO FIGURE OUT HOW TO DECIDE
        # BETWEEN LESSER AND GREATER


class Weapon(Item):
    def __init__(self):
        Item.__init__(self, KEY_WEAPON)
        # weapon special abilities
        self.specials = []
        #print("Weapon.__init__")

    def __repr__(self):
        result = '<Weapon'
        result += '>'
        return result

    def __str__(self):
        return ''

    def lookup(self, strength, roller):
        pass


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
        # Armor and Shield special abilities
        self.specials = []
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
