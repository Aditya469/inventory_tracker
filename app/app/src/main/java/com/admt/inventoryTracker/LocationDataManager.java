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
