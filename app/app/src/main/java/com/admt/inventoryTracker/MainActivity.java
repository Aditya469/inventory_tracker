package com.admt.inventoryTracker;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import com.android.volley.toolbox.JsonObjectRequest;

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

    private static AddStockManager mAddStockManager = null;
    private static CheckStockInOutManager mCheckStockInOutManager = null;


    private Timer mSendDataTimer;
    private TimerTask mSendDataTimerTask;

    private enum CurrentState {MODE_SELECT, ADD_STOCK, CHECK_STOCK};
    private CurrentState mCurrentState;

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

        mModeSelectFragment = new modeSelectorFragment();

        // As this app is expected to only have intermittent access to the network
        mSendDataTimer = new Timer(true);
        mSendDataTimerTask = new TimerTask() {
            @Override
            public void run() {
                syncWithServer();
            }
        };
        mSendDataTimer.scheduleAtFixedRate(mSendDataTimerTask, 1000, 10000);


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
                    mUserDataManager
            );

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragmentContainer1, mCameraFragment)
                .replace(R.id.fragmentContainer2, mCheckItemsFragment)
                .commit();

        mCurrentState = CurrentState.CHECK_STOCK;
    }
}
