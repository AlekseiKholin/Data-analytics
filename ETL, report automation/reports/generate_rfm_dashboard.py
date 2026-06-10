#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
📊 Генерация интерактивного дашборда для RFM-сегментации
Вход: 
  - reports/rfm_segment_summary.csv   (агрегация по сегментам)
  - reports/rfm_customer_scatter.csv  (данные на уровне клиента)
Выход: reports/rfm_dashboard.html
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
from dotenv import load_dotenv

# Глобальные настройки
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#C73E1D']

load_dotenv()

# Пути
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
SUMMARY_PATH = os.getenv("RFM_SUMMARY_PATH", os.path.join(REPORTS_DIR, "rfm_segment_summary.csv"))
SCATTER_PATH = os.getenv("RFM_SCATTER_PATH", os.path.join(REPORTS_DIR, "rfm_customer_scatter.csv"))
OUTPUT_HTML = os.getenv("RFM_DASHBOARD_OUTPUT", os.path.join(REPORTS_DIR, "rfm_dashboard.html"))

# Цветовая карта сегментов (единая для всех графиков)
SEGMENT_COLORS = {
    'Champions': '#2E7D32',  # тёмно-зелёный
    'Loyal': '#4CAF50',      # зелёный
    'Recent': '#FFEB3B',     # жёлтый
    'At Risk': '#F44336',    # красный
    'Regular': '#9E9E9E'     # серый
}


# =============================================================================
# 🔹 ФУНКЦИИ ВИЗУАЛИЗАЦИИ
# =============================================================================

def create_segment_pie(df_summary: pd.DataFrame) -> go.Figure:
    """🥧 Pie Chart: Доля клиентов по сегментам"""
    fig = px.pie(
        df_summary,
        names='rfm_segment',
        values='customer_count',
        title='🥧 Distribution by Segment (Customers)',
        color='rfm_segment',
        color_discrete_map=SEGMENT_COLORS,
        hole=0.4  # Donut chart
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Clients: %{value:,}<br>Percent: %{percent:.1%}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_segment_bar(df_summary: pd.DataFrame) -> go.Figure:
    """📊 Bar Chart: Выручка по сегментам"""
    fig = px.bar(
        df_summary.sort_values('total_monetary', ascending=False),
        x='rfm_segment',
        y='total_monetary',
        title='💰 Total Revenue by Segment',
        labels={'rfm_segment': 'Segment', 'total_monetary': 'Revenue (£)'},
        color='rfm_segment',
        color_discrete_map=SEGMENT_COLORS,
        text_auto='.2s'
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_tickangle=-45,
        xaxis_title='',
        yaxis_tickprefix='£',
        yaxis_tickformat=',.0f',
        height=400,
        margin=dict(l=50, r=30, t=50, b=80)
    )
    
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Revenue: £%{y:,.0f}<extra></extra>'
    )
    return fig


def create_kpi_cards(df_summary: pd.DataFrame) -> str:
    """📋 HTML-блок с ключевыми метриками по сегментам"""
    total_customers = df_summary['customer_count'].sum()
    total_revenue = df_summary['total_monetary'].sum()
    champions_pct = df_summary[df_summary['rfm_segment'] == 'Champions']['customer_count'].sum() / total_customers * 100
    at_risk_pct = df_summary[df_summary['rfm_segment'] == 'At Risk']['customer_count'].sum() / total_customers * 100
    
    return f"""
    <div class="metrics-grid">
        <div class="metric-card blue">
            <div class="metric-value">{total_customers:,}</div>
            <div class="metric-label">Total Customers</div>
        </div>
        <div class="metric-card purple">
            <div class="metric-value">£{total_revenue:,.0f}</div>
            <div class="metric-label">Total Revenue</div>
        </div>
        <div class="metric-card green">
            <div class="metric-value">{champions_pct:.1f}%</div>
            <div class="metric-label">Champions Share</div>
        </div>
        <div class="metric-card orange">
            <div class="metric-value">{at_risk_pct:.1f}%</div>
            <div class="metric-label">At Risk Share</div>
        </div>
    </div>
    """


def create_scatter_plot(df_scatter: pd.DataFrame) -> go.Figure:
    """🔍 Scatter: Frequency vs Monetary, colored by segment"""
    # Ограничиваем выбросы для лучшей визуализации (опционально)
    df_viz = df_scatter.copy()
    monetary_limit = df_viz['monetary'].quantile(0.99)
    df_viz = df_viz[df_viz['monetary'] <= monetary_limit].copy()
    
    fig = px.scatter(
        df_viz,
        x='frequency',
        y='monetary',
        color='rfm_segment',
        color_discrete_map=SEGMENT_COLORS,
        title='🔍 Customer Behavior: Frequency vs Monetary',
        labels={
            'frequency': 'Order Frequency',
            'monetary': 'Total Spent (£)',
            'rfm_segment': 'Segment'
        },
        hover_data=['customer_id', 'country', 'recency_days'],
        opacity=0.7
    )
    
    fig.update_layout(
        hovermode='closest',
        legend_title='Segment',
        xaxis=dict(title='Orders', showgrid=True, gridcolor='#eee'),
        yaxis=dict(title='Spent (£)', tickprefix='£', tickformat=',.0f', showgrid=True, gridcolor='#eee'),
        height=500,
        margin=dict(l=50, r=30, t=50, b=50)
    )
    
    fig.update_traces(
        marker=dict(size=8, line=dict(width=0.5, color='white')),
        hovertemplate='<b>Customer %{hoverdata[0]}</b><br>Country: %{hoverdata[1]}<br>Orders: %{x}<br>Spent: £%{y:,.0f}<br>Recency: %{hoverdata[2]} days<extra></extra>'
    )
    return fig


