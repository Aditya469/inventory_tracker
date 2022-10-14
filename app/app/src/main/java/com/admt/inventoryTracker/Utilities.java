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

    static Semaphore sem = null;
    public static void serverTest(Context context)
    {
        String tag = "serverTest";
        sem = new Semaphore(1);
        try {
            Log.d(tag, "entering server test");
            RequestQueue requestQueue = Volley.newRequestQueue(context);
            requestQueue.start();

            RequestFuture<String> future = RequestFuture.newFuture();
            StringRequest stringRequest = new StringRequest(
                    "http://192.168.0.167:5000/serverTest",
                    new Response.Listener<String>() {
                        @Override
                        public void onResponse(String response) {
                            Log.d(tag, "Got response");
                            Runnable runnable = new Runnable() {
                                @Override
                                public void run() {
                                    // this has to run in a new thread because volley puts response
                                    // handlers on the main thread and things didn't work
                                    sem.release();
                                }
                            };
                            Thread t = new Thread(runnable);
                            t.start();
                        }
                    },
                    new Response.ErrorListener() {
                        @Override
                        public void onErrorResponse(VolleyError error) {
                            Log.d(tag, "ERROR");
                        }
                    }
            );

            for (int i = 0; i < 5; i++) {
                Log.d(tag, "pend on sem");
                sem.acquire();
                requestQueue.add(stringRequest);
                Log.d(tag, "Posted request to queue. Awaiting response");
            }
        }
        catch (InterruptedException e) {
            Log.d(tag, "InterruptedException");
            e.printStackTrace();
        }
    }
}
