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

public class JobLookupDataManager extends UpdateableServerDataManager<JobNameLookup>{
    public JobLookupDataManager(Application application){
        super(application, "jobDataCache.json", "/getAppJobData");
    }

    @Override
    protected JobNameLookup parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        JobNameLookup jobNameLookup = new JobNameLookup();
        jobNameLookup.JobIdString = ItemJson.getString("idString");
        jobNameLookup.JobName = ItemJson.getString("jobName");
        return jobNameLookup;
    }

    @Override
    protected JSONObject parseItemToJsonObject(JobNameLookup Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("idString", Item.JobIdString);
        jsonObject.put("jobName", Item.JobName);
        return jsonObject;
    }

    @Override
    protected String getItemDictKeyString(JobNameLookup Item) {
        return Item.JobIdString;
    }
}
