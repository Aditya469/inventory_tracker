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
    protected JSONObject convertRequestParametersToJsonObject(AddStockRequestParameters Request) throws JSONException{
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
        if(Request.BatchNumber != null)
            addStockRequestJson.put("batchNumber", Request.BatchNumber);
        if(Request.SerialNumber != null)
            addStockRequestJson.put("serialNumber", Request.SerialNumber);
        if(Request.DateOfManufacture != null)
            addStockRequestJson.put("dateOfManufacture", Request.DateOfManufacture);

        return addStockRequestJson;
    }

    @Override
    protected AddStockRequestParameters convertJsonObjectToRequestParameters(JSONObject JsonObject) throws JSONException{
        AddStockRequestParameters addStockRequestParameters = new AddStockRequestParameters();
        if(JsonObject.has("barcode"))
            addStockRequestParameters.Barcode = JsonObject.getString("barcode");
        if(JsonObject.has("idString"))
            addStockRequestParameters.ItemId = JsonObject.getString("idString");
        if(JsonObject.has("binIdString"))
            addStockRequestParameters.LocationId = JsonObject.getString("binIdString");
        if(JsonObject.has("bulkItemCount"))
            addStockRequestParameters.BulkItemCount = JsonObject.getDouble("bulkItemCount");
        if(JsonObject.has("quantityCheckingIn"))
            addStockRequestParameters.ItemQuantityToAdd = JsonObject.getDouble("quantityCheckingIn");
        if(JsonObject.has("expiryDate"))
            addStockRequestParameters.ExpiryDate = JsonObject.getString("expiryDate");
        if(JsonObject.has("batchNumber"))
            addStockRequestParameters.BatchNumber = JsonObject.getString("batchNumber");
        if(JsonObject.has("serialNumber"))
            addStockRequestParameters.SerialNumber = JsonObject.getString("serialNumber");
        if(JsonObject.has("dateOfManufacture"))
            addStockRequestParameters.DateOfManufacture = JsonObject.getString("dateOfManufacture");

        return addStockRequestParameters;
    }

    @Override
    protected String getServerEndpointName(AddStockRequestParameters CurrentRequest) {
        return "/addStockRequest";
    }
}