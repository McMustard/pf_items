#!/usr/bin/env python3.3

#!/usr/local/bin/python3.3
# vim: set fileencoding=utf-8

# Note: The shebang is set specifically for _my_ server deployment.
# It's probably a good idea to search for some method of making it a bit more
# standardized. Perhaps a symlink that must be set up on deployment?

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
This module is the web interface for item generation.
'''


#
# Standard Imports

import json
import select
import sqlite3 as sqlite
import sys
import time
import traceback

#
# Local Imports

import hoard
import item
import rollers
import settlements

#
# Execution

def default_get(d, k, val):
    if k not in d:
        return str(val)
    rv = d[k]
    if rv == '':
        return val
    return d[k]


def output_json(result, f):
    print('Content-Type: application/json\n', file=f)
    print(json.dumps(result))


def run_webgen(params):

    ##raise Exception(str(data))
    #print('Content-Type: text\n')
    #print('Data:', sys.stdin.read())
    #sys.exit(0)


    # Options.
    DEBUG = False

    # Set output file descriptor.
    out = sys.stdout

    conn = None
    try:
        # Mode of operation:
        # Settlement:
        #     List of items based on a formula.
        # Custom Settlement:
        #     Basically, a series of individual items.
        # Single Item:
        #     Generate a single item, perhaps as a reroll.
        # More to come: treature hoards, monster loot, etc.

        mode = params['mode']

        if mode == 'echo_test':
            # Echo back the input.
            output_json(params, out)

        elif mode == 'settlement':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            settlement_size = params['size']
            result = settlements.generate_settlement_items(conn,
                    settlement_size, rollers.PseudorandomRoller())
            output_json(result, out)

        elif mode == 'custom':
            # Open the database.
            conn = sqlite.connect('data/freq.db')
            conn.row_factory = sqlite.Row

            base_value = default_get(params, 'base_value', 0)
            q_ls_min = default_get(params, 'q_ls_min', '1')
            q_gt_min = default_get(params, 'q_gt_min', '1')
            q_ls_med = default_get(params, 'q_ls_med', '1')
            q_gt_med = default_get(params, 'q_gt_med', '1')
            q_ls_maj = default_get(params, 'q_ls_maj', '1')
            q_gt_maj = default_get(params, 'q_gt_maj', '1')
            result = settlements.generate_custom(conn,
                    base_value, q_ls_min, q_gt_min, q_ls_med, q_gt_med,
                    q_ls_maj, q_gt_maj)
            output_json(result, out)

        elif mode == 'individual':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            strength = params['strength']
            kind = params['type']
            result = item.generate_item(conn, strength + ' ' + kind,
                    rollers.PseudorandomRoller(), None)
            # In this case, item is an Item object.
            output_json(str(result), out)

        elif mode == 'hoard_budget':
            if params['type'] == 'custom':
                result = hoard.calculate_budget_custom(params['custom_gp'])
                output_json(result, out)
            elif params['type'] == 'encounter':
                apl = params['apl']
                rate = params['rate']
                magnitude = params['magnitude']
                result = hoard.calculate_budget_encounter(apl, rate, magnitude)
                output_json(result, out)
            elif params['type'] == 'npc_gear':
                npc_level = params['npc_level']
                is_heroic = params['heroic']
                result = hoard.calculate_budget_npc_gear(npc_level, is_heroic)
                output_json(result, out)
            else:
                result = {}
                output_json(result, out)
        
        elif mode == 'hoard_treasuretype':
            types = ''
            if default_get(params, 'type_a', 'false') == 'true': types += 'a'
            if default_get(params, 'type_b', 'false') == 'true': types += 'b'
            if default_get(params, 'type_c', 'false') == 'true': types += 'c'
            if default_get(params, 'type_d', 'false') == 'true': types += 'd'
            if default_get(params, 'type_e', 'false') == 'true': types += 'e'
            if default_get(params, 'type_f', 'false') == 'true': types += 'f'
            if default_get(params, 'type_g', 'false') == 'true': types += 'g'
            if default_get(params, 'type_h', 'false') == 'true': types += 'h'
            if default_get(params, 'type_i', 'false') == 'true': types += 'i'
            result = hoard.get_treasure_list(types)
            output_json(result, out)

        elif mode == 'hoard_generate':
            # Future
            pass

        else:
            result = {}
            output_json(result, out)

    except sqlite.Error as e:
        #print('Error: ', e, file=sys.stderr)
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
    finally:
        if conn:
            conn.close()


# Main Function
if __name__ == '__main__':

    ## Just some temporary test code.
    #if sys.stdin.isatty():
    #    print('Content-Type: application/json')
    #    print('')
    #    print('{["no data"]}'
    #    sys.exit(1)

    # Access the CGI form.

    params = json.load(sys.stdin)
    run_webgen(params)

