#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
📊 Генерация интерактивного дашборда из daily_metrics.csv
Для проекта: Online Retail ETL Pipeline
Выход: reports/retail_dashboard.html
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Глобальные настройки для всех графиков
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#C73E1D']

load_dotenv()

# Пути
REPORT_PATH = os.getenv("REPORT_OUTPUT_PATH", "./reports/daily_metrics.csv")
OUTPUT_HTML = os.getenv("DASHBOARD_OUTPUT", "./reports/retail_dashboard.html")


def load_data(path: str, days: int = None) -> pd.DataFrame:
    """Загрузка и фильтрация данных за последние N дней"""
    df = pd.read_csv(path, parse_dates=['order_date'])
    
    # Фильтрация по датам, если указан параметр days
    if days and 'order_date' in df.columns:
        max_date = df['order_date'].max()
        df = df[df['order_date'] >= max_date - pd.Timedelta(days=days)].copy()
        print(f"📅 Показываем данные за последние {days} дней ({df['order_date'].min().date()} — {max_date.date()})")
        
    assert 'daily_revenue' in df.columns, "❌ Отсутствует столбец 'daily_revenue'"
    assert 'country' in df.columns, "❌ Отсутствует столбец 'country'"
    print(f"✅ Загружено {len(df)} строк")
    return df


def create_revenue_trend(df: pd.DataFrame) -> go.Figure:
    """📈 Динамика выручки — непрерывная линия с маркерами"""
    # 1. Агрегация по дате (суммируем выручку по всем странам за каждый день)
    df_daily = df.groupby('order_date', as_index=False)['daily_revenue'].sum()
    
    # 2. Сортируем строго по дате и сбрасываем индекс
    df_daily = df_daily.sort_values('order_date').reset_index(drop=True)
    
    # 3. Скользящее среднее (сглаживает шум)
    df_daily['revenue_ma7'] = df_daily['daily_revenue'].rolling(7, min_periods=1).mean()
    
    # 4. Основной график: линия + маркеры
    fig = px.line(
        df_daily,
        x='order_date',
        y='daily_revenue',
        title='📈 Daily Revenue',
        labels={'daily_revenue': 'Revenue (£)', 'order_date': 'Date'},
        markers=True,
        line_shape='linear',
        color_discrete_sequence=['#2E86AB']
    )

    # 5. Стилизация основной линии ДО добавления MA7
    fig.update_traces(
        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Revenue: £%{y:,.0f}<extra></extra>',
        line=dict(width=2.5),
        marker=dict(size=9, line=dict(width=2, color='white')) 
    )
    
    # 6. Скользящее среднее (пунктир, без маркеров)
    fig.add_scatter(
        x=df_daily['order_date'],
        y=df_daily['revenue_ma7'],
        mode='lines',
        name='7-day MA',
        line=dict(color='#A23B72', width=2.5, dash='dash'),
        showlegend=True,
        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>7-day MA: £%{y:,.0f}<extra></extra>'
    )
    
    # 7. Настройка осей и поведения
    fig.update_layout(
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True, gridcolor='#eee', gridwidth=1,
            tickformat='%d.%m.%Y', tickangle=45, tickfont=dict(size=10)
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#eee', gridwidth=1,
            tickprefix='£', tickformat=',.0f', tickfont=dict(size=11),
            rangemode='tozero'
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=50, r=30, t=60, b=80),
        height=400
    )
    
    return fig


