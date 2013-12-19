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

// Initializer
$(document).ready(function(){

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
    });

    // Default page
    select_page("settlement");

    setup_generator("settlement", process_settlement_response, true);
    setup_generator("custom", process_custom_response, true);
    setup_generator("individual", process_individual_response, true);
    // The Hoard generator has sub-forms.
    setup_generator("hoard_budget", process_hoard_budget_response, true);
    setup_generator("hoard_types",  process_hoard_types_response,  true);
    setup_generator("hoard_alloc",  process_hoard_alloc_response,  true);

    // Additional handlers
    $("#form_hoard_budget_calc_openclose").click(function(event){
        anchor = $("#form_hoard_budget_calc_openclose");
        panel = $("#form_hoard_budget_calc");
        if (panel.is(":visible")) {
            panel.hide();
            anchor.text("Open calculator");
        }
        else {
            panel.show();
            anchor.text("Close calculator");
        }
    });

    // list_creatures, cb_tt_<a..i>
    $("#list_creatures").change(on_click_creatures);
});

// Sets up a button to "submit" a form.
function setup_generator(page, handler, clear) {
    // Set up the form's Generate button handler.
    $("#btn_" + page + "_generate").click(function(event){
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
    console.log("send: %s", json_string);
    $.ajax({
        type: "POST",
        url: "cgi-bin/webgen.py",
        datatype: "json",
        data: json_string,
        success: handler
    });
}

// Accept the data back from webgen.py and populate the settlement result
// area with it.
function process_settlement_response(response, textStatus, jqXHR) {
    //console.log("Settlement Results: %o", response);
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
    if (response.minor_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Minor Items:</strong>");
        results.append("<ul>");
        for (i in response.minor_items) {
            results.append("<li>" +
                response.minor_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.medium_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Medium Items:</strong>");
        results.append("<ul>");
        for (i in response.medium_items) {
            results.append("<li>" +
                    response.medium_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.major_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Major Items:</strong>");
        results.append("<ul>");
        for (i in response.major_items) {
            results.append("<li>" +
                    response.major_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
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
    if (response.minor_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Minor Items:</strong>");
        results.append("<ul>");
        for (i in response.minor_items) {
            results.append("<li>" +
                response.minor_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.medium_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Medium Items:</strong>");
        results.append("<ul>");
        for (i in response.medium_items) {
            results.append("<li>" +
                    response.medium_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
    if (response.major_items.length > 0) {
        results.append("<p>");
        results.append("<strong>Major Items:</strong>");
        results.append("<ul>");
        for (i in response.major_items) {
            results.append("<li>" +
                    response.major_items[i] + "</li>");
        }
        results.append("</ul>");
        results.append("</p>");
    }
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
    types = ""
    if (val == "none") {
        types = ""
    }
    else if (val == "aberration") {
        types = "abde";
    }
    else if (val == "aberration_cunning") {
        types = "abdefgh";
    }
    else if (val == "animal") {
        types = "abde";
    }
    else if (val == "construct") {
        types = "ef";
    }
    else if (val == "construct_guardian") {
        types = "efbch";
    }
    else if (val == "dragon") {
        types = "abchi";
    }
    else if (val == "fey") {
        types = "bcdg";
    }
    else if (val == "humanoid") {
        types = "abdefg";
    }
    else if (val == "humanoid_community") {
        types = "abdefgh";
    }
    else if (val == "magicalbeast") {
        types = "abde";
    }
    else if (val == "monstroushumanoid") {
        types = "abcdeh";
    }
    else if (val == "ooze") {
        types = "abd";
    }
    else if (val == "outsider") {
        // Outsiders can have any type. TODO put a note indicating such.
        types = "";
    }
    else if (val == "plant") {
        types = "abde";
    }
    else if (val == "undead") {
        types = "abde";
    }
    else if (val == "undead_intelligent") {
        types = "abdefg";
    }
    else if (val == "vermin") {
        types = "abd";
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
    $("#form_hoard_types_budget").val(response.budget);
    $("#form_hoard_alloc_budget").val(response.budget);
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
    results.append("<ul><li>" + response + "</li></ul>");
}

// Accept the data back from webgen.py and populate the hoard alloc result
// area with it.
function process_hoard_alloc_response(response, textStatus, jqXHR) {
    //console.log("Hoard Alloc Results: %o", response);
    var results = $("#hoard_alloc_results");
    results.html("");
    if (response == "") {
        results.append("An error has occurred.");
        return;
    }
    results.append("<ul><li>" + response + "</li></ul>");
}

