"""Report generation router."""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io

router = APIRouter()


async def get_analytics_service(days: int = 90):
    """Get analytics service for a specific time range."""
    from index import get_analytics_service as _get_service
    return await _get_service(days=days)


@router.get("/pdf")
async def generate_pdf_report(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> StreamingResponse:
    """
    Generate and download PDF report.
    
    Creates a comprehensive PDF report with all analytics findings
    including rodent analysis, revenue at risk, grade breakdown,
    borough analysis, and watchlist.
    """
    from services.pdf_generator import PDFReportGenerator
    
    analytics_service = await get_analytics_service(days=days)
    
    # Generate PDF
    generator = PDFReportGenerator(analytics_service)
    pdf_buffer = generator.generate()
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=rat_challenge_report_{days}days.pdf"
        }
    )