def create_country_revenue(df: pd.DataFrame) -> go.Figure:
    """🌍 Выручка по странам — контрастная шкала + читаемость"""
    country_rev = df.groupby('country')['daily_revenue'].sum().nlargest(10).reset_index()
    
    custom_scale = [
        (0.0, '#FFEB3B'),   
        (0.25, '#CDDC39'),  
        (0.5, '#8BC34A'),   
        (0.75, '#4CAF50'), 
        (1.0, '#2E7D32')    
    ]
    
    fig = px.bar(
        country_rev, 
        x='daily_revenue', 
        y='country', 
        orientation='h',
        title='🌍 Top 10 Countries by Revenue',
        labels={'daily_revenue': 'Revenue (£)', 'country': 'Country'},
        color='daily_revenue', 
        color_continuous_scale=custom_scale,
        color_continuous_midpoint=country_rev['daily_revenue'].median()
    )
    
    fig.update_layout(
        template='plotly_white',
        showlegend=False,
        # ✅ Исправлено: убран titleside, добавлена читаемая цветовая шкала
        coloraxis_colorbar=dict(
            title='Revenue (£)', 
            thickness=25,      # ✅ Толще шкала
            len=0.6,           # ✅ Короче, чтобы не перекрывать график
            tickformat=',.0f', # ✅ Формат чисел с разделителями
            ticks='outside'    # ✅ Риски снаружи
        ),
        yaxis=dict(
            autorange='reversed',  # Топ-1 сверху
            tickfont=dict(size=11, color='#222', family='Segoe UI'),
            showgrid=True, gridcolor='#f0f0f0', gridwidth=1
        ),
        xaxis=dict(
            tickprefix='£', 
            tickformat=',.0f', 
            tickfont=dict(size=10, family='Segoe UI'),
            showgrid=True, gridcolor='#eee', gridwidth=1,
            zeroline=True, zerolinecolor='#ddd'
        ),
        margin=dict(l=130, r=50, t=50, b=40),  
        height=420,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_traces(
        texttemplate='£%{x:,.0f}', 
        textposition='outside',
        textfont=dict(size=10, color='#111', family='Segoe UI', weight='bold'),
        hovertemplate='<b>%{y}</b><br>Revenue: £%{x:,.0f}<extra></extra>',
        marker=dict(line=dict(width=1, color='white'))  # ✅ Белая обводка столбцов
    )
    
    return fig


def create_aov_trend(df: pd.DataFrame) -> go.Figure:
    """🛒 AOV — средневзвешенное по всем странам за каждый день"""
    # Агрегация: взвешенное среднее AOV (по выручке) по странам за каждый день
    df_daily = df.groupby('order_date').apply(
        lambda g: (g['daily_revenue'].sum() / g['unique_customers'].replace(0, 1).sum())
                  if g['unique_customers'].sum() > 0 else g['avg_order_value'].mean(),
        include_groups=False
    ).reset_index(name='avg_order_value')
    df_daily = df_daily.sort_values('order_date').reset_index(drop=True)
    
    fig = px.line(
        df_daily, 
        x='order_date', 
        y='avg_order_value',
        title='🛒 Average Order Value',
        labels={'avg_order_value': 'AOV (£)', 'order_date': 'Date'},
        markers=False,
        line_shape='linear',
        color_discrete_sequence=['#06A77D']
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(
            tickformat='%d.%m', tickangle=45, tickfont=dict(size=10),
            showgrid=True, gridcolor='#eee'
        ),
        yaxis=dict(
            tickprefix='£', tickformat='.2f', tickfont=dict(size=11),
            showgrid=True, gridcolor='#eee', 
            rangemode='normal'
        ),
        margin=dict(l=50, r=30, t=50, b=80),
        height=350
    )
    
    fig.update_traces(
        line=dict(width=2),
        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>AOV: £%{y:.2f}<extra></extra>'
    )
    return fig


def create_customer_activity(df: pd.DataFrame) -> go.Figure:
    """👥 Клиенты — area chart с агрегацией по дате"""
    # Агрегация: суммируем уникальных клиентов по всем странам за каждый день
    df_daily = df.groupby('order_date', as_index=False)['unique_customers'].sum()
    df_daily = df_daily.sort_values('order_date').reset_index(drop=True)
    
    fig = px.area(
        df_daily, 
        x='order_date', 
        y='unique_customers',
        title='👥 Daily Unique Customers',
        labels={'unique_customers': 'Customers', 'order_date': 'Date'},
        color_discrete_sequence=['#F18F01']
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(
            tickformat='%d.%m', tickangle=45, tickfont=dict(size=10),
            showgrid=True, gridcolor='#eee'
        ),
        yaxis=dict(
            tickfont=dict(size=11), 
            showgrid=True, gridcolor='#eee',
            rangemode='tozero'
        ),
        margin=dict(l=50, r=30, t=50, b=80),
        height=350
    )
    
    fig.update_traces(
        fillcolor='rgba(241, 143, 1, 0.2)',
        line=dict(color='#F18F01', width=2.5),
        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Customers: %{y:,.0f}<extra></extra>'
    )
    return fig


def create_summary_metrics(df: pd.DataFrame) -> str:
    """📋 Генерация HTML-блока с ключевыми метриками"""
    # Агрегация по датам для корректных метрик
    df_daily = df.groupby('order_date', as_index=False).agg({
        'daily_revenue': 'sum',
        'unique_customers': 'sum'
    })
    total_revenue = df_daily['daily_revenue'].sum()
    avg_daily_revenue = df_daily['daily_revenue'].mean()
    # Взвешенный AOV: общая выручка / общее кол-во клиентов
    total_customers = df_daily['unique_customers'].sum()
    avg_aov = total_revenue / total_customers if total_customers > 0 else 0
    countries_count = df['country'].nunique()
    
    return f"""
    <div class="metrics-grid">
        <div class="metric-card blue">
            <div class="metric-value">£{total_revenue:,.0f}</div>
            <div class="metric-label">Total Revenue</div>
        </div>
        <div class="metric-card purple">
            <div class="metric-value">£{avg_daily_revenue:,.0f}</div>
            <div class="metric-label">Avg Daily Revenue</div>
        </div>
        <div class="metric-card green">
            <div class="metric-value">£{avg_aov:.2f}</div>
            <div class="metric-label">Avg Order Value</div>
        </div>
        <div class="metric-card orange">
            <div class="metric-value">{countries_count}</div>
            <div class="metric-label">Countries</div>
        </div>
    </div>
    """


def generate_dashboard(input_csv: str, output_html: str, days: int = None):
    """🚀 Основная функция генерации дашборда"""
    print(f"🔍 Loading data from {input_csv}...")
    df = load_data(input_csv, days=days)
    print("🎨 Creating visualizations...")
    
    fig_revenue = create_revenue_trend(df)
    fig_country = create_country_revenue(df)
    fig_aov = create_aov_trend(df)
    fig_customers = create_customer_activity(df)
    summary_html = create_summary_metrics(df)
    
    # ✅ Настройка шрифтов (перемещено ВНУТРЬ функции, после создания фигур)
    font_cfg = dict(family='Segoe UI, Arial, sans-serif', size=12)
    fig_revenue.update_layout(font=font_cfg)
    fig_country.update_layout(font=font_cfg)
    fig_aov.update_layout(font=font_cfg)
    fig_customers.update_layout(font=font_cfg)
    
    # Сохраняем полный дашборд
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Online Retail Dashboard</title>
    <!-- Plotly JS загружается один раз через первый график -->
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #fafafa; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 25px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .header h1 {{ margin: 0 0 5px 0; font-size: 24px; }}
        .header p {{ margin: 0; color: #666; font-size: 14px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; }}
        .metric-card {{ background: white; padding: 18px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid; }}
        .metric-card.blue {{ border-left-color: #2E86AB; }} .metric-card.purple {{ border-left-color: #A23B72; }}
        .metric-card.green {{ border-left-color: #06A77D; }} .metric-card.orange {{ border-left-color: #F18F01; }}
        .metric-value {{ font-size: 26px; font-weight: 700; margin: 5px 0; }}
        .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(650px, 1fr)); gap: 20px; margin-top: 20px; }}
        .chart-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 3px 12px rgba(0,0,0,0.1); }}
        @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} .metric-card {{ padding: 14px; }} .metric-value {{ font-size: 22px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 Online Retail Analytics</h1>
            <p style="color: #666;">Automated ETL Pipeline • Data updated daily</p>
        </div>
        {summary_html}
        <div class="charts-grid">
            <div class="chart-card">{fig_revenue.to_html(full_html=False, include_plotlyjs='cdn')}</div>
            <div class="chart-card">{fig_country.to_html(full_html=False, include_plotlyjs=False)}</div>
            <div class="chart-card">{fig_aov.to_html(full_html=False, include_plotlyjs=False)}</div>
            <div class="chart-card">{fig_customers.to_html(full_html=False, include_plotlyjs=False)}</div>
        </div>
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            Generated by Online Retail ETL Pipeline • <a href="https://github.com/your-username/online-retail-etl" target="_blank">View Code</a>
        </div>
    </div>
</body>
</html>""")
    print(f"✅ Dashboard saved to {output_html}")
    print(f"🔗 Open in browser: file:///{os.path.abspath(output_html)}")
    return output_html


if __name__ == "__main__":
    load_dotenv()
    days = int(os.getenv("DASHBOARD_DAYS", 0)) or None  # 0 = все данные
    generate_dashboard(REPORT_PATH, OUTPUT_HTML, days=days)