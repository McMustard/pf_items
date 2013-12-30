PFRPG Item Generator
Version 0.4
29 December 2013
-------------------------------------------------------------------------------

1. Identification

The PFRPG Item Generator is a tool to assist with the selection of
random items from the Pathinder Roleplaying Game. It is intended for GMs who
wish to generate available magic items for settlements, or items found from
vanquished monsters, loot caches, and treasure hoards. For settlement item
generation, it follows the rules laid out in the Core Rulebook and Game Mastery
Guide, with some exceptions. For other loot generation, it follows the rules
laid out in Ultimate Equipment. The items it generates are specified in
Ultimate Equipment.

Acronyms:

CRB: Core Rulebook
GMG: Game Mastery Guide
UE: Ultimate Equipment


2. Usage at mcmustard.com

Using a web browser, visit:

http://www.mcmustard.com/pf_items.html

The following subsections describe how to generate items for different needs.


2.1 Generating Items for a Standard Settlement

To generate items for sale in a standard settlement (as defined in the CRB):

1. Determine the settlement size: thorp, hamlet, village, small town, large
town, small city, large city, or metropolis

2. Click the *Settlement* link if is it not already selected.

3. In the *Settlement size* list, click the size determined earlier.

4. Click *Generate items*.

Under the *Results* section, the settlement's *Base Value* appears, since any
magic item valued less than this price has a 75% chance of being found. Lists
of *Minor Items*, *Medium Items*, and *Major Items* appear next, listing the
items that were randomly generated.

Relevant Rules:

* Game Master Guide, Settlements, Settlements in Play:
  - Table "Settlement Population Ranges" lists settlement size labels and their
associated populations. This table isn't used by the software, but might help
GMs determine the size of a city if only the population count is known.
  - Table "Settlement Statistics" lists settlement sizes and their base limits
(referred to as "base values" in this documentation and software).
  - Table "Available Magic Items" lists settlement sizes and the number of
random items that can be found, in terms of dice.

* Core Rulebook, Magic Items, Using Items:
  - Table "Random Magic Item Generation" lists d100 rolls that can be made to
select a type of magic item (armor, weapons, potions, etc.) randomly, for
minor, medium, or major magic items.

* Ultimate Equipment
  - Too many tables to mention! Seriously. There are 82 of them.

Notes on Operation:

1. The generator determines the settlement's base value (base limit) using
Table: Settlement Statistics, and how many of each item the settlment has,
using Table: Available Magic Items, and rolling dice accordingly. In the case
of a metropolis, a note is simply printed, similar to the table's footnote in
the GMG.

2. For each minor, medium, or major magic item, the generator selects an item
type by rolling a d100 under the appropriate column in Table: Random Magic item
Generation. At this point, Ultimate Equipment enters the picture. There is a
slight catch, however. At this point, the generator has a target item type, and
minor, medium, or major, but Ultimate Equipment further divides each of these
into lesser and greater (and "least" for minor slotless wondrous items), and
there is no officially prescribed method of choosing. So, the generator follows
its own rule on this matter: 50% chance of lesser, 50% chance of greater (or
25% least, 25% lesser, 50% greater in the case of minor slotless wondrous
items). This may change in a future version.

3. With least/lesser/greater, minor/medium/major, and a type of item, as
criteria, the generator uses the many, many (many, many, many) tables in
Ultimate Equipment to randomly generate an item.

4. Once the item is generated, its value is checked against the settlement's
base value. If the value is less than the base value, the item is discarded,
and a new one is chosen, starting back at step 2. It's statistically possible
for undervalued items to be generated repeatedly, so to avoid an indefinite
loop, the generator will "give up" after a set number of times. Otherwise, the
item is kept and listed in the results.


3. Usage on the Command Line

The software is somewhat usable from the command line, but such use has been
neglected in development since it graduated from only being usable on the
command line (for initial development) to being a web application. Instead of
listing instructions for use, here is a list of the scripts, and their
purposes (assuming you've downloaded a copy from Github):

initdb.py:
Reads the data files in data/ and produces an SQLite 3 database file: the
standard database. This database is needed for the settlement, individual, and
treasure item generators. Usable on the command line.

cgi-bin/pf_items/enumerate.py:
Reads the standard database, and iterates through all the possible rolls in
sequence (smartly, so as not to take too much time), producing another SQLite 3
database file: the frequency database. The frequency database is used for the
custom settlement generator. Usable on the command line.

cgi-bin/pf_items/generate.py:
The main entry point to the item generator, coordinating the other parts.
Usable on the command line.

cgi-bin/pf_items/hoard.py:
Handles budget calculation, provides treasure type data for the web form, and
selects random item critera for the generator core (item.py).

cgi-bin/pf_items/item.py:
The core of the item generator, handling most of the database lookups and price
calculations, once given randomization criteria by another module.

cgi-bin/pf_items/rollers.py:
Implements virtual dice for selection of random numbers.

cgi-bin/pf_items/settlements.py:
Selects random item criteria for settlements, and calls the generator core
(item.py).

cgi-bin/pf_items/test_webgen.py:
Runs tests on the web generator by calling functions in webgen.py with sample
JSON data, in the way it is expected from the web form.

cgi-bin/pf_items/webgen.py:
The only script that generate.js calls.


4. Prerequisites

This software requires:

* Python 3.x (tested with 3.0 and 3.3)
  - When deploying

* bootstrap (www.getbootstrap.com)

* (more to come?)


5. Legal

The software in this package is copyright (c) 2012-2012, Steven Clark. All
rights reserved, and is stated in each source code file. See the file
"LICENSE.txt" for licensing information, terms and conditions for usage, and a
DISCLAIMER OF ALL WARRANTIES.

This softare package also includes Open Game Content. See the file "OGL.txt"
for a copy of the Open Game License and list of Open Game Content used by this
software.

All trademarks referenced herein are property of their respective holders.

The source code and accompanying data files contains Open Game Content. See
OGL.txt for more information.

