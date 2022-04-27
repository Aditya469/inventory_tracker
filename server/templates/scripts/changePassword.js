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
        url: {{ url_for("users.changePassword") }},
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function(responseData){
            console.log(responseData);
            $("#feedback").html(responseData);
        },
        error: function(e){
            console.log(e);
            $("#feedback").html(e.responseText);
        }
    });
}