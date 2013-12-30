#!/usr/bin/env python3
# vim: set fileencoding=utf-8

# Pathfinder Item Generator
#
# Copyright 2012-2014, Steven Clark.
#
# This program is free software, and is provided "as is", without warranty of
# any kind, express or implied, to the extent permitted by applicable law.
# See the full license in the file 'LICENSE'.
#
# This software includes Open Game Content.  See the file 'OGL' for more
# information.
#
'''
This module takes the text (tab delimited) data files, and (re)initializes the
database with the information contained within.
'''

#
# Standard imports

import argparse
import codecs
import getpass
import os
import sqlite3 as sqlite
import sys


#
# Classes


class NullCursor(object):

    def __init__(self):
        pass

    def execute(self, command):
        print('Dry run:', command)

    def fetchone(self):
        return 'Dry run'


class FileFormatError(Exception):
    pass


class Table(object):

    def __init__(self, tablename, filename):
        # Initialize members.
        self.tablename = tablename
        self.filename = filename
        self.metadata = []
        self.columns = []
        self.types = []
        self.rows = []
        self.sql_create = None
        self.sql_inserts = None
        # Setup the table commands.
        self.read()
        self.process()

    def read(self):
        # Open the file, of course.
        f = codecs.open(self.filename, encoding='utf-8')
        # Non-comment line number, for tracking what kind of line to expect.
        lineno = 0
        # Actual line number, for error reporting.
        reallineno = 0
        # Iterate over the lines of the table, ignoring comment lines.
        for line in f:
            # Ignore comment lines, and they should not increment 'lineno'.
            if line.startswith('#'):
                # We do want to increment the absolute line number, though.
                reallineno += 1
                continue
            # Split the line into parts (tab delimited file)
            line = line[:-1]
            if line.endswith('\r'): line = line[:-1]
            # TODO can this be handled more elegantly?
            data = line.split('\t')

            # Depending on the ordinality of non-comment lines, assign.
            if lineno == 0:
                # This is the metadata line.  It has a different number of
                # columns than the remaining lines, and should eventually
                # go into a metadata table.
                self.metadata = data
            elif lineno == 1:
                # This is the line containing column names.  The number of
                # entries here dictates how many columns there are going to
                # be.
                self.columns = data
            elif lineno == 2:
                # This line contains the types.  The length should match the
                # numnber of columns.
                self.types = data
                if len(self.types) != len(self.columns):
                    raise FileFormatError(('Error: table file {0}, ' +
                            'line {1}, number of columns in types line ' +
                            'does not match the number of columns in the ' +
                            'column names line.').format(self.filename, reallineno))
            else:
                if len(data) != len(self.columns):
                    raise FileFormatError(('Error: table file {0}, ' +
                            'line {1}, number of columns in data line ' +
                            'does not match the number of columns in the ' +
                            'column names line.').format(self.filename, reallineno))
                self.rows.append(data)
            # Increment the (non-comment) line number.
            lineno += 1
            # Increment the absolute line number.
            reallineno += 1

    def process(self):
        # Combine the column names and types for easy access.
        col_data = list(zip(self.columns, self.types))
        # Form the SQL CREATE TABLE statement.
        parts = []
        row_parts = []
        for (col_name, col_type) in col_data:
            # Each column in the source table equals one column in the
            # database, except for 'range' columns, which need to be split
            # into two.
            if col_type == 'range':
                parts.append('"{0}_low" int'.format(col_name))
                parts.append('"{0}_high" int'.format(col_name))
            else:
                parts.append('"{0}" {1}'.format(col_name.strip(), col_type)) 
        # Bind variables/substitutions works with known quantities.
        # We don't know the quantities at parse time, so we have to build
        # strings at runtime.
        percent_esses  = '(' + ','.join(['%s'] * 1) + ')'
        question_marks = '(' + ','.join(['?' ] * len(parts)) + ')'

        # Let's hope this works!
        #self.sql_create = ('CREATE TABLE ' + self.tablename + ' ' + \
        #        question_marks, tuple(parts))
        self.sql_create = ('CREATE TABLE ' + self.tablename + ' ' + \
                '(' + ', '.join(parts) + ');', )

        # And now, the insert statements
        for row in self.rows:
            values = []
            for col in range(len(col_data)):
                if col_data[col][1] == 'range':
                    range_parts = split_range(row[col])
                    values.append(range_parts[0])
                    values.append(range_parts[1])
                else:
                    values.append(row[col])
            row_parts.append(tuple(values))
        self.sql_inserts = ('INSERT INTO %s VALUES %s' %
                (self.tablename, question_marks), row_parts)

    def get_sql_create(self):
        return self.sql_create

    def get_sql_inserts(self):
        return self.sql_inserts

#
# Functions

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


