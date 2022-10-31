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

public class ItemIdLookUpDataManager extends UpdateableServerDataManager<ItemIdBarcodeLookup>{
    public ItemIdLookUpDataManager(Application application)
    {
        super(application, "itemBarcodesLookup.json", "/getAppItemIdBarcodeList");
    }

    @Override
    protected ItemIdBarcodeLookup parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        ItemIdBarcodeLookup itemIdBarcodeLookup = new ItemIdBarcodeLookup();
        if(ItemJson.has("itemId"))
            itemIdBarcodeLookup.ItemId = ItemJson.getString("itemId");
        if(ItemJson.has("barcode"))
            itemIdBarcodeLookup.Barcode = ItemJson.getString("barcode");
        return itemIdBarcodeLookup;
    }

    @Override
    protected JSONObject parseItemToJsonObject(ItemIdBarcodeLookup Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("itemId", Item.ItemId);
        jsonObject.put("barcode", Item.Barcode);
        return jsonObject;
    }

    @Override
    protected String getItemDictKeyString(ItemIdBarcodeLookup Item) {
        return Item.ItemId;
    }
}
