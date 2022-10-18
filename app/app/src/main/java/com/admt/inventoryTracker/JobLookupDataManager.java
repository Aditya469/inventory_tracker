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
