package com.admt.inventoryTracker;

import android.app.Application;
import android.content.Context;
import android.widget.ArrayAdapter;
import android.widget.Spinner;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;

public class CheckingReasonDataManager extends UpdateableServerDataManager<CheckingReason>{
    private Spinner mReasonSpinnerRef;
    private Context mContextRef;
    private HashMap<String, CheckingReason> mReasonsMap;
    public CheckingReasonDataManager(Application application)
    {
        super(application, "checkingReasons.json", "/getAppCheckingReasons");
        mContextRef = application.getApplicationContext();
        mReasonSpinnerRef = null;
    }

    @Override
    protected CheckingReason parseJsonObjectToItem(JSONObject ItemJson) throws JSONException {
        CheckingReason checkingReason = new CheckingReason();
        checkingReason.id = ItemJson.getString("id");
        checkingReason.reason = ItemJson.getString("reason");
        return checkingReason;
    }

    @Override
    protected JSONObject parseItemToJsonObject(CheckingReason Item) throws JSONException {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("id", Item.id);
        jsonObject.put("reason", Item.reason);
        return jsonObject;
    }

    @Override
    protected String getItemDictKeyString(CheckingReason Item) {
        return Item.reason;
    }

    @Override
    protected void onUpdateComplete(final HashMap<String, CheckingReason> ItemMap) {
        mReasonsMap = ItemMap;
        updateSpinnerOptions();
    }

    public void setSpinnerReference(Spinner reasonSpinner)
    {
        mReasonSpinnerRef = reasonSpinner;
        updateSpinnerOptions();
    }

    public void blankSpinnerReference()
    {
        mReasonSpinnerRef = null;
    }

    private void updateSpinnerOptions()
    {
        // The data fetched from the server is used to populate the list of reasons,
        // so it needs to be updated after every update, including the initial loading.
        // A blank option is included, which equates to not providing a reason. This
        // will line up with a null in the checkstock request parameters
        try {
            if (mReasonSpinnerRef != null) {
                String startingValue = (String) mReasonSpinnerRef.getSelectedItem();

                ArrayList<String> nameList = new ArrayList<>();
                for (Iterator<String> i = mReasonsMap.keySet().iterator(); i.hasNext(); )
                    nameList.add(i.next());
                Collections.sort(nameList);
                ArrayAdapter<String> adapter =
                        new ArrayAdapter<>(mContextRef, android.R.layout.simple_spinner_item, nameList);
                adapter.insert("Unspecified", 0);
                adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                mReasonSpinnerRef.setAdapter(adapter);

                if (nameList.contains(startingValue))
                {
                    for(int i = 0; i < adapter.getCount(); i++)
                    {
                        if(adapter.getItem(i).equals(startingValue))
                        {
                            mReasonSpinnerRef.setSelection(i);
                            break;
                        }
                    }
                }
                else
                    mReasonSpinnerRef.setSelection(0);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
