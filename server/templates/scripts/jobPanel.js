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

refreshCheckIntervalId = null;
lastUpdateTimestamp = "";

$(document).ready(function(){
    setJobStockTableSizes();
    $(window).resize(function(){ setJobStockTableSizes(); });
});

function closePanels(){
    $("#greyout").prop("hidden",true);
    $("#editJobPanel").prop("hidden",true);
    $(".editJobInput").val("");
    $(".editJobInput").empty();
    $(".editJobInput").removeClass('is-invalid');
    $("#stockUsedTableBody").empty();
    $("#assignedStockTableBody").empty();
    if(refreshCheckIntervalId != null)
        clearInterval(refreshCheckIntervalId);
}

function openJobDetailsPanel(jobId){
    $("#greyout").prop("hidden",false);
    $("#editJobPanel").prop("hidden",false);
    $("#templateId").val("");
    // trigger a few handlers to get data loaded into elements on screen
    setJobStockTableSizes();
    onRequiredStockSearchBarInput();
    assignedStockIdsToDelete = [];
    if(jobId != -1){
        $("#jobQrCodeLink").prop("hidden", false);
        $("#stockUsedContainer").prop("hidden", false);
        $("#deleteButton").prop("hidden", false);
        $("#saveTemplateButton").prop("hidden", true);
        $("#jobName").val("");

        var pickingListUrl = new URL(window.location.origin + '{{ url_for("jobs.getPickingList")}}');
        pickingListUrl.searchParams.append("jobId", jobId);
        $("#pickingListLink").prop("hidden", false).prop("href", pickingListUrl);

        var jobDataUrl = new URL(window.location.origin + "{{ url_for( 'jobs.getJob')}}");
        jobDataUrl.searchParams.append("jobId", jobId);
        $.ajax({
            type:"GET",
            url: jobDataUrl,
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
        $("#saveTemplateButton").prop("hidden", false);
        $("#pickingListLink").prop("hidden", true);
        $("#jobName").val("");
    }
}

function populateJobPanel(jobData){
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

        row.append($("<td class='assignedStockQuantityContainer'>").append(qtyContainerDiv));

        $("#assignedStockTableBody").append(row);
    }

    lastUpdateTimestamp = jobData.lastUpdated;

    // set up event to check for the job having been updated elsewhere
    if(refreshCheckIntervalId != null)
        clearInterval(refreshCheckIntervalId);

    startJobUpdatedInterval();
}

function startJobUpdatedInterval(){
    refreshCheckIntervalId = setInterval(function(){
        var id = $("#jobId").val();
        if(id == "-1" || id == "")
            return;

        var url = new URL(window.location.origin + "{{ url_for('jobs.getJobLastUpdateTimestamp') }}");
        url.searchParams.append("itemId", id);

        $.ajax({
            url: url,
            type: "GET",
             success: function(responseTimestamp){
                console.log("got response: " + responseTimestamp);
                if(lastUpdateTimestamp != responseTimestamp){
                    console.log("an update has occurred");
                    clearInterval(refreshCheckIntervalId);
                    if(confirm("This jobs's status has changed. Reload?"))
                        openJobDetailsPanel(id);
                    else
                    {
                        lastUpdateTimestamp = responseTimestamp;
                        startJobUpdatedInterval();
                    }
                }
            }
        });
    }, 5000);
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

function onAddStockButtonClicked(){
    var quantity = $("#quantityToAssign").val();
    var selectedProductOption = $("#knownProductDropdown").children("option:selected").first();
    var productName = selectedProductOption.html();
    var productId = selectedProductOption.val();
    var productQtyUnit = selectedProductOption.data("qtyUnit");

    addStockToAssignedList(productName, productId, quantity, productQtyUnit);
    $("#pickingListLink").prop("hidden", true); // hide the picking link list until the job is saved
}

function addStockToAssignedList(ProductName, ProductId, ProductQuantity, ProductQtyUnit){
    var row = $("<tr>");
    var checkbox = $("<input type='checkbox' class='assignedStockSelectCheckbox'>");
    checkbox.on("click", function(){ onAssignedStockSelectCheckboxClicked() });

    row.addClass("newAssignedQty")
    row.addClass("stockAssignmentRow")
    row.data("productId", ProductId);

    row.append($("<td>").append(checkbox));
    row.append($("<td>").html(ProductName));

    var qtyContainerDiv = $("<div class='input-group'>");
    var numberInput = $("<input type='number' class='assignedStockQuantity form-control'>");
    numberInput.val(ProductQuantity)
    var numberUnitSpan = $("<span class='input-group-text'>");
    numberUnitSpan.html(ProductQtyUnit);

    qtyContainerDiv.append(numberInput);
    qtyContainerDiv.append(numberUnitSpan);

    row.append($("<td class='assignedStockQuantityContainer'>").append(qtyContainerDiv));

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
    // and a list of changed assignments, as well as the name and ID of the job.
    // validate inputs as we go
    var dataValid = true;

    var changedStockAssignments = [];
    var changedRows = $(".changedAssignedQty");
    for(var i = 0; i < changedRows.length; i++){
        var assignmentId = $(changedRows[i]).data("assignedStockRecordId");
        var qtyInput = $(changedRows[i]).find(".assignedStockQuantity").first();
        var newQty = qtyInput.val();
        if(Number(newQty) == NaN || Number(newQty) == 0 || newQty == ""){
            dataValid = false;
            qtyInput.addClass('is-invalid');
        }
        else
            qtyInput.removeClass('is-invalid');
        changedStockAssignments.push({"assignmentId": assignmentId,"newQuantity": newQty});
    }

    var newStockAssignments = [];
    var newRows = $(".newAssignedQty");
    for(var i = 0; i < newRows.length; i++){
        var productId = $(newRows[i]).data("productId");
        var qtyInput = $(newRows[i]).find(".assignedStockQuantity").first();
        var newQty =  qtyInput.val();
        if(Number(newQty) == NaN || Number(newQty) == 0 || newQty == ""){
            dataValid = false;
            qtyInput.addClass('is-invalid');
        }
        else
            qtyInput.removeClass('is-invalid');
        newStockAssignments.push({"productId": productId,"quantity": newQty});
    }


    requestArgs = {};
    requestArgs["jobId"] = $("#jobId").val();
    requestArgs["jobName"] = $("#jobName").val();
    requestArgs["newStockAssignments"] = newStockAssignments;
    requestArgs["changedStockAssignments"] = changedStockAssignments;
    requestArgs["deletedStockAssignments"] = assignedStockIdsToDelete;

    if(requestArgs["jobName"] == ""){
        dataValid = false;
        $("#jobName").addClass("is-invalid");
    }
    else
        $("#jobName").removeClass("is-invalid");

    if(dataValid == false){
        $("#saveJobFeedbackSpan").html("Please fill in the required fields");
        return;
    }

    if($("#jobId").val() == "-1")
        url = "{{ url_for('jobs.createJob') }}";
    else
        url = "{{ url_for('jobs.updateJob') }}";

    console.log(requestArgs);

    if(refreshCheckIntervalId != null)
        clearInterval(refreshCheckIntervalId);

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
        if(refreshCheckIntervalId != null)
            clearInterval(refreshCheckIntervalId);
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

function saveJobTemplate(){
    // this needs a list of newly assigned stock, a list of deleted assignments,
    // and a list of changed assignments, as well as the name and ID of the job.
    // validate inputs as we go
    var dataValid = true;

    var newStockAssignments = [];
    var newRows = $(".stockAssignmentRow");
    for(var i = 0; i < newRows.length; i++){
        var productId = $(newRows[i]).data("productId");
        var qtyInput = $(newRows[i]).find(".assignedStockQuantity").first();
        var newQty =  qtyInput.val();
        if(Number(newQty) == NaN || Number(newQty) == 0 || newQty == ""){
            dataValid = false;
            qtyInput.addClass('is-invalid');
        }
        else
            qtyInput.removeClass('is-invalid');
        newStockAssignments.push({"productId": productId,"quantity": newQty});
    }

    requestArgs = {};
    requestArgs["templateId"] = $("#templateId").val();
    requestArgs["templateName"] = $("#jobName").val();
    requestArgs["templateStockAssignments"] = newStockAssignments;

    if(requestArgs["jobName"] == ""){
        dataValid = false;
        $("#jobName").addClass("is-invalid");
    }
    else
        $("#jobName").removeClass("is-invalid");

    if(dataValid == false){
        $("#saveJobFeedbackSpan").html("Please fill in the required fields");
        return;
    }

    url = "{{ url_for('jobs.processJobTemplate') }}";

    $.ajax({
        url: url,
        type: "POST",
        data: JSON.stringify(requestArgs),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(responseData){
            $("#saveJobFeedbackSpan").html("template saved");
            $("#templateId").val(responseData.templateId);
            setTimeout(function(){$("#saveJobFeedbackSpan").empty();}, 5000);
        },
        error: function(jqXHR, textStatus, errorThrown){
            alert(jqXHR.responseText);
        }
    });
}

function setJobStockTableSizes(){
    // calculate the height of the required stock and stock used table containers and set
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
        $("#pickingListLink").outerHeight() +
        $("#commitButtonsContainer").outerHeight()
    );
    newHeightStyling = "height: " + assignedStockContainerHeight + "px;";
    $("#assignedStockTableContainer").prop("style", newHeightStyling);
}

function onOpenTemplatePanelButtonClicked(){
    $("#templatesGreyout").prop("hidden", false);
    $("#templatesPanel").prop("hidden", false);
    populateTemplateNameList();
}

function closeTemplatesPanel(){
    $("#templatesGreyout").prop("hidden", true);
    $("#templatesPanel").prop("hidden", true);
}

function populateTemplateNameList(){
    url = new URL(window.location.origin + "{{ url_for('jobs.getTemplateList') }}");
    url.searchParams.append("searchTerm", $("#templatesSearchBox").val());
    $.ajax({
        type: "GET",
        url: url,
        datatype: "json",
        success: function(templateNameList){
            $("#templateSelect").empty();
            for(var i = 0; i < templateNameList.length; i++){
                var nameOption = $("<option>");
                nameOption.val(templateNameList[i].id);
                nameOption.html(templateNameList[i].templateName);
                $("#templateSelect").append(nameOption);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function onApplyTemplateButtonClicked(){
    if($("#assignedStockTableBody").children().length > 0){
        if(!confirm("Clear current stock assigment?"))
            return;
    }
    setAssignedStockFromTemplate($("#templateSelect").val());
    $("#templatesGreyout").prop("hidden", true);
    $("#templatesPanel").prop("hidden", true);
}

function setAssignedStockFromTemplate(templateId){
    $("#assignedStockTableBody").empty();
    url = new URL(window.location.origin + "{{ url_for('jobs.getTemplateStockAssignment') }}");
    url.searchParams.append("templateId", templateId);
    $.ajax({
        type: "GET",
        url: url,
        datatype: "json",
        success: function(templateAssignmentsList){
            for(var i = 0; i < templateAssignmentsList.length; i++){
                addStockToAssignedList(
                    templateAssignmentsList[i].productName,
                    templateAssignmentsList[i].productId,
                    templateAssignmentsList[i].quantity,
                    templateAssignmentsList[i].quantityUnit
                );
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            alert(jqXHR.responseText);
        }
    });
}

function deleteSelectedTemplate(){
    url = new URL(window.location.origin + "{{ url_for('jobs.deleteTemplate') }}");
    url.searchParams.append("templateId", $("#templateSelect").val());
    $.ajax({
        url: url,
        type: "POST",
        success: function(){
            populateTemplateNameList();
        }
    });
}