def create_recency_histogram(df_scatter: pd.DataFrame) -> go.Figure:
    """📅 Histogram: Distribution of Recency Days by Segment"""
    fig = px.histogram(
        df_scatter,
        x='recency_days',
        color='rfm_segment',
        color_discrete_map=SEGMENT_COLORS,
        title='📅 Recency Distribution by Segment',
        labels={'recency_days': 'Days Since Last Order', 'count': 'Customers'},
        barmode='overlay',
        opacity=0.7,
        nbins=30
    )
    
    fig.update_layout(
        hovermode='x unified',
        legend_title='Segment',
        xaxis=dict(title='Recency (days)', showgrid=True, gridcolor='#eee'),
        yaxis=dict(title='Customers', showgrid=True, gridcolor='#eee'),
        height=400,
        margin=dict(l=50, r=30, t=50, b=50)
    )
    
    fig.update_traces(
        hovertemplate='<b>%{x} days</b><br>Customers: %{y}<extra></extra>'
    )
    return fig


def generate_insights_text(df_summary: pd.DataFrame, df_scatter: pd.DataFrame) -> str:
    """Генерирует Markdown-отчёт с бизнес-инсайтами"""
    total_customers = df_summary['customer_count'].sum()
    total_revenue = df_summary['total_monetary'].sum()
    
    champions = df_summary[df_summary['rfm_segment'] == 'Champions']
    at_risk = df_summary[df_summary['rfm_segment'] == 'At Risk']
    
    c_cust = champions['customer_count'].sum() if not champions.empty else 0
    c_rev = champions['total_monetary'].sum() if not champions.empty else 0
    a_cust = at_risk['customer_count'].sum() if not at_risk.empty else 0
    a_rev = at_risk['total_monetary'].sum() if not at_risk.empty else 0
    
    c_cust_pct = (c_cust / total_customers * 100) if total_customers else 0
    c_rev_pct = (c_rev / total_revenue * 100) if total_revenue else 0
    a_cust_pct = (a_cust / total_customers * 100) if total_customers else 0
    a_rev_pct = (a_rev / total_revenue * 100) if total_revenue else 0
    
    pareto = "✅ Подтверждён принцип Парето: >50% выручки от <20% клиентов" if c_rev_pct > 50 else "⚠️ Выручка распределена равномерно, фокус на удержание"
    churn_alert = "🚨 Критический риск оттока: требуется срочная реактивация" if a_cust_pct > 30 else "✅ Уровень оттока в пределах нормы"
    
    return f"""# 🎯 RFM Segmentation Insights Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## 📊 Key Metrics
- Total Customers: `{total_customers:,}`
- Total Revenue: `£{total_revenue:,.0f}`
- Avg Revenue/Customer: `£{total_revenue/total_customers:,.2f}`

## 🏆 Champions (Top Clients)
- Share of Customers: `{c_cust_pct:.1f}%`
- Share of Revenue: `{c_rev_pct:.1f}%`
- `{pareto}`

## ⚠️ At Risk Clients
- Share of Customers: `{a_cust_pct:.1f}%`
- Share of Revenue: `£{a_rev:,.0f} ({a_rev_pct:.1f}%)`
- `{churn_alert}`

## 💡 Strategic Recommendations
1. Focus `{c_rev_pct:.0f}%` of marketing budget on retaining Champions.
2. Launch targeted reactivation campaigns for `{a_cust:,} At-Risk` customers.
3. Implement loyalty program for Loyal & Recent segments to boost frequency.
4. Monitor recency distribution weekly to catch churn early.

---
*Generated automatically by Online Retail ETL Pipeline*
"""

# =============================================================================
# 🔹 ОСНОВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ
# =============================================================================

