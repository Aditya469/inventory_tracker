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

public class AddStockManager extends StockHandlingRequestManager<AddStockRequestParameters> {
    private String TAG = "InventoryTracker_AddStockManager";

    public AddStockManager(Application application) {
        super(application, "addStockCache.json");
    }

    @Override
    protected JSONObject convertRequestToJsonObject(AddStockRequestParameters Request) throws JSONException{
        JSONObject addStockRequestJson = new JSONObject();

        if(Request.Barcode != null)
            addStockRequestJson.put("barcode", Request.Barcode);
        if(Request.ItemId != null)
            addStockRequestJson.put("idString", Request.ItemId);
        if(Request.LocationId != null)
            addStockRequestJson.put("binIdString", Request.LocationId);
        if(Request.BulkItemCount != null)
            addStockRequestJson.put("bulkItemCount", Request.BulkItemCount);
        if(Request.ItemQuantityToAdd != null)
            addStockRequestJson.put(
                    "quantityCheckingIn", Request.ItemQuantityToAdd);
        if(Request.ExpiryDate != null)
            addStockRequestJson.put("expiryDate", Request.ExpiryDate);

        return addStockRequestJson;
    }

    @Override
    protected AddStockRequestParameters convertJsonObjectToRequest(JSONObject JsonObject) throws JSONException{
        AddStockRequestParameters addStockRequestParameters = new AddStockRequestParameters();
        if(JsonObject.has("barcode"))
            addStockRequestParameters.Barcode = JsonObject.getString("barcode");
        if(JsonObject.has("idString"))
            addStockRequestParameters.ItemId = JsonObject.getString("idString");
        if(JsonObject.has("binIdString"))
            addStockRequestParameters.LocationId = JsonObject.getString("binIdString");
        if(JsonObject.has("bulkItemCount"))
            addStockRequestParameters.BulkItemCount = JsonObject.getInt("bulkItemCount");
        if(JsonObject.has("quantityCheckingIn"))
            addStockRequestParameters.ItemQuantityToAdd = JsonObject.getDouble("quantityCheckingIn");
        if(JsonObject.has("expiryDate"))
            addStockRequestParameters.ExpiryDate = JsonObject.getString("expiryDate");

        return addStockRequestParameters;
    }

    @Override
    protected String getServerEndpointName(AddStockRequestParameters CurrentRequest) {
        return "/addStockRequest";
    }
}