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

import android.app.DatePickerDialog;
import android.app.Dialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.EditText;
import android.widget.TableRow;
import android.widget.TextView;

import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.fragment.app.DialogFragment;
import androidx.fragment.app.Fragment;

import com.google.android.material.snackbar.Snackbar;

import org.json.JSONException;

import java.io.IOException;
import java.util.Calendar;


/**
 * The data display fragment is used to display the barcode that was
 * read by the camera, and allows the user to set the rework level
 * and send the data to the server.
 */
public class addNewStockFragment extends Fragment implements DatePickerDialog.OnDateSetListener
{
    ProductDataManager mProductDataManager;
    LocationDataManager mLocationDataManager;
    AddStockManager mAddStockManager;
    AddStockRequestParameters mAddStockRequestParameters;
    ItemIdLookUpDataManager mItemIdLookUpDataManager;

    StockInteractionHandlingCallbacks mStockHandlingInteractionCallbacks;
    Product mCurrentProduct;

    String TAG = "DigitME2InventoryTrackerAddStockFragment";

    public addNewStockFragment()
    {
        // Required empty public constructor
    }

    public addNewStockFragment(ProductDataManager PDMRef, LocationDataManager LDMRef, AddStockManager ASMRef, ItemIdLookUpDataManager ILMRef)
    {
        MainActivity mainActivity = (MainActivity)getActivity();
        mStockHandlingInteractionCallbacks = mainActivity;

        mProductDataManager = PDMRef;
        mLocationDataManager = LDMRef;
        mAddStockManager = ASMRef;
        mItemIdLookUpDataManager = ILMRef; // mote: the item lookup is used to cache newly added IDs prior to server sync
        mAddStockRequestParameters = new AddStockRequestParameters();
    }

    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);

        MainActivity mainActivity = (MainActivity)getActivity();
        mStockHandlingInteractionCallbacks = mainActivity;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState)
    {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_add_new_stock, container, false);

        Button btnSave = (Button)view.findViewById(R.id.btnAddStockSave);
        btnSave.setOnClickListener(new View.OnClickListener()
        {
            // btnSend handler
            @Override
            public void onClick(View v)
            {
                onBtnSavePressed();
            }
        });

        Button btnCancel = (Button)view.findViewById(R.id.btnAddStockCancel);
        btnCancel.setOnClickListener(new View.OnClickListener()
        {
            @Override
            public void onClick(View v)
            {
                onBtnCancelPressed();
            }
        });

        EditText etItemBarcode = (EditText) view.findViewById(R.id.etAddStockItemBarcode);
        etItemBarcode.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable editable) {
                // if the user types a barcode into the input field, this handler will fire
                // to allow ID codes (not necessarily actual barcode numbers) to be entered
                String barcode = editable.toString();
                if(barcode == "")
                    mAddStockRequestParameters.Barcode = null;
                else {
                    Product product = mProductDataManager.get(barcode);
                    if(product != null)
                        addBarcode(barcode, false);
                }
                if (isAddStockRequestValid()) {
                    TextView tvPrompt = (TextView) (getActivity().
                            findViewById(R.id.tvAddStockPrompt));
                    tvPrompt.setText(getString(R.string.prompt_add_stock_ready));

                    enableSaveButton();
                }
            }
        });

        TableRow trExpiry = (TableRow) view.findViewById(R.id.trAddStockExpiry);
        trExpiry.setVisibility(View.GONE);
        TableRow trBulkQty = (TableRow) view.findViewById(R.id.trAddStockBulkAddQty);
        trBulkQty.setVisibility(View.GONE);
        TableRow trSpecQty = (TableRow) view.findViewById(R.id.trAddStockSpecificItemQty);
        trSpecQty.setVisibility(View.GONE);

        EditText etExpiry = (EditText) view.findViewById(R.id.etAddStockExpiryDate);
        etExpiry.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showDatePickerDialog(view);
            }
        });

        EditText etPartialQty = (EditText) view.findViewById(R.id.etAddStockPartialStockQty);
        etPartialQty.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable editable) {
                try {
                    if(editable.toString() == "")
                        mAddStockRequestParameters.ItemQuantityToAdd = null;
                    else
                        mAddStockRequestParameters.ItemQuantityToAdd = Double.parseDouble(editable.toString());
                    if (isAddStockRequestValid()) {
                        TextView tvPrompt = (TextView) (getActivity().
                                findViewById(R.id.tvAddStockPrompt));
                        tvPrompt.setText(getString(R.string.prompt_add_stock_ready));

                        enableSaveButton();
                    }
                }
                catch (java.lang.NumberFormatException e)
                {
                    e.printStackTrace();
                }
            }
        });

        EditText etPackCount = (EditText) view.findViewById(R.id.etAddStockPacksToAdd);
        etPackCount.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable editable) {
                try {
                    if(editable.toString() == "")
                        mAddStockRequestParameters.BulkItemCount = null;
                    else
                        mAddStockRequestParameters.BulkItemCount = Double.parseDouble(editable.toString());
                    if (isAddStockRequestValid()) {
                        TextView tvPrompt = (TextView) (getActivity().
                                findViewById(R.id.tvAddStockPrompt));
                        tvPrompt.setText(getString(R.string.prompt_add_stock_ready));

                        enableSaveButton();
                    }
                }
                catch (java.lang.NumberFormatException e)
                {
                    e.printStackTrace();
                }
            }
        });

        view.setBackgroundColor(Color.WHITE);

        return view;
    }

    @Override
    public void onResume()
    {
        super.onResume();
    }

    @Override
    public void onPause()
    {
        super.onPause();
    }

    // borrowed from https://developer.android.com/guide/topics/ui/controls/pickers
    public static class DatePickerFragment extends DialogFragment{

        @Override
        public Dialog onCreateDialog(Bundle savedInstanceState) {
            // Use the current date as the default date in the picker
            final Calendar c = Calendar.getInstance();
            int year = c.get(Calendar.YEAR);
            int month = c.get(Calendar.MONTH);
            int day = c.get(Calendar.DAY_OF_MONTH);

            addNewStockFragment addNewStockFragment = (addNewStockFragment) getParentFragmentManager().findFragmentById(R.id.fragmentContainer2);
            DatePickerDialog.OnDateSetListener onDateSetListener = (DatePickerDialog.OnDateSetListener)addNewStockFragment;

            // Create a new instance of DatePickerDialog and return it
            return new DatePickerDialog(requireContext(), onDateSetListener, year, month, day);
        }
//
//        public void onDateSet(DatePicker view, int year, int month, int day) {
//            // Do something with the date chosen by the user
//
//        }
    }

    public void showDatePickerDialog(View v) {
        DialogFragment newFragment = new DatePickerFragment();
        newFragment.show(getParentFragmentManager(), "datePicker");
    }

    @Override
    public void onDateSet(DatePicker datePicker, int year, int month, int day) {
        Handler mainHandler = new Handler(getContext().getMainLooper());
        String expDateSystem = String.format("%d-%02d-%02d", year, month, day);
        String expDateHumanReadable = String.format("%02d-%02d-%d", day, month, year);
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                EditText etExpiryDate = getActivity().findViewById(R.id.etAddStockExpiryDate);
                etExpiryDate.setText(expDateHumanReadable);
            }
        };
        mainHandler.post(runnable);
        mAddStockRequestParameters.ExpiryDate = expDateSystem;
        if(isAddStockRequestValid()) {
            enableSaveButton();
            TextView tvPrompt = (TextView)(getActivity().
                    findViewById(R.id.tvAddStockPrompt));
            tvPrompt.setText(getString(R.string.prompt_add_stock_ready));
        }
    }


    public  void addBarcode(String BarcodeData)
    {
        addBarcode(BarcodeData, true);
    }

    private void addBarcode(String BarcodeData, final Boolean UpdateBarcodeField)
    {
        String error = null;
        Runnable runnable;
        Handler mainHandler = new Handler(getContext().getMainLooper());

        mStockHandlingInteractionCallbacks.onBarcodeSeen();

        // add a new barcode to the collection of data for this request. Update
        // mAddStockRequestParameters and the screen as appropriate.
        if(BarcodeData.startsWith(getContext().getString(R.string.sys_prefix_job)))
            error = "Scanned JOB code in ADD STOCK mode";

        else if(BarcodeData.startsWith(getContext().getString(R.string.sys_prefix_item))) {
            if(mAddStockRequestParameters.Barcode == null || mCurrentProduct == null)
                error = "Scan a product barcode first";
            else
            {
                mAddStockRequestParameters.ItemId = BarcodeData;
                if(UpdateBarcodeField)
                {
                    runnable = new Runnable() {
                        @Override
                        public void run() {
                            TextView tvItemId = (TextView) getActivity().findViewById(R.id.etAddStockItemQrCode);
                            tvItemId.setText(BarcodeData);

                            TextView tvPrompt = (TextView) getActivity().findViewById(R.id.tvAddStockPrompt);
                            if (mCurrentProduct.CanExpire && mAddStockRequestParameters.LocationId == null)
                                tvPrompt.setText(getString(R.string.prompt_add_stock_scan_bin_qr_code_or_set_expiry));
                            else
                                tvPrompt.setText(getString(R.string.prompt_add_stock_scan_bin_qr_code));
                        }
                    };
                    mainHandler.post(runnable);
                }
            }
        }

        else if(BarcodeData.startsWith(getContext().getString(R.string.sys_prefix_location)))
        {
            Location location = mLocationDataManager.get(BarcodeData);
            if(location == null)
                error = "This location is not recognised";
            else
            {
                mAddStockRequestParameters.LocationId = BarcodeData;
                if(UpdateBarcodeField) {
                    runnable = new Runnable() {
                        @Override
                        public void run()
                        {
                            TextView tvLocationName = (TextView) (getActivity()
                                    .findViewById(R.id.etAddStockLocationName));

                            tvLocationName.setText(location.LocationName);

                            TextView tvPrompt = (TextView) (getActivity().
                                    findViewById(R.id.tvAddStockPrompt));

                            // prompt for expiry date if other fields have been filled
                            if (mCurrentProduct.CanExpire &&
                                    mAddStockRequestParameters.ExpiryDate == null &&
                                    mAddStockRequestParameters.Barcode != null &&
                                    mAddStockRequestParameters.ItemId != null) {
                                tvPrompt.setText(getString(R.string.prompt_add_stock_set_expiry_date));
                            }
                            // or to send if all fields ready
                            else if (isAddStockRequestValid())
                                tvPrompt.setText(getString(R.string.prompt_add_stock_ready));

                        }
                    };
                    mainHandler.post(runnable);
                }
            }
        }

        else // assumed to be a product barcode at this point
        {
            mCurrentProduct = mProductDataManager.get(BarcodeData);
            if(mCurrentProduct == null)
                error = "This product is not recognised";
            else {
                mAddStockRequestParameters.Barcode = BarcodeData;

                if(mCurrentProduct.IsAssignedStockId)
                {
                    mAddStockRequestParameters.ItemId = mCurrentProduct.AssociatedStockId;
                }

                runnable = new Runnable() {
                    @Override
                    public void run() {
                        if(UpdateBarcodeField) {
                            TextView etItemBarcode = (TextView) (getActivity()
                                    .findViewById(R.id.etAddStockItemBarcode));
                            etItemBarcode.setText(BarcodeData);
                        }

                        TextView tvProductName = (TextView) (getActivity()
                                .findViewById(R.id.etAddStockProductName));
                        tvProductName.setText(mCurrentProduct.Name);

                        TextView tvPrompt = (TextView) (getActivity()
                                .findViewById(R.id.tvAddStockPrompt));
                        tvPrompt.setText(getString(R.string.prompt_add_stock_scan_qr_code));

                        if(mCurrentProduct.CanExpire) {
                            TableRow trExpiry = (TableRow) getActivity()
                                    .findViewById(R.id.trAddStockExpiry);
                            trExpiry.setVisibility(View.VISIBLE);
                        }
                        if(mCurrentProduct.IsBulkProduct) {
                            TableRow trBulkQty = (TableRow) getActivity()
                                    .findViewById(R.id.trAddStockBulkAddQty);
                            trBulkQty.setVisibility(View.VISIBLE);

                            if(mCurrentProduct.IsAssignedStockId)
                            {
                                EditText etItemId = (EditText) getActivity()
                                        .findViewById(R.id.etAddStockItemQrCode);
                                etItemId.setText(mCurrentProduct.AssociatedStockId);
                                tvPrompt.setText(getString(R.string.prompt_add_stock_scan_bin_qr_code));
                            }
                        }
                        else {
                            TableRow trSpecQty = (TableRow) getActivity()
                                    .findViewById(R.id.trAddStockSpecificItemQty);
                            trSpecQty.setVisibility(View.VISIBLE);

                            TextView tvQtyUnit = (TextView) getActivity()
                                    .findViewById(R.id.tvAddStockPartialPackUnit);
                            tvQtyUnit.setText(mCurrentProduct.Unit);
                        }
                    }
                };
                mainHandler.post(runnable);
            }
        }

        if(error != null)
        {
            final String errorText = error;
            runnable = new Runnable() {
                @Override
                public void run() {
                    ConstraintLayout rootLayout = getActivity().findViewById(R.id.clAddStockLayout);
                    Snackbar snackbar = Snackbar
                            .make(rootLayout, errorText, Snackbar.LENGTH_LONG);
                    snackbar.show();
                }
            };
            mainHandler.post(runnable);
        }
        else if(isAddStockRequestValid())
            enableSaveButton();
    }

    private boolean isAddStockRequestValid()
    {
        if(mAddStockRequestParameters.Barcode == null)
            return false;
        if(mAddStockRequestParameters.ItemId == null)
            return false;
        if(mCurrentProduct.CanExpire && mAddStockRequestParameters.ExpiryDate == null)
            return false;
        return true;
    }


    private void onBtnSavePressed()
    {
        AddStockRequestParameters requestToAdd = mAddStockRequestParameters;
        ConstraintLayout rootLayout = getActivity().findViewById(R.id.clAddStockLayout);
        Snackbar snackbar = Snackbar
                .make(rootLayout, R.string.label_add_stock_item_added_confirmation, Snackbar.LENGTH_LONG)
                .addCallback(new Snackbar.Callback() {
                    @Override
                    public void onDismissed(Snackbar transientBottomBar, int event) {
                        try {
                            super.onDismissed(transientBottomBar, event);
                            switch (event) {
                                case Snackbar.Callback.DISMISS_EVENT_CONSECUTIVE:
                                case Snackbar.Callback.DISMISS_EVENT_SWIPE:
                                case Snackbar.Callback.DISMISS_EVENT_TIMEOUT:
                                    mAddStockManager.QueueRequest(requestToAdd);
                                    mItemIdLookUpDataManager.addItem(new ItemIdBarcodeLookup(requestToAdd.ItemId, requestToAdd.Barcode));
                            }
                        }
                        catch (JSONException e) {
                                e.printStackTrace();
                            }
                        catch (IOException e) {
                                e.printStackTrace();
                            }
                    }
                })
                .setAction("Undo", new View.OnClickListener() {
                    @Override
                    public void onClick(View view) {
                        // no code actually needed here as the new request is added on a timeout
                        Log.i(TAG, "onSaveSnackbar: undo action pressed. Request will not be added.");
                    }
                });

        snackbar.show();
        resetDisplay();
    }

    private void onBtnCancelPressed()
    {
        resetDisplay();
    }

    void resetDisplay()
    {
        Button saveBtn = (Button) getActivity().findViewById(R.id.btnAddStockSave);
        saveBtn.setEnabled(false);
        EditText editText = (EditText) getActivity().findViewById(R.id.etAddStockItemBarcode);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockItemQrCode);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockProductName);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockExpiryDate);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockPacksToAdd);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockLocationName);
        editText.setText("");
        editText = (EditText) getActivity().findViewById(R.id.etAddStockPartialStockQty);
        editText.setText("");
        TextView tvQtyUnit = (TextView) getActivity().findViewById(R.id.tvAddStockPartialPackUnit);
        tvQtyUnit.setText("");

        TextView prompt = (TextView) getActivity().findViewById(R.id.tvAddStockPrompt);
        prompt.setText(getString(R.string.prompt_add_stock_scan_product_barcode));

        TableRow trExpiry = (TableRow) getActivity().findViewById(R.id.trAddStockExpiry);
        trExpiry.setVisibility(View.GONE);
        TableRow trBulkQty = (TableRow) getActivity().findViewById(R.id.trAddStockBulkAddQty);
        trBulkQty.setVisibility(View.GONE);
        TableRow trSpecQty = (TableRow) getActivity().findViewById(R.id.trAddStockSpecificItemQty);
        trSpecQty.setVisibility(View.GONE);

        mAddStockRequestParameters = new AddStockRequestParameters();
    }



    private void enableSaveButton(){
        Handler mainHandler = new Handler(getContext().getMainLooper());
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                Button saveBtn = (Button) getActivity().findViewById(R.id.btnAddStockSave);
                saveBtn.setEnabled(true);
            }
        };
        mainHandler.post(runnable);
    }

}
