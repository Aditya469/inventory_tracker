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

public class Product {
    private Integer id;
    public String Barcode;
    public Boolean CanExpire;
    public Boolean IsBulkProduct;
    public String Name;
    public Boolean IsAssignedStockId;
    public String AssociatedStockId;
    public String Unit;

    public Product(String Name, String Barcode, Boolean CanExpire, Boolean IsBulk, Boolean IsAssignedStockId, String AssociatedStockId, String Unit){
        this.Name = Name;
        this.Barcode = Barcode;
        this.CanExpire = CanExpire;
        this.IsBulkProduct = IsBulk;
        this.IsAssignedStockId = IsAssignedStockId;
        this.AssociatedStockId = AssociatedStockId;
        this.Unit = Unit;
    }

}
