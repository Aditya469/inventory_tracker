package com.admt.inventoryTracker;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;

import androidx.activity.OnBackPressedCallback;
import androidx.fragment.app.Fragment;

import com.android.volley.RequestQueue;
import com.android.volley.toolbox.Volley;

import java.util.HashMap;
import java.util.Timer;
import java.util.TimerTask;


/**
 * The data display fragment is used to display the barcode that was
 * read by the camera, and allows the user to set the rework level
 * and send the data to the server.
 */
public class addNewStockFragment extends Fragment
{
    public interface AddStockInteractionCallbacks
    {
        void onBarcodeReadHandled();
        void onBarcodeSeen();
        void onrequestCheckingMode();
    }

    ProductDataManager mProductDataManager;
    AddStockInteractionCallbacks mAddStockInteractionCallbacks;

    String TAG = "ADMTBarcodeReaderDataDisplay";

    public addNewStockFragment()
    {
        // Required empty public constructor
    }

    public addNewStockFragment(ProductDataManager ProductDataManagerReference)
    {
        mProductDataManager = ProductDataManagerReference;
    }

    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);

        MainActivity mainActivity = (MainActivity)getActivity();
        mAddStockInteractionCallbacks = (AddStockInteractionCallbacks) mainActivity;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState)
    {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_add_new_stock, container, false);

        SharedPreferences prefs =getContext().getSharedPreferences(
                getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        Button btnSend = (Button)view.findViewById(R.id.btnSend);
        btnSend.setOnClickListener(new View.OnClickListener()
        {
            // btnSend handler
            @Override
            public void onClick(View v)
            {
                onBtnSendPressed();
            }
        });

        Button btnCancel = (Button)view.findViewById(R.id.btnCancel);
        btnCancel.setOnClickListener(new View.OnClickListener()
        {
            @Override
            public void onClick(View v)
            {
                onBtnCancelPressed();
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

    private boolean isConnectedToWifiNetwork()
    {
        ConnectivityManager connectivityManager = (ConnectivityManager)getContext()
                .getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo networkInfo = connectivityManager.getNetworkInfo(ConnectivityManager.TYPE_WIFI);
        return networkInfo.isConnected();
    }

    @Override
    public void onPause()
    {
        super.onPause();
    }

    private void onBtnSendPressed()
    {

    }

    private void onBtnCancelPressed()
    {
        resetDisplay();

    }

    void resetDisplay()
    {
        setSendBtnEnabled(true);
    }


    private void setSendBtnEnabled(boolean enabled)
    {
        Button btnSend = (Button)getActivity().findViewById(R.id.btnSend);
        btnSend.setEnabled(enabled);
    }
}
