// generate.js

// Copyright (c) 2012-2014, Steven Clark
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy of
// this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

// These are globals; I need to determine if this is typically "okay" in
// JavaScript, or if I should start using classes, or what. Fine for now.
var g_TreasureTablesLoaded = false;
var g_TreasureTables = {};
var g_Budget = 0.00;
var g_AllTreasureTypes = "abcdefghi";
var g_TreasureTypePresets = {
    "none"                : "",
    "all"                 : "abcdefghi",
    "aberration"          : "abde",
    "aberration_cunning"  : "abdefgh",
    "animal"              : "abde",
    "construct"           : "ef",
    "construct_guardian"  : "efbch",
    "dragon"              : "abchi",
    "fey"                 : "bcdg",
    "humanoid"            : "abdefg",
    "humanoid_community"  : "abdefgh",
    "magicalbeast"        : "abde",
    "monstroushumanoid"   : "abcdeh",
    "ooze"                : "abd",
    "outsider"            : "abdefg",
    "plant"               : "abde",
    "undead"              : "abde",
    "undead_intelligent"  : "abdefg",
    "vermin"              : "abd" };

// Initializer
$(document).ready(function(){

    // Just in case
    g_TreasureTablesLoaded = false;

    // Set up the page handlers.
    $("#page_settlement_sel").click(function(event){
        select_page("settlement");
    });
    $("#page_custom_sel").click(function(event){
        select_page("custom");
    });
    $("#page_individual_sel").click(function(event){
        select_page("individual");
    });
    $("#page_hoard_sel").click(function(event){
        select_page("hoard");
        if (g_TreasureTablesLoaded == false) {
            // Immediately request treasure types.
            send_request(JSON.stringify({'mode': 'hoard_types',
                'type_a': 'true', 'type_b': 'true', 'type_c': 'true', 'type_d': 'true',
                'type_e': 'true', 'type_f': 'true', 'type_g': 'true', 'type_h': 'true',
                'type_i': 'true'}), process_hoard_types_response);
            g_TreasureTablesLoaded = true;
        }
    });

    // Default page
    select_page("settlement");

    setup_generator("settlement", process_settlement_response, true);
    setup_generator("custom", process_custom_response, true);
    setup_generator("individual", process_individual_response, true);
    // The Hoard generator has sub-forms.
    setup_generator("hoard_budget", process_hoard_budget_response, true);
    //setup_generator("hoard_types",  process_hoard_types_response,  true);
    //setup_generator("hoard_alloc",  process_hoard_results,  true);
    $("#btn_hoard_execute").click(submit_hoard_generate);
    $("#btn_hoard_alloc_reset").click(clear_hoard_alloc);
    $("#btn_hoard_alloc_randomize").click(random_hoard_alloc);

    // Additional handlers
    $("ul#p_hoard_custom :input").focus(function(){
        $("#rb_hoard_custom").prop("checked", true);
    });

    $("ul#p_hoard_encounter :input").focus(function(){
        $("#rb_hoard_encounter").prop("checked", true);
    });

    $("ul#p_hoard_npc :input").focus(function(){
        $("#rb_hoard_npc").prop("checked", true);
    });

    $(".ttcb").change(function(){
        // See what's selected.
        var types = get_selected_treasure_types();
        var selector = $("#list_creatures");
        var selection = selector.val();
        // If no types are selected.
        if (types == "") {
            // Select the "none" option.
            selector.val("none");
            // And clear the note.
            $("#l_creatures_note").text("");
        }
        // If the type is not outsider, this is a custom selection.
        else if (selection != "outsider") {
            selector.val("custom");
        }
        else if (selection == "outsider") {
            // keep outsider
        }
        // If all types are selected, pick "all".
        else if (types == g_AllTreasureTypes) {
            selector.val("all");
        }
        // Also show/hide treasure lists based on this setting.
        update_treasure_list_visibilities();
    });

    // list_creatures, cb_tt_<a..i>
    $("#list_creatures").change(on_click_creatures);
});

