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

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class AddStockManager {
    private int mPendingCount;
    private List<AddStockRequestParameters> mRequestList;
    private Context mAppContextRef;
    private RequestQueue mRequestQueue;

    private String TAG = "InventoryTracker_AddStockManager";

    public AddStockManager(Application application)
    {
        mAppContextRef = application.getApplicationContext();
        mRequestList = new ArrayList<AddStockRequestParameters>();
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
    }

    public Boolean hasPending()
    {
        return mPendingCount == 0;
    }

    public void onPause()
    {
        mRequestQueue.stop();
    }

    public void onResume()
    {
        mRequestQueue.start();
    }

    public void QueueRequest(AddStockRequestParameters NewRequest)
    {
        mRequestList.add(NewRequest);
        mPendingCount += 1;
    }

    // note this function exists so that the various network-connected classes can be choreographed,
    // rather than a free-for-all
    public void SendAddRequests()
    {
        try
        {
            if(Utilities.isWifiConnected(mAppContextRef))
            {
                SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                        mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

                String ipAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_ip_address), "");
                String url = "http://" + ipAddress + "/addStock";

                Iterator<AddStockRequestParameters> stockRequestIterator = mRequestList.iterator();
                while(stockRequestIterator.hasNext())
                {
                    AddStockRequestParameters addStockRequestParameters = stockRequestIterator.next();

                    JSONObject addStockRequestJson = new JSONObject();
                    addStockRequestJson.put("idNumber", addStockRequestParameters.ItemId);
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

                    JsonObjectRequest addStockRequest = new JsonObjectRequest(
                            Request.Method.POST,
                            url,
                            addStockRequestJson,
                            new Response.Listener<JSONObject>() {
                                @Override
                                public void onResponse(JSONObject response) {
                                    mPendingCount -= 1;
                                    mRequestList.remove((Object) addStockRequestParameters);
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
            }
        }
        catch (JSONException e)
        {
            e.printStackTrace();
        }
    }
}
