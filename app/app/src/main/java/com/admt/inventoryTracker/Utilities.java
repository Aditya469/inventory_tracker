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
import android.content.SharedPreferences;
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
    static String TAG = "Utilities";
    public static boolean isWifiConnected(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(
                context.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        // if the wifi check is disabled, always assume we have a connection.
        if(!prefs.getBoolean(context.getString(R.string.prefs_enable_wifi_check), true))
            return true;

        try {
            ConnectivityManager connectivityManager =
                    (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkCapabilities networkCapabilities =
                    connectivityManager.getNetworkCapabilities(connectivityManager.getActiveNetwork());

            if (networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))
                return true;

            return false;
        }
        catch (NullPointerException e)
        {
            Log.d(TAG, "isWifiConnected: got null pointer");
            return false;
        }
    }

    public static void showDebugMessage(Context context, String messageText)
    {
        SharedPreferences prefs = context.getSharedPreferences(context.getString(R.string.prefs_file_key),
                Context.MODE_PRIVATE);

        if(prefs.getBoolean(context.getString(R.string.prefs_show_debug_messages), true)) {
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
}
