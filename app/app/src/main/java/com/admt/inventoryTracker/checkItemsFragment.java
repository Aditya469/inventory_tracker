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

import android.os.Build;
import android.os.Bundle;

import androidx.annotation.RequiresApi;
import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.fragment.app.Fragment;

import android.os.Handler;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;

import com.google.android.material.snackbar.Snackbar;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;


public class checkItemsFragment extends Fragment implements AdapterView.OnItemSelectedListener {
    ProductDataManager mProductDataManger;
    LocationDataManager mLocationDataManager;
    CheckStockInOutManager mCheckStockInOutManager;
    ItemIdLookUpDataManager mItemIdLookUpDataManager;
    JobLookupDataManager mJobLookupDataManager;
    UserDataManager mUserDataManager;
    CheckingReasonDataManager mCheckingReasonsDataManager;

    StockInteractionHandlingCallbacks mStockInteractionHandlingCallbacks;
    CheckStockInOutRequestParameters mCurrentCheckingRequest;

    String TAG = "CheckItemsFragment";

    public checkItemsFragment() {
        // Required empty public constructor
    }

    public checkItemsFragment(
            ProductDataManager PDM, LocationDataManager LDM, CheckStockInOutManager CSM,
            ItemIdLookUpDataManager ILDM, JobLookupDataManager JDM, UserDataManager UDM,
            CheckingReasonDataManager CRDM
    )
    {
        MainActivity mainActivity = (MainActivity)getActivity();
        mStockInteractionHandlingCallbacks = mainActivity;

        mProductDataManger = PDM;
        mLocationDataManager = LDM;
        mCheckStockInOutManager = CSM;
        mItemIdLookUpDataManager = ILDM;
        mJobLookupDataManager = JDM;
        mUserDataManager = UDM;
        mCheckingReasonsDataManager = CRDM;

        mCurrentCheckingRequest = new CheckStockInOutRequestParameters();
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        MainActivity mainActivity = (MainActivity)getActivity();
        mStockInteractionHandlingCallbacks = mainActivity;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_check_items, container, false);

