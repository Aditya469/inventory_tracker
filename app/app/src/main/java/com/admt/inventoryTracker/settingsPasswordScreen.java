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

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

public class settingsPasswordScreen extends AppCompatActivity
{

    @Override
    protected void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings_password_screen);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        
        EditText tbPassword = (EditText)findViewById(R.id.etPassword);

        tbPassword.setOnEditorActionListener(new TextView.OnEditorActionListener() {
            @Override
            public boolean onEditorAction(TextView v, int actionId, KeyEvent event) {
                if ((event != null && (event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) || (actionId == EditorInfo.IME_ACTION_DONE)) {
                    return submitPassword();
                }
                return false;
            }
        });
    }

    public void onOkBtnPress(View view)
    {
        submitPassword();
    }

    private boolean submitPassword(){
        boolean successResult = false;

        SharedPreferences prefs = getSharedPreferences(getString(R.string.prefs_file_key),
                Context.MODE_PRIVATE);

        EditText tbPassword = (EditText)findViewById(R.id.etPassword);
        String enteredPassword = tbPassword.getText().toString();
        String storedPassword = prefs.getString(
                getString(R.string.prefs_settings_password),"1234");

        if(enteredPassword.equals(storedPassword))
        {
            successResult = true;
            Intent intent = new Intent(this, settings_page.class);
            startActivity(intent);
        }
        else
        {
            successResult = false;
            tbPassword.setText("");
            Toast.makeText(getApplicationContext(),"Password incorrect",Toast.LENGTH_SHORT)
                    .show();
        }

        return successResult;
    }
}
