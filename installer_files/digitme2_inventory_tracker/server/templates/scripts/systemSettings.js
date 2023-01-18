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
            $("#dbBackupOnMonday").prop("checked", settings.dbBackupOnMonday);
            $("#dbBackupOnTuesday").prop("checked", settings.dbBackupOnTuesday);
            $("#dbBackupOnWednesday").prop("checked", settings.dbBackupOnWednesday);
            $("#dbBackupOnThursday").prop("checked", settings.dbBackupOnThursday);
            $("#dbBackupOnFriday").prop("checked", settings.dbBackupOnFriday);
            $("#dbBackupOnSaturday").prop("checked", settings.dbBackupOnSaturday);
            $("#dbBackupOnSunday").prop("checked", settings.dbBackupOnSunday);
            $("#dbNumberOfBackups").val(settings.dbNumberOfBackups);
            $("#stockLevelReorderCheckAtTime").val(settings.stockLevelReorderCheckAtTime);
            $("#stockCheckOnMonday").prop("checked", settings.stockCheckOnMonday);
            $("#stockCheckOnTuesday").prop("checked", settings.stockCheckOnTuesday);
            $("#stockCheckOnWednesday").prop("checked", settings.stockCheckOnWednesday);
            $("#stockCheckOnThursday").prop("checked", settings.stockCheckOnThursday);
            $("#stockCheckOnFriday").prop("checked", settings.stockCheckOnFriday);
            $("#stockCheckOnSaturday").prop("checked", settings.stockCheckOnSaturday);
            $("#stockCheckOnSunday").prop("checked", settings.stockCheckOnSunday);
            $("#stockCheckAvailableLevels").prop("checked", settings.stockCheckAvailableLevels);
            $("#sendEmails").prop("checked", settings.sendEmails);
            $("#emailSmtpServerName").val(settings.emailSmtpServerName);
            $("#emailSmtpServerPort").val(settings.emailSmtpServerPort);
            $("#emailAccountName").val(settings.emailAccountName);
            $("#emailAccountPassword").val(settings.emailAccountPassword);
            $("#emailSecurityMethod").children("[value=" + settings.emailSecurityMethod + "]").prop("selected",true);
        }
    });
}

function saveSettings(){
    var newSettings = {};
    newSettings.id = $("#settingsId").val();
    newSettings.dbMakeBackups = $("#dbMakeBackups").is(":checked");
    newSettings.dbBackupAtTime = $("#dbBackupAtTime").val();
    newSettings.dbBackupOnMonday = $("#dbBackupOnMonday").is(":checked");
    newSettings.dbBackupOnTuesday = $("#dbBackupOnTuesday").is(":checked");
    newSettings.dbBackupOnWednesday = $("#dbBackupOnWednesday").is(":checked");
    newSettings.dbBackupOnThursday = $("#dbBackupOnThursday").is(":checked");
    newSettings.dbBackupOnFriday = $("#dbBackupOnFriday").is(":checked");
    newSettings.dbBackupOnSaturday = $("#dbBackupOnSaturday").is(":checked");
    newSettings.dbBackupOnSunday = $("#dbBackupOnSunday").is(":checked");
    newSettings.dbNumberOfBackups = $("#dbNumberOfBackups").val();
    newSettings.stockLevelReorderCheckAtTime = $("#stockLevelReorderCheckAtTime").val()
    newSettings.stockCheckOnMonday = $("#stockCheckOnMonday").is(":checked");
    newSettings.stockCheckOnTuesday = $("#stockCheckOnTuesday").is(":checked");
    newSettings.stockCheckOnWednesday = $("#stockCheckOnWednesday").is(":checked");
    newSettings.stockCheckOnThursday = $("#stockCheckOnThursday").is(":checked");
    newSettings.stockCheckOnFriday = $("#stockCheckOnFriday").is(":checked");
    newSettings.stockCheckOnSaturday = $("#stockCheckOnSaturday").is(":checked");
    newSettings.stockCheckOnSunday = $("#stockCheckOnSunday").is(":checked");
    newSettings.stockCheckAvailableLevels = $("#stockCheckAvailableLevels").is(":checked");
    newSettings.sendEmails = $("#sendEmails").is(":checked");
    newSettings.emailSmtpServerName = $("#emailSmtpServerName").val();
    newSettings.emailSmtpServerPort = $("#emailSmtpServerPort").val();
    newSettings.emailAccountName = $("#emailAccountName").val();
    newSettings.emailAccountPassword = $("#emailAccountPassword").val();
    newSettings.emailSecurityMethod = $("#emailSecurityMethod").val();

    $.ajax({
        url: "{{ url_for('systemSettings.saveSystemSettings')}}",
        type: "POST",
        data: JSON.stringify(newSettings),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(){
            console.log("settings updated");
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function runStockCheck(){
    $("#runStockCheckBtn").prop("disabled", true).val("Stock Check In Progress");
    $.ajax({
        url: "{{ url_for('productManagement.runStockCheck')}}",
        type: "POST",
        success: function(){
            setTimeout(function(){$("#runStockCheckBtn").val("Stock Check Completed");}, 3000);
            setTimeout(function(){$("#runStockCheckBtn").prop("disabled", false).val("Run Stock Check Now");}, 6000);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#runStockCheckBtn").val("Error");
            setTimeout(function(){$("#runStockCheckBtn").prop("disabled", false).val("Run Stock Check Now");}, 6000);
        }
    });
}

function initiateBackup(){
    $("#initiateBackupBtn").prop("disabled", true).val("Backup In Progress");
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
    if(backupName == undefined){
        alert("Select a backup to restore from");
        return;
    }
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

function sendTestEmail(){
    $.ajax({
        url: "{{ url_for('systemSettings.sendTestEmail') }}",
        type: "POST",
        data: JSON.stringify({"testEmailRecipientAddress": $("#testEmailRecipientAddress").val()}),
        contentType: "application/json",
        datatype: "JSON",
        success: function(){
            $("#sendTestEmailButton").val("Test Email Sent").prop("disabled", true);
            setTimeout(function(){ $("#sendTestEmailButton").val("Send Test Email").prop("disabled", false); }, 5000)
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}