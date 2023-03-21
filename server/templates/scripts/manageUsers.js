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
    updateUsersTable();
    $(".newUserInput").keypress(function(event){
        // on enter key pressed
        if(event.which == 13)
            addNewUser();
    });
});

function updateUsersTable(){
    $.ajax({
        url: "{{ url_for('users.getUsers') }}",
        type: "GET",
        success:function(responseData){
            console.log(responseData);

            var table = $("<table class='table table-striped'>");
            var header = $("<thead>");
            var headerRow = $("<tr>");
            headerRow.append($("<th>Username</th>"));
            headerRow.append($("<th>Access Level</th>"));
            headerRow.append($("<th>ID Card</th>"));
            headerRow.append($("<th>Stock Alerts</th>"));
            headerRow.append($("<th>Database Alerts</th>"));
            headerRow.append($("<th>Email Address</th>"));
            headerRow.append($("<th>Reset Password</th>"));
            headerRow.append($("<th>Delete User</th>"));
            header.append(headerRow);
            table.append(header);

            var body = $("<tbody>");
            table.append(body);
            var i;
            for(i = 0; i < responseData.length; i++){
                var row = $("<tr>");
                row.data("username", responseData[i]['username']);
                row.append($("<td>").html(responseData[i]['username']));


                var accessLevelSel = $("<select class='accessLevelSelector form-select'>");
                accessLevelSel.on("change", function(){onUserConfigChanged(this);})
                if(responseData[i]['accessLevel'] == "0")
                    accessLevelSel.append($("<option value='0' selected>Read-Only</option>"));
                else
                    accessLevelSel.append($("<option value='0'>Read-Only</option>"));

                if(responseData[i]['accessLevel'] == "1")
                    accessLevelSel.append($("<option value='1' selected>Create/Edit/Delete</option>"));
                else
                    accessLevelSel.append($("<option value='1'>Create</option>"));

                if(responseData[i]['accessLevel'] == "2")
                    accessLevelSel.append($("<option value='2' selected>Admin</option>"));
                else
                    accessLevelSel.append($("<option value='2'>Admin</option>"));

                if(responseData[i].username == "admin") // special case
                    accessLevelSel.prop("disabled", true);
                row.append($("<td>").append(accessLevelSel));


                if(responseData[i].username != "admin") // special case
                {
                    var idCardLink = $("<a>Download ID card</>")
                    idCardLink.prop("href", "{{ url_for('users.getUserIdCard', username='')}}/" + responseData[i].username);
                    row.append($("<th>").append(idCardLink));
                }
                else
                    row.append($("<th>"));

                var receiveStockNotificationsCheckbox = $("<input type='checkbox' class='receiveStockNotificationsCheckbox form-check-input'>");
                receiveStockNotificationsCheckbox.on("change", function(){onUserConfigChanged(this);});
                if(responseData[i]['receiveStockNotifications'])
                    receiveStockNotificationsCheckbox.prop("checked", true);
                else
                    receiveStockNotificationsCheckbox.prop("checked", false);

                row.append($("<td class='text-center'>").append(receiveStockNotificationsCheckbox))

                var receiveDbStatusNotificationsCheckbox = $("<input type='checkbox' class='receiveDbStatusNotificationsCheckbox form-check-input'>");
                receiveDbStatusNotificationsCheckbox.on("change", function(){onUserConfigChanged(this);});
                if(responseData[i]['receiveDbStatusNotifications'])
                    receiveDbStatusNotificationsCheckbox.prop("checked", true);
                else
                    receiveDbStatusNotificationsCheckbox.prop("checked", false);

                row.append($("<td class='text-center'>").append(receiveDbStatusNotificationsCheckbox))

                var emailAddressInput = $("<input type='text' class='emailAddress form-control'>");
                emailAddressInput.on("change", function(){onUserConfigChanged(this);});
                if(responseData[i]['emailAddress'] != null)
                    emailAddressInput.val(responseData[i]['emailAddress']);
                else
                    emailAddressInput.val("");
                row.append($("<td>").append(emailAddressInput));

                var resetPasswordBtn = $("<input class='button btn btn-secondary'>");
                resetPasswordBtn.attr("type","button");
                resetPasswordBtn.attr("value","Reset Password");
                resetPasswordBtn.attr("onclick","resetPassword(\"" + responseData[i]['username'] + "\")");
                row.append($("<td>").append(resetPasswordBtn));

                var deleteUserBtn = $("<input class='button btn btn-danger'>");
                deleteUserBtn.attr("type","button");
                deleteUserBtn.attr("value","Delete User");
                deleteUserBtn.attr("onclick","deleteUser(\"" + responseData[i]['username'] + "\")");
                row.append($("<td>").append(deleteUserBtn));

                if(responseData[i]['username'] == "admin"){
                    deleteUserBtn.prop("disabled","true");
                }

                body.append(row);
            }

            $("#userTableContainer").empty().append(table);
        },
        error:function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
        }
    });
}

