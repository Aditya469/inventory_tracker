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

refreshCheckIntervalId = null;
lastUpdateTimestamp = "";

$(document).ready(function(){
    setProductPanelDetailsHeight();
    $(window).resize(function(){ setProductPanelDetailsHeight(); });
    $(".editProductPanelInput").keypress(function(event){
        // on enter key pressed
        if(event.which == 13)
            saveProductDetails();
    });
});

function setProductPanelDetailsHeight(){
    // calculate the height of the required stock and stock used table containers and set
    var stockUsedContainerHeight = $("#editJobPanel").height() - (
        $("#productPanelNav").outerHeight() +
        $("#commitButtonsContainer").outerHeight()
    );
    var newHeightStyling = "height: " + stockUsedContainerHeight + "px;";
    $("#productPanelDetails").prop("style", newHeightStyling);
}

function onBulkSelectorRadioChanged(){
    if($(".bulkSelectorRadio:checked").val() == "bulk"){
        console.log("bulk");
        $("#canExpireLabel").prop("hidden", true);
        $("#canExpire").prop("hidden", true).prop("checked", false);
        $("#notifyExpiryLabel").prop("hidden", true);
        $("#notifyExpiry").prop("hidden", true).prop("checked", false);
        $("#expiryWarningDayCountLabel").prop("hidden", true);
        $("#expiryWarningDayCount").prop("hidden", true).val("0");
    }
    else{
        console.log("specific");
        $("#canExpireLabel").prop("hidden", false);
        $("#canExpire").prop("hidden", false);
        $("#notifyExpiryLabel").prop("hidden", false);
        $("#notifyExpiry").prop("hidden", false);
        $("#expiryWarningDayCountLabel").prop("hidden", false);
        $("#expiryWarningDayCount").prop("hidden", false).val("7");
    }
}

function openProductDetailsPanel(prodId){
    $("#greyout").prop("hidden", false);
    if(prodId == -1){
        $("#editProductPanel").prop("hidden", false);
        $("#addAnotherProductButton").prop("hidden", true);
        $("#panelTitle").html("Create New Product Type");
        $("#deleteButton").prop("disabled", true);
        $("#productId").val("-1");
    }
    else{
        $("#panelTitle").html("Edit Product Type Details");
        $("#addedTimestampLabel").prop("hidden", false);
        $("#addedTimestamp").prop("hidden", false);
        $("#btnGetBarcodeStickerSheet").prop("disabled", false);
        $("#btnGetBarcodeStickerSingle").prop("disabled", false);
        if($("#userCanCreate").val() == "0")
            $("#deleteButton").prop("disabled", true);
        else
            $("#deleteButton").prop("disabled", false);
        let getDataUrl = new URL(window.location.origin + "{{ url_for('productManagement.getProduct') }}");
        getDataUrl.searchParams.append("productId", prodId);
        $.ajax({
            url: getDataUrl,
            type: "GET",
            success: function(responseData){
                console.log(responseData);
                $("#editProductPanel").prop("hidden", false);
                $("#productId").val(responseData.id);
                $("#productName").val(responseData.productName);
                $("#barcode").val(responseData.barcode);
                if(responseData.tracksSpecificItems){
                    $("#bulkSelector").prop("checked", false);
                    $("#specificItemSelector").prop("checked", true);
                    $("#canExpireLabel").prop("hidden", false);
                    $("#canExpire").prop("hidden", false);
                }
                else{
                    $("#bulkSelector").prop("checked", true);
                    $("#specificItemSelector").prop("checked", false);
                    $("#canExpireLabel").prop("hidden", true);
                    $("#canExpire").prop("hidden", true).prop("checked", false);
                }
                $("#descriptor1").val(responseData.productDescriptor1 ? responseData.productDescriptor1 : "");
                $("#descriptor2").val(responseData.productDescriptor2 ? responseData.productDescriptor2 : "");
                $("#descriptor3").val(responseData.productDescriptor3 ? responseData.productDescriptor3 : "");
                $("#initialQuantity").val(responseData.initialQuantity);
                $("#quantityUnit").val(responseData.quantityUnit ? responseData.quantityUnit : "");
                $("#canExpire").prop("checked", responseData.canExpire);
                $("#notifyExpiry").prop("checked", responseData.notifyExpiry)
                $("#expiryWarningDayCount").val(responseData.expiryWarningDayCount);
                $("#expectedPrice").val(responseData.expectedPrice);
                $("#reorderLevel").val(responseData.reorderLevel);
                if(responseData.sendStockNotifications)
                    $("#sendStockNotifications").prop("checked", true);
                else
                    $("#sendStockNotifications").prop("checked", false);
                if(responseData.needsReordering){
                    $("#newStockOrdered").prop("hidden", false);
                    $("#newStockOrderedLabel").prop("hidden", false);
                    if(responseData.stockReordered)
                        $("#newStockOrdered").prop("checked",true);
                    else
                        $("#newStockOrdered").prop("checked",false);
                }
                else{
                    $("#newStockOrdered").prop("hidden", true);
                    $("#newStockOrderedLabel").prop("hidden", true);
                }
                $("#addedTimestamp").html(responseData.addedTimestamp);

                lastUpdateTimestamp = responseData.lastUpdated;

                // set up event to check for the product having been updated elsewhere
                if(refreshCheckIntervalId != null)
                    clearInterval(refreshCheckIntervalId);
                startProductUpdatedInterval();

            },
            error: function(jqXHR, textStatus, errorThrown){
                alert(jqXHR.responseText);
            }
        });
    }
}