// Sets up a button to "submit" a form.
function setup_generator(page, handler, clear) {
    // Set up the form's Generate button handler.
    $("#btn_" + page + "_execute").click(function(event){
        // Get the form data.
        var data = get_form_data("form_" + page, page);
        // Debug
        //console.log("Sending request: ", data);
        //// Debug: Clear the current results.
        //if (clear) {
        //    $("#" + page + "_results").html("");
        //}
        // Send the request.
        send_request(data, handler);
        // Prevent the default action, which reloads the page.
        // There's probably a more elegant way to set this up.
        event.preventDefault();
    });
}

// Select the specified page, unselecting the others.
function select_page(page) {
    // Hide all page labels, show all page links.
    $(".page_label").hide();
    $(".page_link").show();
    // Likewise, hide all pages.
    $(".page").hide();   

    // Now, do the opposite for the specified page.
    // Hide the specified page's selector link.
    $("#page_" + page + "_sel").hide();
    // Show the specified page's label.
    $("#page_" + page + "_unsel").show();
    // And show the page.
    $("div[id='page_" + page + "']").show();
}

// Examine a form, extract the data, and convert it to a form that webgen.py
// expects.
function get_form_data(form_id, mode) {
    // Access the form data.
    var fields = $("form#" + form_id + " :input").serializeArray();
    //console.log("gfd: %o", fields);
    // 'fields' is now an array of {"name": foo, "value" : bar} items.
    // Convert this into a simpler form, create a new dict.
    var output = {};
    // Set the mode, which is not provided by the form.
    output.mode = mode;
    // Add the rest of the form elements.
    $.each(fields, function(i, field){
        output[field.name] = field.value;
    });
    return JSON.stringify(output);
}

// Send an AJAX request.  Well, AJAJ, really.
function send_request(json_string, handler) {
    //console.log("send: %s", json_string);
    $.ajax({
        type: "POST",
        url: "../cgi-bin/pf_items/webgen.py",
        datatype: "json",
        data: json_string,
        success: handler
    });
}

// Generate a string from an item description block.
function item_str(item) {
    return String(item.item + "; " + item.value_str);
}

