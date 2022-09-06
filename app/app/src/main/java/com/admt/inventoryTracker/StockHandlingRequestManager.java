package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.Semaphore;

public abstract class StockHandlingRequestManager<T>
{
    private HashMap<String, T> mRequestMap;
    private Context mAppContextRef;
    private RequestQueue mRequestQueue;
    private Semaphore mRequestMapAccessSem;
    protected String mJsonFileName;

    protected String TAG;

    public StockHandlingRequestManager(Application application, String cacheFileName)
    {
        mAppContextRef = application.getApplicationContext();
        mRequestMap = new HashMap<>();
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
        mRequestMapAccessSem = new Semaphore(1);
        mJsonFileName = cacheFileName;
        readListFromJsonFile(); // load the list from file. This will exist if the app was
                                // not able to send all requests before it closed/crashed
    }

    private void writeListToJsonFile() throws InterruptedException, JSONException, IOException {
        JSONObject mapJson = new JSONObject();

        Set<String> requestIds = mRequestMap.keySet();
        Iterator<String> requestIdIterator = requestIds.iterator();

        while(requestIdIterator.hasNext()) {
            String requestId = requestIdIterator.next();

            T request = (T)mRequestMap.get(requestId);
            JSONObject requestJson = convertRequestToJsonObject(request);

            mapJson.put(requestId, requestJson);
        }

        File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
        FileWriter fileWriter = new FileWriter(file);
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
        bufferedWriter.write(mapJson.toString());
        bufferedWriter.close();
    }

    void readListFromJsonFile(){
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

            mRequestMapAccessSem.acquire();
            JSONObject mapJsonObject = new JSONObject(stringBuilder.toString());
            Iterator iterator = mapJsonObject.keys();
            while(iterator.hasNext()){
                String requestId = (String) iterator.next();
                JSONObject entryJson = mapJsonObject.getJSONObject(requestId);
                T request = convertJsonObjectToRequest(entryJson);

                mRequestMap.put(requestId, request);
            }
            mRequestMapAccessSem.release();
        }
        catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    protected abstract JSONObject convertRequestToJsonObject(T Request) throws JSONException;
    protected abstract T convertJsonObjectToRequest(JSONObject JsonObject) throws JSONException;

    public Boolean hasPending()
    {
        return !mRequestMap.isEmpty();
    }

    public void onPause()
    {
        mRequestQueue.stop();
    }

    public void onResume()
    {
        mRequestQueue.start();
    }

    public void QueueRequest(T NewRequest){
        try {
            mRequestMapAccessSem.acquire();
            String requestId = String.format("%d", System.currentTimeMillis());
            mRequestMap.put(requestId, NewRequest);
            writeListToJsonFile(); // save a local copy in case the app is closed or crashes
        } catch (JSONException e) {
            e.printStackTrace();
        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
        finally {
            mRequestMapAccessSem.release();
        }
    }

    protected abstract String getServerEndpointName(T CurrentRequest);

    // note this function exists so that the various network-connected classes can be choreographed,
    // rather than a free-for-all
    public void SendAllRequests()
    {
        try
        {
            if(Utilities.isWifiConnected(mAppContextRef))
            {
                SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                        mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

                String ipAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_ip_address), "");

                Set<String> requestIds = mRequestMap.keySet();
                Iterator<String> requestIdIterator = requestIds.iterator();
                while(requestIdIterator.hasNext())
                {
                    mRequestMapAccessSem.acquire();
                    String requestId = requestIdIterator.next();
                    T request = mRequestMap.get(requestId);
                    String url = "http://" + ipAddress + getServerEndpointName(request);

                    JSONObject addStockRequestJson = convertRequestToJsonObject(request);
                    addStockRequestJson.put("requestId", requestId);

                    JsonObjectRequest addStockRequest = new JsonObjectRequest(
                            Request.Method.POST,
                            url,
                            addStockRequestJson,
                            new Response.Listener<JSONObject>() {
                                @Override
                                public void onResponse(JSONObject response) {
                                    try {
                                        mRequestMapAccessSem.acquire();

                                        mRequestMap.remove(response.get("processedId"));
                                        Utilities.showDebugMessage(mAppContextRef, String.format("Processed request ID %s", response.get("processedId")));

                                        /* only update the cached copy when the last pending
                                         * request has been removed. No point hammering the
                                         * disk so much in a short time
                                         */
                                        if(mRequestMap.isEmpty())
                                            writeListToJsonFile();

                                        mRequestMapAccessSem.release();
                                    } catch (JSONException | InterruptedException | IOException e) {
                                        e.printStackTrace();
                                    }
                                }
                            },
                            new Response.ErrorListener() {
                                @Override
                                public void onErrorResponse(VolleyError error) {
                                    Log.e(TAG, "onErrorResponse: " + error.getMessage());
                                }
                            }

                    );
                    mRequestMapAccessSem.release();
                    mRequestQueue.add(addStockRequest);
                }

            }
        }
        catch (JSONException e)
        {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
