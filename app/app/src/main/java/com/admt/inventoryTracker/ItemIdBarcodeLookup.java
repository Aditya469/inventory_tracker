package com.admt.inventoryTracker;

public class ItemIdBarcodeLookup {
    public String ItemId;
    public String Barcode;

    public ItemIdBarcodeLookup()
    {}

    public ItemIdBarcodeLookup(String newItemId, String newBarcode)
    {
        ItemId = newItemId;
        Barcode = newBarcode;
    }
}
