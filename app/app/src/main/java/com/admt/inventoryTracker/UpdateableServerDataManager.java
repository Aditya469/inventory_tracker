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
import java.util.Iterator;
import java.util.Set;
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
    private String mJsonFileName;
    private String mUpdateEndpoint;


    public UpdateableServerDataManager(Application application, String JsonFileName, String UpdateEndpointName){
        mAppContextRef = application.getApplicationContext();
        mItemMap = new HashMap<String, T>();
        mMapAccessSem = new Semaphore(1);
        mRequestQueue = Volley.newRequestQueue(mAppContextRef);
        mRequestQueue.start();
        mJsonFileName = JsonFileName;
        mUpdateEndpoint = UpdateEndpointName;
        initialiseItemList();

        /*
        mTimer = new Timer(true);
        mTimerTask = new TimerTask() {
            @Override
            public void run() {
                if(Utilities.isWifiConnected(mAppContextRef))
                    fetchUpdatedItemList();
            }
        };
        mTimer.scheduleAtFixedRate(mTimerTask, 10000, 10000);
        */
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

    protected void onUpdateComplete(final HashMap<String, T> ItemMap)
    {

    }

    protected void initialiseItemList(){
        if(mListInitialised)
            return;

        // by default attempt to load the local list first
        try {
            loadItemList();
            mListInitialised = true;
            onUpdateComplete(mItemMap);
        } catch (IOException | JSONException | InterruptedException e) {
            e.printStackTrace();
        }

        // then if the wifi is connected, the local copy may be updated from the server
        if(Utilities.isWifiConnected(mAppContextRef))
        {
            // wifi is connected. Attempt to reach server and update.
            fetchUpdatedItemList();
        }
    }

    public void update(){
        if(Utilities.isWifiConnected(mAppContextRef))
            fetchUpdatedItemList();
    }

    private void saveItemListJson(JSONArray ItemArrayJson) throws IOException {
        File file = new File(mAppContextRef.getFilesDir(), mJsonFileName);
        FileWriter fileWriter = new FileWriter(file);
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
        bufferedWriter.write(ItemArrayJson.toString());
        bufferedWriter.close();
    }

    private void loadItemList() throws IOException, JSONException, InterruptedException {
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
    }

    protected abstract T parseJsonObjectToItem(JSONObject ItemJson) throws JSONException;

    protected abstract JSONObject parseItemToJsonObject(T Item) throws JSONException;

    protected abstract String getItemDictKeyString(T Item);

    void parseItemJsonArrayDataToMap(JSONArray ItemListJsonArray) throws InterruptedException, JSONException {
        mMapAccessSem.acquire();
        for (int i = 0; i < ItemListJsonArray.length(); i++) {
            JSONObject itemJson = ItemListJsonArray.getJSONObject(i);
            T item = parseJsonObjectToItem(itemJson);
            mItemMap.put(getItemDictKeyString(item), item);
        }
        mMapAccessSem.release();
    }

    JSONArray parseItemMapToJsonArray() throws JSONException{
        JSONArray jsonArray = new JSONArray();
        Set<String> keys = mItemMap.keySet();
        Iterator iterator = keys.iterator();

        while(iterator.hasNext()){
            T item = mItemMap.get(iterator.next());
            jsonArray.put(parseItemToJsonObject(item));
        }
        return jsonArray;
    }

    private void fetchUpdatedItemList(){
        SharedPreferences prefs = mAppContextRef.getSharedPreferences(
                mAppContextRef.getString(R.string.prefs_file_key), Context.MODE_PRIVATE);

        String serverBaseAddress = prefs.getString(mAppContextRef.getString(R.string.prefs_server_base_address), "");
        String url = serverBaseAddress + mUpdateEndpoint;

        JsonArrayRequest jsonArrayRequest = new JsonArrayRequest(
                Request.Method.GET,
                url,
                null,
                new Response.Listener<JSONArray>() {
                    @Override
                    public void onResponse(JSONArray ItemDataJson) {
                        try {
                            parseItemJsonArrayDataToMap(ItemDataJson);
                            saveItemListJson(ItemDataJson);
                            mListInitialised = true;
                            onUpdateComplete(mItemMap);
                        } catch (InterruptedException | IOException | JSONException e) {
                            e.printStackTrace();
                        }
                    }
                },
                new Response.ErrorListener() {
                    @Override
                    public void onErrorResponse(VolleyError error) {
                        error.printStackTrace();
                        if(!mListInitialised) {
                            try {
                                loadItemList();
                            } catch (IOException e) {
                                e.printStackTrace();
                            } catch (JSONException e) {
                                e.printStackTrace();
                            } catch (InterruptedException e) {
                                e.printStackTrace();
                            }
                        }
                    }
                }
        );

        mRequestQueue.add(jsonArrayRequest);
    }

    public T get(String Key) throws RuntimeException {
        if (!isInitialised())
            throw new RuntimeException("Not initialised");
        return (mItemMap.get(Key));
    }

    // allows an item to be added to the internal map immediately. This will allow lookups
    // to be performed without a server sync.
    protected void addItem(T newItem) throws JSONException, IOException {
        String key = getItemDictKeyString(newItem);
        mItemMap.put(key, newItem);

        // immediately save to file to avoid loss of data if the app closes
        JSONArray mapJson = parseItemMapToJsonArray();
        saveItemListJson(mapJson);
    }
}