function startProductUpdatedInterval(){
    refreshCheckIntervalId = setInterval(function(){
        console.log("Checking if this product has been updated");
        var id = $("#productId").val();
        if(id == "-1" || id == "")
            return;

        var url = new URL(window.location.origin + "{{ url_for('productManagement.getProductTypeLastUpdateTimestamp') }}");
        url.searchParams.append("itemId", id);
        $.ajax({
            url: url,
            type: "GET",
            success: function(responseTimestamp){
                console.log("got response: " + responseTimestamp);
                if(lastUpdateTimestamp != responseTimestamp){
                    console.log("an update has occurred");
                    clearInterval(refreshCheckIntervalId);
                    if(confirm("This product's status has changed. Reload?"))
                        openProductDetailsPanel(id);
                    else
                    {
                        lastUpdateTimestamp = responseTimestamp;
                        startProductUpdatedInterval();
                    }
                }
            }
        });
    }, 5000);
}

function saveProductDetails(){
    // pause update check until the new data has been saved.
    if(refreshCheckIntervalId != null)
        clearInterval(refreshCheckIntervalId);

    var productName = $("#productName").val();
    var productBarcode = $("#barcode").val();
    var bulkSpecSelection = "";
    if($("#bulkSelector").is(":checked"))
        bulkSpecSelection = "bulk";
    else if($("#specificItemSelector").is(":checked"))
        bulkSpecSelection = "specific";
    var initialQuantity = $("#initialQuantity").val();

    var dataValid = true;
    $("#productName").removeClass("is-invalid");
    $("#barcode").removeClass("is-invalid");
    $("#initialQuantity").removeClass("is-invalid");

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

    if($("#notifyExpiry").is(":checked"))
        fd.append("notifyExpiry", "true")
    else
        fd.append("notifyExpiry", "false")

    if($("#expiryWarningDayCount").val() != "")
        fd.append("expiryWarningDayCount", $("#expiryWarningDayCount").val());
    else
        fd.append("expiryWarningDayCount", 0);

    fd.append("reorderLevel", $("#reorderLevel").val());

    if($("#sendStockNotifications").is(":checked"))
        fd.append("sendStockNotifications", "true");
    else
        fd.append("sendStockNotifications", "false");

    if($("#newStockOrdered").is(":checked"))
        fd.append("newStockOrdered", "true");
    else
        fd.append("newStockOrdered", "false");

    if($("#productId").val() == "-1")
        var url = "{{ url_for('productManagement.addNewProductType') }}";
    else
        var url = "{{ url_for('productManagement.updateProductType') }}";

    $.ajax({
        url: url,
        type: "POST",
        data: fd,
        contentType: false,
        processData: false,
        cache: false,
        success: function(response){
            console.log(response);
            if(response.success){
                $("#saveProductFeedbackSpan").html(response.message);
                setTimeout(function(){$("#saveProductFeedbackSpan").empty();}, 3000);
                updateProductsTable();
                updateNewStockTable();

                // if we just saved a new product, make the addAnotherProduct button available, otherwise theres
                // a strong tendency to end up changing details thinking you're adding another product
                if($("#productId").val() == "-1")
                    $("#addAnotherProductButton").prop("hidden", false);

                openProductDetailsPanel(response.id); // most straightforward way to reset the update timer and stuff
            }
            else{
                $("#saveProductFeedbackSpan").html(response.message);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR);
            $("#saveProductFeedbackSpan").html(jqXHR.responseText);
        }
    });
}

function deleteProduct(){
    if(confirm("Delete this product?\n\nWARNING: THIS WILL ALSO DELETE ALL STOCK ITEMS OF THIS TYPE")){
        if(refreshCheckIntervalId != null)
            clearInterval(refreshCheckIntervalId);
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
    $("#newStockOrderedLabel").prop("hidden", true);
    $("#newStockOrdered").prop("hidden", true);
    $("#btnGetBarcodeStickerSheet").prop("disabled", true);
    $("#btnGetBarcodeStickerSingle").prop("disabled", true);
    $("#addAnotherProductButton").prop("hidden", true);
    if(refreshCheckIntervalId != null)
        clearInterval(refreshCheckIntervalId);
}

function getProductIdSticker(){
    let stickerUrl = new URL(window.location.origin +  "{{ url_for('productManagement.getProductIdCard') }}");
    stickerUrl.searchParams.append("productItemId", $("#productId").val())
    window.location.href = stickerUrl;
}

function onBarcodeInput(){
    $("#btnGetBarcodeStickerSheet").prop("disabled", true);
    $("#btnGetBarcodeStickerSingle").prop("disabled", true);
}