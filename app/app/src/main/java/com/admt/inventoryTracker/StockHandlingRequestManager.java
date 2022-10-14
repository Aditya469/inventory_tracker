package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.util.Log;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.RequestFuture;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public abstract class StockHandlingRequestManager<T> {
    private class StockHandlingRequest {
        Long requestId;
        T requestParameters;

        public StockHandlingRequest() {
        }

        public StockHandlingRequest(Long RequestId, T RequestParameters) {
            requestId = RequestId;
            requestParameters = RequestParameters;
        }
    }

    private ArrayList<StockHandlingRequest> mStockHandlingRequestList;
    private Context mAppContextRef;
    private RequestQueue mRequestQueue;
    private Semaphore mRequestListAccessSem;
    private static Semaphore mSendAllSyncSem; // used to synchronise sending requests
    protected String mJsonFileName;

    protected String TAG;

    public StockHandlingRequestManager(Application application, String cacheFileName) {
        TAG = "StockHandlingRequestManager";
        mAppContextRef = application.getApplicationContext();
        mStockHandlingRequestList = new ArrayList<>();
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
        mRequestListAccessSem = new Semaphore(1);
        mJsonFileName = cacheFileName;
        readListFromJsonFile(); // load the list from file. This will contain data if the app was
                                // not able to send all requests before it closed/crashed
    }

    private void writeListToJsonFile() throws InterruptedException, JSONException, IOException {
        JSONArray listJson = new JSONArray();

        for (int i = 0; i < mStockHandlingRequestList.size(); i++) {
            StockHandlingRequest stockHandlingRequest = mStockHandlingRequestList.get(i);

            JSONObject requestParametersJson = convertRequestParametersToJsonObject(stockHandlingRequest.requestParameters);
            JSONObject requestJson = new JSONObject();
            requestJson.put("requestId", stockHandlingRequest.requestId);
            requestJson.put("requestParameters", requestParametersJson);

            listJson.put(requestJson);
        }

        File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
        FileWriter fileWriter = new FileWriter(file);
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
        bufferedWriter.write(listJson.toString());
        bufferedWriter.close();
    }

    void readListFromJsonFile() {
        try {
            File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
            FileReader fileReader = new FileReader(file);
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            StringBuilder stringBuilder = new StringBuilder();
            String line = bufferedReader.readLine();
            while (line != null) {
                stringBuilder.append(line);
                line = bufferedReader.readLine();
            }
            bufferedReader.close();

            mRequestListAccessSem.acquire();
            JSONArray jsonArray = new JSONArray(stringBuilder.toString());
            for (int i = 0; i < jsonArray.length(); i++) {
                JSONObject requestJson = jsonArray.getJSONObject(i);
                StockHandlingRequest stockHandlingRequest = new StockHandlingRequest();
                stockHandlingRequest.requestId = requestJson.getLong("requestId");
                stockHandlingRequest.requestParameters = convertJsonObjectToRequestParameters(
                        requestJson.getJSONObject("requestParameters")
                );
                mStockHandlingRequestList.add(stockHandlingRequest);
            }
        } catch (IOException | JSONException | InterruptedException e) {
            e.printStackTrace();
        } finally {
            mRequestListAccessSem.release();
        }
    }

    protected abstract JSONObject convertRequestParametersToJsonObject(T Request) throws JSONException;

    protected abstract T convertJsonObjectToRequestParameters(JSONObject JsonObject) throws JSONException;

    public Boolean hasPending() {
        return mStockHandlingRequestList.size() > 0;
    }

    public void onPause() {
        mRequestQueue.stop();
    }

    public void onResume() {
        mRequestQueue.start();
    }

    public void QueueRequest(T NewRequest) {
        try {
            mRequestListAccessSem.acquire();
            Long requestId = System.currentTimeMillis();
            mStockHandlingRequestList.add(new StockHandlingRequest(requestId, NewRequest));
            writeListToJsonFile(); // save a local copy in case the app is closed or crashes
        } catch (JSONException | IOException | InterruptedException e) {
            e.printStackTrace();
        } finally {
            mRequestListAccessSem.release();
        }
    }

    protected abstract String getServerEndpointName(T CurrentRequest);

    // note this function exists so that the various network-connected classes can be choreographed,
    // rather than a free-for-all. This function blocks until all requests have been processed or
    // an error occurs.
    public void SendAllRequests() {
        try {
            Log.d(TAG, "Enter SendAllRequests");

            SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                    mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

            String protocol = prefs.getString(mAppContextRef.getString(R.string.prefs_server_protocol), "http");
            String ipAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_ip_address), "");

            Log.d(TAG, "Pend on mRequestListAccessSem");
            mRequestListAccessSem.acquire();
            Log.d(TAG, "Got semaphore");

            Log.i(TAG, String.format("There are %d requests to process", mStockHandlingRequestList.size()));

            mSendAllSyncSem = new Semaphore(1); // init every time this function runs, just to avoid any weird bugs

            for (int i = 0; i < mStockHandlingRequestList.size(); i++) {
                if(!mSendAllSyncSem.tryAcquire(10, TimeUnit.SECONDS))
                {
                    Log.d(TAG, "Failed to acquire mSendAllSyncSem. Stop");
                    return;
                }
                Log.d(TAG, String.format("Processing request %d", i));

                // turn the request into JSON and append the request ID
                StockHandlingRequest stockHandlingRequest = mStockHandlingRequestList.get(i);
                JSONObject requestParamsJson = convertRequestParametersToJsonObject(stockHandlingRequest.requestParameters);
                requestParamsJson.put("requestId", stockHandlingRequest.requestId);

                // url has to be built dynamically as check-in and check-out requests have different endpoints
                String url = protocol + "://" + ipAddress + getServerEndpointName(stockHandlingRequest.requestParameters);

                JsonObjectRequest requestToServer = new JsonObjectRequest(
                        url,
                        requestParamsJson,
                        new Response.Listener<JSONObject>() {
                            @Override
                            public void onResponse(JSONObject response) {
                                try {
                                    Log.d(TAG, String.format("Got response. Processed ID: %s", response.getString("processedId")));
                                    Utilities.showDebugMessage(mAppContextRef, String.format("Got response. Processed ID: %s", response.getString("processedId")));
                                    Runnable runnable = new Runnable() {
                                        @Override
                                        public void run() {
                                            // this has to run in a new thread because volley puts response
                                            // handlers on the main thread and things didn't work
                                            mSendAllSyncSem.release();
                                            Log.d(TAG, "mSendAllSyncSem released");
                                        }
                                    };
                                    new Thread(runnable).start();
                                } catch (JSONException e) {
                                    e.printStackTrace();
                                }
                            }
                        },
                        new Response.ErrorListener() {
                            @Override
                            public void onErrorResponse(VolleyError error) {
                                Log.d(TAG, error.getMessage());
                            }
                        }
                );
                mRequestQueue.add(requestToServer);
                Log.d(TAG, "Request added to queue");
            }
            // wait for last request to be processed
            mSendAllSyncSem.acquire();
            mStockHandlingRequestList.clear();
        } catch (InterruptedException | JSONException e) {
            Log.e(TAG, e.getMessage());
        }
        finally
        {
            mRequestListAccessSem.release();
            Log.d(TAG, "released semaphore");
        }
    }
}

