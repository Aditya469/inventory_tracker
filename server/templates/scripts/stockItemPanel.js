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

$(document).ready(function (){
    setStockItemTableSizes();
    $(window).resize(function(){ setStockItemTableSizes(); });
});

function closeStockItemPanel(){
    $("#editStockItemPanelContainer").prop("hidden", true);
    $(".editStockPanelInput").val("");
    $(".editStockPanelInput").empty();
    $("#stockMovementTableBody").empty();
}

function openStockItemPanel(stockItemId){
    $("#stockId").val(stockItemId);
    getUrl = "{{ url_for('stockManagement.getStockItemById', stockId="") }}" + "/" + stockItemId;
    $.ajax({
        url: getUrl,
        type: "GET",
        success:function (responseData){
            console.log(responseData);
            // unbox for cleaner access
            var bins = responseData.bins;
            var stockItemDetails = responseData.stockItemDetails;

            $("#editStockItemPanelContainer").prop("hidden", false);
            setStockItemTableSizes();
            var i;
            // populate bin select
            for(i = 0; i < bins.length; i++){
                var option = $("<option>");
                option.prop("value", bins[i].id);
                option.html(bins[i].locationName);
                if(bins[i].id == stockItemDetails.bin)
                    option.prop("selected", true);
                $("#location").append(option);
            }
            $("#location").data("locationUpdated", false);

            $("#productTypeName").html(stockItemDetails.productTypeName);
            $("#quantityRemaining").val(stockItemDetails.quantityRemaining);
            $("#quantityUnitDisplay").html(stockItemDetails.quantityUnit);

            if(stockItemDetails.isBulk)
                $("#isBulk").html("Yes");
            else
                $("#isBulk").html("No");

            if(stockItemDetails.isCheckedIn)
                $("#isCheckedIn").html("Yes");
            else
                $("#isCheckedIn").html("No");

            $("#price").val(stockItemDetails.price);
            $("#productDescriptor1").html(stockItemDetails.productDescriptor1 ? stockItemDetails.productDescriptor1 : "");
            $("#productDescriptor2").html(stockItemDetails.productDescriptor2 ? stockItemDetails.productDescriptor2 : "");
            $("#productDescriptor3").html(stockItemDetails.productDescriptor3 ? stockItemDetails.productDescriptor3 : "");

            if(stockItemDetails.canExpire){
                $("#stockItemExpires").prop("checked", true);
                $("#expiryDate").val(stockItemDetails.expiryDate);
            }
            else
                $("#stockItemExpires").prop("checked", false);

            // generate stock movement table body
            for(var i = 0; i < stockItemDetails.movementRecords.length; i++){
                var checkingRecord = stockItemDetails.movementRecords[i];
                var row = $("<tr>");
                row.append($("<td>").append(checkingRecord.timestamp));
                row.append($("<td>").append(checkingRecord.type));
                row.append($("<td>").append(checkingRecord.quantity + " " + stockItemDetails.quantityUnit));
                row.append($("<td>").append(checkingRecord.binName));
                row.append($("<td>").append(checkingRecord.username));
                row.append($("<td>").append(checkingRecord.jobName));
                row.append($("<td>").append(checkingRecord.reasonName));
                $("#stockMovementTableBody").append(row);
            }

        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

// sets the maximum height of the stock item panel table(s) to allow overflow to work correctly
function setStockItemTableSizes(){
    var stockMovementContainerHeight = $("#editStockItemPanel").height() - (
        $("#stockItemPanelNav").outerHeight() +
        $("#commitButtonsContainer").outerHeight()
    );
    var newHeightStyling = "height: " + stockMovementContainerHeight + "px;";
    $("#stockMovementTableContainer").prop("style", newHeightStyling);
}

function onLocationUpdated(){
    $("#location").data("locationUpdated", true);
}

function saveStockItemDetails(){
    var data = new FormData();
    data.append("id", $("#stockId").val());
    data.append("quantityRemaining", $("#quantityRemaining").val());
    var expiryDate = $("#expiryDate").val();
    if(expiryDate != "")
        data.append("expiryDate", expiryDate);
    if($("#stockItemExpires").is(":checked"))
        data.append("canExpire", "true");
    else
        data.append("canExpire", "false");

    data.append("binId", $("#location").val());


    $.ajax({
        url: "{{ url_for('stockManagement.updateStock') }}",
        type: "POST",
        data: data,
        processData: false,
        contentType: false,
        cache: false,
        success: function(){
            updateStockTable();
            $("#saveStockItemFeedbackSpan").html("Changes saved");
            setTimeout(function(){$("#saveStockItemFeedbackSpan").empty();}, 3000);
            $("#deleteStockButton").prop("disabled", true);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function deleteStockItem(){
    if(confirm("Delete this item of stock?")){
        var id = $("#stockId").val();
        var data = {"id": id};
        $.ajax({
            url: "{{ url_for('stockManagement.deleteStockItem') }}",
            type: "POST",
            data: JSON.stringify(data),
            processData: false,
            contentType: "application/json",
            cache: false,
            success: function(){
                closeStockItemPanel();
                updateStockTable();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
            }
        });
    }
}

