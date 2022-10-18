package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class LocationDataManager extends UpdateableServerDataManager<Location>
{
    public LocationDataManager(Application application) {
        super(application,"LocationList.json", "/getAppBinData");
    }

    @Override
    protected Location parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        Location newLocation = new Location();
        newLocation.LocationIdString = ItemJson.getString("idString");
        newLocation.LocationName = ItemJson.getString("locationName");
        return newLocation;
    }

    @Override
    protected JSONObject parseItemToJsonObject(Location Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("idString", Item.LocationIdString);
        jsonObject.put("locationName", Item.LocationName);
        return jsonObject;
    }

    @Override
    protected String getItemDictKeyString(Location Item) {
        return Item.LocationIdString;
    }
}
