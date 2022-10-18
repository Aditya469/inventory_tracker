package com.admt.inventoryTracker;

public class CheckStockInOutRequestParameters {
    public enum CheckingType{CHECK_IN, CHECK_OUT};
    String IdString;
    String Timestamp;
    String JobId;
    String BinId;
    String UserId;
    String ReasonId;
    Double QuantityChecking;
    CheckingType CheckRequestType;

    public CheckStockInOutRequestParameters()
    {
        IdString = null;
        Timestamp = null;
        JobId = null;
        BinId = null;
        UserId = null;
        ReasonId = null;
        QuantityChecking = null;
    }
}