def generate_rfm_dashboard(
    summary_path: str,
    scatter_path: str,
    output_html: str
):
    """🚀 Генерация полного дашборда RFM"""
    
    # 🔹 Загрузка данных
    print(f"🔍 Loading RFM data...")
    
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"❌ Not found: {summary_path}")
    if not os.path.exists(scatter_path):
        raise FileNotFoundError(f"❌ Not found: {scatter_path}")
    
    df_summary = pd.read_csv(summary_path)
    df_scatter = pd.read_csv(scatter_path)
    
    print(f"✅ Summary: {len(df_summary)} segments")
    print(f"✅ Scatter: {len(df_scatter):,} customers")
    
    # 🔹 Создание визуализаций
    print("🎨 Creating visualizations...")
    
    fig_pie = create_segment_pie(df_summary)
    fig_bar = create_segment_bar(df_summary)
    fig_scatter = create_scatter_plot(df_scatter)
    fig_recency = create_recency_histogram(df_scatter)
    kpi_html = create_kpi_cards(df_summary)
    
    # 🔹 Применение единого стиля шрифтов
    font_cfg = dict(family='Segoe UI, Arial, sans-serif', size=12)
    for fig in [fig_pie, fig_bar, fig_scatter, fig_recency]:
        fig.update_layout(font=font_cfg)
    
    # 🔹 Генерация HTML
# 🔹 Подготовка инсайтов для встраивания в JS
    insights_md = generate_insights_text(df_summary, df_scatter)
    insights_js = json.dumps(insights_md)  # Безопасное экранирование для JS

    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFM Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 20px; background: #fafafa; color: #333;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ 
            text-align: center; margin-bottom: 25px; padding: 15px; 
            background: white; border-radius: 10px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;
        }}
        .header h1 {{ margin: 0; font-size: 24px; text-align: left; }}
        .header p {{ margin: 5px 0 0; color: #666; font-size: 14px; text-align: left; }}
        
        /* ✅ Стили кнопки экспорта */
        .export-btn {{
            background: #2E7D32; color: white; border: none; padding: 10px 20px;
            border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;
            transition: all 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            white-space: nowrap;
        }}
        .export-btn:hover {{ background: #1B5E20; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .export-btn:active {{ transform: translateY(0); }}
        
        .metrics-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
            gap: 12px; margin: 20px 0; 
        }}
        .metric-card {{ 
            background: white; padding: 18px; border-radius: 10px; 
            text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid;
        }}
        .metric-card.blue {{ border-left-color: #2E86AB; }}
        .metric-card.purple {{ border-left-color: #A23B72; }}
        .metric-card.green {{ border-left-color: #06A77D; }}
        .metric-card.orange {{ border-left-color: #F18F01; }}
        .metric-value {{ font-size: 26px; font-weight: 700; margin: 5px 0; }}
        .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        .charts-grid {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto auto;
            gap: 20px; 
            margin-top: 20px; 
        }}
        .chart-card {{ 
            background: white; border-radius: 12px; padding: 20px; 
            box-shadow: 0 3px 12px rgba(0,0,0,0.1); 
            min-height: 420px;
        }}
        .chart-card.full {{ grid-column: 1 / -1; min-height: 520px; }}
        
        @media (max-width: 1024px) {{ 
            .charts-grid {{ grid-template-columns: 1fr; }}
            .chart-card {{ min-height: 380px; }}
            .chart-card.full {{ min-height: 500px; }}
        }}
        @media (max-width: 768px) {{ 
            .header {{ flex-direction: column; align-items: flex-start; }}
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .metric-card {{ padding: 14px; }}
            .metric-value {{ font-size: 22px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🎯 RFM Customer Segmentation</h1>
                <p>Recency • Frequency • Monetary Analysis</p>
            </div>
            <!-- ✅ КНОПКА ЭКСПОРТА -->
            <button class="export-btn" onclick="downloadInsights()">📥 Export Insights</button>
        </div>
        
        {kpi_html}
        
        <div class="charts-grid">
            <div class="chart-card">{fig_pie.to_html(full_html=False, include_plotlyjs='cdn')}</div>
            <div class="chart-card">{fig_bar.to_html(full_html=False, include_plotlyjs='cdn')}</div>
            <div class="chart-card full">{fig_scatter.to_html(full_html=False, include_plotlyjs='cdn')}</div>
            <div class="chart-card full">{fig_recency.to_html(full_html=False, include_plotlyjs='cdn')}</div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            Generated by RFM Analytics Pipeline • 
            <a href="https://github.com/your-username/online-retail-etl" target="_blank">View Code</a>
        </div>
    </div>

    <script>
        // ✅ Данные инсайтов встраиваются безопасно через json.dumps
        const INSIGHTS_MARKDOWN = {insights_js};
        
        function downloadInsights() {{
            const blob = new Blob([INSIGHTS_MARKDOWN], {{ type: 'text/markdown;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'rfm_insights.md';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            // Визуальный фидбек
            const btn = document.querySelector('.export-btn');
            const originalText = btn.textContent;
            btn.textContent = '✅ Downloaded!';
            btn.style.background = '#06A77D';
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.style.background = '#2E7D32';
            }}, 2000);
        }}
    </script>
</body>
</html>""")
    
    print(f"✅ RFM Dashboard saved to {output_html}")
    print(f"🔗 Open in browser: file:///{os.path.abspath(output_html)}")
    return output_html


# =============================================================================
# 🔹 ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    try:
        generate_rfm_dashboard(SUMMARY_PATH, SCATTER_PATH, OUTPUT_HTML)
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        raise