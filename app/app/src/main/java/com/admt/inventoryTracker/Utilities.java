package com.admt.inventoryTracker;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.widget.Toast;

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
