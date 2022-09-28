package com.admt.inventoryTracker;

public class CheckStockInOutRequestParameters {
    public enum CheckingType{CHECK_IN, CHECK_OUT};
    String IdString;
    String Timestamp;
    String JobId;
    String BinId;
    String UserId;
    Double QuantityChecking;
    CheckingType CheckRequestType;
}
