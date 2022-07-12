$(document).ready(function(){
    updateJobsTable();
    updateStockTables();
});

function updateJobsTable(){
    // fetch jobs table data and populate
    var searchTerm = $("#jobSearchBar").val();
    $.ajax({
        url: "{{ url_for('jobs.getJobs') }}",
        type: "GET",
        data: {
            "searchTerm": searchTerm
        },
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
            for(i=0; i<responseData.length; i++){
                tr = $("<tr>");
                tr.append($("<td>" + responseData[i].jobName + "</td>"));
                tr.append($("<td>" + responseData[i].addedTimestamp + "</td>"));
                tr.append($("<td>" + responseData[i].totalCost + "</td>"));
                tbody.append(tr);
            }
            table.append(tbody);

            $("#jobsTableContainer").empty().append(table);
        }
    });
}

function updateStockTables(){
    // note that this updates all 4 stock tables at the same time
    var searchTerm = $("#stockSearchBar").val();

    // make a bunch of ajax requests and bring all the tables up to date
    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: { "searchTerm": searchTerm, "overviewType": "totalStock" },
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id","stockTotalTable");
            $("#totalStockTableContainer").empty().append(table);
        }
    });

    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: { "searchTerm": searchTerm, "overviewType": "availableStock" },
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "availableStockTable");
            $("#availableStockTableContainer").empty().append(table);
        }
    });

    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: { "searchTerm": searchTerm, "overviewType": "nearExpiry", "dayCountLimit": $("#stockDaysNearExpiry").val() },
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "oldStockTable");
            $("#oldStockTableContainer").empty().append(table);
        }
    });

    $.ajax({
        url: "{{ url_for('stockManagement.getStockOverview') }}",
        type: "GET",
        data: { "searchTerm": searchTerm, "overviewType": "expired" },
        success:function(responseData){
            console.log(responseData);
            var table = generateOverviewStockTable(responseData);
            table.attr("id", "expiredStockTable");
            $("#expiredStockTableContainer").empty().append(table);
        }
    });
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
        tr.append($("<td>" + stockData[i].productName + "</td>"));
        tr.append($("<td>" + stockData[i].stockAmount + " " + stockData[i].quantityUnit + "</td>"));
        if(stockData[i].isBulk)
            tr.append($("<td>Yes</td>"));
        else
            tr.append($("<td>No</td>"));
        tr.append($("<td>" + stockData[i].descriptor1 + "</td>"));
        tr.append($("<td>" + stockData[i].descriptor2 + "</td>"));
        tr.append($("<td>" + stockData[i].descriptor3 + "</td>"));
        tbody.append(tr);
    }
    table.append(tbody);

    return table;
}