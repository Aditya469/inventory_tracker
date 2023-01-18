/*
Copyright 2022 DigitME2

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

$(document).ready(function(){
    updateBinsTable();
    $("#newBinName").keypress(function(event){
        // on enter key pressed
        if(event.which == 13)
            addBin();
    });
});

function addBin(){
    var requestParams = {};
    var newBinName = $("#newBinName").val();

    if(newBinName == ""){
        $("#addBinFeedbackSpan").html("A bin name must be specified");
        setTimeout(function(){$("#addBinFeedbackSpan").html("");}, 5000);
        return;
    }

    requestParams["locationName"] = newBinName;

    $.ajax({
        url: "{{ url_for("bins.createBin") }}",
        type: "POST",
        data: JSON.stringify(requestParams),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(responseData){
            console.log(responseData);
            $("#addBinFeedbackSpan").html(newBinName + " added");
            setTimeout(function(){$("#addBinFeedbackSpan").empty();}, 5000);
            updateBinsTable();
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#addBinFeedbackSpan").html(jqXHR.responseText);
        }
    });
}

function deleteBin(binId){
    if(confirm("Delete this bin?")){
        $(this).prop("disabled", true);
        $.ajax({
            url: "{{ url_for("bins.deleteBin", binId="") }}" + binId,
            type: "POST",
            success: function(){
                updateBinsTable();
                $("#addBinFeedbackSpan").html("");
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
                $("#addBinFeedbackSpan").html(jqXHR.responseText);
            }
        });
    }
}

function updateBinsTable(){
    $.ajax({
        url: "{{ url_for('bins.getBins') }}",
        type: "GET",
        success: function(responseData){
            $("#binTableBody").empty()
            for(var i = 0; i < responseData.length; i++){
                var row = $("<tr>");
                row.append($("<td>").html(responseData[i].locationName));

                var link = $("<a>");
                var url = new URL(window.location.origin + "{{ url_for('bins.getBinIdCard')}}");
                url.searchParams.append("binId", responseData[i].id);
                link.prop("href", url);
                link.html("Download QR code");
                row.append($("<td>").append(link));

                var delBtn = $("<input type='button' value='Delete'>");
                delBtn.data("binId", responseData[i].id);
                delBtn.on("click", function(){ deleteBin($(this).data("binId")); });
                if($("#userCanCreate").val() == "0")
                    delBtn.prop("disabled", true);
                row.append($("<td>").append(delBtn));
                $("#binTableBody").append(row);
            }
        }
    });
}