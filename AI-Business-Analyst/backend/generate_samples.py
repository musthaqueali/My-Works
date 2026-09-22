import pandas as pd
import numpy as np

def generate_all():
    np.random.seed(42)

    # 1. E-Commerce & Retail Sales
    dates = pd.date_range(start='2023-01-01', end='2024-06-30', freq='D')
    regions = ['North', 'South', 'East', 'West', 'Central']
    products = ['Enterprise Pro', 'Standard Plus', 'Starter Lite', 'Hardware Terminal', 'Accessories Kit']
    categories = {'Enterprise Pro': 'Software', 'Standard Plus': 'Software', 'Starter Lite': 'Software', 'Hardware Terminal': 'Hardware', 'Accessories Kit': 'Supplies'}
    segments = ['Enterprise', 'Mid-Market', 'Small Business', 'Consumer']
    channels = ['Direct Sales', 'Online Store', 'Partner Reseller', 'Inside Sales']

    rows = []
    for i in range(1200):
        dt = np.random.choice(dates)
        dt_str = pd.to_datetime(dt).strftime('%Y-%m-%d')
        reg = np.random.choice(regions, p=[0.25, 0.20, 0.18, 0.22, 0.15])
        prod = np.random.choice(products, p=[0.22, 0.30, 0.25, 0.13, 0.10])
        cat = categories[prod]
        seg = np.random.choice(segments, p=[0.20, 0.35, 0.30, 0.15])
        chan = np.random.choice(channels)
        base_price = {'Enterprise Pro': 1200, 'Standard Plus': 450, 'Starter Lite': 150, 'Hardware Terminal': 850, 'Accessories Kit': 65}[prod]
        
        discount = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.4, 0.25, 0.2, 0.1, 0.05])
        if reg == 'South' and prod == 'Enterprise Pro' and pd.to_datetime(dt) >= pd.Timestamp('2023-09-01'):
            qty = max(1, np.random.poisson(lam=2))
            unit_price = base_price * 1.25
            cost = base_price * 0.55
        else:
            qty = max(1, np.random.poisson(lam=5))
            unit_price = base_price * (1 + np.random.uniform(-0.05, 0.05))
            cost = base_price * 0.50
            
        revenue = round(qty * unit_price * (1 - discount), 2)
        total_cost = round(qty * cost, 2)
        profit = round(revenue - total_cost, 2)
        margin_pct = round((profit / revenue * 100) if revenue > 0 else 0, 1)
        satisfaction = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.08, 0.17, 0.40, 0.30])
        
        rows.append({
            'order_id': f'ORD-{10000 + i}',
            'order_date': dt_str,
            'customer_id': f'CUST-{np.random.randint(100, 999)}',
            'region': reg,
            'customer_segment': seg,
            'channel': chan,
            'category': cat,
            'product': prod,
            'unit_price': round(unit_price, 2),
            'quantity': qty,
            'discount_pct': round(discount * 100, 1),
            'revenue': revenue,
            'cost': total_cost,
            'profit': profit,
            'gross_margin_pct': margin_pct,
            'customer_rating': satisfaction
        })

    df_sales = pd.DataFrame(rows)
    df_sales.loc[15:18, 'customer_rating'] = np.nan
    df_sales.loc[45:47, 'discount_pct'] = np.nan
    df_sales = pd.concat([df_sales, df_sales.iloc[[10, 25]]], ignore_index=True)
    df_sales.to_csv('data/ecommerce_sales_performance.csv', index=False)
    print('Generated data/ecommerce_sales_performance.csv with', len(df_sales), 'rows')

    # 2. SaaS Subscription & Churn
    saas_rows = []
    tiers = ['Free', 'Basic', 'Professional', 'Enterprise']
    industries = ['Fintech', 'Healthcare', 'E-commerce', 'EdTech', 'Manufacturing']
    for i in range(850):
        tier = np.random.choice(tiers, p=[0.15, 0.35, 0.35, 0.15])
        mrr = {'Free': 0, 'Basic': 49, 'Professional': 199, 'Enterprise': 999}[tier]
        if mrr > 0:
            mrr = round(mrr * (1 + np.random.uniform(-0.1, 0.15)), 2)
        tenure_months = int(np.random.randint(1, 36))
        nps = int(np.random.randint(1, 11))
        logins_per_week = int(np.random.poisson(lam=12 if tier in ['Professional', 'Enterprise'] else 4))
        support_tickets = int(np.random.poisson(lam=3 if nps < 6 else 1))
        
        churn_prob = 0.05
        if nps < 5: churn_prob += 0.35
        if support_tickets > 4: churn_prob += 0.25
        if logins_per_week < 3: churn_prob += 0.30
        if tier == 'Basic': churn_prob += 0.10
        churned = 'Yes' if np.random.random() < min(0.9, churn_prob) else 'No'
        
        cac = round(float(np.random.uniform(200, 1500)), 2)
        ltv = round(float(mrr * tenure_months), 2)
        signup_dt = (pd.Timestamp('2024-01-01') - pd.Timedelta(days=tenure_months*30)).strftime('%Y-%m-%d')
        
        saas_rows.append({
            'account_id': f'ACCT-{20000 + i}',
            'signup_date': signup_dt,
            'plan_tier': tier,
            'industry': np.random.choice(industries),
            'mrr': mrr,
            'arr': round(mrr * 12, 2),
            'tenure_months': tenure_months,
            'weekly_logins': logins_per_week,
            'support_tickets_30d': support_tickets,
            'nps_score': nps,
            'customer_acquisition_cost': cac,
            'lifetime_value': ltv,
            'ltv_to_cac_ratio': round(ltv / max(1.0, cac), 2),
            'churn_status': churned
        })

    df_saas = pd.DataFrame(saas_rows)
    df_saas.to_csv('data/saas_subscription_churn.csv', index=False)
    print('Generated data/saas_subscription_churn.csv with', len(df_saas), 'rows')

    # 3. Supply Chain & Inventory
    inv_rows = []
    warehouses = ['WH-North-Chicago', 'WH-South-Dallas', 'WH-East-Newark', 'WH-West-Reno']
    suppliers = ['Apex Logistics', 'Global Components', 'Pinnacle Fabricators', 'Vanguard Precision', 'Pacific Maritime']

    for i in range(650):
        sku = f'SKU-{30000 + i}'
        wh = np.random.choice(warehouses)
        sup = np.random.choice(suppliers)
        unit_cost = round(float(np.random.uniform(15, 650)), 2)
        stock_on_hand = int(np.random.randint(0, 1500))
        reorder_point = int(np.random.randint(100, 400))
        lead_time_days = max(2, int(np.random.normal(loc=14, scale=5)))
        holding_cost_annual = round(unit_cost * 0.18, 2)
        stock_turnover_rate = round(float(np.random.uniform(1.2, 9.5)), 2)
        defect_rate_pct = round(max(0.0, float(np.random.normal(loc=1.8, scale=1.2))), 2)
        
        status = 'Optimal'
        if stock_on_hand == 0: status = 'Stockout Risk'
        elif stock_on_hand < reorder_point: status = 'Low Stock'
        elif stock_turnover_rate < 2.0 and stock_on_hand > 800: status = 'Overstocked'
        elif defect_rate_pct > 4.5: status = 'Defective Quarantine'
        
        inv_rows.append({
            'sku_id': sku,
            'warehouse_location': wh,
            'primary_supplier': sup,
            'category': np.random.choice(['Electronics', 'Mechanical', 'Hydraulics', 'Fasteners', 'Packaging']),
            'units_in_stock': stock_on_hand,
            'reorder_threshold': reorder_point,
            'unit_purchase_cost': unit_cost,
            'total_inventory_value': round(stock_on_hand * unit_cost, 2),
            'lead_time_days': lead_time_days,
            'annual_holding_cost': holding_cost_annual,
            'inventory_turnover_ratio': stock_turnover_rate,
            'defect_rate_pct': defect_rate_pct,
            'stock_health_status': status
        })

    df_inv = pd.DataFrame(inv_rows)
    df_inv.to_csv('data/supply_chain_inventory.csv', index=False)
    print('Generated data/supply_chain_inventory.csv with', len(df_inv), 'rows')

if __name__ == '__main__':
    generate_all()
