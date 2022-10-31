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

public class UserDataManager extends UpdateableServerDataManager<User>
{
    public UserDataManager(Application application){
        super(application, "UserList.json", "/getAppUserIdList");
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
