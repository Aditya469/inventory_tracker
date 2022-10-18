package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class CheckStockInOutManager extends StockHandlingRequestManager<CheckStockInOutRequestParameters>{
    public CheckStockInOutManager(Application application){
        super(application, "stockCheckRequests.json");
    }

    @Override
    protected JSONObject convertRequestParametersToJsonObject(CheckStockInOutRequestParameters Request) throws JSONException {
        JSONObject requestJson = new JSONObject();
        if(Request.IdString != null)
            requestJson.put("idString", Request.IdString);
        if(Request.Timestamp != null)
            requestJson.put("timestamp", Request.Timestamp);
        if(Request.JobId != null)
            requestJson.put("jobIdString", Request.JobId);
        if(Request.BinId != null)
            requestJson.put("binIdString", Request.BinId);
        if(Request.UserId != null)
            requestJson.put("userIdString", Request.UserId);
        if(Request.QuantityChecking != null)
            requestJson.put("quantity", Request.QuantityChecking);
        if(Request.ReasonId != null)
            requestJson.put("reasonId", Request.ReasonId);

        if(Request.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_IN)
            requestJson.put("checkRequestType", "checkIn");
        else if(Request.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_OUT)
            requestJson.put("checkRequestType", "checkOut");

        return requestJson;
    }

    @Override
    protected CheckStockInOutRequestParameters convertJsonObjectToRequestParameters(JSONObject JsonObject) throws JSONException {
        CheckStockInOutRequestParameters parameters = new CheckStockInOutRequestParameters();
        if(JsonObject.has("idString"))
            parameters.IdString = JsonObject.getString("idString");
        if(JsonObject.has("timestamp"))
            parameters.Timestamp = JsonObject.getString("timestamp");
        if(JsonObject.has("jobIdString"))
            parameters.JobId = JsonObject.getString("jobIdString");
        if(JsonObject.has("binIdString"))
            parameters.BinId = JsonObject.getString("binIdString");
        if(JsonObject.has("userIdString"))
            parameters.UserId = JsonObject.getString("userIdString");
        if(JsonObject.has("quantity"))
            parameters.QuantityChecking = JsonObject.getDouble("quantity");
        if(JsonObject.has("reasonId"))
            parameters.ReasonId = JsonObject.getString("reasonId");

        if(JsonObject.has("checkRequestType")){
            if(JsonObject.getString("checkRequestType").equals("checkIn"))
                parameters.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_IN;
            else if(JsonObject.getString("checkRequestType").equals("checkOut"))
                parameters.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_OUT;
        }
        return parameters;
    }

    @Override
    protected String getServerEndpointName(CheckStockInOutRequestParameters CurrentRequest) {
        if(CurrentRequest.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_OUT)
            return "/checkStockOut";
        else if(CurrentRequest.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_IN)
            return "/checkStockIn";
        throw new RuntimeException();
    }
}