// Standard handling of minor/medium/major items.
function post_grouped_items(response, results) {
    if (response.minor_items.length > 0 ||
            response.minor_heading.length > 0) {
        results.append("<p>");
       results.append("<strong>Minor Items:</strong>");
        if (response.minor_heading.length > 0) {
            results.append("<br>" + response.minor_heading);
        }
        results.append("<ul>");
        for (i in response.minor_items) {
            results.append("<li>" +
                item_str(response.minor_items[i]) + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.medium_items.length > 0 ||
            response.medium_heading.length > 0) {
        results.append("<p>");
        results.append("<strong>Medium Items:</strong>");
        if (response.medium_heading.length > 0) {
            results.append("<br>" + response.medium_heading);
        }
        results.append("<ul>");
        for (i in response.medium_items) {
            results.append("<li>" +
                item_str(response.medium_items[i]) + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.major_items.length > 0 ||
            response.major_heading.length > 0) {
        results.append("<p>");
        results.append("<strong>Major Items:</strong>");
        if (response.major_heading.length > 0) {
            results.append("<br>" + response.major_heading);
        }
        results.append("<ul>");
        for (i in response.major_items) {
            results.append("<li>" +
                item_str(response.major_items[i]) + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
}

// Accept the data back from webgen.py and populate the settlement result
// area with it.
function process_settlement_response(response, textStatus, jqXHR) {
    console.log("Settlement Results: %o", response);
    // Fill out the results receptacle with the result data.
    var results = $("#settlement_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }
    results.append("<strong>Base Value:</strong> ");
    if (response.base_value != null) {+
        results.append(response.base_value + "gp<br/>");
    }
    else {
        results.append("unknown");
    }
    post_grouped_items(response, results);

    var rolls = $("#settlement_rolls");
    rolls.html("");
    if ('rolls' in response) {
        rolls.show();
        for (i in response.rolls) {
            rolls.append(response.rolls[i] + "<br>");
        }
    }
    else {
        rolls.hide();
    }
}

// Accept the data back from webgen.py and populate the custom settlement
// result area with it.
function process_custom_response(response, textStatus, jqXHR) {
    //console.log("Custom Results: %o", response);
    // Fill out the results receptacle with the result data.
    var results = $("#custom_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }
    post_grouped_items(response, results);
}

// Accept the data back from webgen.py and populate the individual item result
// area with it.
function process_individual_response(response, textStatus, jqXHR) {
    //console.log("Individual Results: %o", response);
    var results = $("#individual_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }
    results.append("<ul><li>" + response + "</li></ul>");
}


// Handle selection of a creature type.
function on_click_creatures() {
    selector = $("#list_creatures");
    val = selector.val();
    types = "";

    // Clear the note.
    $("#l_creatures_note").text("");

    // If "custom" was selected, do nothing.
    if (val == "custom") {
        return;
    }

    // Handle generically.
    types = g_TreasureTypePresets[val];

    // Handle special cases.
    if (val == "outsider") {
        $("#l_creatures_note").text("Outsiders can carry any kind of gear. The treasure types for \"Humanoid\" have been selected for you as a starting point. Customize the selections as you see fit.");
    }

    // Select checkboxes
    $("#cb_tt_a").prop("checked", jQuery.inArray("a", types) >= 0);
    $("#cb_tt_b").prop("checked", jQuery.inArray("b", types) >= 0);
    $("#cb_tt_c").prop("checked", jQuery.inArray("c", types) >= 0);
    $("#cb_tt_d").prop("checked", jQuery.inArray("d", types) >= 0);
    $("#cb_tt_e").prop("checked", jQuery.inArray("e", types) >= 0);
    $("#cb_tt_f").prop("checked", jQuery.inArray("f", types) >= 0);
    $("#cb_tt_g").prop("checked", jQuery.inArray("g", types) >= 0);
    $("#cb_tt_h").prop("checked", jQuery.inArray("h", types) >= 0);
    $("#cb_tt_i").prop("checked", jQuery.inArray("i", types) >= 0);

    // Update the visibilities of the treasure type selectors.
    update_treasure_list_visibilities();

    //selector.val("idle");
}

function get_selected_treasure_types() {
    var types = "";
    var allTypes = g_AllTreasureTypes;
    for (var i = 0; i < allTypes.length; ++i) {
        var id = "#cb_tt_" + allTypes[i];
        if ($(id).prop("checked")) {
            types += allTypes[i];
        }
    }
    return types;
}

function check_visibility(type) {
    cb = $("#cb_tt_"+type);
    div = $("#hoard_tt_"+type);
    if (cb.prop("checked")) {
        div.show();
        return 1;
    }
    else {
        div.hide();
        return 0;
    }
}

function update_treasure_list_visibilities() {
    var total = 0;
    total += check_visibility("a");
    total += check_visibility("b");
    total += check_visibility("c");
    total += check_visibility("d");
    total += check_visibility("e");
    total += check_visibility("f");
    total += check_visibility("g");
    total += check_visibility("h");
    total += check_visibility("i");
    if (total == 0) {
        $("#hoard_tt_0").show();
    }
    else {
        $("#hoard_tt_0").hide();
    }
}

// Accept the data back from webgen.py and populate the hoard budget result
// area with it.
function process_hoard_budget_response(response, textStatus, jqXHR) {
    //console.log("Hoard Budget Results: %o", response);
    var results = $("#hoard_budget_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }
    //console.log("Budget: %o", response.budget);
    $(".budget_out").val(response.budget);
    g_Budget = parseFloat(response.budget.replace(/,/g, ''));
}

// Accept the data back from webgen.py and populate the hoard types result
// area with it.
function process_hoard_types_response(response, textStatus, jqXHR) {
    //console.log("Hoard Types Results: %o", response);
    var results = $("#hoard_types_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }

    g_TreasureTables = response;

    //console.log(response);
    for (var tt in response) {
        div = $("#hoard_tt_"+tt+"_select");
        div.html("");
        var html = "";
        arr = response[tt];
        html += '<ul>';
        for (var i = 0; i < arr.length; i++) {
            item = arr[i];
            html += '<li>';
            html += '<output                                id="tt'+tt+'_o_'+i+'">0</output>';
            html += '<input type="button" class="tt_adjust" id="tt'+tt+'_0_'+i+'" value="0" />';
            html += '<input type="button" class="tt_adjust" id="tt'+tt+'_p_'+i+'" value="+" />';
            html += '<input type="button" class="tt_adjust" id="tt'+tt+'_m_'+i+'" value="-" />';
            html += ' - ' + item.item;
            html += ' - ' + item.description;
            html += '</li>';
        }
        html += '</ul>';
        div.html(html);
    }

    $(".tt_adjust").click(function() {
        handle_adjustment(this.id);
    });
}

function handle_adjustment(id) {
    // IDs are of the form ttX_Y_I
    // where X is the treasure type a..i
    // where Y is the operation: 0, p, m
    // where I is the item index, 0-based

    var type = id[2];
    var operation = id[4];
    var index = parseInt(id.slice(6, id.length));

    // Reference to the entry for easy repeat usage.
    var entry = g_TreasureTables[type][index];

    var pre = entry.count * entry.cost;

    // Handle the operation type.
    if (operation == "0") {
        // Zero-out
        entry.count = 0;
    }
    else if (operation == "p") {
        // Plus
        entry.count += 1;
    }
    else if (operation == "m") {
        // Minus
        if (entry.count > 0) {
            entry.count -= 1;
        }
    }
    else {
        return;
    }

    var post = entry.count * entry.cost;
    var difference = post - pre;
    var total = $("#total_allocated");
    total.val(parseInt(total.val()) + parseInt(difference));

    // Update the output indicator to show the quantity.
    var outid = "tt"+type+"_o_"+index;
    $("#"+outid).val(entry.count);
}

//
function submit_hoard_generate() {
    // All of the "form" data is in g_TreasureTables.
    // Convert it into a nicer transmission format.

    var copy = {};
    copy.mode = "hoard_generate";

    for (var tt in g_TreasureTables) {
        arr = g_TreasureTables[tt];
        for (var i = 0; i < arr.length; i++) {
            item = arr[i];
            if (item.count > 0) {
                if (!(tt in copy)) {
                    copy[tt] = [];
                }
                copy[tt].push({"index": item.index, "count": item.count});
            }
        }
    }
    
    var submission = JSON.stringify(copy)
    //console.log("send: %s", submission);
    send_request(submission, process_hoard_results);
}

function clear_hoard_alloc() {
    for (var tt in g_TreasureTables) { arr = g_TreasureTables[tt];
        for (var i = 0; i < arr.length; i++) {
            handle_adjustment("tt"+tt+"_0_"+i);
        }
    }
}

//
function compare_random_treasure_lines(lhs, rhs) {
    if (lhs.cost < rhs.cost) { return -1; }
    if (rhs.cost < lhs.cost) { return 1; }
    return 0;
}

//
function get_random_weight(index, cost) {
    var this_fn = get_random_weight;
    var method = 0;
    if (method == 0) {
        // Method 0: 2^n
        return Math.pow(2, index);
    }
    else if (method == 1) {
        // Method 1: Fibonacci
        if (typeof this_fn.fibonacci == 'undefined') {
            this_fn.fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144,
                233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657,
                46368, 75025, 121393, 196418, 317811, 514229];
        }
        if (this_fn.fibonacci.length <= index) {
            // Need more numbers.
            for (var i = this_fn.fibonacci.length - 2; i < index; ++i) {
               this_fn.fibonacci.push(this_fn.fibonacci[i] +
                      this_fn.fibonacci[i+1]);
            }
            return this_fn.fibonacci[index];
        }
    }
    else if (method == 2) {
        // Method 2: straight cost
        return cost | 0;
    }
    else if (method == 3) {
        // Method 3: cost doubled
        return (cost * 2) | 0;
    }
    else if (method == 4) {
        // Method 4: cost squared
        return Math.pow(cost, 2);
    }

    // Default in case of error.
    return cost | 0;
}

//
function random_hoard_alloc() {

    // Clear the selections first.
    clear_hoard_alloc();

    // Create a single list of all eligible treasure lots.
    var lots = [];
    var typesSelectCount = 0;
    for (var tt in g_TreasureTables) {

        // Skip this lot if it is not a selected type.
        if ($('#cb_tt_'+tt).prop('checked')) {
            typesSelectCount += 1;
            // Push on elements with cost <= g_Budget.
            var typeLots = g_TreasureTables[tt];
            for (var i = 0; i < typeLots.length; ++i) {
                // Duplicate the treasure table entry.
                var entry = JSON.parse(JSON.stringify(typeLots[i]));
                if (entry.cost <= g_Budget) {
                    // Supply the treasure type and index.
                    entry['treasureType'] = tt;
                    entry['treasureIndex'] = i;
                    // Add to the lots list.
                    lots.push(entry);
                }
            }
        }
    }

    if (lots.length == 0) {
        var error = $('#randomize_error');
        // No types are selected, or the selected types are over budget.
        if (typesSelectCount) {
            error.text('The selected treasure types do not have any lots that can fit in the budget.');
        }
        else {
            error.text('Select a creature type, or one or more treasure types');
        }
        error.show();

        // Nothing to do.
        return;
    }
    else {
        var error = $('#randomize_error');
        error.text('');
        error.hide();
    }

    // Now, sort the lots.
    lots.sort(compare_random_treasure_lines);

    // DEBUG
    //console.log('Lots, sorted: %o', lots);
 
    // Assign random weights.
    // The weight index (used by some weighting methods) should only increase
    // when an item is more expensive than its predecessor.
    var prevCost = -1;
    var weightIndex = -1;
    for (var i = 0; i < lots.length; ++i) {
        var entry = lots[i];

        // Does this increase the weight index?
        if (entry.cost > prevCost) { weightIndex += 1; }

        // Assign a weight.
        entry['random_weight'] = get_random_weight(weightIndex, entry.cost); 

        // This is the new previous cost.
        prevCost = entry.cost;
    }

    // Start allocating items!
    var budgetLeft = g_Budget;

    // Limit the number of attempts to avoid lockup.
    var attemptsLeft = 1000;

    // Select a random treasure type from the list.
    while (budgetLeft > 0 && attemptsLeft-- > 0) {

        // Delete any entries which are unaffordable.
        for (var i = 0; i < lots.length; ++i) {
            if (lots[i].cost > budgetLeft) {

                // Lob off the rest, they will also be too expensive.
                var eliminated = lots.splice(i, lots.length);

                // DEBUG
                //console.log('Dropped %o as too expensive', eliminated);
                break;
            }
        }

        // If there are no more treasures, we are done.
        if (lots.length == 0) {
            // DEBUG
            //console.log('No more lots!');
            break;
        }

        // DEBUG
        //console.log('There are %s lots', lots.length);

        // Total up the random weights.
        var weightsTotal = 0;
        for (var i = 0; i < lots.length; ++i) {
            weightsTotal += lots[i].random_weight;
        }

        // Select a value from that range.
        var ran_x = ((Math.random() * weightsTotal) | 0);

        // DEBUG
        //console.log('Random pick %s of %s', ran_x, weightsTotal);

        // Count up elements until we reach the bucket.
        var bucket = lots.length;
        var accum = 0;
        for (var i = 0; i < lots.length; ++i) {
            accum += lots[i].random_weight;

            // DEBUG
            //console.log('testing ran_x=%s < accum=%d', ran_x, accum);

            if (ran_x < accum) {
                bucket = i;
                break;
            }
        }
        // Select the bucket.
        if (bucket < lots.length) {

            // DEBUG
            //console.log('ran_x=%s --> bucket=%s w random_weight=%s', ran_x, bucket, lots[i].random_weight);
 
            var treasureType = lots[bucket].treasureType;
            var treasureIndex = lots[bucket].treasureIndex;
            var cost = lots[bucket].cost;

            // DEBUG
            //console.log('selected item with cost %s', cost);

            // Increment.
            handle_adjustment('tt'+treasureType+'_p_'+treasureIndex);

            // Account for the cost.
            budgetLeft -= cost;
        }
        else {
            // DEBUG
            //console.log('Could not find bucket for ran_x=%s', ran_x);
        }

        // DEBUG
        //console.log('Budget left %s', budgetLeft);
    }
}

// Accept the data back from webgen.py and populate the hoard alloc result
// area with it.
function process_hoard_results(response, textStatus, jqXHR) {
    //console.log("Hoard Results: %o", response);
    var results = $("#hoard_results");
    if (response == "") {
        results.html("An error has occurred.");
        return;
    }
    html = "<ol>";
    //results.append("<ul><li>" + response + "</li></ul>");
    for (var i = 0; i < response.length; i++) {
        html += "<li>";
        html += response[i];
        html += "</li>";
    }
    html += "</ol>";
    results.html(html);
}

