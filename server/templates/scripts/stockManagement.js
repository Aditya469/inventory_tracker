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
    updateStockTable();
});

function updateStockTable(){
    var requestParams = {};

    requestParams.searchTerm = $("#searchBar").val();
    if(requestParams.searchTerm != ""){
        requestParams.searchByProductTypeName = $("#searchProductTypeName").is(":checked");
        requestParams.searchByIdNumber = $("#searchByIdNumber").is(":checked");
        requestParams.searchByBarcode = $("#searchByBarcode").is(":checked");
        requestParams.searchByDescriptors = $("#searchByDescriptors").is(":checked");
    }

    requestParams.onlyShowExpirableStock = $("#canExpire").is(":checked");
    requestParams.limitExpiryDates = $("#limitExpiryDates").is(":checked");
    if($("#limitExpiryDates").is(":checked")){
        var startDate = $("#startDate").val();
        var endDate = $("#endDate").val();
        if(startDate != "")
            requestParams.expiryStartDate = startDate;
        if(endDate != "")
            requestParams.expiryEndDate = endDate;
    }

    requestParams.limitByPrice = $("#limitByPrice").is(":checked");
    var startPrice = $("#priceRangeStart").val();
    if(startPrice != "")
        requestParams.priceRangeStart = startPrice;
    var endPrice =  $("#priceRangeEnd").val();
    if(endPrice != "")
        requestParams.priceRangeEnd = endPrice;

    requestParams.sortBy = $("input[name='stockSortingOptions']:checked").val();

    $.ajax({
        url: "{{ url_for('stockManagement.getStock') }}",
        type: "GET",
        data: requestParams,
        success: function(responseData){
            console.log(responseData)
            var table = generateStockTable(responseData);
            $("#stockTableContainer").empty().append(table);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

}

function generateStockTable(stockData){
    var table = $("<table id='stockTable' class='table'>");
    var thead = $("<thead>");
    var tr = $("<tr>");
    var selectAllCheckbox = $("<input type='checkbox' class='form-check-input' id='selectAllCheckbox'>");
    selectAllCheckbox.on("click", function(){onSelectAllCheckboxClicked();});
    tr.append($("<th>").append(selectAllCheckbox));
    tr.append($("<th scope='col'>Product Name</th>"));
    tr.append($("<th scope='col'>Qty Remaining</th>"));
    tr.append($("<th scope='col'>Expires?</th>"));
    tr.append($("<th scope='col'>Expiry Date</th>"));
    tr.append($("<th scope='col'>Cost at Purchase</th>"));
    tr.append($("<th scope='col'>Barcode</th>"));
    tr.append($("<th scope='col'>Identifier</th>"));
    thead.append(tr);
    table.append(thead);

    var tbody = $("<tbody>");
    for(i = 0; i < stockData.length; i++){
        tr = $("<tr>");
        tr.data("stockId", stockData[i].id)
        tr.on("click", function(){ openStockItemPanel($(this).data("stockId")); });
        var selectChk = $("<input type='checkbox' class='form-check-input stockItemSelectCheckbox'>");
        selectChk.on("click", function(e){
            e.stopPropagation();
            onStockItemSelectCheckboxClicked();
        });
        tr.append($("<td/>").append(selectChk));
        tr.append($("<td>" + stockData[i].productName + "</td>"));
        tr.append($("<td>" + stockData[i].quantityRemaining + (stockData[i].quantityUnit ? " " + stockData[i].quantityUnit : "") +"</td>"));
        tr.append($("<td>" + (stockData[i].canExpire ? "Yes" : "No") + "</td>"));
        if(stockData[i].canExpire)
            tr.append($("<td>").html(stockData[i].expiryDate));
        else
            tr.append("<td/>");
        if(stockData[i].price)
            tr.append($("<td>" + "£" + stockData[i].price + "</td>"));
        else
            tr.append("<td>");
        tr.append($("<td>" + stockData[i].productBarcode + "</td>"));
        tr.append($("<td>" + stockData[i].idNumber + "</td>"));
        tbody.append(tr);
    }
    table.append(tbody);

    return table;
}

function onSelectAllCheckboxClicked(){
    if($("#selectAllCheckbox").is(":checked")){
        $(".stockItemSelectCheckbox").prop("checked",true);
        $("#deleteStockButton").prop("disabled", false);
    }
    else{
        $(".stockItemSelectCheckbox").prop("checked",false);
        $("#deleteStockButton").prop("disabled", true);
    }
}

function onStockItemSelectCheckboxClicked(){
    if($(".stockItemSelectCheckbox").length == $(".stockItemSelectCheckbox:checked").length)
        $("#selectAllCheckbox").prop("checked", true);
    else
        $("#selectAllCheckbox").prop("checked", false);

    if($(".stockItemSelectCheckbox:checked").length > 0)
        $("#deleteStockButton").prop("disabled", false);
    else
        $("#deleteStockButton").prop("disabled", true);
}

function onCanExpireCheckboxClicked(){
    if($("#canExpire").is(":checked")){
        $("#limitExpiryDates").prop("disabled", false);
    }
    else{
        $("#limitExpiryDates").prop("disabled", true);
        $("#limitExpiryDates").prop("checked", false);
        $("#startDate").prop("disabled", true);
        $("#endDate").prop("disabled", true);
    }
    updateStockTable();
}

function onLimitExpiryDatesClicked(){
    if($("#limitExpiryDates").is(":checked")){
        $("#startDate").prop("disabled", false);
        $("#endDate").prop("disabled", false);
    }
    else{
        $("#startDate").prop("disabled", true);
        $("#endDate").prop("disabled", true);
    }
    updateStockTable();
}

function onLimitByPriceCheckboxClicked(){
    if($("#limitByPrice").is(":checked")){
        $("#priceRangeStart").prop("disabled", false);
        $("#priceRangeEnd").prop("disabled", false);
    }
    else{
        $("#priceRangeStart").prop("disabled", true);
        $("#priceRangeEnd").prop("disabled", true);
    }
    updateStockTable();
}

function onDeleteSelectedButtonClicked(){
    if(confirm("Delete the selected items?")){
        var selectedRows = $(".stockItemSelectCheckbox:checked").closest("tr");
        var idList = []
        for(var i = 0; i < selectedRows.length; i++){
            idList.push($(selectedRows[i]).data("stockId"));
        }

        $.ajax({
            url: "{{ url_for('stockManagement.deleteMultipleStockItems') }}",
            type: "POST",
            data: JSON.stringify({"idList":idList}),
            processData: false,
            contentType: "application/json",
            cache: false,
            success: function(){
                updateStockTable();
                $("#deleteStockButton").prop("disabled", true);
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
            }
        });
    }
}

function closeStockItemPanel(){
    $("#greyout").prop("hidden", true);
    $("#editStockItemPanel").prop("hidden", true);
    $(".editStockPanelInput").val("");
    $(".editStockPanelInput").empty();
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

            $("#greyout").prop("hidden", false);
            $("#editStockItemPanel").prop("hidden", false);
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


        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
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