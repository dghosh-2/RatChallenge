"""PDF report generator for food safety analytics."""

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from .analytics import AnalyticsService


class PDFReportGenerator:
    """Generate PDF reports from analytics data."""
    
    # Color scheme
    PRIMARY_COLOR = colors.HexColor("#1a1a2e")
    ACCENT_COLOR = colors.HexColor("#e94560")
    SUCCESS_COLOR = colors.HexColor("#0f3460")
    WARNING_COLOR = colors.HexColor("#f39c12")
    DANGER_COLOR = colors.HexColor("#e74c3c")
    
    def __init__(self, analytics_service: AnalyticsService):
        """
        Initialize the PDF generator.
        
        Args:
            analytics_service: Analytics service instance with computed data
        """
        self.analytics = analytics_service
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=28,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=30,
            alignment=1,  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=colors.gray,
            spaceAfter=20,
            alignment=1,
        ))
        
        self.styles.add(ParagraphStyle(
            name="RatSectionTitle",
            parent=self.styles["Heading2"],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=20,
            spaceAfter=12,
        ))
        
        self.styles.add(ParagraphStyle(
            name="RatMetricValue",
            parent=self.styles["Normal"],
            fontSize=24,
            textColor=self.ACCENT_COLOR,
            alignment=1,
        ))
        
        self.styles.add(ParagraphStyle(
            name="RatMetricLabel",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            alignment=1,
        ))
        
        self.styles.add(ParagraphStyle(
            name="RatBodyText",
            parent=self.styles["Normal"],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=10,
        ))
    
    def generate(self) -> bytes:
        """
        Generate the complete PDF report.
        
        Returns:
            PDF file as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        # Build story (content)
        story = []
        
        # Title page
        story.extend(self._build_title_page())
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._build_executive_summary())
        story.append(PageBreak())
        
        # Section 1: Rodent Analysis
        story.extend(self._build_rodent_section())
        story.append(PageBreak())
        
        # Section 2: Revenue by Grade
        story.extend(self._build_grade_section())
        story.append(PageBreak())
        
        # Section 3: Revenue at Risk
        story.extend(self._build_rar_section())
        story.append(PageBreak())
        
        # Section 4: Borough Breakdown
        story.extend(self._build_borough_section())
        story.append(PageBreak())
        
        # Section 5: Watchlist
        story.extend(self._build_watchlist_section())
        story.append(PageBreak())
        
        # Methodology
        story.extend(self._build_methodology_section())
        
        # Build PDF
        doc.build(story)
        
        return buffer.getvalue()
    
    def _build_title_page(self) -> list:
        """Build the title page."""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        
        elements.append(Paragraph(
            "🐀 Is There a Rat in My Food?",
            self.styles["ReportTitle"]
        ))
        
        elements.append(Paragraph(
            "Food Safety Risk Analysis Report",
            self.styles["ReportSubtitle"]
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles["ReportSubtitle"]
        ))
        
        elements.append(Spacer(1, 1*inch))
        
        # Summary stats box
        summary = self.analytics.get_summary()
        
        summary_data = [
            ["Total Orders", f"{summary['total_orders']:,}"],
            ["Total Revenue", f"${summary['total_revenue']:,.2f}"],
            ["Matched Orders", f"{summary['matched_orders']:,}"],
            ["Revenue at Risk", f"${summary['revenue_at_risk']:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.gray),
            ("TEXTCOLOR", (1, 0), (1, -1), self.PRIMARY_COLOR),
            ("FONTSIZE", (0, 0), (-1, -1), 14),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 15),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e9ecef")),
        ]))
        
        elements.append(summary_table)
        
        return elements
    
    def _build_executive_summary(self) -> list:
        """Build the executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles["RatSectionTitle"]))
        
        summary = self.analytics.get_summary()
        
        # Key findings
        findings = [
            f"This report analyzes <b>{summary['total_orders']:,}</b> food delivery orders "
            f"totaling <b>${summary['total_revenue']:,.2f}</b> in revenue.",
            
            f"Of these orders, <b>{summary['matched_orders']:,}</b> were successfully matched "
            f"to NYC restaurant inspection records.",
            
            f"<b>${summary['rodent_revenue']:,.2f}</b> in revenue came from <b>{summary['rodent_restaurant_count']}</b> "
            f"restaurants with documented rodent violations.",
            
            f"Total <b>Revenue at Risk (RAR)</b> is estimated at <b>${summary['revenue_at_risk']:,.2f}</b>, "
            f"representing orders from restaurants with closures, poor grades, or critical violations.",
        ]
        
        for finding in findings:
            elements.append(Paragraph(f"• {finding}", self.styles["RatBodyText"]))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Risk assessment
        elements.append(Paragraph("Risk Assessment", self.styles["RatSectionTitle"]))
        
        rar_pct = (summary["revenue_at_risk"] / summary["total_revenue"] * 100) if summary["total_revenue"] > 0 else 0
        rodent_pct = (summary["rodent_revenue"] / summary["total_revenue"] * 100) if summary["total_revenue"] > 0 else 0
        
        risk_text = (
            f"Approximately <b>{rar_pct:.1f}%</b> of total revenue is considered 'at risk' based on "
            f"food safety indicators. Rodent-related revenue accounts for <b>{rodent_pct:.1f}%</b> of total revenue. "
            f"The top 10 highest-earning restaurants with health flags account for "
            f"<b>${sum(r['revenue'] for r in summary['top_watchlist']):,.2f}</b> in combined revenue."
        )
        
        elements.append(Paragraph(risk_text, self.styles["RatBodyText"]))
        
        return elements
    
    def _build_rodent_section(self) -> list:
        """Build the rodent analysis section."""
        elements = []
        
        elements.append(Paragraph(
            "Section 1: Rodent Violation Analysis",
            self.styles["RatSectionTitle"]
        ))
        
        rodent_data = self.analytics.get_rodent_orders()
        
        elements.append(Paragraph(
            f"This section identifies all orders from restaurants with documented rodent-related "
            f"violations (rats, mice, vermin) in their NYC health inspection records.",
            self.styles["RatBodyText"]
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Key metrics
        metrics_data = [
            ["Total Rodent Revenue", "Affected Orders", "Restaurants"],
            [
                f"${rodent_data['total_rodent_revenue']:,.2f}",
                f"{rodent_data['order_count']:,}",
                f"{rodent_data['unique_restaurants']}"
            ],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        metrics_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DANGER_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fce4e4")),
            ("TEXTCOLOR", (0, 1), (-1, 1), self.DANGER_COLOR),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("FONTSIZE", (0, 1), (-1, 1), 16),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e9ecef")),
        ]))
        
        elements.append(metrics_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Sample orders table
        if rodent_data["orders"]:
            elements.append(Paragraph("Sample Affected Orders:", self.styles["RatBodyText"]))
            
            order_rows = [["Restaurant", "Order Cost", "Inspection Date"]]
            for order in rodent_data["orders"][:10]:
                order_rows.append([
                    order["restaurant_name"][:30],
                    f"${order['cost']:.2f}",
                    order["inspection_date"],
                ])
            
            order_table = Table(order_rows, colWidths=[3*inch, 1.5*inch, 2*inch])
            order_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ]))
            
            elements.append(order_table)
        
        return elements
    
    def _build_grade_section(self) -> list:
        """Build the revenue by grade section."""
        elements = []
        
        elements.append(Paragraph(
            "Section 2: Revenue by Health Grade",
            self.styles["RatSectionTitle"]
        ))
        
        grade_data = self.analytics.get_revenue_by_grade()
        
        elements.append(Paragraph(
            "NYC restaurants receive letter grades (A, B, C) based on health inspections. "
            "Grade A indicates the best conditions, while C indicates significant violations. "
            "Z, P, and N indicate pending or not-yet-graded status.",
            self.styles["RatBodyText"]
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Grade table
        grade_rows = [["Grade", "Revenue", "Orders", "% of Total"]]
        
        grade_colors = {
            "A": colors.HexColor("#28a745"),
            "B": colors.HexColor("#ffc107"),
            "C": colors.HexColor("#dc3545"),
            "Z": colors.HexColor("#6c757d"),
            "P": colors.HexColor("#6c757d"),
            "N": colors.HexColor("#6c757d"),
        }
        
        for grade in grade_data["grades"]:
            grade_rows.append([
                grade["grade"],
                f"${grade['revenue']:,.2f}",
                f"{grade['order_count']:,}",
                f"{grade['percentage']:.1f}%",
            ])
        
        grade_rows.append([
            "Unmatched",
            f"${grade_data['unmatched_revenue']:,.2f}",
            f"{grade_data['unmatched_order_count']:,}",
            f"{(grade_data['unmatched_revenue']/grade_data['total_revenue']*100):.1f}%"
        ])
        
        grade_table = Table(grade_rows, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
        grade_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        
        elements.append(grade_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Interpretation
        elements.append(Paragraph(
            f"<b>Key Finding:</b> ${grade_data['total_revenue']:,.2f} in total revenue was analyzed. "
            f"Restaurants with unmatched or unknown grades account for "
            f"${grade_data['unmatched_revenue']:,.2f} in revenue.",
            self.styles["RatBodyText"]
        ))
        
        return elements
    
    def _build_rar_section(self) -> list:
        """Build the Revenue at Risk section."""
        elements = []
        
        elements.append(Paragraph(
            "Section 3: Revenue at Risk (RAR)",
            self.styles["RatSectionTitle"]
        ))
        
        rar_data = self.analytics.get_revenue_at_risk()
        
        elements.append(Paragraph(
            "Revenue at Risk (RAR) represents orders from restaurants with concerning health indicators. "
            "This includes restaurants that have been closed, have poor grades, or have critical violations.",
            self.styles["RatBodyText"]
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Total RAR highlight
        rar_highlight = [
            ["TOTAL REVENUE AT RISK"],
            [f"${rar_data['total_revenue_at_risk']:,.2f}"],
            [f"{rar_data['order_count']:,} orders affected"],
        ]
        
        rar_table = Table(rar_highlight, colWidths=[4*inch])
        rar_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3cd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WARNING_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, 1), self.DANGER_COLOR),
            ("TEXTCOLOR", (0, 2), (-1, 2), colors.gray),
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("FONTSIZE", (0, 1), (-1, 1), 28),
            ("FONTSIZE", (0, 2), (-1, 2), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 15),
            ("BOX", (0, 0), (-1, -1), 2, self.WARNING_COLOR),
        ]))
        
        elements.append(rar_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Breakdown by category
        elements.append(Paragraph("Breakdown by Risk Category:", self.styles["RatBodyText"]))
        
        breakdown_rows = [["Risk Category", "Revenue", "Order Count"]]
        category_labels = {
            "closed": "Closed/Re-closed",
            "grade_c": "Grade C",
            "grade_pending": "Pending Grades (P/N/Z)",
            "critical_violation": "Critical Violations",
        }
        
        for key, label in category_labels.items():
            breakdown_rows.append([
                label,
                f"${rar_data['breakdown'].get(key, 0):,.2f}",
                f"{rar_data['risk_categories'].get(key, 0):,}",
            ])
        
        breakdown_table = Table(breakdown_rows, colWidths=[3*inch, 2*inch, 1.5*inch])
        breakdown_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        
        elements.append(breakdown_table)
        
        return elements
    
    def _build_borough_section(self) -> list:
        """Build the borough breakdown section."""
        elements = []
        
        elements.append(Paragraph(
            "Section 4: Borough Breakdown",
            self.styles["RatSectionTitle"]
        ))
        
        boro_data = self.analytics.get_borough_breakdown()
        
        elements.append(Paragraph(
            "This section shows how order revenue is distributed across NYC's five boroughs, "
            "along with the most common violation categories in each area.",
            self.styles["RatBodyText"]
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Borough table
        boro_rows = [["Borough", "Revenue", "Orders", "% of Total"]]
        
        for boro in boro_data["boroughs"]:
            boro_rows.append([
                boro["borough"],
                f"${boro['revenue']:,.2f}",
                f"{boro['order_count']:,}",
                f"{boro['percentage']:.1f}%",
            ])
        
        boro_table = Table(boro_rows, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
        boro_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        
        elements.append(boro_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Violation categories
        if boro_data["violation_categories"]:
            elements.append(Paragraph("Revenue by Violation Category:", self.styles["RatBodyText"]))
            
            viol_rows = [["Category", "Revenue"]]
            for cat, rev in sorted(boro_data["violation_categories"].items(), key=lambda x: -x[1]):
                viol_rows.append([cat.title(), f"${rev:,.2f}"])
            
            viol_table = Table(viol_rows, colWidths=[3*inch, 2*inch])
            viol_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.SUCCESS_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ]))
            
            elements.append(viol_table)
        
        return elements
    
    def _build_watchlist_section(self) -> list:
        """Build the watchlist section."""
        elements = []
        
        elements.append(Paragraph(
            "Section 5: Top 10 Watchlist",
            self.styles["RatSectionTitle"]
        ))
        
        watchlist_data = self.analytics.get_watchlist(10)
        
        elements.append(Paragraph(
            "These are the 10 highest-earning restaurants that have open health risk flags. "
            "Risk flags include critical violations, rodent issues, closure history, or poor grades.",
            self.styles["RatBodyText"]
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Watchlist table
        watch_rows = [["#", "Restaurant", "Revenue", "Grade", "Risk Flags"]]
        
        for r in watchlist_data["restaurants"]:
            flags_str = ", ".join(r["risk_flags"][:2])  # Limit to 2 flags for space
            if len(r["risk_flags"]) > 2:
                flags_str += f" +{len(r['risk_flags'])-2} more"
            
            watch_rows.append([
                str(r["rank"]),
                r["restaurant_name"][:25],
                f"${r['revenue']:,.2f}",
                r["latest_grade"] or "N/A",
                flags_str[:40],
            ])
        
        watch_table = Table(watch_rows, colWidths=[0.4*inch, 2*inch, 1.3*inch, 0.7*inch, 2.1*inch])
        watch_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DANGER_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fce4e4")]),
        ]))
        
        elements.append(watch_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            f"<b>Total Watchlist Revenue:</b> ${watchlist_data['total_watchlist_revenue']:,.2f}",
            self.styles["RatBodyText"]
        ))
        
        return elements
    
    def _build_methodology_section(self) -> list:
        """Build the methodology section."""
        elements = []
        
        elements.append(Paragraph("Methodology", self.styles["RatSectionTitle"]))
        
        methodology_text = """
        <b>Data Sources:</b><br/>
        • Internal food order data (CSV file with order details)<br/>
        • NYC DOHMH Restaurant Inspection Results API (public dataset)<br/><br/>
        
        <b>Matching Process:</b><br/>
        • Restaurant names from orders are normalized (removing suffixes like "- CLOSED", "$0 Delivery Fee")<br/>
        • Manual mapping file links restaurant names to NYC CAMIS IDs<br/>
        • Orders are matched to inspection records via CAMIS ID<br/><br/>
        
        <b>Risk Definitions:</b><br/>
        • <b>Rodent Violations:</b> Inspections mentioning "rodent", "rat", "mice", "mouse", or "vermin"<br/>
        • <b>Critical Violations:</b> Violations flagged as "Critical" in inspection records<br/>
        • <b>Revenue at Risk:</b> Orders from restaurants with closures, Grade C, pending grades, or critical violations<br/><br/>
        
        <b>Limitations:</b><br/>
        • Not all restaurants could be matched to inspection records<br/>
        • Order dates are not available; all orders treated as within analysis period<br/>
        • Inspection data reflects historical records, not current conditions<br/>
        """
        
        elements.append(Paragraph(methodology_text, self.styles["RatBodyText"]))
        
        return elements

