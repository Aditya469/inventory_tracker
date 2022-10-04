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

function openStickerSheetPanel(){
    populateStickerSheetPanel();
    $("#stickerSheetGreyout").prop("hidden", false);
    $("#stickerSheetPanel").prop("hidden", false);
    $(".form-control").removeClass("is-invalid");
}

function closeStickerSheetPanel(){
    $("#stickerSheetGreyout").prop("hidden", true);
    $("#stickerSheetPanel").prop("hidden", true);
}

function populateStickerSheetPanel(){
    $.ajax({
        url: "{{ url_for('systemSettings.getSystemSettings') }}",
        type: "GET",
        datatype:"JSON",
        success: function(settings){
            console.log(settings);
            $("#settingsId").val(settings.id);
            $("#stickerSheetPageHeight").val(settings.stickerSheetPageHeight_mm);
            $("#stickerSheetPageWidth").val(settings.stickerSheetPageWidth_mm);
            $("#stickerSheetStickersHeight").val(settings.stickerSheetStickersHeight_mm);
            $("#stickerSheetStickersWidth").val(settings.stickerSheetStickersWidth_mm);
            $("#stickerSheetRowCount").val(settings.stickerSheetRows);
            $("#stickerSheetColumnCount").val(settings.stickerSheetColumns);
        }
    });
}

function updateSettings(){
    var newSettings = {};
    newSettings.id = $("#settingsId").val();
    newSettings.stickerSheetPageHeight_mm = $("#stickerSheetPageHeight").val();
    newSettings.stickerSheetPageWidth_mm = $("#stickerSheetPageWidth").val();
    newSettings.stickerSheetStickersHeight_mm = $("#stickerSheetStickersHeight").val()
    newSettings.stickerSheetStickersWidth_mm = $("#stickerSheetStickersWidth").val();
    newSettings.stickerSheetRows = $("#stickerSheetRowCount").val();
    newSettings.stickerSheetColumns = $("#stickerSheetColumnCount").val()

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

function fetchStickerSheet(){
    $("#getStickerSheetButton").prop("disabled", true).val("Working...");
    setTimeout(function(){
            $("#getStickerSheetButton").prop("disabled", false).val("Get Sticker Sheet");
        }, 1500);

    url = new URL(window.location.origin + "{{ url_for('stockManagement.getItemStickerSheet') }}");
    window.location.href = url;
}