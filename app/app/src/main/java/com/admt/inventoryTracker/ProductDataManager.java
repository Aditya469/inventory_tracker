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
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.Volley;

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
import java.util.Timer;
import java.util.concurrent.Semaphore;

public class ProductDataManager extends UpdateableServerDataManager<Product>{
     public ProductDataManager(Application application) {
        super(application, "productsData.json", "/getAppProductData");
    }

    @Override
    protected Product parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        Product product = new Product(
                ItemJson.getString("name"),
                ItemJson.getString("barcode"),
                ItemJson.getBoolean("expires"),
                ItemJson.getBoolean("isBulk"),
                ItemJson.getBoolean("isAssignedStockId"),
                ItemJson.getString("associatedStockId"),
                ItemJson.getString("quantityUnit")
        );
        return product;
    }

    @Override
    protected JSONObject parseItemToJsonObject(Product Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("name", Item.Name);
        jsonObject.put("barcode", Item.Barcode);
        jsonObject.put("expires", Item.CanExpire);
        jsonObject.put("isBulk", Item.IsBulkProduct);
        jsonObject.put("isAssignedStockId", Item.IsAssignedStockId);
        jsonObject.put("associatedStockId", Item.AssociatedStockId);
        jsonObject.put("quantityUnit", Item.Unit);
        return jsonObject;

    }

    @Override
    protected String getItemDictKeyString(Product Item) {
        return Item.Barcode;
    }
}