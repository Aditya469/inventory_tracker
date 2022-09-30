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

var assignedStockIdsToDelete = [];

$(document).ready(function(){
    updateJobsTable();
    updateStockTables();
    setJobStockTableSizes();
    $(window).resize(function(){ setJobStockTableSizes(); });
});

function updateJobsTable(){
    // fetch jobs table data and populate
    var searchTerm = $("#jobSearchBar").val();
    var jobSearchParams = {"searchTerm": searchTerm};
    $.ajax({
        url: "{{ url_for('jobs.getJobs') }}",
        type: "GET",
        data: jobSearchParams,
        success:function(responseData){
            console.log(responseData);

            var table = $("<table id='jobsTable' class='table'>");
            var thead = $("<thead>");
            var tr = $("<tr>");
            tr.append($("<th scope='col'>Job Name</th>"));
            tr.append($("<th scope='col'>Created</th>"));
            tr.append($("<th scope='col'>Cumulative Cost</th>"));
            thead.append(tr);
            table.append(thead);

            var tbody = $("<tbody>");
            for(i=0; i < responseData.length; i++){
                tr = $("<tr>");
                tr.data("jobId", responseData[i].id);
                tr.on("click", function(){ openJobDetailsPanel($(this).data("jobId")); });
                tr.append($("<td>" + responseData[i].jobName + "</td>"));
                tr.append($("<td>" + responseData[i].addedTimestamp + "</td>"));
                tr.append($("<td>" + responseData[i].totalCost + "</td>"));
                tbody.append(tr);
            }
            table.append(tbody);

            $("#jobsTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
    var url = new URL("http://" + document.location.host + "{{ url_for('jobs.getJobsCsvFile') }}");
    for (key in jobSearchParams)
        url.searchParams.append(key, jobSearchParams[key]);
    $("#jobsOverviewCsvDownloadLink").prop("href", url);
}

function updateStockTables(){
    // note that this updates all 4 stock tables at the same time
    var searchTerm = $("#stockSearchBar").val();

    // make a bunch of ajax requests and bring all the tables up to date
    var totalStockParams = { "searchTerm": searchTerm, "overviewType": "totalStock" };
    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: totalStockParams,
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id","stockTotalTable");
            $("#totalStockTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var availableStockParams = { "searchTerm": searchTerm, "overviewType": "availableStock" };
    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: availableStockParams,
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "availableStockTable");
            $("#availableStockTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var expiringStockParams = {
        "searchTerm": searchTerm,
        "overviewType": "nearExpiry",
        "dayCountLimit": $("#stockDaysNearExpiry").val()
    };
    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: expiringStockParams,
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "oldStockTable");
            $("#oldStockTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var expiredStockParams = { "searchTerm": searchTerm, "overviewType": "expired" };
    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: expiredStockParams,
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "expiredStockTable");
            $("#expiredStockTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var url = new URL("http://" + document.location.host + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in totalStockParams)
        url.searchParams.append(key, totalStockParams[key]);
    $("#totalStockCsvDownloadLink").prop("href", url);

    var url = new URL("http://" + document.location.host + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in availableStockParams)
        url.searchParams.append(key, availableStockParams[key]);
    $("#availableStockCsvDownloadLink").prop("href", url);

    var url = new URL("http://" + document.location.host + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in expiringStockParams)
        url.searchParams.append(key, expiringStockParams[key]);
    $("#oldStockCsvDownloadLink").prop("href", url);

    var url = new URL("http://" + document.location.host + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in expiredStockParams)
        url.searchParams.append(key, expiredStockParams[key]);
    $("#expiredStockCsvDownloadLink").prop("href", url);
}

function generateOverviewStockTable(stockData)
{
    var table = $("<table class='table'>");
    var thead = $("<thead>");
    var tr = $("<tr>");
    tr.append($("<th scope='col'>Product Name</th>"));
    tr.append($("<th scope='col'>Stock Quantity</th>"));
    tr.append($("<th scope='col'>Bulk Item?</th>"));
    tr.append($("<th scope='col'>Descriptor 1</th>"));
    tr.append($("<th scope='col'>Descriptor 2</th>"));
    tr.append($("<th scope='col'>Descriptor 3</th>"));
    thead.append(tr);
    table.append(thead);

    var tbody = $("<tbody>");
    for(i=0; i<stockData.length; i++){
        tr = $("<tr>");
        tr.data("productName", stockData[i].productName);
        tr.on("click", function(){
            searchUrl = new URL(window.location.origin + "{{ url_for("stockManagement.getStockPage")}}");
            searchUrl.searchParams.append("productName",$(this).data("productName"));
            window.location.href = searchUrl.href;
        });

        tr.append($("<td>" + stockData[i].productName + "</td>"));
        tr.append($("<td>" + stockData[i].stockAmount + " " + stockData[i].quantityUnit + "</td>"));
        if(stockData[i].isBulk)
            tr.append($("<td>Yes</td>"));
        else
            tr.append($("<td>No</td>"));
        tr.append($("<td>" + (stockData[i].descriptor1 ? stockData[i].descriptor1 : "") + "</td>"));
        tr.append($("<td>" + (stockData[i].descriptor2 ? stockData[i].descriptor2 : "") + "</td>"));
        tr.append($("<td>" + (stockData[i].descriptor3 ? stockData[i].descriptor3 : "") + "</td>"));
        tbody.append(tr);
    }
    table.append(tbody);

    return table;
}

function closePanels(){
    $("#greyout").prop("hidden",true);
    $("#editJobPanel").prop("hidden",true);
    $(".editJobInput").val("");
    $(".editJobInput").empty();
    $("#stockUsedTableBody").empty();
    $("#assignedStockTableBody").empty();
}

function openJobDetailsPanel(jobId){
    $("#greyout").prop("hidden",false);
    $("#editJobPanel").prop("hidden",false);
    // trigger a few handlers to get data loaded into elements on screen
    onRequiredStockSearchBarInput();
    assignedStockIdsToDelete = [];
    if(jobId != -1){
        $("#jobQrCodeLink").prop("hidden", false);
        $("#stockUsedContainer").prop("hidden", false);
        $("#deleteButton").prop("hidden", false);
        $("#jobName").val("");

        var url = "{{ url_for( 'jobs.getJob', jobId='')}}" + jobId;
        $.ajax({
            type:"GET",
            url: url,
            success: function(jobData){
                console.log(jobData);
                populateJobPanel(jobData);
            },
            error:function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
            }
        });
    }
    else{
        $("#jobId").val(jobId);
        $("#jobQrCodeLink").prop("hidden", true);
        $("#stockUsedContainer").prop("hidden", true);
        $("#deleteButton").prop("hidden", true);
        $("#jobName").val("");
    }
}

function populateJobPanel(jobData){
    setJobStockTableSizes();
    assignedStockIdsToDelete = [];
    $("#jobId").val(jobData.id);
    $("#jobName").val(jobData.jobName);
    $("#jobQrCodeLink").prop("href","{{ url_for('files.getFile', filename='') }}" + jobData.qrCodeName);
    $("#totalCost").html("£" + jobData.cost);

    $("#stockUsedTableBody").empty();

    for(var i = 0; i < jobData.stockTotals.length; i++){
        var row = $("<tr>");
        row.append($("<td>").html(jobData.stockTotals[i].productName));
        row.append($("<td>").html(
            jobData.stockTotals[i].qtyOfProductUsed + " " +
            (jobData.stockTotals[i].quantityUnit ? jobData.stockTotals[i].quantityUnit : "")));
        row.append($("<td>").html(jobData.stockTotals[i].costOfProductUsed));
        $("#stockUsedTableBody").append(row);
    }

    $("#assignedStockTableBody").empty();
    for(var i = 0; i < jobData.assignedStock.length; i++){
        var row = $("<tr>");
        row.data("assignedStockRecordId", jobData.assignedStock[i].assignationId)

        var checkbox = $("<input type='checkbox' class='assignedStockSelectCheckbox'>")
        checkbox.on('click', function(){ onAssignedStockSelectCheckboxClicked(); });
        row.append($("<td>").append(checkbox));

        row.append($("<td>").html(jobData.assignedStock[i].productName));

        var qtyContainerDiv = $("<div class='input-group'>");

        var numberInput = $("<input type='number' class='assignedStockQuantity form-control'>");
        numberInput.on('input', function(){ $(this).parents("tr").first().addClass("changedAssignedQty"); } );
        numberInput.val(jobData.assignedStock[i].quantity)

        var numberUnitSpan = $("<span class='input-group-text'>");
        numberUnitSpan.html(jobData.assignedStock[i].unit);

        qtyContainerDiv.append(numberInput);
        qtyContainerDiv.append(numberUnitSpan);

        row.append($("<td>").append(qtyContainerDiv));

        $("#assignedStockTableBody").append(row);
    }
}

function onRequiredStockSearchBarInput(){
    $.ajax({
        type: "GET",
        url: "{{ url_for('productManagement.getProducts') }}",
        data: {"searchTerm": $("#assignStockSearchBar").val()},
        success: function(products){
            $("#knownProductDropdown").empty();
            for(var i = 0; i < products.length; i++){
                var option = $("<option>");
                option.prop("value", products[i].id);
                option.html(products[i].productName);
                option.data("qtyUnit", products[i].quantityUnit);
                if(i == 0)
                    option.prop("selected", true);
                $("#knownProductDropdown").append(option);
            }
            onKnownProductSelectChange();
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText)
        }
    });
}

function onKnownProductSelectChange(){
    $("#quantityUnitDisplay").html($("#knownProductDropdown").children("option:selected").first().data("qtyUnit"));
}

function addStockToAssignedList(){
    var row = $("<tr>");
    var checkbox = $("<input type='checkbox' class='assignedStockSelectCheckbox'>");
    checkbox.on("click", function(){ onAssignedStockSelectCheckboxClicked() });

    var quantity = $("#quantityToAssign").val();
    var selectedProductOption = $("#knownProductDropdown").children("option:selected").first();
    var productName = selectedProductOption.html();
    var productId = selectedProductOption.val();
    var productQtyUnit = selectedProductOption.data("qtyUnit");

    row.addClass("newAssignedQty")
    row.data("productId", productId);

    row.append($("<td>").append(checkbox));
    row.append($("<td>").html(productName));

    var qtyContainerDiv = $("<div class='input-group'>");
    var numberInput = $("<input type='number' class='assignedStockQuantity form-control'>");
    numberInput.val(quantity)
    var numberUnitSpan = $("<span class='input-group-text'>");
    numberUnitSpan.html(productQtyUnit);

    qtyContainerDiv.append(numberInput);
    qtyContainerDiv.append(numberUnitSpan);

    row.append($("<td>").append(qtyContainerDiv));

    $("#assignedStockTableBody").append(row);
}

function onAssignedStockSelectCheckboxClicked(){
    if($(".assignedStockSelectCheckbox:checked").length == $(".assignedStockSelectCheckbox").length)
        $("#selectAllRequiredStock").prop("checked", true);
    else
        $("#selectAllRequiredStock").prop("checked", false);

    if($(".assignedStockSelectCheckbox:checked").length > 0)
        $("#removeAssignedStockButton").prop("disabled", false);
    else
        $("#removeAssignedStockButton").prop("disabled", true);
}

function onSelectAllRequiredStockClicked(){
    if($("#selectAllRequiredStock").is(":checked"))
        $(".assignedStockSelectCheckbox").prop("checked", true);
    else
        $(".assignedStockSelectCheckbox").prop("checked", false);

    if($(".assignedStockSelectCheckbox:checked").length > 0)
        $("#removeAssignedStockButton").prop("disabled", false);
    else
        $("#removeAssignedStockButton").prop("disabled", true);
}

function onRemoveAssignedStockButtonClicked(){
    var rows = $(".assignedStockSelectCheckbox:checked").parents("tr");
    for(var i = 0; i < rows.length; i++){
        if($(rows[i]).data("assignedStockRecordId"))
            assignedStockIdsToDelete.push($(rows[i]).data("assignedStockRecordId"));
        $(rows[i]).remove();
    }
    console.log("assigned stock IDs to be deleted: " + assignedStockIdsToDelete);
}

function saveJobDetails(){
    // this needs a list of newly assigned stock, a list of deleted assignments,
    // and a list of changed assignments, as well as the name and ID of the job
    var changedStockAssignments = [];
    var changedRows = $(".changedAssignedQty");
    for(var i = 0; i < changedRows.length; i++){
        var assignmentId = $(changedRows[i]).data("assignedStockRecordId");
        var newQty = $(changedRows[i]).find(".assignedStockQuantity").first().val();
        changedStockAssignments.push({"assignmentId": assignmentId,"newQuantity": newQty});
    }
    var newStockAssignments = [];
    var newRows = $(".newAssignedQty");
    for(var i = 0; i < newRows.length; i++){
        var productId = $(newRows[i]).data("productId");
        var newQty =  $(newRows[i]).find(".assignedStockQuantity").first().val();
        newStockAssignments.push({"productId": productId,"quantity": newQty});
    }

    requestArgs = {};
    requestArgs["jobId"] = $("#jobId").val();
    requestArgs["jobName"] = $("#jobName").val();
    requestArgs["newStockAssignments"] = newStockAssignments;
    requestArgs["changedStockAssignments"] = changedStockAssignments;
    requestArgs["deletedStockAssignments"] = assignedStockIdsToDelete;


    if($("#jobId").val() == "-1")
        url = "{{ url_for('jobs.createJob') }}";
    else
        url = "{{ url_for('jobs.updateJob') }}";

    console.log(requestArgs);

    $.ajax({
        url: url,
        type: "POST",
        data: JSON.stringify(requestArgs),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(responseData){
            openJobDetailsPanel(responseData.newJobId); // this is an east way to get the panel to reload into the state for an existing job
            updateJobsTable();
            updateStockTables();
            $("#saveJobFeedbackSpan").html("Job saved");
            setTimeout(function(){$("#saveJobFeedbackSpan").empty();}, 5000);
        },
        error: function(jqXHR, textStatus, errorThrown){
            alert(jqXHR.responseText);
        }
    });
}

function deleteJob(){
    if(confirm("Delete this job?")){
        $.ajax({
            url: "{{ url_for('jobs.deleteJob', jobId="")}}" + $("#jobId").val(),
            type: "POST",
            success: function(jobId){
                closePanels();
                updateJobsTable();
                updateStockTables();
            },
            error: function(jqXHR, textStatus, errorThrown){
                alert(jqXHR.responseText);
            }
        });
    }
}

function setJobStockTableSizes(){
    // calculate the height of the required stock adn stock used table containers and set
    var stockUsedContainerHeight = $("#editJobPanel").height() - (
        $("#jobPanelNav").outerHeight() +
        $("#jobNameContainer").outerHeight() +
        $("#commitButtonsContainer").outerHeight()
    );
    var newHeightStyling = "height: " + stockUsedContainerHeight + "px;";
    $("#stockUsedContainer").prop("style", newHeightStyling);

    var assignedStockContainerHeight = $("#editJobPanel").height() - (
        $("#jobPanelNav").outerHeight() +
        $("#reqStockTitle").outerHeight() +
        $("#reqStockSearch").outerHeight() +
        $("#reqStockAssign").outerHeight() +
        $("#commitButtonsContainer").outerHeight()
    );
    newHeightStyling = "height: " + assignedStockContainerHeight + "px;";
    $("#assignedStockTableContainer").prop("style", newHeightStyling);
}