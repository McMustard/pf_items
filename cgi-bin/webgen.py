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


# Main Function
if __name__ == '__main__':

    # Just some temporary test code.
    if sys.stdin.isatty():
        #sample = '{"medium_items": ["Wand of Dimension door (4th Level, CL 7th); 21,000.00 gp", "Dryad sandals; 24,000.00 gp", "Ring of wizardry I; 20,000.00 gp", "Headband of arcane energy; 20,000.00 gp", "Belt of mighty constitution +4; 16,000.00 gp", "Jellyfish cape; 19,200.00 gp", "Carpet of flying (5 ft. by 5 ft.); 20,000.00 gp", "Golem manual (stone); 22,000.00 gp", "Ring of energy shroud; 19,500.00 gp", "Rainbow lenses; 21,000.00 gp", "Spectral shroud; 26,000.00 gp", "Robe of arcane heritage; 16,000.00 gp"], "minor_items": ["This metropolis has virtually every minor magic item."], "major_items": ["Ring of djinni calling; 125,000.00 gp", "Ring of protection +5; 50,000.00 gp", "Rod of steadfast resolve; 38,305.00 gp", "Staff of toxins; 34,200.00 gp", "Cloak of etherealness; 55,000.00 gp", "Staff of divination; 82,000.00 gp", "Staff of acid; 28,600.00 gp"], "base_value": 16000}'
        sample = '{"minor_items": ["No data"], "medium_items": ["No data"], "major_items": ["No data"]}'
        print('Content-Type: application/json')
        print('')
        print(sample)
        sys.exit(1)

    ##raise Exception(str(data))
    #print('Content-Type: text\n')
    #print('Data:', sys.stdin.read())
    #sys.exit(0)

    # Options.
    DEBUG = False

    # Set output file descriptor.
    out = sys.stdout

    # Access the CGI form.
    params = json.load(sys.stdin)

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

        if mode == 'settlement':
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

    except sqlite.Error as e:
        print('Error: ', e, file=sys.stderr)
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
    finally:
        if conn:
            conn.close()

