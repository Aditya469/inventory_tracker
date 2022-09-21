$(document).ready(function(){
    loadSettings();
});

function loadSettings(){
    $.ajax({
        url: "{{ url_for('systemSettings.getSystemSettings') }}",
        type: "GET",
        datatype:"JSON",
        success: function(settings){
            console.log(settings);
            $("#dbMakeBackups").prop("checked", settings.dbMakeBackups);
            $("#dbBackupAtTime").val(settings.dbAutoBackupTime);
            $("#dbNumberOfBackups").val(settings.dbNumberOfBackups);
        }
    });
}

function saveSettings(){
    var newSettings = {};
    newSettings.dbMakeBackups = $("#dbMakeBackups").is(":checked");
    newSettings.dbBackupAtTime = $("#dbBackupAtTime").val();
    newSettings.dbNumberOfBackups = $("#dbNumberOfBackups").val();

    $.ajax({
        url: "{{ url_for('systemSettings.saveSystemSettings')}}",
        type: "POST",
        data: JSON.stringify(newSettings),
        processData: false,
        contentType: "application/json",
        cache: false,
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function initiateBackup(){
    $("#initiateBackupBtn").prop("enabled", false).val("");
    $.ajax({
        url: "{{ url_for('backup.startBackupCommand')}}",
        type: "POST",
        success: function(){
            $("#initiateBackupBtn").val("Backup In Progress...");
            setTimeout(onBackupButtonUpdateTimer, 1000);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#initiateBackupBtn").prop("enabled", false).val("An Error Occured");
            setTimeout(function(){$("#initiateBackupBtn").prop("enabled", true).val("Initiate Backup Now");}, 5000);
        }
    });
}

function onBackupButtonUpdateTimer(){
    $.ajax({
        url: "{{ url_for('backup.getBackupStatus') }}",
        type: "GET",
        success:function(statusJson){
            // if not finished, update status, otherwise reset button
            if(!statusJson.isDone){
                $("#initiateBackupBtn").val(statusJson.status)
                setTimeout(onBackupButtonUpdateTimer, 1000);
            }
            else
            {
                $("#initiateBackupBtn").val("Backup Successful");
                setTimeout(function(){$("#initiateBackupBtn").prop("enabled", true).val("Initiate Backup Now");}, 5000);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#initiateBackupBtn").prop("enabled", false).val("An Error Occured");
            setTimeout(function(){$("#initiateBackupBtn").prop("enabled", true).val("Initiate Backup Now");}, 5000);
        }
    });
}

function showRestoreBackupPanel(){
}
