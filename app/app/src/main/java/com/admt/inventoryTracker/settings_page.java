package com.admt.inventoryTracker;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.CompoundButton;
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
        Switch swUseServerDiscovery = (Switch) findViewById(R.id.swUseServerDiscovery);
        Button btnFindServerNow = (Button) findViewById(R.id.btnFindServerNow);
        Spinner spCameraSelect = (Spinner) findViewById(R.id.spCameraSelect);
        Spinner spDetectionDelay = (Spinner) findViewById(R.id.spDetectionDelay);

        SharedPreferences prefs = getSharedPreferences(
                getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        tbServerURL.setText(prefs.getString(
                getString(R.string.prefs_server_base_address), "")
        );
        tbSettingsPassword.setText(prefs.getString(
                getString(R.string.prefs_settings_password), "1234"));

        if(prefs.getBoolean(getString(R.string.prefs_use_server_discovery), false)){
            swUseServerDiscovery.setChecked(true);
            btnFindServerNow.setEnabled(true);
        }
        else{
            swUseServerDiscovery.setChecked(false);
            btnFindServerNow.setEnabled(false);
        }
        swUseServerDiscovery.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                onUseServerDiscoveryChanged();
            }
        });
        btnFindServerNow.setOnClickListener(this::onFindServerBtnClicked);

        boolean useFrontCamera = prefs.getBoolean(
                getString(R.string.prefs_use_front_camera), true);
        if (useFrontCamera)
            spCameraSelect.setSelection(0);
        else
            spCameraSelect.setSelection(1);

        // note times are in milliseconds
        long detectionDelay = prefs.getLong(getString(R.string.prefs_camera_detection_delay), 1000);
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

    }

    public void onUseServerDiscoveryChanged(){
        Switch swUseServerDiscovery = (Switch) findViewById(R.id.swUseServerDiscovery);
        Button btnFindServerNow = (Button) findViewById(R.id.btnFindServerNow);
        Boolean state = swUseServerDiscovery.isChecked();
        btnFindServerNow.setEnabled(state);
    }

    public void onFindServerBtnClicked(View v){
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                EditText tbServerURL = (EditText) findViewById(R.id.tbServerURL);

                String TAG = "ServerDiscoverySettings";
                Log.d(TAG, "Begin server discovery");
                ServerDiscovery.DiscoveryResult discoveryResult =
                        ServerDiscovery.findServer(getApplicationContext());
                if (discoveryResult == null) {
                    Log.i(TAG, "Failed to find server");
                    return;
                }

                Log.i(TAG, "Found server. Base address is " + discoveryResult.serverBaseAddress);

                Handler mainHandler = new Handler(getApplicationContext().getMainLooper());
                Runnable runnable = new Runnable() {
                    @Override
                    public void run() {
                        tbServerURL.setText(discoveryResult.serverBaseAddress);
                    }
                };
                mainHandler.post(runnable);
            }
        };
        new Thread(runnable).start();
    }

    public void onBtnOkClicked(View v) {
        SharedPreferences prefs = getSharedPreferences(getString(R.string.prefs_file_key),
                Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        EditText tbServerURL = (EditText) findViewById(R.id.tbServerURL);
        EditText tbSettingsPassword = (EditText) findViewById(R.id.tbSettingsPassword);
        Switch swUseServerDiscovery = (Switch) findViewById(R.id.swUseServerDiscovery);
        Spinner spCameraSelect = (Spinner) findViewById(R.id.spCameraSelect);
        Spinner spDetectionDelay = (Spinner) findViewById(R.id.spDetectionDelay);

        int camOptionSelection = spCameraSelect.getSelectedItemPosition();
        boolean useFrontCamera = true;
        if (camOptionSelection == 1) {
            useFrontCamera = false;
        }

        String serverBaseAddress = tbServerURL.getText().toString();
        String password = tbSettingsPassword.getText().toString();

        editor.putString(getString(R.string.prefs_server_base_address), serverBaseAddress);
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

        editor.putBoolean(getString(R.string.prefs_use_server_discovery), swUseServerDiscovery.isChecked());

        editor.commit();

        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(intent);
    }
}
