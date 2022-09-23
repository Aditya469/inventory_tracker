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
            $("#settingsId").val(settings.id);
            $("#dbMakeBackups").prop("checked", settings.dbMakeBackups);
            $("#dbBackupAtTime").val(settings.dbBackupAtTime);
            $("#dbNumberOfBackups").val(settings.dbNumberOfBackups);
            $("#stockLevelReorderCheckAtTime").val(settings.stockLevelReorderCheckAtTime);
        }
    });
}

function saveSettings(){
    var newSettings = {};
    newSettings.id = $("#settingsId").val();
    newSettings.dbMakeBackups = $("#dbMakeBackups").is(":checked");
    newSettings.dbBackupAtTime = $("#dbBackupAtTime").val();
    newSettings.dbNumberOfBackups = $("#dbNumberOfBackups").val();
    newSettings.stockLevelReorderCheckAtTime = $("#stockLevelReorderCheckAtTime").val()

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
    $("#initiateBackupBtn").prop("enabled", false).val("Backup In Progress");
    $.ajax({
        url: "{{ url_for('backup.startBackupCommand')}}",
        type: "POST",
        success: function(){
            // the delays are to allow the button to be read by the user before it changes
            setTimeout(function(){$("#initiateBackupBtn").val("Backup Successful");}, 3000);
            setTimeout(function(){$("#initiateBackupBtn").prop("disabled", false).val("Initiate Backup Now");}, 6000);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#initiateBackupBtn").val(jqXHR.responseText);
            setTimeout(function(){$("#initiateBackupBtn").prop("disabled", false).val("Initiate Backup Now");}, 5000);
        }
    });
}

function showRestoreBackupPanel(){
    $("#greyout").prop("hidden", false);
    $("#restoreDbFromBackupPanel").prop("hidden", false);
    $("#dbBackupNamesList").empty();

    $.ajax({
        url: "{{ url_for('backup.getAvailableBackupNames') }}",
        type: "GET",
        datatype: "JSON",
        success: function(namesList){
            for(var i = 0; i < namesList.length; i++){
                var radioButton = $("<input type='radio' name='backupNameOption' class='form-check-input'>");
                radioButton.prop("value", namesList[i]);
                var label = $("<label class='form-check-label'>").html(namesList[i]);
                var containingDiv = $("<div class='form-check'>");
                containingDiv.append(radioButton);
                containingDiv.append(label);
                $("#dbBackupNamesList").append(containingDiv);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#initiateBackupBtn").val(jqXHR.responseText);
            setTimeout(function(){$("#initiateBackupBtn").prop("disabled", false).val("Initiate Backup Now");}, 5000);
        }
    });
}

function closePanels(){
    $("#greyout").prop("hidden", true);
    $("#restoreDbFromBackupPanel").prop("hidden", true);
}

function restoreBackup(){
    var backupName = $("input[name='backupNameOption']:checked").val();
    if(confirm("Restore the Database from " + backupName + "?")){
        $.ajax({
            url: "{{ url_for('backup.restoreDbFromBackup') }}",
            type: "POST",
            data: JSON.stringify({"backupFileName": backupName}),
            contentType: "application/json",
            datatype: "JSON",
            success: function(){
                alert("Database restored");
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
                alert("Database Restoration Failed");
            }
        });
    }
}