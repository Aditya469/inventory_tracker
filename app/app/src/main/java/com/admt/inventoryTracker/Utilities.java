package com.admt.inventoryTracker;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.util.Log;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.RequestFuture;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class Utilities {

    public static boolean isWifiConnected(Context context) {
        // temporary. TODO: REMOVE
        //return true;
        ConnectivityManager connectivityManager =
                (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkCapabilities networkCapabilities =
                connectivityManager.getNetworkCapabilities(connectivityManager.getActiveNetwork());

        if (networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))
            return true;

        return false;
    }

    public static void showDebugMessage(Context context, String messageText)
    {
        Handler mainHandler = new Handler(context.getMainLooper());
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                Toast.makeText(
                        context,
                        messageText,
                        Toast.LENGTH_SHORT
                ).show();
            }
        };
        mainHandler.post(runnable);
    }
}
