// generate.js

// Copyright (c) 2012-2013, Steven Clark
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

// These references will point to items pertaining to a "page" of date, so
// that it's easy to show only one set at a time.
//var settlement_page = null;
//var individual_page = null;

$(document).ready(function(){

    // Set the page variables.
    var settlement_page = $("#div_settlement");
    var individual_page = $("#div_individual");
    
    // Set up the page handlers.
    $("#page_settlement_sel").click(function(event){
        select_page("settlement");
    });
    $("#page_individual_sel").click(function(event){
        select_page("individual");
    });

    // Default page
    select_page("settlement");

    setup_generator("settlement", process_settlement_response, true)
    setup_generator("individual", process_individual_response, true)
});

// Sets up a button to "submit" a form.
function setup_generator(page, handler, clear) {
    // Set up the form's Generate button handler.
    $("#btn_" + page + "_generate").click(function(event){
        // Get the form data.
        var json = get_form_data("form_" + page, page);
        // Debug
        console.log("Sending request: ", json);
        //// Debug: Clear the current results.
        //if (clear) {
        //    $("#" + page + "_results").html("");
        //}
        // Send the request.
        send_request(json, handler);
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
    console.log("gfd: %o", fields);
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
function process_settlement_response(response) {
    //console.log("Results: %o", response);
    // Fill out the results receptacle with the result data.
    var results = $("#settlement_results");
    results.html("");
    results.append("<strong>Base Value:</strong> " +
        response.base_value + "gp<br/>");
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
function process_individual_response(response) {
    //console.log("Results: %o", response);
    var results = $("#individual_results");
    results.html("");
    results.append("<ul><li>" + response + "</li></ul>");
}

// Accept the data back from webgen.py and populate the <???> result
// area with it.
