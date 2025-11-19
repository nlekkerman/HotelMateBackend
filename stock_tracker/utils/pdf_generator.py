"""
PDF Report Generator for Stock Tracker
Generates formatted PDF reports for stocktakes and periods
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from decimal import Decimal
from datetime import datetime


def generate_stocktake_pdf(stocktake, include_variance=True):
    """
    Generate PDF report for a stocktake.
    
    Args:
        stocktake: Stocktake model instance
        include_variance: Include variance details (default: True)
    
    Returns:
        BytesIO: PDF file buffer
    """
    buffer = BytesIO()
    
    # Use landscape for better table display
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=50,
        bottomMargin=30
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title - Single line as requested
    title = Paragraph(
        f"<b>Stocktake Report - {stocktake.hotel.name}</b>",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Period Information
    period_data = [
        ['Period:', f"{stocktake.period_start} to {stocktake.period_end}"],
        ['Status:', stocktake.status],
        ['Created:', stocktake.created_at.strftime('%Y-%m-%d %H:%M')],
    ]
    
    if stocktake.approved_at:
        period_data.append([
            'Approved:',
            f"{stocktake.approved_at.strftime('%Y-%m-%d %H:%M')} by {stocktake.approved_by}"
        ])
    
    period_table = Table(period_data, colWidths=[2*inch, 4*inch])
    period_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary Totals
    lines = stocktake.lines.all()
    total_expected_value = sum(line.expected_value for line in lines)
    total_counted_value = sum(line.counted_value for line in lines)
    total_variance_value = sum(line.variance_value for line in lines)
    
    summary_heading = Paragraph("<b>Summary</b>", heading_style)
    elements.append(summary_heading)
    
    summary_data = [
        ['Total Items:', str(lines.count())],
        ['Expected Stock Value:', f"€{total_expected_value:,.2f}"],
        ['Counted Stock Value:', f"€{total_counted_value:,.2f}"],
        ['Variance:', f"€{total_variance_value:,.2f}"],
    ]
    
    # Add profitability metrics
    if stocktake.total_cogs:
        summary_data.extend([
            ['Total COGS:', f"€{stocktake.total_cogs:,.2f}"],
            ['Total Revenue:', f"€{stocktake.total_revenue:,.2f}" if stocktake.total_revenue else 'N/A'],
            ['GP%:', f"{stocktake.gross_profit_percentage}%" if stocktake.gross_profit_percentage else 'N/A'],
            ['Pour Cost%:', f"{stocktake.pour_cost_percentage}%" if stocktake.pour_cost_percentage else 'N/A'],
        ])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    
    # Apply colors: red for negative values
    summary_styles = [
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    
    # Apply red color to variance if negative
    if total_variance_value < 0:
        summary_styles.extend([
            ('TEXTCOLOR', (1, 3), (1, 3), colors.red),
            ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
        ])
    
    summary_table.setStyle(TableStyle(summary_styles))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Category Breakdown
    category_heading = Paragraph("<b>Category Totals</b>", heading_style)
    elements.append(category_heading)
    
    category_totals = stocktake.get_category_totals()
    
    category_table_data = [
        ['Category', 'Opening', 'Purchases', 'Expected', 'Counted', 'Variance', 'Value']
    ]
    
    # Build category table with color-coded variances
    row_num = 1  # Start after header
    variance_styles = []
    
    for cat_code in ['D', 'B', 'S', 'W', 'M']:
        if cat_code in category_totals:
            cat = category_totals[cat_code]
            category_table_data.append([
                f"{cat['category_name']}",
                f"{float(cat['opening_qty']):,.2f}",
                f"{float(cat['purchases']):,.2f}",
                f"{float(cat['expected_qty']):,.2f}",
                f"{float(cat['counted_qty']):,.2f}",
                f"{float(cat['variance_qty']):,.2f}",
                f"€{float(cat['variance_value']):,.2f}"
            ])
            
            # Add red color for negative variance quantity
            var_qty = float(cat['variance_qty'])
            if var_qty < 0:
                variance_styles.append(
                    ('TEXTCOLOR', (5, row_num), (5, row_num), colors.red)
                )
                variance_styles.append(
                    ('FONTNAME', (5, row_num), (5, row_num), 'Helvetica-Bold')
                )
            
            # Add red color for negative variance values
            var_value = float(cat['variance_value'])
            if var_value < 0:
                variance_styles.append(
                    ('TEXTCOLOR', (6, row_num), (6, row_num), colors.red)
                )
                variance_styles.append(
                    ('FONTNAME', (6, row_num), (6, row_num), 'Helvetica-Bold')
                )
            row_num += 1
    
    category_table = Table(
        category_table_data,
        colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 
                   1*inch, 1*inch, 1*inch]
    )
    
    # Base styles + variance colors
    base_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
         [colors.white, colors.HexColor('#f9f9f9')]),
    ]
    
    category_table.setStyle(TableStyle(base_styles + variance_styles))
    elements.append(category_table)
    
    # Keep Summary and Category Totals on first page - no page break yet
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed Line Items - Each category on new page
    # Group by category
    for cat_idx, cat_code in enumerate(['D', 'B', 'S', 'W', 'M']):
        cat_lines = [
            line for line in lines 
            if line.item.category.code == cat_code
        ]
        
        if not cat_lines:
            continue
        
        # Start each category on a NEW PAGE (as requested)
        elements.append(PageBreak())
        
        # Category header
        cat_name = {
            'D': 'Draught Beer',
            'B': 'Bottled Beer',
            'S': 'Spirits',
            'W': 'Wine',
            'M': 'Minerals & Syrups'
        }.get(cat_code, cat_code)
        
        cat_header = Paragraph(
            f"<b>{cat_name} - Detailed Items</b>", 
            heading_style
        )
        elements.append(cat_header)
        elements.append(Spacer(1, 0.1*inch))
        
        # Items table
        items_data = [
            ['SKU', 'Name', 'Opening', 'Purchases', 
             'Expected', 'Counted', 'Variance', 'Value €']
        ]
        
        # Track row numbers for variance coloring
        row_num = 1  # Start after header
        variance_styles = []
        
        for line in cat_lines:
            items_data.append([
                line.item.sku[:15],  # Truncate long SKUs
                line.item.name[:30],  # Truncate long names
                f"{float(line.opening_qty):,.1f}",
                f"{float(line.purchases):,.1f}",
                f"{float(line.expected_qty):,.1f}",
                f"{float(line.counted_qty):,.1f}",
                f"{float(line.variance_qty):,.1f}",
                f"€{float(line.variance_value):,.2f}"
            ])
            
            # Apply red color to negative variance quantity
            var_qty = float(line.variance_qty)
            if var_qty < 0:
                variance_styles.append(
                    ('TEXTCOLOR', (6, row_num), (6, row_num), colors.red)
                )
                variance_styles.append(
                    ('FONTNAME', (6, row_num), (6, row_num), 'Helvetica-Bold')
                )
            
            # Apply red color to negative variance values
            var_value = float(line.variance_value)
            if var_value < 0:
                variance_styles.append(
                    ('TEXTCOLOR', (7, row_num), (7, row_num), colors.red)
                )
                variance_styles.append(
                    ('FONTNAME', (7, row_num), (7, row_num), 'Helvetica-Bold')
                )
            row_num += 1
        
        items_table = Table(
            items_data,
            colWidths=[0.8*inch, 2*inch, 0.7*inch, 0.8*inch, 
                       0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch]
        )
        
        # Base styles
        base_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#f9f9f9')]),
        ]
        
        items_table.setStyle(TableStyle(base_styles + variance_styles))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_period_pdf(period, include_cocktails=True):
    """
    Generate PDF report for a stock period.
    
    Args:
        period: StockPeriod model instance
        include_cocktails: Include cocktail sales data
    
    Returns:
        BytesIO: PDF file buffer
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=50,
        bottomMargin=30
    )
    
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph(
        f"<b>Period Report</b><br/>{period.hotel.name}",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Period Information
    period_data = [
        ['Period:', period.period_name],
        ['Dates:', f"{period.start_date} to {period.end_date}"],
        ['Type:', period.get_period_type_display()],
        ['Status:', 'Closed' if period.is_closed else 'Open'],
    ]
    
    if period.is_closed:
        period_data.append([
            'Closed:',
            f"{period.closed_at.strftime('%Y-%m-%d')} by {period.closed_by}" if period.closed_at else 'N/A'
        ])
    
    period_table = Table(period_data, colWidths=[2*inch, 4*inch])
    period_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Get snapshots
    from stock_tracker.models import StockSnapshot
    snapshots = StockSnapshot.objects.filter(period=period).select_related('item', 'item__category')
    
    # Summary
    summary_heading = Paragraph("<b>Period Summary</b>", heading_style)
    elements.append(summary_heading)
    
    total_closing_value = sum(s.closing_stock_value for s in snapshots)
    
    summary_data = [
        ['Total Items:', str(snapshots.count())],
        ['Closing Stock Value:', f"€{total_closing_value:,.2f}"],
    ]
    
    # Add sales data if available
    if include_cocktails:
        summary_data.extend([
            ['Cocktail Sales Revenue:', f"€{period.cocktail_revenue:,.2f}"],
            ['Cocktail Quantity:', str(period.cocktail_quantity)],
        ])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Category Breakdown
    category_heading = Paragraph("<b>Stock Value by Category</b>", heading_style)
    elements.append(category_heading)
    
    category_data = {}
    for snapshot in snapshots:
        cat_code = snapshot.item.category.code
        if cat_code not in category_data:
            category_data[cat_code] = {
                'name': snapshot.item.category.name,
                'value': Decimal('0.00'),
                'items': 0
            }
        category_data[cat_code]['value'] += snapshot.closing_stock_value
        category_data[cat_code]['items'] += 1
    
    cat_table_data = [['Category', 'Items', 'Value', '% of Total']]
    
    for cat_code in ['D', 'B', 'S', 'W', 'M']:
        if cat_code in category_data:
            cat = category_data[cat_code]
            percentage = (cat['value'] / total_closing_value * 100) if total_closing_value > 0 else 0
            cat_table_data.append([
                cat['name'],
                str(cat['items']),
                f"€{float(cat['value']):,.2f}",
                f"{float(percentage):.1f}%"
            ])
    
    cat_table = Table(cat_table_data, colWidths=[2*inch, 1*inch, 2*inch, 1.5*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    elements.append(cat_table)
    elements.append(PageBreak())
    
    # Detailed Snapshots by Category
    items_heading = Paragraph("<b>Detailed Stock Snapshots</b>", heading_style)
    elements.append(items_heading)
    elements.append(Spacer(1, 0.1*inch))
    
    for cat_code in ['D', 'B', 'S', 'W', 'M']:
        cat_snapshots = [s for s in snapshots if s.item.category.code == cat_code]
        
        if not cat_snapshots:
            continue
        
        cat_name = {
            'D': 'Draught Beer',
            'B': 'Bottled Beer',
            'S': 'Spirits',
            'W': 'Wine',
            'M': 'Minerals & Syrups'
        }.get(cat_code, cat_code)
        
        cat_header = Paragraph(f"<b>{cat_name}</b>", heading_style)
        elements.append(cat_header)
        
        items_data = [
            ['SKU', 'Name', 'Size', 'Full', 'Partial', 'Total Servings', 'Value €']
        ]
        
        for snapshot in cat_snapshots:
            items_data.append([
                snapshot.item.sku[:15],
                snapshot.item.name[:35],
                snapshot.item.size[:15],
                f"{float(snapshot.closing_full_units):,.1f}",
                f"{float(snapshot.closing_partial_units):,.2f}",
                f"{float(snapshot.total_servings):,.2f}",
                f"€{float(snapshot.closing_stock_value):,.2f}"
            ])
        
        items_table = Table(
            items_data,
            colWidths=[0.7*inch, 2.3*inch, 0.8*inch, 0.7*inch, 0.8*inch, 1*inch, 1*inch]
        )
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
