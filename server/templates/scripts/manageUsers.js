$(document).ready(function(){
    $.ajax({
        url: {{ url_for('users.getUsers') }},
        type: "GET",
        success:function(responseData){
            console.log(responseData);
            updateUsersTable(responseData);
        }
    });
});

function updateUsersTable(responseData){
    var table = $("<table>");
    var header = $("<thead>");
    var headerRow = $("<tr class='header'>");
    headerRow.append($("<th>Username</th>"));
    headerRow.append($("<th>Is User Admin</th>"));
    headerRow.append($("<th>Reset Password</th>"));
    headerRow.append($("<th>Delete User</th>"));
    table.append(headerRow);

    var i;
    for(i = 0; i < responseData.length; i++){
        var row = $("<tr>");
        row.append($("<td>").html(responseData[i]['username']));

        if(responseData[i]['isAdmin'])
            row.append($("<td>Yes</td>"));
        else
            row.append($("<td>No</td>"));

        var resetPasswordBtn = $("<input>");
        resetPasswordBtn.attr("type","button");
        resetPasswordBtn.attr("value","Reset Password");
        resetPasswordBtn.attr("onclick","resetPassword(\"" + responseData[i]['username'] + "\")");
        row.append($("<td>").append(resetPasswordBtn));

        var deleteUserBtn = $("<input>");
        deleteUserBtn.attr("type","button");
        deleteUserBtn.attr("value","Delete User");
        deleteUserBtn.attr("onclick","deleteUser(\"" + responseData[i]['username'] + "\")");
        row.append($("<td>").append(deleteUserBtn));

        if(responseData[i]['username'] == "admin"){
            deleteUserBtn.prop("disabled","true");
        }

        table.append(row);
    }

    $("#userTableContainer").empty().append(table);
}

function addNewUser(){
    var formData = new FormData();
    formData.append("newUsername", $("#newUsername").val());
    formData.append("newPassword", $("#newPassword").val());
    if($("#isAdmin").is(":checked"))
        formData.append("isAdmin", "1");
    else
        formData.append("isAdmin", "0");

    $.ajax({
        url: {{ url_for("users.addUser") }},
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            updateUsersTable(responseData);
            $("#newUsername").val("");
            $("#newPassword").val("");
            $("#newUserFeedback").html("New User " + $("#newUsername").val() + " added");
        },
        error: function(e){
            console.log(e);
            $("#newUserFeedback").html(e.responseText);
        }
    });
}

function resetPassword(username){
    var formData = new FormData();
    formData.append("username", username);

    $.ajax({
        url: {{ url_for("users.resetPassword") }},
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            $("#currentUserFeedback").html("Password reset complete");
        },
        error: function(e){
            console.log(e);
            $("#currentUserFeedback").html(e.responseText);
        }
    });
}

function deleteUser(username){
    var formData = new FormData();
    formData.append("username", username);

    $.ajax({
        url: {{ url_for("users.deleteUser") }},
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            updateUsersTable(responseData);
            $("#currentUserFeedback").html("User deleted");
        },
        error: function(e){
            console.log(e);
            $("#currentUserFeedback").html(e.responseText);
        }
    });
}
