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
This module is the web interface for item generation.
'''

#
# Standard Imports

import cgi
import cgitb
import json
import sqlite3 as sqlite
import sys
import traceback

#
# Local Imports

import rollers
import settlements

#
# Execution

if __name__ == '__main__':

    # Enable CGI traceback manager (DEVELOPMENT)
    cgitb.enable(display=0, logdir='tblog.txt')
    
    # Output selection for debugging.
    #f = open('log.txt', 'a')
    f = sys.stdout
    #f = sys.stderr
    
    # Access the CGI form
    #form = cgi.FieldStorage()
    params = json.load(sys.stdin)

    conn = None
    # If an exception happens, return HTML containing an error.
    try:
        # Open the database.
        conn = sqlite.connect('data\\data.db')
        conn.row_factory = sqlite.Row

        # Mode of operation:
        # settlement:
        #     List of items based on a formula.
        # Single Item:
        #     Generate a single item, perhaps as a reroll.
        # More to come: treature hoards, monster loot, etc.

        #mode = form["mode"].value
        mode = params["mode"]

        if mode == "settlement":
            #settlement_size = form["settlement_size"].value
            settlement_size = params["settlement_size"]
            result = settlements.generate_settlement_items(conn,
                    settlement_size, rollers.PseudorandomRoller())
            result['settlement_size'] = settlement_size
            print('Content-Type: application/json', file=f)
            print('', file=f)
            print(json.dumps(result), file=f)

            # Older, XML version
            #print('<b>Base Value:</b>', result.base_value, 'gp ', file=f)
            #print('<br/>', file=f)
            #print('<p>Minor Items</p>', file=f)
            #print('<ul>', file=f)
            #for x in result.minor_items:
            #    print('<li>', x, '</li>', file=f)
            #print('</ul>', file=f)
            #print('<p>Medium Items</p>', file=f)
            #print('<ul>', file=f)
            #for x in result.medium_items:
            #    print('<li>', x, '</li>', file=f)
            #print('</ul>', file=f)
            #print('<p>Major Items</p>', file=f)
            #print('<ul>', file=f)
            #for x in result.major_items:
            #    print('<li>', x, '</li>', file=f)
            #print('</ul>', file=f)

        elif mode == "single-item":
            strength = form["strength"].value
            # Not yet implemented.
            pass

    except sqlite.Error as e:
        #print('Error: %s' % e.message, file=f)
        pass

    except Exception as ex:
        print("<h1>Error!</h1>", file=f)
        traceback.print_exc(file=f)

    finally:
        if conn: conn.close()

