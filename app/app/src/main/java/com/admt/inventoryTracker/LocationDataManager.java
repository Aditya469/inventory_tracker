package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.widget.Toast;

import com.admt.inventoryTracker.Product;
import com.admt.inventoryTracker.R;
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

public class LocationDataManager extends UpdateableServerDataManager<Location>
{
    public LocationDataManager(Application application) {
        super(application);

        super.mJsonFileName = "LocationList.json";
        super.mUpdateEndpoint = "/getAppBinData";
        super.initialiseItemList();
    }

    @Override
    protected Location parseJsonObjectToItem(JSONObject ItemJson) {
        return null;
    }

    @Override
    protected String getItemDictKeyString(Location Item) {
        return null;
    }
}
