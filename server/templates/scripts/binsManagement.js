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
            updateBinsTable();
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(textStatus);
            $("#addBinFeedbackSpan").html(textStatus);
        }
    });
}

function deleteBin(binId){
    if(confirm("Delete this bin?")){
        $.ajax({
            url: "{{ url_for("bins.deleteBin", binId="") }}" + binId,
            type: "POST",
            success: function(){
                updateBinsTable();
                $("#addBinFeedbackSpan").html("");
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $("#addBinFeedbackSpan").html(textStatus);
            }
        });
    }
}

function updateBinsTable(){
    $.ajax({
        url: "{{ url_for('bins.getBins') }}",
        type: "GET",
        success: function(responseData){
            var table = $("<table class='table'>");
            table.append(
                $("<thead>")
                .append($("<tr>")
                    .append($("<td>Location Name</td>"))
                    .append($("<td>QR Code</td>"))
                    .append($("<td>Delete</td>"))
                )
            );
            var tbody = $("<tbody>");
            table.append(tbody);

            for(var i = 0; i < responseData.length; i++){
                var row = $("<tr>");
                row.append($("<td>").html(responseData[i].locationName));

                var link = $("<a>");
                var href = "{{ url_for('files.getFile', filename='')}}" + responseData[i].qrCodeName;
                link.prop("href", href);
                link.html("Download QR code");
                row.append($("<td>").append(link));

                var delBtn = $("<input type='button' value='Delete'>");
                delBtn.data("binId", responseData[i].id);
                delBtn.on("click", function(){ deleteBin($(this).data("binId")); });
                row.append($("<td>").append(delBtn));
                tbody.append(row);
            }

            $("#binListContainer").empty().append(table);
        }
    });
}