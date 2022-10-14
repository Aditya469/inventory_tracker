package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class ItemIdLookUpDataManager extends UpdateableServerDataManager<ItemIdBarcodeLookup>{
    public ItemIdLookUpDataManager(Application application)
    {
        super(application);
        super.mJsonFileName = "itemBarcodesLookup.json";
        super.mUpdateEndpoint = "/getAppItemIdBarcodeList";
        super.initialiseItemList();
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
