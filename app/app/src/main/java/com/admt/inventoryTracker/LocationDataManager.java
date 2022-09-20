package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class LocationDataManager extends UpdateableServerDataManager<Location>
{
    public LocationDataManager(Application application) {
        super(application);

        super.mJsonFileName = "LocationList.json";
        super.mUpdateEndpoint = "/getAppBinData";
        super.initialiseItemList();
    }

    @Override
    protected Location parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        Location newLocation = new Location();
        newLocation.LocationIdString = ItemJson.getString("idString");
        newLocation.LocationName = ItemJson.getString("locationName");
        return newLocation;
    }

    @Override
    protected String getItemDictKeyString(Location Item) {
        return Item.LocationIdString;
    }
}
