import pandas as pd

def reconcile(declared_quantities: dict, erp_df: pd.DataFrame) -> list:
    """
    Reconciles declared quantities against ERP procurement records.
    Ensures division-by-zero protection and handles missing categories.
    """
    results = []
    
    categories = ["rigid_plastic", "flexible_plastic", "multilayer_plastic"]
    
    for category in categories:
        declared_value = float(declared_quantities.get(category, 0.0))
        
        row = erp_df[erp_df["category"] == category]
        
        if row.empty:
            procured_value = 0.0
        else:
            procured_value = float(row.iloc[0]["procured_kg"])
            
        if procured_value == 0.0:
            difference_percent = 100.0 if declared_value > 0.0 else 0.0
        else:
            difference_percent = (abs(declared_value - procured_value) / procured_value) * 100
            
        results.append({
            "category": category,
            "declared_kg": declared_value,
            "procured_kg": procured_value,
            "difference_percent": round(difference_percent, 2),
            "flagged": difference_percent > 5.0
        })
        
    return results