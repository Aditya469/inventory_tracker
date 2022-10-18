package com.admt.inventoryTracker;

public class CheckingReason {
    public String id;
    public String reason;

    public CheckingReason()
    {}

    public CheckingReason(String ReasonId, String ReasonName)
    {
        id = ReasonId;
        reason = ReasonName;
    }
}
