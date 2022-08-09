package com.admt.inventoryTracker;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Switch;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

public class settings_page extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings_page);

        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        EditText tbServerURL = (EditText) findViewById(R.id.tbServerURL);
        EditText tbSettingsPassword = (EditText) findViewById(R.id.tbSettingsPassword);
        Spinner spCameraSelect = (Spinner) findViewById(R.id.spCameraSelect);
        Spinner spDetectionDelay = (Spinner) findViewById(R.id.spDetectionDelay);
        Switch swUseFullscreenConfirmations = (Switch) findViewById(R.id.swUseFullscreenConfirmations);

        SharedPreferences prefs = getSharedPreferences(
                getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        String serverAddress = prefs.getString(
                getString(R.string.prefs_server_ip_address), "");
        String settingsPassword = prefs.getString(
                getString(R.string.prefs_settings_password), "1234");
        boolean useFrontCamera = prefs.getBoolean(
                getString(R.string.prefs_use_front_camera), true);
        long detectionDelay = prefs.getLong(getString(R.string.prefs_camera_detection_delay), 1000);
        boolean useFullscreenConfirmations = prefs.getBoolean(getString(R.string.prefs_use_fullscreen_confirmations), true);

        tbServerURL.setText(serverAddress);
        tbSettingsPassword.setText(settingsPassword);
        if (useFrontCamera)
            spCameraSelect.setSelection(0);
        else
            spCameraSelect.setSelection(1);

        // note times are in milliseconds
        if (detectionDelay == 0)
            spDetectionDelay.setSelection(0);
        else if (detectionDelay == 500)
            spDetectionDelay.setSelection(1);
        else if (detectionDelay == 1000)
            spDetectionDelay.setSelection(2);
        else if (detectionDelay == 2000)
            spDetectionDelay.setSelection(3);
        else if (detectionDelay == 3000)
            spDetectionDelay.setSelection(4);

        swUseFullscreenConfirmations.setChecked(useFullscreenConfirmations);
    }

    public void onBtnOkClicked(View v) {
        SharedPreferences prefs = getSharedPreferences(getString(R.string.prefs_file_key),
                Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        EditText tbServerURL = (EditText) findViewById(R.id.tbServerURL);
        EditText tbSettingsPassword = (EditText) findViewById(R.id.tbSettingsPassword);
        Spinner spCameraSelect = (Spinner) findViewById(R.id.spCameraSelect);
        Spinner spDetectionDelay = (Spinner) findViewById(R.id.spDetectionDelay);
        Switch swUseFullscreenConfirmations = (Switch) findViewById(R.id.swUseFullscreenConfirmations);

        int camOptionSelection = spCameraSelect.getSelectedItemPosition();
        boolean useFrontCamera = true;
        if (camOptionSelection == 1) {
            useFrontCamera = false;
        }

        String serverAddress = tbServerURL.getText().toString();
        String password = tbSettingsPassword.getText().toString();

        editor.putString(getString(R.string.prefs_server_ip_address), serverAddress);
        editor.putString(getString(R.string.prefs_settings_password), password);
        editor.putBoolean(getString(R.string.prefs_use_front_camera), useFrontCamera);

        if (spDetectionDelay.getSelectedItemPosition() == 0)
            editor.putLong(getString(R.string.prefs_camera_detection_delay), 0);
        else if (spDetectionDelay.getSelectedItemPosition() == 1)
            editor.putLong(getString(R.string.prefs_camera_detection_delay), 500);
        else if (spDetectionDelay.getSelectedItemPosition() == 2)
            editor.putLong(getString(R.string.prefs_camera_detection_delay), 1000);
        else if (spDetectionDelay.getSelectedItemPosition() == 3)
            editor.putLong(getString(R.string.prefs_camera_detection_delay), 2000);
        else if (spDetectionDelay.getSelectedItemPosition() == 4)
            editor.putLong(getString(R.string.prefs_camera_detection_delay), 3000);

        editor.putBoolean("useFullscreenConfirmations", swUseFullscreenConfirmations.isChecked());

        editor.commit();

        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(intent);
    }
}
