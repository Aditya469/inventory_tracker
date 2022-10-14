package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class UserDataManager extends UpdateableServerDataManager<User>
{
    public UserDataManager(Application application){
        super(application);

        super.mJsonFileName = "UserList.json";
        super.mUpdateEndpoint = "/getAppUserIdList";
        super.initialiseItemList();
    }

    @Override
    protected User parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        User user = new User();
        user.UserIdString = ItemJson.getString("idString");
        user.Username = ItemJson.getString("username");
        return user;
    }

    @Override
    protected JSONObject parseItemToJsonObject(User Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("idString", Item.UserIdString);
        jsonObject.put("userName", Item.Username);
        return jsonObject;
    }

    @Override
    protected String getItemDictKeyString(User Item) {
        return Item.UserIdString;
    }
}