        Button btnCheckIn = (Button)view.findViewById(R.id.btnCheckStockIn);
        btnCheckIn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                onBtnCheckInPressed();
            }
        });

        Button btnCheckOut = (Button)view.findViewById(R.id.btnCheckStockOut);
        btnCheckOut.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                onBtnCheckOutPressed();
            }
        });

        Button btnCancel = (Button)view.findViewById(R.id.btnCheckStockCancel);
        btnCancel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                onBtnCancelPressed();
            }
        });

        EditText etQtyToCheck = (EditText) view.findViewById(R.id.etCheckStockQuantity);
        etQtyToCheck.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable editable) {
                try {
                    mCurrentCheckingRequest.QuantityChecking = Double.parseDouble(editable.toString());
                    if (isValidCheckInRequest()) {
                        TextView tvPrompt = (TextView) (getActivity()
                                .findViewById(R.id.tvCheckItemsPrompt));
                        tvPrompt.setText(getString(R.string.prompt_check_stock_ready));

                        enableCheckInButton();
                    }
                }
                catch(java.lang.NumberFormatException e)
                {
                    e.printStackTrace();
                }
            }
        });

        Spinner spCheckingReason = (Spinner) view.findViewById(R.id.spCheckStockJobReason);
        spCheckingReason.setOnItemSelectedListener(this);
        mCheckingReasonsDataManager.setSpinnerReference(spCheckingReason);

        return view;
    }

    public void onResume() {super.onResume();}
    public void onPause() {super.onPause();}

    private boolean isValidCheckInRequest()
    {
        if(mCurrentCheckingRequest.IdString != null && mCurrentCheckingRequest.QuantityChecking != null)
            return true;
        return false;
    }

    private boolean isValidCheckOutRequest()
    {
        if(mCurrentCheckingRequest.IdString != null)
            return true;
        return false;
    }

    private void enableCheckInButton(){
        Button btnCheckIn = (Button) getActivity().findViewById(R.id.btnCheckStockIn);
        btnCheckIn.setEnabled(true);
    }

    private void enableCheckOutButton(){
        Button btnCheckOut = (Button) getActivity().findViewById(R.id.btnCheckStockOut);
        btnCheckOut.setEnabled(true);
    }

    public void addBarcode(String BarcodeData)
    {
        String error = null;
        Runnable runnable;
        Handler mainHandler = new Handler(getContext().getMainLooper());

        mStockInteractionHandlingCallbacks.onBarcodeSeen();

        if(BarcodeData.startsWith(getString(R.string.sys_prefix_item))) {
            mCurrentCheckingRequest.IdString = BarcodeData;

            // get the itemLookup for this ID and retreive the product name and barcode
            ItemIdBarcodeLookup itemIdBarcodeLookup = mItemIdLookUpDataManager.get(BarcodeData);
            if(itemIdBarcodeLookup == null)
                error = getString(R.string.error_check_stock_item_unknown);
            else {
                final Product productType = mProductDataManger.get(itemIdBarcodeLookup.Barcode);
                runnable = new Runnable() {
                    @Override
                    public void run() {
                        EditText etItemId = (EditText) getActivity().findViewById(R.id.etCheckStockItemId);
                        etItemId.setText(BarcodeData);

                        EditText etProdName = (EditText) getActivity().findViewById(R.id.etCheckStockProductName);
                        etProdName.setText(productType.Name);

                        EditText etBarcode = (EditText) getActivity().findViewById(R.id.etCheckStockProductBarcode);
                        etBarcode.setText(productType.Barcode);

                        TextView tvUnit = (TextView) getActivity().findViewById(R.id.tvCheckStockQtyUnit);
                        tvUnit.setText(productType.Unit);
                    }
                };
                mainHandler.post(runnable);
            }
        }
        else if(BarcodeData.startsWith(getString(R.string.sys_prefix_job))) {
            JobNameLookup jobNameLookup = mJobLookupDataManager.get(BarcodeData);
            if(jobNameLookup == null){
                error = getString(R.string.error_check_job_id_unknown);
            }
            else {
                mCurrentCheckingRequest.JobId = jobNameLookup.JobIdString;
                runnable = new Runnable() {
                    @Override
                    public void run() {
                        if (jobNameLookup != null) {
                            EditText etJobId = (EditText) getActivity().findViewById(R.id.etCheckStockJobName);
                            etJobId.setText(jobNameLookup.JobName);
                        }
                    }
                };
                mainHandler.post(runnable);
            }
        }
        else if(BarcodeData.startsWith(getString(R.string.sys_prefix_location))){
            mCurrentCheckingRequest.BinId = BarcodeData;
            Location location = mLocationDataManager.get(BarcodeData);
            if(location == null)
                error = getString(R.string.error_check_location_id_unknown);
            else {
                runnable = new Runnable() {
                    @Override
                    public void run() {
                        EditText etLocationId = (EditText) getActivity().findViewById(R.id.etCheckStockLocationName);
                        etLocationId.setText(location.LocationName);
                    }
                };
                mainHandler.post(runnable);
            }
        }
        else if(BarcodeData.startsWith(getString(R.string.sys_prefix_user))){
            mCurrentCheckingRequest.UserId = BarcodeData;
            User user = mUserDataManager.get(BarcodeData);
            if(user == null)
                error = getString(R.string.error_check_user_id_unknown);
            else {
                runnable = new Runnable() {
                    @Override
                    public void run() {
                        EditText etUsername = (EditText) getActivity().findViewById(R.id.etCheckStockUserName);
                        etUsername.setText(user.Username);
                    }
                };
                mainHandler.post(runnable);
            }
        }
        else { // at this point, probably the barcode of the product packaging itself.
            // look up the product. If it is a bulk item, fill in the appropriate fields.
            // otherwise, ignore.
            Product productType = mProductDataManger.get(BarcodeData);
            if(productType != null && productType.IsBulkProduct && productType.IsAssignedStockId){
                mCurrentCheckingRequest.IdString = productType.AssociatedStockId;
                runnable = new Runnable() {
                    @Override
                    public void run() {
                        EditText etItemId = (EditText) getActivity().findViewById(R.id.etCheckStockItemId);
                        etItemId.setText(BarcodeData);

                        if(productType != null){
                            EditText etProdName = (EditText) getActivity().findViewById(R.id.etCheckStockProductName);
                            etProdName.setText(productType.Name);

                            EditText etBarcode = (EditText) getActivity().findViewById(R.id.etCheckStockProductBarcode);
                            etBarcode.setText(productType.Barcode);
                        }
                    }
                };
                mainHandler.post(runnable);
            }
            else{
                error = getString(R.string.error_check_scanned_non_bulk_product);
            }
        }

        if(error != null)
        {
            final String errorText = error;
            runnable = new Runnable() {
                @Override
                public void run() {
                    ConstraintLayout rootLayout = getActivity().findViewById(R.id.clCheckItemsLayout);
                    Snackbar snackbar = Snackbar
                            .make(rootLayout, errorText, Snackbar.LENGTH_LONG);
                    snackbar.show();
                }
            };
            mainHandler.post(runnable);
        }
        else {
            runnable = new Runnable() {
                @Override
                public void run() {
                    // update prompt
                    TextView tvPrompt = (TextView) getActivity().findViewById(R.id.tvCheckItemsPrompt);
                    tvPrompt.setText(getStatusPrompt());

                    if (isValidCheckInRequest())
                        enableCheckInButton();
                    if (isValidCheckOutRequest())
                        enableCheckOutButton();
                }
            };
            mainHandler.post(runnable);
        }
    }

    private String getStatusPrompt()
    {
        String prompt = "";
        if(mCurrentCheckingRequest.IdString == null)
            prompt = getString(R.string.prompt_check_stock_scan_item_id);
        else if(mCurrentCheckingRequest.QuantityChecking == null)
            prompt = getString(R.string.prompt_check_stock_add_qty_options_or_check_out);
        else
            prompt = getString(R.string.prompt_check_stock_ready);

        return prompt;
    }

    private void resetDisplay()
    {
        mCurrentCheckingRequest = new CheckStockInOutRequestParameters();
        EditText etItemId = (EditText) getActivity().findViewById(R.id.etCheckStockItemId);
        etItemId.setText("");
        EditText etProdName = (EditText) getActivity().findViewById(R.id.etCheckStockProductName);
        etProdName.setText("");
        EditText etBarcode = (EditText) getActivity().findViewById(R.id.etCheckStockProductBarcode);
        etBarcode.setText("");
        EditText etLocationId = (EditText) getActivity().findViewById(R.id.etCheckStockLocationName);
        etLocationId.setText("");
        EditText etUsername = (EditText) getActivity().findViewById(R.id.etCheckStockUserName);
        etUsername.setText("");
        EditText etQty = (EditText) getActivity().findViewById(R.id.etCheckStockQuantity);
        etQty.setText("");
        TextView tvQtyUnit = (TextView) getActivity().findViewById(R.id.tvCheckStockQtyUnit);
        tvQtyUnit.setText("");
        EditText etJobId = (EditText) getActivity().findViewById(R.id.etCheckStockJobName);
        etJobId.setText("");
        Spinner spReason = (Spinner) getActivity().findViewById(R.id.spCheckStockJobReason);
        spReason.setSelection(0);
        Button btnCheckIn = (Button) getActivity().findViewById(R.id.btnCheckStockIn);
        btnCheckIn.setEnabled(false);
        Button btnCheckOut = (Button) getActivity().findViewById(R.id.btnCheckStockOut);
        btnCheckOut.setEnabled(false);
        TextView tvPrompt = (TextView) getActivity().findViewById(R.id.tvCheckItemsPrompt);
        tvPrompt.setText(getString(R.string.prompt_check_stock_scan_item_id));
    }

    private void onBtnCheckInPressed()
    {
        mCurrentCheckingRequest.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_IN;
        handleQueueingRequest(getString(R.string.label_check_stock_item_checked_in));
    }

    private void onBtnCheckOutPressed()
    {
        mCurrentCheckingRequest.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_OUT;
        handleQueueingRequest(getString(R.string.label_check_stock_item_checked_out));
    }

    private void handleQueueingRequest(String ConfirmationMessage)
    {
        mCurrentCheckingRequest.Timestamp = getTimestamp();
        CheckStockInOutRequestParameters requestToAdd = mCurrentCheckingRequest;
        mCurrentCheckingRequest = new CheckStockInOutRequestParameters();

        ConstraintLayout rootLayout = getActivity().findViewById(R.id.clCheckItemsLayout);
        Snackbar snackbar = Snackbar
                .make(rootLayout, ConfirmationMessage, Snackbar.LENGTH_LONG)
                .addCallback(new Snackbar.Callback(){
                    @Override
                    public void onDismissed(Snackbar transientBottomBar, int event) {
                        super.onDismissed(transientBottomBar, event);
                        switch (event){
                            case Snackbar.Callback.DISMISS_EVENT_CONSECUTIVE:
                            case Snackbar.Callback.DISMISS_EVENT_SWIPE:
                            case Snackbar.Callback.DISMISS_EVENT_TIMEOUT:
                                mCheckStockInOutManager.QueueRequest(requestToAdd);
                        }
                    }
                })
                .setAction("Undo", new View.OnClickListener() {
                    @Override
                    public void onClick(View view) {
                        // no code actually needed here as the new request is added on a timeout
                        Log.i(TAG, "undo action pressed. Request will not be added.");
                    }
                });

        snackbar.show();
        resetDisplay();
    }

    private void onBtnCancelPressed()
    {
        resetDisplay();
        mCurrentCheckingRequest  = new CheckStockInOutRequestParameters();
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    private String getTimestamp(){
        String pattern = "yyyy-MM-dd HH:mm:ss";
        LocalDateTime timeStamp = LocalDateTime.now();
        String formattedTimeStamp = timeStamp.format(DateTimeFormatter.ofPattern(pattern));
        return formattedTimeStamp;

    }

    @Override
    public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
        String selectedName = (String) parent.getItemAtPosition(position);
        CheckingReason checkingReason = mCheckingReasonsDataManager.get(selectedName);

        if(checkingReason != null) {
            mCurrentCheckingRequest.ReasonId = checkingReason.id;

            TextView tvPrompt = (TextView) getActivity().findViewById(R.id.tvCheckItemsPrompt);
            tvPrompt.setText(getStatusPrompt());
        }
    }

    @Override
    public void onNothingSelected(AdapterView<?> parent) {
        mCurrentCheckingRequest.ReasonId = null;
    }
}