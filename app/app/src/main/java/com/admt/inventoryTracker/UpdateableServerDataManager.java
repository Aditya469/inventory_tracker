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
import java.util.TimerTask;
import java.util.concurrent.Semaphore;

abstract class UpdateableServerDataManager<T> {
    private HashMap<String, T> mItemMap;
    private Semaphore mMapAccessSem;
    private Timer mTimer;
    private TimerTask mTimerTask;
    private RequestQueue mRequestQueue;
    private Context mAppContextRef;
    private boolean mListInitialised = false;
    protected String mJsonFileName;
    protected String mUpdateEndpoint;


    public UpdateableServerDataManager(Application application){
        mAppContextRef = application.getApplicationContext();
        mItemMap = new HashMap<String, T>();
        mMapAccessSem = new Semaphore(1);
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
        mTimer = new Timer(true);
        mTimerTask = new TimerTask() {
            @Override
            public void run() {
                if(Utilities.isWifiConnected(mAppContextRef))
                    fetchUpdatedItemList();
            }
        };
        mTimer.scheduleAtFixedRate(mTimerTask, 60000, 60000);
    }

    public boolean isInitialised(){
        return mListInitialised;
    }

    public void onPause(){
        mRequestQueue.stop();
    }

    public void onResume(){
        mRequestQueue.start();
    }

    protected void initialiseItemList(){
        if(mListInitialised)
            return;

        if(Utilities.isWifiConnected(mAppContextRef))
        {
            // wifi is connected. Attempt to reach server and update.
            fetchUpdatedItemList();
        }
        else
        {
            // wifi is not connected. Attempt to initialise the product list from the local copy
            Runnable runnable = () -> {
                loadItemList();
            };
            Thread t = new Thread(runnable);
            t.start();
        }
    }

    private void saveItemListJson(JSONArray ProductArrayJson){
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

    private void loadItemList(){
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
            parseItemJsonArrayDataToMap(new JSONArray(stringBuilder.toString()));
            mListInitialised = true;

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    protected abstract T parseJsonObjectToItem(JSONObject ItemJson);

    protected abstract String getItemDictKeyString(T Item);

    void parseItemJsonArrayDataToMap(JSONArray ItemListJsonArray){
        try {
            mMapAccessSem.acquire();
            for (int i = 0; i < ItemListJsonArray.length(); i++) {
                JSONObject itemJson = ItemListJsonArray.getJSONObject(i);
                T item = parseJsonObjectToItem(itemJson);
                mItemMap.put(getItemDictKeyString(item), item);
            }
        } catch (JSONException | InterruptedException e) {
            e.printStackTrace();
        }
        finally{
            mMapAccessSem.release();
        }

    }

    private void fetchUpdatedItemList(){
        SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        String ipAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_ip_address), "");
        String url = "http://" + ipAddress + mUpdateEndpoint;

        JsonArrayRequest jsonArrayRequest = new JsonArrayRequest(
                Request.Method.GET,
                url,
                null,
                new Response.Listener<JSONArray>() {
                    @Override
                    public void onResponse(JSONArray ItemDataJson) {
                        parseItemJsonArrayDataToMap(ItemDataJson);
                        saveItemListJson(ItemDataJson);
                        mListInitialised = true;
                    }
                },
                new Response.ErrorListener() {
                    @Override
                    public void onErrorResponse(VolleyError error) {
                        error.printStackTrace();
                        if(!mListInitialised)
                            loadItemList();
                    }
                }
        );

        mRequestQueue.add(jsonArrayRequest);
    }

    public T get(String Key) throws RuntimeException
    {
        if(!isInitialised())
            throw new RuntimeException("Not initialised");
        return(mItemMap.get(Key));
    }
}
