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
                tr.click(function(){ openProductEditPanel($(this).data("productId")); });
                tr.append($("<td>" + responseData[i].productName + "</td>"));
                tr.append($("<td>" + responseData[i].barcode + "</td>"));
                if(responseData[i].tracksSpecificItems)
                    tr.append($("<td>Yes</td>"));
                else
                    tr.append($("<td>No</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor1 ? " " + responseData[i].productDescriptor1 : "") + "</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor2 ? " " + responseData[i].productDescriptor2 : "") + "</td>"));
                tr.append($("<td>" + (responseData[i].productDescriptor3 ? " " + responseData[i].productDescriptor3 : "") + "</td>"));

                tbody.append(tr);
            }

            $("#productsTableContainer").empty().append(table);
        }
    });
}

function updateNewStockTable(){
    var searchTerm = $("#productsSearchBar").val();
    var onlyShowUnknownProducts = $("onlyShowUnknownProductsCheckbox").is(":checked");

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
                        responseData[i].quantityCheckedIn +
                        (responseData[i].productQuantityUnit ? responseData[i].productQuantityUnit : "") +
                        "</td>"
                    )
                );

                tbody.append(tr);
            }

            $("#stockOverviewTableContainer").empty().append(table);
        }
    });
}

function openProductEditPanel(ProductId){
    console.log("Open panel for product id " + ProductId);
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
    selectedCheckboxes = $(".newStockSelectCheckbox:checked");
    idList = [];
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
            alert(textStatus);
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
            alert(textStatus);
        }
    });
}
