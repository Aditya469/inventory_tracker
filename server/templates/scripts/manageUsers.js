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
});

function updateUsersTable(){
    $.ajax({
        url: "{{ url_for('users.getUsers') }}",
        type: "GET",
        success:function(responseData){
            console.log(responseData);

            var table = $("<table class='table m-2'>");
            var header = $("<thead>");
            var headerRow = $("<tr>");
            headerRow.append($("<th>Username</th>"));
            headerRow.append($("<th>Is User Admin</th>"));
            headerRow.append($("<th>Reset Password</th>"));
            headerRow.append($("<th>Delete User</th>"));
            header.append(headerRow);
            table.append(header);

            var body = $("<tbody>");
            table.append(body);
            var i;
            for(i = 0; i < responseData.length; i++){
                var row = $("<tr>");
                row.append($("<td>").html(responseData[i]['username']));

                if(responseData[i]['isAdmin'])
                    row.append($("<td>Yes</td>"));
                else
                    row.append($("<td>No</td>"));

                var resetPasswordBtn = $("<input class='button'>");
                resetPasswordBtn.attr("type","button");
                resetPasswordBtn.attr("value","Reset Password");
                resetPasswordBtn.attr("onclick","resetPassword(\"" + responseData[i]['username'] + "\")");
                row.append($("<td>").append(resetPasswordBtn));

                var deleteUserBtn = $("<input class='button'>");
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
    formData.append("newUsername", $("#newUsername").val());
    formData.append("newPassword", $("#newPassword").val());
    formData.append("isAdmin", $("#isAdmin").is(":checked"));

    $.ajax({
        url: "{{ url_for("users.addUser") }}",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            updateUsersTable();
            $("#newUsername").val("");
            $("#newPassword").val("");
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
        url: "{{ url_for("users.resetPassword") }}",
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
    var formData = new FormData();
    formData.append("username", username);

    $.ajax({
        url: "{{ url_for("users.deleteUser") }}",
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
