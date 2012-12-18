#!/usr/local/bin/python3.0
# vim: set fileencoding=utf-8

# Note: The shebang is set specifically for _my_ server deployment.
# It's probably a good idea to search for some method of making it a bit more
# standardized. Perhaps a symlink that must be set up on deployment?

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
This module is the web interface for item generation.
'''

#
# Standard Imports

import json
import sqlite3 as sqlite
import sys
import traceback

#
# Local Imports

import item
import rollers
import settlements

#
# Execution

def output_json(result, f):
    print('Content-Type: application/json', file=f)
    print('', file=f)
    print(json.dumps(result), file=f)

if __name__ == '__main__':

    DEBUG = False
    #DEBUG = True

    # Output selection for normal mode or debugging.
    f = sys.stdout
    if DEBUG:
        f = open('log.txt', 'a')
    
    # Access the CGI form
    params = json.load(sys.stdin)

    if DEBUG:
        print('Paramers:', params, file=f)

    conn = None
    # If an exception happens, return HTML containing an error.
    try:
        # Open the database.
        conn = sqlite.connect('data/data.db')
        conn.row_factory = sqlite.Row

        # Mode of operation:
        # settlement:
        #     List of items based on a formula.
        # Single Item:
        #     Generate a single item, perhaps as a reroll.
        # More to come: treature hoards, monster loot, etc.

        mode = params['mode']

        if mode == 'settlement':
            settlement_size = params['size']
            result = settlements.generate_settlement_items(conn,
                    settlement_size, rollers.PseudorandomRoller())
            output_json(result, f)

        elif mode == 'individual':
            strength = params['strength']
            kind = params['type']
            result = item.generate_item(conn, strength + ' ' + kind,
                    rollers.PseudorandomRoller())
            # In this case, item is an Item object.
            output_json(str(result), f)

    except sqlite.Error as e:
        print('Error: ', e, file=f)
        if DEBUG:
            traceback.print_exc(file=f)
        pass

    except Exception as ex:
        print('<h1>Error!</h1>', file=f)
        if DEBUG:
            traceback.print_exc(file=f)
        pass

    finally:
        if conn: conn.close()

