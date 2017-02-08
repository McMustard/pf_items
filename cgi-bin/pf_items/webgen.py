#!/usr/bin/env python3.3
# vim: set fileencoding=utf-8

# Note: The shebang is set specifically for _my_ server deployment.
# It's probably a good idea to search for some method of making it a bit more
# standardized. Perhaps a symlink that must be set up on deployment?

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
This module is the web interface for item generation.
'''


#
# Standard Imports

import json
import os
import os.path
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
# Variables

# Options.
# This *must* be set when running local.
LOCAL = True

DEBUG = True


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
    print('Content-Type: application/json; charset=UTF-8\n', file=f)
    print(json.dumps(result), file=f)

def run_webgen(params):
    # Set output file descriptor.
    out = sys.stdout

    # Obtain the result.
    result = run_webgen_internal(params);

    #log = open('log.txt', 'a')
    #print('Input: ', file=log)
    #print(params, file=log)
    #print('Output:', file=log)
    #output_json(result, log)
    #log.close()

    output_json(result, out)

def run_webgen_internal(params):


    conn = None
    result = "Error: unspecified program error"
    try:
        # Mode of operation:
        mode = params['mode']

        # List rolls?
        list_rolls = params.get('list_rolls', '')

        if mode == 'echo_test':
            # Echo back the input.
            result = params

        elif mode == 'settlement':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            settlement_size = params.get('size','Thorp')
            options = {
                    'list_rolls' : list_rolls
                    }
            roller = rollers.PseudorandomRoller()
            result = settlements.generate_settlement_items(conn,
                    settlement_size, roller, **options)
            if list_rolls == 'true':
                    result['rolls'] = roller.get_log()
                    result['roll_count'] = roller.get_rollcount()

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
                    rollers.PseudorandomRoller(),
                    base_value, q_ls_min, q_gt_min, q_ls_med, q_gt_med,
                    q_ls_maj, q_gt_maj)

        elif mode == 'individual':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            strength = params['strength']
            kind = params['type']
            result = item.generate_item(conn, strength + ' ' + kind,
                    rollers.PseudorandomRoller(), None)
            # In this case, item is an Item object.
            result = str(result)

        elif mode == 'hoard_budget':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            if params['type'] == 'custom':
                result = hoard.calculate_budget_custom(conn, params['custom_gp'])
            elif params['type'] == 'encounter':
                apl = params['apl']
                rate = params['rate']
                magnitude = params['magnitude']
                result = hoard.calculate_budget_encounter(conn, apl, rate, magnitude)
            elif params['type'] == 'npc_gear':
                npc_level = params['npc_level']
                is_heroic = default_get(params, 'heroic', "false") == "true"
                result = hoard.calculate_budget_npc_gear(conn, npc_level, is_heroic)
            else:
                result = {}
        
        elif mode == 'hoard_types':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

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
            result = hoard.get_treasure_list(conn, types)

        elif mode == 'hoard_generate':
            # Open the database.
            conn = sqlite.connect('data/data.db')
            conn.row_factory = sqlite.Row

            # This one is so complex, it only operates via a map. It'll ignore
            # the transmission-related keys in the dict, e.g. "mode". So we
            # can simple pass the param dict to the function.
            result = hoard.generate_treasure(conn, params,
                    rollers.PseudorandomRoller(), None)

        else:
            result = "Error: invalid mode value"

    except sqlite.Error as e:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)

    except:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)

    finally:
        if conn:
            conn.close()

    return result


# Main Function
if __name__ == '__main__':

    ## Just some temporary test code.
    #if sys.stdin.isatty():
    #    print('Content-Type: application/json')
    #    print('')
    #    print('{["no data"]}'
    #    sys.exit(1)

    # If we're not in the CGI-BIN directory, change to it.
    if LOCAL:
        # This is necessary because the simple web server I use for testing
        # runs from the HTML file's directory, and that's the context for
        # scripts it tries to run, whereas on a real deployment, scripts are
        # already run from the cgi-bin directory.
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Access the CGI form.
    params = json.load(sys.stdin)

    log = open('log.txt', 'w+')
    print(params, file=log)
    log.close()

    run_webgen(params)

