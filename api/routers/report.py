"""Report generation router."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import io

router = APIRouter()


async def get_analytics_service():
    """Get analytics service - lazy initialization."""
    from index import get_analytics_service as _get_service
    return await _get_service()


@router.get("/pdf")
async def generate_pdf_report(request: Request) -> StreamingResponse:
    """
    Generate and download PDF report.
    
    Creates a comprehensive PDF report with all analytics findings
    including rodent analysis, revenue at risk, grade breakdown,
    borough analysis, and watchlist.
    """
    from services.pdf_generator import PDFReportGenerator
    
    analytics_service = await get_analytics_service()
    
    # Generate PDF
    generator = PDFReportGenerator(analytics_service)
    pdf_buffer = generator.generate()
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=rat_challenge_report.pdf"
        }
    )
