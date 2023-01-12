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
    $(".changePasswordInput").keypress(function(event){
        // on enter key pressed
        if(event.which == 13)
            changePassword();
    });
});

function changePassword(){
    if($("#currentPassword").val() == ""){
        $("#feedback").html("Enter current password");
        return;
    }

    if($("#newPassword").val() == ""){
        $("#feedback").html("Enter new password");
        return;
    }

    if($("#confirmNewPassword").val() == ""){
        $("#feedback").html("Confirm new password");
        return;
    }

    if($("#newPassword").val() != $("#confirmNewPassword").val()){
        $("#feedback").html("New passwords do not match");
        return;
    }

    var formData = new FormData();
    formData.append("currentPassword", $("#currentPassword").val());
    formData.append("newPassword", $("#newPassword").val());

    $.ajax({
        url: "{{ url_for("users.changePassword") }}",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            $("#feedback").html(responseData);
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log(jqXHR.responseText);
            $("#feedback").html(jqXHR.responseText);
        }
    });
}