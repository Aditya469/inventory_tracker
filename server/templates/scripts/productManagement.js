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
    $.ajax({
        url: "{{ url_for('productManagement.getProducts') }}",
        type: "GET",
        data: {"searchTerm": $("#productsSearchBar").val()},
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
                        tr.addClass("table-info");
                    else
                        tr.addClass("table-warning");
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

                var checkbox = $("<input type='checkbox' class='newStockSelectCheckbox'>");
                checkbox.on("click", function(){ onNewStockSelectCheckboxClicked() });
                checkbox.data("verificationRecordId", responseData[i].verificationRecordId);
                tr.append(checkbox);

                tr.append($("<td>" + responseData[i].productName + "</td>"));
                tr.append(
                    $(
                        "<td>" +
                        responseData[i].quantityCheckedIn + " " +
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

//function openProductEditPanel(ProductId){
//    console.log("Open panel for product id " + ProductId);
//}

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

function openProductDetailsPanel(prodId){
    $("#greyout").prop("hidden", false);
    $("#editProductPanel").prop("hidden", false);
    if(prodId != -1){
        $("#addedTimestampLabel").prop("hidden", false);
        $("#addedTimestamp").prop("hidden", false);
        var getDataUrl = "{{ url_for('productManagement.getProduct', productId="") }}" + prodId; // temporary. TODO: improve this
        $.ajax({
            url: getDataUrl,
            type: "GET",
            success: function(responseData){
                console.log(responseData);
                $("#productId").val(responseData.id);
                $("#productName").val(responseData.productName);
                $("#barcode").val(responseData.barcode);
                if(responseData.tracksSpecificItems){
                    $("#bulkSelector").prop("checked", false);
                    $("#specificItemSelector").prop("checked", true);
                }
                else{
                    $("#bulkSelector").prop("checked", true);
                    $("#specificItemSelector").prop("checked", false);
                }
                $("#descriptor1").val(responseData.productDescriptor1 ? responseData.productDescriptor1 : "");
                $("#descriptor2").val(responseData.productDescriptor2 ? responseData.productDescriptor2 : "");
                $("#descriptor3").val(responseData.productDescriptor3 ? responseData.productDescriptor3 : "");
                $("#initialQuantity").val(responseData.initialQuantity);
                $("#quantityUnit").val(responseData.quantityUnit ? responseData.quantityUnit : "");
                if(responseData.canExpire)
                    $("#canExpire").prop("checked", true);
                else
                    $("#canExpire").prop("checked", false);
                $("#expectedPrice").val(responseData.expectedPrice);
                $("#reorderLevel").val(responseData.reorderLevel);
                if(responseData.sendStockNotifications)
                    $("#sendStockNotifications").prop("checked", true);
                else
                    $("#sendStockNotifications").prop("checked", false);
                if(responseData.needsReordering){
                    $("#newStockOrdered").prop("hidden", false);
                    if(responseData.stockReordered)
                        $("#newStockOrdered").prop("checked",true);
                    else
                        $("#newStockOrdered").prop("checked",false);
                }
                else
                    $("#newStockOrdered").prop("hidden", true);
                $("#addedTimestamp").html(responseData.addedTimestamp);
            },
            error: function(jqXHR, textStatus, errorThrown){
                alert(jqXHR.responseText);
            }
        });
    }
}

function saveProductDetails(){
    var productName = $("#productName").val();
    var productBarcode = $("#barcode").val();
    var bulkSpecSelection = "";
    if($("#bulkSelector").is(":checked"))
        bulkSpecSelection = "bulk";
    else if($("#specificItemSelector").is(":checked"))
        bulkSpecSelection = "specific";
    var initialQuantity = $("#initialQuantity").val();

    var dataValid = true;

    if(productName == ""){
        $("#productName").addClass("is-invalid")
        dataValid = false;
    }
    if(productBarcode == ""){
        $("#barcode").addClass("is-invalid");
        dataValid = false;
    }
    if(initialQuantity == ""){
        $("#initialQuantity").addClass("is-invalid");
        dataValid = false;
    }

    if(!dataValid){
        $("#saveProductFeedbackSpan").html("Please fill in all required fields");
        return;
    }

    var fd = new FormData();
    fd.append("id", $("#productId").val());
    fd.append("productName", productName);
    fd.append("barcode", productBarcode);
    fd.append("itemTrackingType", bulkSpecSelection);
    fd.append("productDescriptor1", $("#descriptor1").val());
    fd.append("productDescriptor2", $("#descriptor2").val());
    fd.append("productDescriptor3", $("#descriptor3").val());
    fd.append("initialQuantity", initialQuantity);
    fd.append("expectedPrice", $("#expectedPrice").val());
    fd.append("quantityUnit", ($("#quantityUnit").val() ? $("#quantityUnit").val() : ""));
    if($("#canExpire").is(":checked"))
        fd.append("canExpire", "true");
    else
        fd.append("canExpire", "false");
    fd.append("reorderLevel", $("#reorderLevel").val());
    if($("#sendStockNotifications").is(":checked"))
        fd.append("sendStockNotifications", "true");
    else
        fd.append("sendStockNotifications", "false");
    if($("#newStockOrdered").is(":checked"))
        fd.append("newStockOrdered", "true");
    else
        fd.append("newStockOrdered", "false");

    if($("#productId").val() == "")
        var url = "{{ url_for('productManagement.addNewProductType') }}";
    else
        var url = "{{ url_for('productManagement.updateProductType') }}";

    $.ajax({
        url: url,
        type: "POST",
        data: fd,
        contentType: false,
        processData: false,
        success: function(response){
            $("#saveProductFeedbackSpan").html(response);
            setTimeout(function(){$("#saveProductFeedbackSpan").empty();}, 3000);
            updateProductsTable();
            updateNewStockTable();
        },
        error: function(jqXHR, textStatus, errorThrown){
            $("#saveProductFeedbackSpan").html(jqXHR.responseText);
        }
    });
}

function deleteProduct(){
    if(confirm("Delete this product?")){
        var productId = $("#productId").val();
        var fd = new FormData();
        fd.append("id", productId);
        $.ajax({
            url: "{{ url_for('productManagement.deleteProductType') }}",
            type: "POST",
            data: fd,
            contentType: false,
            processData: false,
            success: function(response){
                closeProductDetailsPanel();
                updateProductsTable();
            },
            error: function(jqXHR, textStatus, errorThrown){
                $("#saveProductFeedbackSpan").html(jqXHR.responseText);
            }
        });
    }
}

function closeProductDetailsPanel(){
    $(".editProductPanelInput").val("").removeClass("is-invalid");
    $("#saveProductFeedbackSpan").html("");
    $("#addedTimestampLabel").prop("hidden", true);
    $("#addedTimestamp").prop("hidden", true);
    $("#addedTimestamp").html("");
    $("#greyout").prop("hidden", true);
    $("#editProductPanel").prop("hidden", true);
    $("#markReorderedButton").prop("hidden", true);
}