def build_table(cursor, tablename, filename):
    # File format:
    # * Any line that starts with '#' is a comment.
    # The first non-comment line is metadata, which should go in a
    # metadata table.  That is a future effort.
    # The second line contains the column names.
    # The third line contains column types.  These do not correspond with
    # database types, but rather: string, int, range.  Ranges have to be
    # split, using the names col_low and col_high, where 'col' is the column
    # name, and the resulting columns are then INT.  When using a string
    # column, we must first determine the longest string so we can set the
    # length of the VARCHAR.  int corresponds with the INT type, I believe.
    t = Table(tablename, filename)
    sql_create = t.get_sql_create()
    sql_inserts = t.get_sql_inserts()
    if sql_create:
        print('Creating table ' + tablename)
        try:
            # SQL Create
            if len(sql_create) == 1:
                cursor.execute(sql_create[0])
            else:
                cursor.execute(sql_create[0], sql_create[1])
            # SQL Insert
            cursor.executemany(sql_inserts[0], sql_inserts[1])
        except sqlite.Error as e:
            print('Error:', e.message)
    else:
        print('Skipping table ' + tablename + ' due to null SQL')


def build_tables(cursor):
    tables = [ 
            ('Settlements',                     'data_src/Settlements'),
            ('Item_Types',                      'data_src/Item_Types'),
            ('Magic_Armor_and_Shields',         'data_src/ue/Magic_Armor_and_Shields'),
            ('Magic_Weapons',                   'data_src/ue/Magic_Weapons'),
            ('Metamagic_Rods_1',                'data_src/ue/Metamagic_Rods_1'),
            ('Metamagic_Rods_2',                'data_src/ue/Metamagic_Rods_2'),
            ('Metamagic_Rods_3',                'data_src/ue/Metamagic_Rods_3'),
            ('Potion_or_Oil_Level_0',           'data_src/ue/Potion_or_Oil_Level_0'),
            ('Potion_or_Oil_Level_1',           'data_src/ue/Potion_or_Oil_Level_1'),
            ('Potion_or_Oil_Level_2',           'data_src/ue/Potion_or_Oil_Level_2'),
            ('Potion_or_Oil_Level_3',           'data_src/ue/Potion_or_Oil_Level_3'),
            ('Potion_or_Oil_Type',              'data_src/ue/Potion_or_Oil_Type'),
            ('Random_Armor_or_Shield',          'data_src/ue/Random_Armor_or_Shield'),
            ('Random_Art_Objects',              'data_src/ue/Random_Art_Objects'),
            ('Random_Gems',                     'data_src/ue/Random_Gems'),
            ('Random_Potions_and_Oils',         'data_src/ue/Random_Potions_and_Oils'),
            ('Random_Scrolls',                  'data_src/ue/Random_Scrolls'),
            ('Random_Wands',                    'data_src/ue/Random_Wands'),
            ('Random_Weapon',                   'data_src/ue/Random_Weapon'),
            ('Rings',                           'data_src/ue/Rings'),
            ('Rods',                            'data_src/ue/Rods'),
            ('Scrolls_Arcane_Level_0',          'data_src/ue/Scrolls_Arcane_Level_0'),
            ('Scrolls_Arcane_Level_1',          'data_src/ue/Scrolls_Arcane_Level_1'),
            ('Scrolls_Arcane_Level_2',          'data_src/ue/Scrolls_Arcane_Level_2'),
            ('Scrolls_Arcane_Level_3',          'data_src/ue/Scrolls_Arcane_Level_3'),
            ('Scrolls_Arcane_Level_4',          'data_src/ue/Scrolls_Arcane_Level_4'),
            ('Scrolls_Arcane_Level_5',          'data_src/ue/Scrolls_Arcane_Level_5'),
            ('Scrolls_Arcane_Level_6',          'data_src/ue/Scrolls_Arcane_Level_6'),
            ('Scrolls_Arcane_Level_7',          'data_src/ue/Scrolls_Arcane_Level_7'),
            ('Scrolls_Arcane_Level_8',          'data_src/ue/Scrolls_Arcane_Level_8'),
            ('Scrolls_Arcane_Level_9',          'data_src/ue/Scrolls_Arcane_Level_9'),
            ('Scrolls_Divine_Level_0',          'data_src/ue/Scrolls_Divine_Level_0'),
            ('Scrolls_Divine_Level_1',          'data_src/ue/Scrolls_Divine_Level_1'),
            ('Scrolls_Divine_Level_2',          'data_src/ue/Scrolls_Divine_Level_2'),
            ('Scrolls_Divine_Level_3',          'data_src/ue/Scrolls_Divine_Level_3'),
            ('Scrolls_Divine_Level_4',          'data_src/ue/Scrolls_Divine_Level_4'),
            ('Scrolls_Divine_Level_5',          'data_src/ue/Scrolls_Divine_Level_5'),
            ('Scrolls_Divine_Level_6',          'data_src/ue/Scrolls_Divine_Level_6'),
            ('Scrolls_Divine_Level_7',          'data_src/ue/Scrolls_Divine_Level_7'),
            ('Scrolls_Divine_Level_8',          'data_src/ue/Scrolls_Divine_Level_8'),
            ('Scrolls_Divine_Level_9',          'data_src/ue/Scrolls_Divine_Level_9'),
            ('Scroll_Type',                     'data_src/ue/Scroll_Type'),
            ('Special_Abilities_Ammunition',    'data_src/ue/Special_Abilities_Ammunition'),
            ('Special_Abilities_Armor',         'data_src/ue/Special_Abilities_Armor'),
            ('Special_Abilities_Melee_Weapon',  'data_src/ue/Special_Abilities_Melee_Weapon'),
            ('Special_Abilities_Ranged_Weapon', 'data_src/ue/Special_Abilities_Ranged_Weapon'),
            ('Special_Abilities_Shield',        'data_src/ue/Special_Abilities_Shield'),
            ('Special_Bane',                    'data_src/ue/Special_Bane'),
            ('Special_Slaying_Arrow',           'data_src/ue/Special_Slaying_Arrow'),
            ('Specific_Armor',                  'data_src/ue/Specific_Armor'),
            ('Specific_Cursed_Items',           'data_src/ue/Specific_Cursed_Items'),
            ('Specific_Shields',                'data_src/ue/Specific_Shields'),
            ('Specific_Weapons',                'data_src/ue/Specific_Weapons'),
            ('Staves',                          'data_src/ue/Staves'),
            ('Wand_Level_0',                    'data_src/ue/Wand_Level_0'),
            ('Wand_Level_1',                    'data_src/ue/Wand_Level_1'),
            ('Wand_Level_2',                    'data_src/ue/Wand_Level_2'),
            ('Wand_Level_3',                    'data_src/ue/Wand_Level_3'),
            ('Wand_Level_4',                    'data_src/ue/Wand_Level_4'),
            ('Wand_Type',                       'data_src/ue/Wand_Type'),
            ('Wondrous_Items',                  'data_src/ue/Wondrous_Items'),
            ('Wondrous_Items_Belt',             'data_src/ue/Wondrous_Items_Belt'),
            ('Wondrous_Items_Body',             'data_src/ue/Wondrous_Items_Body'),
            ('Wondrous_Items_Chest',            'data_src/ue/Wondrous_Items_Chest'),
            ('Wondrous_Items_Eyes',             'data_src/ue/Wondrous_Items_Eyes'),
            ('Wondrous_Items_Feet',             'data_src/ue/Wondrous_Items_Feet'),
            ('Wondrous_Items_Hands',            'data_src/ue/Wondrous_Items_Hands'),
            ('Wondrous_Items_Head',             'data_src/ue/Wondrous_Items_Head'),
            ('Wondrous_Items_Headband',         'data_src/ue/Wondrous_Items_Headband'),
            ('Wondrous_Items_Neck',             'data_src/ue/Wondrous_Items_Neck'),
            ('Wondrous_Items_Shoulders',        'data_src/ue/Wondrous_Items_Shoulders'),
            ('Wondrous_Items_Slotless',         'data_src/ue/Wondrous_Items_Slotless'),
            ('Wondrous_Items_Wrists',           'data_src/ue/Wondrous_Items_Wrists'),
            ('Treasure_Values_Per_Encounter',   'data_src/ue/Treasure_Values_Per_Encounter'),
            ('NPC_Gear',                        'data_src/ue/NPC_Gear'),
            ('Type_A_Treasure',                 'data_src/ue/Type_A_Treasure'),
            ('Type_B_Treasure',                 'data_src/ue/Type_B_Treasure'),
            ('Type_C_Treasure',                 'data_src/ue/Type_C_Treasure'),
            ('Type_D_Treasure',                 'data_src/ue/Type_D_Treasure'),
            ('Type_E_Treasure',                 'data_src/ue/Type_E_Treasure'),
            ('Type_F_Treasure',                 'data_src/ue/Type_F_Treasure'),
            ('Type_G_Treasure',                 'data_src/ue/Type_G_Treasure'),
            ('Type_H_Treasure',                 'data_src/ue/Type_H_Treasure'),
            ('Type_I_Treasure',                 'data_src/ue/Type_I_Treasure'),
            ]

    for (table_name, table_file) in tables:
        build_table(cursor, table_name, table_file)


def initialize_database(database):
    try:
        # Open a connection
        con = None

        # We're starting over, so erase the file.
        if os.path.isfile(database):
            os.remove(database)
        # Open the database file.
        con = sqlite.connect(database)

    for (table_name, table_file) in tables:
        build_table(cursor, table_name, table_file)


def initialize_database(database):
    try:
        # Open a connection
        con = None

        # We're starting over, so erase the file.
        if os.path.isfile(database):
            os.remove(database)
        # Open the database file.
        con = sqlite.connect(database)

        # Build the tables!
        build_tables(con.cursor())

        # Commit
        con.commit()

    except sqlite.Error as e:
        print('Error: %s' % e.message)
        sys.exit(1)
    finally:
        if con:
            con.close()

#
# Main

if __name__ == '__main__':

    # Set up a cushy argument parser.
    parser = argparse.ArgumentParser(
            description='Initializes databases from text files')

    # Positional arguments: database name
    parser.add_argument('database', metavar='DATABASE',
            help='The database name')

    # We'll ask for the password when we execute.

    # Go.
    args = parser.parse_args()
    initialize_database(args.database)
