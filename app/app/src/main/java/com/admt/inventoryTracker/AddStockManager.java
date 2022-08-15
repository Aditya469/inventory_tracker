package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import com.android.volley.RequestQueue;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;
import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.Semaphore;

public class AddStockManager {
    private HashMap<String, AddStockRequestParameters> mRequestMap;
    private Context mAppContextRef;
    private RequestQueue mRequestQueue;
    private Semaphore mRequestMapAccessSem;
    private final String mJsonFileName = "addStockRequests.json";

    private String TAG = "InventoryTracker_AddStockManager";

    public AddStockManager(Application application)
    {
        mAppContextRef = application.getApplicationContext();
        mRequestMap = new HashMap<>();
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
        mRequestMapAccessSem = new Semaphore(1);
        readListFromJsonFile(); // load the list from file. This will exist if the app was
                                // not able to send all requests before it closed/crashed
    }

    private void writeListToJsonFile() throws InterruptedException, JSONException, IOException {
        JSONObject mapJson = new JSONObject();

        Set<String> requestIds = mRequestMap.keySet();
        Iterator<String> requestIdIterator = requestIds.iterator();
        while(requestIdIterator.hasNext()) {
            String requestId = requestIdIterator.next();
            JSONObject addStockRequestJson = convertAddStockRequestToJson(requestId);
            mapJson.put(requestId, addStockRequestJson);
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
            JSONObject listJsonObject = new JSONObject(stringBuilder.toString());
            Iterator iterator = listJsonObject.keys();
            while(iterator.hasNext()){
                String requestId = (String) iterator.next();
                JSONObject entryJson = listJsonObject.getJSONObject(requestId);

                AddStockRequestParameters parameters = new AddStockRequestParameters();
                parameters.ItemId = entryJson.getString("idString");
                if(entryJson.has("barcode"))
                    parameters.Barcode = entryJson.getString("barcode");
                if(entryJson.has("binIdString"))
                    parameters.LocationId = entryJson.getString("binIdString");
                if(entryJson.has("bulkItemCount"))
                    parameters.BulkItemCount = entryJson.getInt("bulkItemCount");
                if(entryJson.has("quantityCheckingIn"))
                    parameters.ItemQuantityToAdd = entryJson.getDouble("quantityCheckingIn");
                if(entryJson.has("expiryDate"))
                    parameters.ExpiryDate = entryJson.getString("expiryDate");

                mRequestMap.put(requestId, parameters);
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

    public Boolean hasPending()
    {
        return mRequestMap.isEmpty();
    }

    public void onPause()
    {
        mRequestQueue.stop();
    }

    public void onResume()
    {
        mRequestQueue.start();
    }

    public void QueueRequest(AddStockRequestParameters NewRequest){
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

    JSONObject convertAddStockRequestToJson(String requestId) throws JSONException {
        AddStockRequestParameters addStockRequestParameters = mRequestMap.get(requestId);

        JSONObject addStockRequestJson = new JSONObject();

        addStockRequestJson.put("idString", addStockRequestParameters.ItemId);
        if(addStockRequestParameters.Barcode != null)
            addStockRequestJson.put("barcode", addStockRequestParameters.Barcode);
        if(addStockRequestParameters.LocationId != null)
            addStockRequestJson.put("binIdString", addStockRequestParameters.LocationId);
        if(addStockRequestParameters.BulkItemCount != null)
            addStockRequestJson.put("bulkItemCount", addStockRequestParameters.BulkItemCount);
        if(addStockRequestParameters.ItemQuantityToAdd != null)
            addStockRequestJson.put(
                    "quantityCheckingIn", addStockRequestParameters.ItemQuantityToAdd);
        if(addStockRequestParameters.ExpiryDate != null)
            addStockRequestJson.put("expiryDate", addStockRequestParameters.ExpiryDate);

        return addStockRequestJson;
    }

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
                String url = "http://" + ipAddress + "/addStockRequest";

                Set<String> requestIds = mRequestMap.keySet();
                Iterator<String> requestIdIterator = requestIds.iterator();
                mRequestMapAccessSem.acquire();
                while(requestIdIterator.hasNext())
                {
                    String requestId = requestIdIterator.next();


                    JSONObject addStockRequestJson = convertAddStockRequestToJson(requestId);
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
                    mRequestQueue.add(addStockRequest);
                }
                mRequestMapAccessSem.release();
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
