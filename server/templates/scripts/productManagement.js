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
    updateProductsTable();
    updateNewStockTable();
});

function updateProductsTable(){
    var productSearchParams = {"searchTerm": $("#productsSearchBar").val()};
    $.ajax({
        url: "{{ url_for('productManagement.getProducts') }}",
        type: "GET",
        data: productSearchParams,
        success: function(responseData){
            var table = $("<table id='productsTable' class='table'>");
            var thead = $("<thead>");
            var tr = $("<tr>");
            tr.append($("<th>Product Name</th>"));
            tr.append($("<th>Barcode</th>"));
            tr.append($("<th>Is Bulk?</th>"));
            tr.append($("<th>Descriptor 1</th>"));
            tr.append($("<th>Descriptor 2</th>"));
            tr.append($("<th>Descriptor 3</th>"));

            table.append(thead);
            thead.append(tr);

            var tbody = $("<tbody>");
            table.append(tbody);
            for(var i = 0; i < responseData.length; i++){
                tr = $("<tr>");
                tr.data("productId", responseData[i].id);
                tr.click(function(){ openProductDetailsPanel($(this).data("productId")); });
                if(responseData[i].needsReordering == true)
                {
                    if(responseData[i].stockReordered == true)
                        tr.addClass("productOnReorder");
                    else
                        tr.addClass("productNeedsReorder");
                }
                tr.append($("<td>" + responseData[i].productName + "</td>"));
                tr.append($("<td>" + responseData[i].barcode + "</td>"));
                if(responseData[i].tracksAllItemsOfProductType)
                    tr.append($("<td>Yes</td>"));
                else
                    tr.append($("<td>No</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor1 ? " " + responseData[i].productDescriptor1 : "") + "</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor2 ? " " + responseData[i].productDescriptor2 : "") + "</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor3 ? " " + responseData[i].productDescriptor3 : "") + "</td>"));

                tbody.append(tr);
            }

            $("#productsTableContainer").empty().append(table);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var url = new URL(window.location.origin + "{{ url_for('productManagement.getProductsCsvFile') }}");
    for (key in productSearchParams)
        url.searchParams.append(key, productSearchParams[key]);
    $("#productsCsvDownloadLink").prop("href", url);
}

function updateNewStockTable(){
    var searchTerm = $("#stockSearchBar").val();
    var onlyShowUnknownProducts = $("#onlyShowUnknownProductsCheckbox").is(":checked");

    $.ajax({
        url: "{{ url_for('stockManagement.getNewlyAddedStock') }}",
        type: "GET",
        data: {
                "searchTerm": searchTerm,
                "onlyShowUnknownProducts": onlyShowUnknownProducts
            },
        success: function(responseData){
            var table = $("<table id='productsTable' class='table'>");
            var thead = $("<thead>");
            var tr = $("<tr>");
            tr.append($("<th/>"));
            tr.append($("<th>Product Name</th>"));
            tr.append($("<th>Quantity checked in</th>"));
            table.append(thead);
            thead.append(tr);

            var tbody = $("<tbody>");
            table.append(tbody);
            for(var i = 0; i < responseData.length; i++){
                tr = $("<tr>");
                tr.data("verificationRecordId", responseData[i].verificationRecordId);
                tr.click(function(){ });

                var checkbox = $("<input type='checkbox' class='newStockSelectCheckbox form-check-input mt-2'>");
                checkbox.on("click", function(){ onNewStockSelectCheckboxClicked() });
                checkbox.data("verificationRecordId", responseData[i].verificationRecordId);
                if($("#userCanCreate").val() == "0")
                    checkbox.prop("disabled", true);
                tr.append(checkbox);

                tr.append($("<td>" + responseData[i].productName + "</td>"));
                tr.append(
                    $(
                        "<td>" +
                        responseData[i].quantity + " " +
                        (responseData[i].productQuantityUnit ? responseData[i].productQuantityUnit : "") +
                        "</td>"
                    )
                );

                tbody.append(tr);
            }

            $("#stockOverviewTableContainer").empty().append(table);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function onNewStockSelectCheckboxClicked(){
    if($(".newStockSelectCheckbox:checked").length == $(".newStockSelectCheckbox").length){
        $("#selectAllCheckbox").prop("checked", true);
    }
    else{
        $("#selectAllCheckbox").prop("checked", false);
    }

    if($(".newStockSelectCheckbox:checked").length > 0)
        $("#deleteSelectedNewStockButton").prop("disabled", false);
    else
        $("#deleteSelectedNewStockButton").prop("disabled", true);
}

function onSelectAllCheckboxClicked(){
    if($("#selectAllCheckbox").is(":checked")){
        $(".newStockSelectCheckbox").prop("checked", true)
        $("#deleteSelectedNewStockButton").prop("disabled", false);
    }
    else{
        $(".newStockSelectCheckbox").prop("checked", false)
        $("#deleteSelectedNewStockButton").prop("disabled", true);
    }
}

function deleteSelectedNewStockItems(){
    if(confirm("Delete the selected items?")){
        var selectedCheckboxes = $(".newStockSelectCheckbox:checked");
        var idList = [];
        for(var i = 0; i < selectedCheckboxes.length; i++){
            var id = $(selectedCheckboxes[i]).data("verificationRecordId");
            console.log("Add verification record " + id + "to the list to delete");
            idList.push(id);
        }

        var data = JSON.stringify(idList);

        $.ajax({
            url: "{{ url_for('stockManagement.deleteNewlyAddedStock') }}",
            type: "POST",
            data: data,
            processData: false,
            contentType: "application/json",
            cache: false,
            success: function(){
                updateNewStockTable();
            },
            error: function(jqXHR, textStatus, errorThrown){
                alert(jqXHR.responseText);
            }
        });
    }
}

function verifyAllNewStock(){
    $.ajax({
        url: "{{ url_for('stockManagement.verifyAllNewStock') }}",
        type: "POST",
        success: function(){
            updateNewStockTable();
        },
        error: function(jqXHR, textStatus, errorThrown){
            alert(jqXHR.responseText);
        }
    });
}