function addNewUser(){
    var formData = new FormData();
    var valid = true;
    $("#newUsername").removeClass("is-invalid");
    $("#newPassword").removeClass("is-invalid");
    $("#emailAddress").removeClass("is-invalid");

    var newUsername = $("#newUsername").val();
    if(newUsername == ""){
        $("#newUsername").addClass("is-invalid");
        valid = false;
    }

    var newPassword = $("#newPassword").val();
    if(newPassword == ""){
        $("#newPassword").addClass("is-invalid");
        valid = false;
    }

    var receiveStockNotifications = $("#receiveStockNotifications").is(":checked");
    var receiveDbStatusNotifications = $("#receiveDbStatusNotifications").is(":checked");
    var emailAddress = $("#emailAddress").val();
    if(emailAddress == "" && (receiveStockNotifications || receiveDbStatusNotifications)){
        $("#emailAddress").addClass("is-invalid");
        valid = false;
    }

    if(!valid){
        $("#newUserFeedback").html("Please fill all required fields");
        return;
    }

    formData.append("newUsername", newUsername);
    formData.append("newPassword", newPassword);
    formData.append("accessLevel", $("#accessLevel").val());
    formData.append("emailAddress", emailAddress);
    formData.append("receiveStockNotifications", receiveStockNotifications);
    formData.append("receiveDbStatusNotifications", receiveDbStatusNotifications);

    var newUserId = $("#newUserId").val();
    if(newUserId != "")
        formData.append("newUserId", newUserId);

    $.ajax({
        url: "{{ url_for('users.addUser') }}",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            updateUsersTable();
            $("#newUsername").val("");
            $("#newUserId").val("");
            $("#newPassword").val("");
            $("#accessLevel").val("0");
            $("#emailAddress").val("");
            $("#receiveStockNotifications").prop("checked", false);
            $("#receiveDbStatusNotifications").prop("checked", false);
            $("#newUserFeedback").html("New User " + $("#newUsername").val() + " added");
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#newUserFeedback").html(jqXHR.responseText);
        }
    });
}

function resetPassword(username){
    var formData = new FormData();
    formData.append("username", username);

    $.ajax({
        url: "{{ url_for('users.resetPassword') }}",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            $("#currentUserFeedback").html("Password reset complete");
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#currentUserFeedback").html(jqXHR.responseText);
        }
    });
}

function deleteUser(username){
    if(confirm("Delete User " + username + "?")){
        var formData = new FormData();
        formData.append("username", username);

        $.ajax({
            url: "{{ url_for('users.deleteUser') }}",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            cache: false,
            success: function(responseData){
                console.log(responseData);
                updateUsersTable();
                $("#currentUserFeedback").html("User deleted");
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(jqXHR.responseText);
                $("#currentUserFeedback").html(jqXHR.responseText);
            }
        });
    }
}

function onUserConfigChanged(element){
    var row = $(element).closest("tr");

    var requestJson = {}
    requestJson["username"]  = row.data("username");
    requestJson["accessLevel"] = row.find(".accessLevelSelector").val();
    requestJson["emailAddress"] = row.find(".emailAddress").val();
    requestJson["receiveStockNotifications"] = row.find(".receiveStockNotificationsCheckbox").is(":checked");
    requestJson["receiveDbStatusNotifications"] = row.find(".receiveDbStatusNotificationsCheckbox").is(":checked");

    $.ajax({
        url: "{{ url_for('users.updateUser') }}",
        type: "POST",
        data: JSON.stringify(requestJson),
        processData: false,
        contentType: "application/json",
        cache: false,
        success: function(responseData){
            console.log(responseData);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#currentUserFeedback").html(jqXHR.responseText);
        }
    });
}