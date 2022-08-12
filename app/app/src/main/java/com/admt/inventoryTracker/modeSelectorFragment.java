package com.admt.inventoryTracker;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

public class modeSelectorFragment extends Fragment {

    public interface onModeSelectedListener
    {
        void onAddStockModeSelected();
        void onCheckItemsModeSelected();
    }

    private onModeSelectedListener mOnModeSelectedCallback;

    public modeSelectorFragment() {
        // Required empty public constructor
    }

    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        MainActivity mainActivity = (MainActivity)getActivity();
        mOnModeSelectedCallback = (onModeSelectedListener)mainActivity;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        Button addStockBtn = (Button)getView().findViewById(R.id.btnAddStockMode);
        addStockBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mOnModeSelectedCallback.onAddStockModeSelected();
            }
        });

        Button checkItemsBtn = (Button)getView().findViewById(R.id.btnCheckItemsMode);
        checkItemsBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mOnModeSelectedCallback.onCheckItemsModeSelected();
            }
        });
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        return inflater.inflate(R.layout.fragment_mode_selector, container, false);
    }
}