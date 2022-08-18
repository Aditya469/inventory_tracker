package com.admt.inventoryTracker;

import android.app.Application;

import org.json.JSONException;
import org.json.JSONObject;

public class CheckStockInOutManager extends StockHandlingRequestManager<CheckStockInOutRequestParameters>{
    public CheckStockInOutManager(Application application){
        super(application, "stockCheckRequests.json");
    }

    @Override
    protected JSONObject convertRequestToJsonObject(CheckStockInOutRequestParameters Request) throws JSONException {
        JSONObject requestJson = new JSONObject();
        if(Request.IdString != null)
            requestJson.put("idString", Request.IdString);
        if(Request.Timestamp != null)
            requestJson.put("timestamp", Request.Timestamp);
        if(Request.JobId != null)
            requestJson.put("jobId", Request.JobId);
        if(Request.BinId != null)
            requestJson.put("binId", Request.BinId);
        if(Request.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_IN) {
            if (Request.QuantityChecking != null)
                requestJson.put("quantityCheckedIn", Request.QuantityChecking);
            requestJson.put("checkRequestType", "checkIn");
        }
        else if(Request.CheckRequestType == CheckStockInOutRequestParameters.CheckingType.CHECK_OUT) {
            if (Request.QuantityChecking != null)
                requestJson.put("quantityCheckedOut", Request.QuantityChecking);
            requestJson.put("checkRequestType", "checkOut");
        }
        return requestJson;
    }

    @Override
    protected CheckStockInOutRequestParameters convertJsonObjectToRequest(JSONObject JsonObject) throws JSONException {
        CheckStockInOutRequestParameters parameters = new CheckStockInOutRequestParameters();
        if(JsonObject.has("idString"))
            parameters.IdString = JsonObject.getString("idString");
        if(JsonObject.has("timestamp"))
            parameters.Timestamp = JsonObject.getString("timestamp");
        if(JsonObject.has("jobId"))
            parameters.JobId = JsonObject.getString("jobId");
        if(JsonObject.has("binId"))
            parameters.BinId = JsonObject.getString("binId");
        if(JsonObject.has("checkRequestType")){
            if(JsonObject.getString("checkRequestType").equals("checkIn")){
                parameters.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_IN;
                if(JsonObject.has("quantityCheckedIn"))
                    parameters.QuantityChecking = JsonObject.getDouble("quantityCheckingIn");
            }
            else if(JsonObject.getString("checkRequestType").equals("checkOut")){
                parameters.CheckRequestType = CheckStockInOutRequestParameters.CheckingType.CHECK_OUT;
                if(JsonObject.has("quantityCheckedOut"))
                    parameters.QuantityChecking = JsonObject.getDouble("quantityCheckedOut");
            }
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
