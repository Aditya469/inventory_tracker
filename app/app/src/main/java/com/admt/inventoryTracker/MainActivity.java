package com.admt.inventoryTracker;

import android.content.Intent;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

public class MainActivity extends AppCompatActivity
        implements cameraFragment.onBarcodeReadListener,
        numberPadFragment.OnNumpadInteractionListener,
        modeSelectorFragment.onModeSelectedListener,
        addNewStockFragment.AddStockInteractionCallbacks
{
    private cameraFragment mCameraFragment = null;
    private addNewStockFragment mAddNewStockFragment = null;
    private checkItemsFragment mCheckItemsFragment = null;
    private numberPadFragment mNumPadFragment = null;
    private modeSelectorFragment mModeSelectFragment = null;
    boolean torchOn = false;

    private ProductDataManager mProductDataManager = null;

    private enum CurrentState {MODE_SELECT, ADD_STOCK, CHECK_STOCK};
    private CurrentState mCurrentState;

    public void onBarcodeRead(String barcodeValue)
    {
        //mAddNewStockFragment.UpdateDisplayedbarcodeReading(barcodeValue);
    }

    public void onBarcodeEntered(String barcodeValue)
    {
        //mAddNewStockFragment.UpdateDisplayedbarcodeReading(barcodeValue);
        //onToggleNumPadRequest();
    }

    public void onBarcodeSeen()
    {
        if(mCameraFragment != null)
            mCameraFragment.flashScreen();
    }

    @Override
    public void onrequestCheckingMode() {

    }

    public void onBarcodeReadHandled()
    {
        if(mCameraFragment != null)
            mCameraFragment.cancelBarcodeReadWait();
    }

    public void onToggleTorchRequest()
    {
        if(mCameraFragment != null)
            mCameraFragment.toggleTorch();
    }

    public void onToggleNumPadRequest()
    {
        if(mNumPadFragment == null)
        {
            mNumPadFragment = new numberPadFragment();
            getSupportFragmentManager().beginTransaction()
                    .replace(R.id.fragmentContainer1, mNumPadFragment)
                    .commit();

            mCameraFragment = null;
        }
        else
        {
            mCameraFragment = new cameraFragment();
            getSupportFragmentManager().beginTransaction()
                    .replace(R.id.fragmentContainer1, mCameraFragment)
                    .commit();

            mNumPadFragment = null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Toolbar toolbar = (Toolbar)findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // don't add fragments if the app has resumed from suspension
        if (savedInstanceState != null) {
            return;
        }

        if(mProductDataManager == null)
            mProductDataManager = new ProductDataManager(getApplication());

        mModeSelectFragment = new modeSelectorFragment();

        getSupportFragmentManager().beginTransaction()
                .add(R.id.fragmentContainer1, mModeSelectFragment).commit();
        mCurrentState = CurrentState.MODE_SELECT;

        // since this works by swapping fragments around, the back button is overridden to
        // allow the correct fragments to be swapped back into place
        OnBackPressedCallback callback = new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if(mCurrentState == CurrentState.MODE_SELECT)
                    finish();
                else if(mCurrentState == CurrentState.CHECK_STOCK || mCurrentState == CurrentState.ADD_STOCK){
                    switchToSelectModeState();
                }
            }
        };
        getOnBackPressedDispatcher().addCallback(this, callback);

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

        }

        return true;
    }

    private void switchToSelectModeState(){
        if(mCurrentState == CurrentState.ADD_STOCK) {
            getSupportFragmentManager().beginTransaction()
                    .remove(mAddNewStockFragment)
                    .replace(R.id.fragmentContainer1, mModeSelectFragment)
                    .commit();
        }
        else if(mCurrentState == CurrentState.CHECK_STOCK) {
            getSupportFragmentManager().beginTransaction()
                    .remove(mCheckItemsFragment)
                    .replace(R.id.fragmentContainer1, mModeSelectFragment)
                    .commit();
        }
        mCurrentState = CurrentState.MODE_SELECT;
    }



    @Override
    public void onAddStockModeSelected() {
        Button addStockBtn = (Button)findViewById(R.id.btnAddStock);
        addStockBtn.setEnabled(false);
        Button checkItemsBtn = (Button)findViewById(R.id.btnCheckItems);
        checkItemsBtn.setEnabled(false);

        if(mCameraFragment == null)
            mCameraFragment = new cameraFragment();

        if(mAddNewStockFragment == null)
            mAddNewStockFragment = new addNewStockFragment();

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragmentContainer1, mCameraFragment)
                .replace(R.id.fragmentContainer2, mAddNewStockFragment)
                .commit();

        mCurrentState = CurrentState.ADD_STOCK;
    }

    @Override
    public void onCheckItemsModeSelected() {
        Button addStockBtn = (Button)findViewById(R.id.btnAddStock);
        addStockBtn.setEnabled(false);
        Button checkItemsBtn = (Button)findViewById(R.id.btnCheckItems);
        checkItemsBtn.setEnabled(false);

        if(mCameraFragment == null)
            mCameraFragment = new cameraFragment();

        if(mCheckItemsFragment == null)
            mCheckItemsFragment = new checkItemsFragment();

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.fragmentContainer1, mCameraFragment)
                .replace(R.id.fragmentContainer2, mCheckItemsFragment)
                .commit();

        mCurrentState = CurrentState.CHECK_STOCK;
    }
}
