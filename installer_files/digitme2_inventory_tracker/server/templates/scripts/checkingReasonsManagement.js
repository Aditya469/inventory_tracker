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
    updateReasonsTable();
});

function addReason(){
    var requestParams = {};
    var newReason = $("#newReason").val();

    if(newReason == ""){
        $("#addReasonFeedbackSpan").html("A checking reason must be specified");
        setTimeout(function(){$("#addReasonFeedbackSpan").html("");}, 5000);
        return;
    }

    requestParams["reason"] = newReason;

    $.ajax({
        url: "{{ url_for("checkingReasons.createCheckingReason") }}",
        type: "POST",
        data: JSON.stringify(requestParams),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(responseData){
            console.log(responseData);
            updateReasonsTable();
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#addReasonsFeedbackSpan").html(jqXHR.responseText);
        }
    });
}

function deleteReason(reasonId){
    if(confirm("Delete this checking reason?")){
        $(this).prop("disabled", true);
        var url = new URL("{{ url_for("checkingReasons.deleteCheckingReason") }}")
        requestParams = {"reasonId": reasonId}
        $.ajax({
        url: url,
            type: "POST",
            data: JSON.stringify(requestParams),
            processData: false,
            contentType: "application/json",
            cache: false,
            success: function(){
                updateReasonsTable();
                $("#addReasonFeedbackSpan").html("");
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
                $("#addReasonFeedbackSpan").html(jqXHR.responseText);
            }
        });
    }
}

function updateReasonsTable(){
    $.ajax({
        url: "{{ url_for('checkingReasons.getCheckingReasons') }}",
        type: "GET",
        success: function(responseData){
            $("#reasonTableBody").empty()
            for(var i = 0; i < responseData.length; i++){
                var row = $("<tr>");
                row.append($("<td>").html(responseData[i].reason));

                var delBtn = $("<input type='button' value='Delete'>");
                delBtn.data("reasonId", responseData[i].id);
                delBtn.on("click", function(){ deleteBin($(this).data("reasonId")); });
                row.append($("<td>").append(delBtn));
                $("#reasonTableBody").append(row);
            }
        }
    });
}