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

package com.admt.inventoryTracker;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Button;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import java.util.Timer;
import java.util.TimerTask;

public class MainActivity extends AppCompatActivity
        implements cameraFragment.onBarcodeReadListener,
        numberPadFragment.OnNumpadInteractionListener,
        modeSelectorFragment.onModeSelectedListener,
        StockInteractionHandlingCallbacks {
    private cameraFragment mCameraFragment = null;
    private addNewStockFragment mAddNewStockFragment = null;
    private checkItemsFragment mCheckItemsFragment = null;
    private numberPadFragment mNumPadFragment = null;
    private modeSelectorFragment mModeSelectFragment = null;
    boolean torchOn = false;

    private static ProductDataManager mProductDataManager = null;
    private static LocationDataManager mLocationDataManger = null;
    private static ItemIdLookUpDataManager mItemIdLookUpDataManager = null;
    private static JobLookupDataManager mJobLookupDataManager = null;
    private static UserDataManager mUserDataManager = null;
    private static CheckingReasonDataManager mCheckingReasonDataManager = null;

    private static AddStockManager mAddStockManager = null;
    private static CheckStockInOutManager mCheckStockInOutManager = null;

    // note that the sendData task is started in onCreate so that it will run as long as the app
    // is active, even if it's in the background. The server discovery only runs when MainActivity
    // is actually running to prevent weirdness whilst in the settings page. Both tasks are created
    // in oncreate
    private Timer mPeriodicActionsTimer = null;
    private TimerTask mSendDataTimerTask = null;
    private TimerTask mDiscoverServerTimerTask = null;

    private String TAG = "MainActivity";

    private enum CurrentState {MODE_SELECT, ADD_STOCK, CHECK_STOCK};
    private CurrentState mCurrentState;

    @Override
    public void onResume() {
        super.onResume();

        mDiscoverServerTimerTask = new TimerTask() {
            @Override
            public void run() {
                String TAG = "ServerDiscoveryTimerTask";
                SharedPreferences prefs = getSharedPreferences(getString(R.string.prefs_file_key),
                        Context.MODE_PRIVATE);
                SharedPreferences.Editor editor = prefs.edit();

                if(prefs.getBoolean(getString(R.string.prefs_use_server_discovery), true))
                {
                    Log.d(TAG, "Begin server discovery");
                    ServerDiscovery.DiscoveryResult discoveryResult =
                            ServerDiscovery.findServer(getApplicationContext());
                    if(discoveryResult == null)
                    {
                        Log.i(TAG, "Failed to find server");
                        return;
                    }

                    Log.i(TAG, "Found server. Base address is " + discoveryResult.serverBaseAddress);

                    editor.putString(
                            getString(R.string.prefs_server_protocol),
                            discoveryResult.protocol);
                    editor.putString(
                            getString(R.string.prefs_server_url),
                            discoveryResult.ipAddress + ":" + discoveryResult.port);
                    editor.putString(
                            getString(R.string.prefs_server_base_address),
                            discoveryResult.serverBaseAddress);
                }
            }
        };

        mPeriodicActionsTimer.scheduleAtFixedRate(mDiscoverServerTimerTask, 1000, 15000);
        Log.d(TAG, "mDiscoverServerTimerTask scheduled for repeated execution");
    }

    @Override
    public void onPause() {
        super.onPause();

        if(mDiscoverServerTimerTask != null)
        {
            mDiscoverServerTimerTask.cancel();
            Log.d(TAG, "mDiscoverServerTimerTask cancelled");
        }
    }

    public void onBarcodeRead(String barcodeValue) {
        if (mCurrentState == CurrentState.ADD_STOCK)
            mAddNewStockFragment.addBarcode(barcodeValue);
        else if (mCurrentState == CurrentState.CHECK_STOCK)
            mCheckItemsFragment.addBarcode(barcodeValue);
    }

    public void onBarcodeEntered(String barcodeValue) {
        //mAddNewStockFragment.UpdateDisplayedbarcodeReading(barcodeValue);
        //onToggleNumPadRequest();
    }

    public void onBarcodeSeen() {
        if (mCameraFragment != null)
            mCameraFragment.flashScreen();
    }

    public void onToggleTorchRequest() {
        if (mCameraFragment != null)
            mCameraFragment.toggleTorch();
    }

    public void onToggleNumPadRequest() {
        if (mNumPadFragment == null) {
            mNumPadFragment = new numberPadFragment();
            getSupportFragmentManager().beginTransaction()
                    .replace(R.id.fragmentContainer1, mNumPadFragment)
                    .commit();

            mCameraFragment = null;
        } else {
            mCameraFragment = new cameraFragment();
            getSupportFragmentManager().beginTransaction()
                    .replace(R.id.fragmentContainer1, mCameraFragment)
                    .commit();

            mNumPadFragment = null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // don't add fragments if the app has resumed from suspension
        if (savedInstanceState != null) {
            return;
        }

        // create all of the data managers that fetch lists of data from the server. These are all
        // based on the same abstract class, and all work the same way.
        if (mProductDataManager == null)
            mProductDataManager = new ProductDataManager(getApplication());

        if (mLocationDataManger == null)
            mLocationDataManger = new LocationDataManager(getApplication());

        if (mAddStockManager == null)
            mAddStockManager = new AddStockManager(getApplication());

        if (mCheckStockInOutManager == null)
            mCheckStockInOutManager = new CheckStockInOutManager(getApplication());

        if (mItemIdLookUpDataManager == null)
            mItemIdLookUpDataManager = new ItemIdLookUpDataManager(getApplication());

        if (mJobLookupDataManager == null)
            mJobLookupDataManager = new JobLookupDataManager(getApplication());

        if (mUserDataManager == null)
            mUserDataManager = new UserDataManager(getApplication());

        if (mCheckingReasonDataManager == null)
            mCheckingReasonDataManager = new CheckingReasonDataManager(getApplication());

        mModeSelectFragment = new modeSelectorFragment();

        // As this app is expected to only have intermittent access to the network
        mPeriodicActionsTimer = new Timer(true);
        mSendDataTimerTask = new TimerTask() {
            @Override
            public void run() {
                SharedPreferences prefs = getSharedPreferences(getString(R.string.prefs_file_key),
                        Context.MODE_PRIVATE);

                if(prefs.getBoolean(getString(R.string.prefs_server_auto_sync), true))
                    syncWithServer();
            }
        };
        mPeriodicActionsTimer.scheduleAtFixedRate(mSendDataTimerTask, 1000, 10000);

        getSupportFragmentManager().beginTransaction()
                .add(R.id.fragmentContainer2, mModeSelectFragment).commit();
        mCurrentState = CurrentState.MODE_SELECT;

        // since this works by swapping fragments around, the back button is overridden to
        // allow the correct fragments to be swapped back into place
        OnBackPressedCallback callback = new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (mCurrentState == CurrentState.MODE_SELECT)
                    finish();
                else if (mCurrentState == CurrentState.CHECK_STOCK || mCurrentState == CurrentState.ADD_STOCK) {
                    switchToSelectModeState();
                }
            }
        };
        getOnBackPressedDispatcher().addCallback(this, callback);

    }

    private void syncWithServer() {
        if (Utilities.isWifiConnected(getApplicationContext())) {
            mProductDataManager.update();
            mLocationDataManger.update();
            mItemIdLookUpDataManager.update();
            mJobLookupDataManager.update();
            mUserDataManager.update();
            mCheckingReasonDataManager.update();

            if (mAddStockManager != null) {
                if (mAddStockManager.hasPending()) {
                    Utilities.showDebugMessage(getApplicationContext(), "Begin sending addStock requests");
                    mAddStockManager.SendAllRequests();
                    Utilities.showDebugMessage(getApplicationContext(), "addStock requests processed");
                }
            }

            if (mCheckStockInOutManager != null) {
                if (mCheckStockInOutManager.hasPending()) {
                    Utilities.showDebugMessage(getApplicationContext(), "Begin send checkStock requests");
                    mCheckStockInOutManager.SendAllRequests();
                    Utilities.showDebugMessage(getApplicationContext(), "checkStock requests processed");
                }
            }
        }
        else {
            Utilities.showDebugMessage(getApplicationContext(), "Wifi is not connected");
        }
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu)
    {
        getMenuInflater().inflate(R.menu.menu,menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item)
    {
        switch(item.getItemId())
        {
            // access the settings page (password protected)
            case R.id.miSettings:
                Intent intent = new Intent(this, settingsPasswordScreen.class);
                startActivity(intent);
                break;
            case R.id.miTorch:
                if(mCameraFragment != null)
                    mCameraFragment.toggleTorch();
                    torchOn = !torchOn;
                    if (torchOn)
                        item.setIcon(R.drawable.ic_flashlight_yellow);
                    else
                        item.setIcon(R.drawable.ic_flashlight_black);
                    break;
            case R.id.miSync:
                Runnable runnable = new Runnable() {
                    @Override
                    public void run(){
                            syncWithServer();
                    }
                };
                new Thread(runnable).start();
                break;
        }

        return true;
    }

    private void switchToSelectModeState(){
        if(mCurrentState == CurrentState.ADD_STOCK) {
            getSupportFragmentManager().beginTransaction()
                    .remove(mAddNewStockFragment)
                    .remove(mCameraFragment)
                    .replace(R.id.fragmentContainer2, mModeSelectFragment)
                    .commit();
        }
        else if(mCurrentState == CurrentState.CHECK_STOCK) {
            getSupportFragmentManager().beginTransaction()
                    .remove(mCheckItemsFragment)
                    .remove(mCameraFragment)
                    .replace(R.id.fragmentContainer2, mModeSelectFragment)
                    .commit();
        }
        mCurrentState = CurrentState.MODE_SELECT;
    }



    @Override
    public void onAddStockModeSelected() {
        Button addStockBtn = (Button)findViewById(R.id.btnAddStockMode);
        addStockBtn.setEnabled(false);
        Button checkItemsBtn = (Button)findViewById(R.id.btnCheckItemsMode);
        checkItemsBtn.setEnabled(false);

        //if(mAddNewStockFragment == null)
        mCameraFragment = new cameraFragment();

        if(mAddNewStockFragment == null)
            mAddNewStockFragment = new addNewStockFragment(
                    mProductDataManager,
                    mLocationDataManger,
                    mAddStockManager,
                    mItemIdLookUpDataManager
            );

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragmentContainer1, mCameraFragment)
                .replace(R.id.fragmentContainer2, mAddNewStockFragment)
                .commit();

        mCurrentState = CurrentState.ADD_STOCK;
    }

    @Override
    public void onCheckItemsModeSelected() {
        Button addStockBtn = (Button)findViewById(R.id.btnAddStockMode);
        addStockBtn.setEnabled(false);
        Button checkItemsBtn = (Button)findViewById(R.id.btnCheckItemsMode);
        checkItemsBtn.setEnabled(false);

        //if(mCameraFragment == null)
        mCameraFragment = new cameraFragment();

        if(mCheckItemsFragment == null)
            mCheckItemsFragment = new checkItemsFragment(
                    mProductDataManager,
                    mLocationDataManger,
                    mCheckStockInOutManager,
                    mItemIdLookUpDataManager,
                    mJobLookupDataManager,
                    mUserDataManager,
                    mCheckingReasonDataManager
            );

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragmentContainer1, mCameraFragment)
                .replace(R.id.fragmentContainer2, mCheckItemsFragment)
                .commit();

        mCurrentState = CurrentState.CHECK_STOCK;
    }
}
