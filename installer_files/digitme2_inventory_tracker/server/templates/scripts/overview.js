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
    updateJobsTable();
    updateStockTables();
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
    var url = new URL(window.location.origin + "{{ url_for('jobs.getJobsCsvFile') }}");
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
            var table = generateOverviewStockTable(responseData, onTotalStockRowClicked);
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
            var table = generateOverviewStockTable(responseData, onTotalStockRowClicked);
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
            var table = generateOverviewStockTable(responseData, onNearExpiryRowClicked);
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
            var table = generateOverviewStockTable(responseData, onExpiredRowClicked);
            table.attr("id", "expiredStockTable");
            $("#expiredStockTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });

    var url = new URL(window.location.origin + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in totalStockParams)
        url.searchParams.append(key, totalStockParams[key]);
    $("#totalStockCsvDownloadLink").prop("href", url);

    var url = new URL(window.location.origin + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in availableStockParams)
        url.searchParams.append(key, availableStockParams[key]);
    $("#availableStockCsvDownloadLink").prop("href", url);

    var url = new URL(window.location.origin + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in expiringStockParams)
        url.searchParams.append(key, expiringStockParams[key]);
    $("#oldStockCsvDownloadLink").prop("href", url);

    var url = new URL(window.location.origin + "{{ url_for('stockManagement.getStockOverviewCsvFile') }}");
    for (key in expiredStockParams)
        url.searchParams.append(key, expiredStockParams[key]);
    $("#expiredStockCsvDownloadLink").prop("href", url);
}

function onTotalStockRowClicked(){
    searchUrl = new URL(window.location.origin + "{{ url_for("stockManagement.getStockPage")}}");
    searchUrl.searchParams.append("productName",$(this).data("productName"));
    window.location.href = searchUrl.href;
}

function onNearExpiryRowClicked(){
    searchUrl = new URL(window.location.origin + "{{ url_for("stockManagement.getStockPage")}}");
    searchUrl.searchParams.append("productName",$(this).data("productName"));
    searchUrl.searchParams.append("expiryDayCount", $("#stockDaysNearExpiry").val());
    window.location.href = searchUrl.href;
}

function onExpiredRowClicked(){
    searchUrl = new URL(window.location.origin + "{{ url_for("stockManagement.getStockPage")}}");
    searchUrl.searchParams.append("productName",$(this).data("productName"));
    searchUrl.searchParams.append("showExpiredOnly", "true");
    window.location.href = searchUrl.href;
}

function generateOverviewStockTable(stockData, onClickFunction)
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
        tr.on("click", onClickFunction);

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

