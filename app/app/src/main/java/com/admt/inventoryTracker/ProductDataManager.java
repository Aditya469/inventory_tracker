package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

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
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.Timer;
import java.util.concurrent.Semaphore;

public class ProductDataManager {
    private HashMap<String, Product> mProductMap;
    private Semaphore mMapAccessSem;
    private Timer mTimer;
    private RequestQueue mRequestQueue;
    private Context mAppContextRef;
    private boolean mProductListInitialised = false;
    private final String mJsonFileName = "productsData.json";

    public ProductDataManager(Application application){
        mAppContextRef = application.getApplicationContext();
        mProductMap = new HashMap<String, Product>();
        mMapAccessSem = new Semaphore(1);
        mTimer = new Timer(true);
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();

        // the server might not be accessible, so if not load the products list from a json file
        // if it exists. If the server is reachable, check for new data and save it to the same file
        initialiseProductList();


    }

    public boolean isInitialised(){
        return mProductListInitialised;
    }

    public void onPause(){
        mRequestQueue.stop();
    }

    public void onResume(){
        mRequestQueue.start();
    }

    private void initialiseProductList(){
        if(mProductListInitialised)
            return;

        ConnectivityManager connectivityManager =
                (ConnectivityManager)mAppContextRef.getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkCapabilities networkCapabilities =
                connectivityManager.getNetworkCapabilities(connectivityManager.getActiveNetwork());

        if(networkCapabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)){
            // wifi is connected. Attempt to reach server and update.
            fetchUpdatedProductList();
        }
        else {
            // wifi is not connected. Attempt to initialise the product list from the local copy
            Runnable runnable = () -> {
                loadProductsList();
                showConfirmationToastMessage("Initialised product list from cache");
            };
            Thread t = new Thread(runnable);
            t.start();
        }
    }

    private void saveProductListJson(JSONArray ProductArrayJson){
        try {
            File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
            FileWriter fileWriter = new FileWriter(file);
            BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
            bufferedWriter.write(ProductArrayJson.toString());
            bufferedWriter.close();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void loadProductsList(){
        try{
            File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
            FileReader fileReader = new FileReader(file);
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            StringBuilder stringBuilder = new StringBuilder();
            String line = bufferedReader.readLine();
            while(line != null){
                stringBuilder.append(line);
                line = bufferedReader.readLine();
            }
            bufferedReader.close();
            parseProductJsonDataToMap(new JSONArray(stringBuilder.toString()));
            mProductListInitialised = true;

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    void parseProductJsonDataToMap(JSONArray ProductJsonData){
        try {
            mMapAccessSem.acquire();
            for (int i = 0; i < ProductJsonData.length(); i++) {
                JSONObject productJson = ProductJsonData.getJSONObject(i);
                Product product = new Product(
                        productJson.getString("name"),
                        productJson.getString("barcode"),
                        productJson.getBoolean("expires"),
                        productJson.getBoolean("isBulk"),
                        productJson.getBoolean("isAssignedStockId"),
                        productJson.getString("associatedStockId")
                );
                mProductMap.put(productJson.getString("barcode"), product);
            }
        } catch (JSONException | InterruptedException e) {
            e.printStackTrace();
        }
        finally{
            mMapAccessSem.release();
        }

    }

    private void fetchUpdatedProductList(){
        SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        String ipAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_ip_address), "");
        String url = "http://" + ipAddress + "/getAppProductData";

        JsonArrayRequest jsonArrayRequest = new JsonArrayRequest(
                Request.Method.GET,
                url,
                null,
                new Response.Listener<JSONArray>() {
                    @Override
                    public void onResponse(JSONArray productDataJson) {
                        parseProductJsonDataToMap(productDataJson);
                        saveProductListJson(productDataJson);
                        mProductListInitialised = true;
                        showConfirmationToastMessage("Initialised product list from server");
                    }
                },
                new Response.ErrorListener() {
                    @Override
                    public void onErrorResponse(VolleyError error) {
                        error.printStackTrace();
                        loadProductsList();
                        showConfirmationToastMessage("Initialised product list from cache");
                    }
                }
        );

        mRequestQueue.add(jsonArrayRequest);
    }

    public Product getProduct(String ProductBarcode){
        Product product = null;
        try {
            mMapAccessSem.acquire();
            product = mProductMap.get(ProductBarcode);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        finally{
            mMapAccessSem.release();
        }
        return product;
    }

    private void showConfirmationToastMessage(String MessageText){
        // Get a handler that can be used to post to the main thread
        Handler mainHandler = new Handler(mAppContextRef.getMainLooper());

        Runnable runnable = new Runnable() {
            @Override
            public void run()
            {
                Toast.makeText(
                        mAppContextRef,
                        MessageText,
                        Toast.LENGTH_LONG)
                        .show();
            }
        };

        mainHandler.post(runnable);
    }
}

