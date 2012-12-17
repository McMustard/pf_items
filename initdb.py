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
            ('Settlements',                     'data/Settlements'),
            ('Item_Types',                      'data/Item_Types'),
            ('Magic_Armor_and_Shields',         'data/ue/Magic_Armor_and_Shields'),
            ('Magic_Weapons',                   'data/ue/Magic_Weapons'),
            ('Metamagic_Rods_1',                'data/ue/Metamagic_Rods_1'),
            ('Metamagic_Rods_2',                'data/ue/Metamagic_Rods_2'),
            ('Metamagic_Rods_3',                'data/ue/Metamagic_Rods_3'),
            ('Potion_or_Oil_Level_0',           'data/ue/Potion_or_Oil_Level_0'),
            ('Potion_or_Oil_Level_1',           'data/ue/Potion_or_Oil_Level_1'),
            ('Potion_or_Oil_Level_2',           'data/ue/Potion_or_Oil_Level_2'),
            ('Potion_or_Oil_Level_3',           'data/ue/Potion_or_Oil_Level_3'),
            ('Potion_or_Oil_Type',              'data/ue/Potion_or_Oil_Type'),
            ('Random_Armor_or_Shield',          'data/ue/Random_Armor_or_Shield'),
            ('Random_Art_Objects',              'data/ue/Random_Art_Objects'),
            ('Random_Gems',                     'data/ue/Random_Gems'),
            ('Random_Potions_and_Oils',         'data/ue/Random_Potions_and_Oils'),
            ('Random_Scrolls',                  'data/ue/Random_Scrolls'),
            ('Random_Wands',                    'data/ue/Random_Wands'),
            ('Random_Weapon',                   'data/ue/Random_Weapon'),
            ('Rings',                           'data/ue/Rings'),
            ('Rods',                            'data/ue/Rods'),
            ('Scrolls_Arcane_Level_0',          'data/ue/Scrolls_Arcane_Level_0'),
            ('Scrolls_Arcane_Level_1',          'data/ue/Scrolls_Arcane_Level_1'),
            ('Scrolls_Arcane_Level_2',          'data/ue/Scrolls_Arcane_Level_2'),
            ('Scrolls_Arcane_Level_3',          'data/ue/Scrolls_Arcane_Level_3'),
            ('Scrolls_Arcane_Level_4',          'data/ue/Scrolls_Arcane_Level_4'),
            ('Scrolls_Arcane_Level_5',          'data/ue/Scrolls_Arcane_Level_5'),
            ('Scrolls_Arcane_Level_6',          'data/ue/Scrolls_Arcane_Level_6'),
            ('Scrolls_Arcane_Level_7',          'data/ue/Scrolls_Arcane_Level_7'),
            ('Scrolls_Arcane_Level_8',          'data/ue/Scrolls_Arcane_Level_8'),
            ('Scrolls_Arcane_Level_9',          'data/ue/Scrolls_Arcane_Level_9'),
            ('Scrolls_Divine_Level_0',          'data/ue/Scrolls_Divine_Level_0'),
            ('Scrolls_Divine_Level_1',          'data/ue/Scrolls_Divine_Level_1'),
            ('Scrolls_Divine_Level_2',          'data/ue/Scrolls_Divine_Level_2'),
            ('Scrolls_Divine_Level_3',          'data/ue/Scrolls_Divine_Level_3'),
            ('Scrolls_Divine_Level_4',          'data/ue/Scrolls_Divine_Level_4'),
            ('Scrolls_Divine_Level_5',          'data/ue/Scrolls_Divine_Level_5'),
            ('Scrolls_Divine_Level_6',          'data/ue/Scrolls_Divine_Level_6'),
            ('Scrolls_Divine_Level_7',          'data/ue/Scrolls_Divine_Level_7'),
            ('Scrolls_Divine_Level_8',          'data/ue/Scrolls_Divine_Level_8'),
            ('Scrolls_Divine_Level_9',          'data/ue/Scrolls_Divine_Level_9'),
            ('Scroll_Type',                     'data/ue/Scroll_Type'),
            ('Special_Abilities_Ammunition',    'data/ue/Special_Abilities_Ammunition'),
            ('Special_Abilities_Armor',         'data/ue/Special_Abilities_Armor'),
            ('Special_Abilities_Melee_Weapon',  'data/ue/Special_Abilities_Melee_Weapon'),
            ('Special_Abilities_Ranged_Weapon', 'data/ue/Special_Abilities_Ranged_Weapon'),
            ('Special_Abilities_Shield',        'data/ue/Special_Abilities_Shield'),
            ('Special_Bane',                    'data/ue/Special_Bane'),
            ('Special_Slaying_Arrow',           'data/ue/Special_Slaying_Arrow'),
            ('Specific_Armor',                  'data/ue/Specific_Armor'),
            ('Specific_Cursed_Items',           'data/ue/Specific_Cursed_Items'),
            ('Specific_Shields',                'data/ue/Specific_Shields'),
            ('Specific_Weapons',                'data/ue/Specific_Weapons'),
            ('Staves',                          'data/ue/Staves'),
            ('Wand_Level_0',                    'data/ue/Wand_Level_0'),
            ('Wand_Level_1',                    'data/ue/Wand_Level_1'),
            ('Wand_Level_2',                    'data/ue/Wand_Level_2'),
            ('Wand_Level_3',                    'data/ue/Wand_Level_3'),
            ('Wand_Level_4',                    'data/ue/Wand_Level_4'),
            ('Wand_Type',                       'data/ue/Wand_Type'),
            ('Wondrous_Items',                  'data/ue/Wondrous_Items'),
            ('Wondrous_Items_Belt',             'data/ue/Wondrous_Items_Belt'),
            ('Wondrous_Items_Body',             'data/ue/Wondrous_Items_Body'),
            ('Wondrous_Items_Chest',            'data/ue/Wondrous_Items_Chest'),
            ('Wondrous_Items_Eyes',             'data/ue/Wondrous_Items_Eyes'),
            ('Wondrous_Items_Feet',             'data/ue/Wondrous_Items_Feet'),
            ('Wondrous_Items_Hands',            'data/ue/Wondrous_Items_Hands'),
            ('Wondrous_Items_Head',             'data/ue/Wondrous_Items_Head'),
            ('Wondrous_Items_Headband',         'data/ue/Wondrous_Items_Headband'),
            ('Wondrous_Items_Neck',             'data/ue/Wondrous_Items_Neck'),
            ('Wondrous_Items_Shoulders',        'data/ue/Wondrous_Items_Shoulders'),
            ('Wondrous_Items_Slotless',         'data/ue/Wondrous_Items_Slotless'),
            ('Wondrous_Items_Wrists',           'data/ue/Wondrous_Items_Wrists') ]

    for (table_name, table_file) in tables:
        build_table(cursor, table_name, table_file)


def initialize_database(hostname, user_name, database):
    try:
        # Open a connection
        con = None
        # A blank user name means a file-based database.
        if user_name == '':
            # We're starting over, so erase the file.
            if os.path.isfile(database):
                os.remove(database)
            # Open the database file.
            con = sqlite.connect(database)
        else:
            ## A non-blank username means a daemon-style database, which we may
            ## support in the future.
            ## It'll need a password.
            #password = getpass.getpass()
            #con = db.connect(hostname, user_name, password, database)
            print('Only sqlite3 databases are supported at the moment')
            return

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

    # Positional arguments: hostname, user name, database name
    parser.add_argument('hostname', metavar='HOSTNAME',
            help='IP address or name of host')
    parser.add_argument('user_name', metavar='USERNAME',
            help='Username for the database')
    parser.add_argument('database', metavar='DATABASE',
            help='The database name')

    # We'll ask for the password when we execute.

    # Go.
    args = parser.parse_args()
    initialize_database(args.hostname, args.user_name, args.database)
