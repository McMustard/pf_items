// generate.js
//
// Copyright (c) 2012, Steven Clark
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

$(document).ready(function(){
    $("#btn_gen_settlement").click(function(event){
        // Get the user's Settlement Size selection.
        var settlement = $("select#settlement_size").val()

        var data_json = {"mode": "settlement",
            "settlement_size": settlement};

    $.ajax({
        type: "POST",
        url:  "cgi-bin/webgen.py",
        datatype: "json",
        data: JSON.stringify(data_json),
        success: function(response) {
            var results = $("#results");
            //console.log("Results: %o", results);
            results.html("");
            results.append("<strong>Base Value:</strong> " +
                response.base_value + "gp<br/>");
            if (response.minor_items.length > 0) {
                results.append("<p>");
                results.append("<strong>Minor Items:</strong><br/>");
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
                results.append("<strong>Medium Items:</strong><br/>");
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
                results.append("<strong>Major Items:</strong><br/>");
                results.append("<ul>");
                for (i in response.major_items) {
                    results.append("<li>" +
                            response.major_items[i] + "</li>");
                }
                results.append("</ul>");
                results.append("</p>");
            }
        }
    });

    // Prevent the default action, which reloads the page.
    // There's probably a more elegant way to set this up.
    event.preventDefault();
    });
});

