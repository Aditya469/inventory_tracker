package com.admt.inventoryTracker;

import java.util.Date;

public class AddStockRequestParameters {
    public String Barcode;
    public String ItemId;
    public String LocationId;
    public Integer BulkItemCount; // only applicable for bulk items
    public Double ItemQuantityToAdd; // allows for adding a partial pack to the system
    public String ExpiryDate;

    public AddStockRequestParameters(){}
}
