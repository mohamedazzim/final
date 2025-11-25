from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from rapidfuzz import fuzz
from datetime import date
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from database import get_db
from models import Cause, User
from schemas import CauseResponse, CauseSearchParams, RelatedCase
from routers.auth import get_current_user

router = APIRouter()


def calculate_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    return fuzz.ratio(text1.lower(), text2.lower()) / 100.0


@router.get("/search", response_model=List[CauseResponse])
async def search_causes(
    query: str = None,
    case_no: str = None,
    petitioner: str = None,
    respondent: str = None,
    advocate: str = None,
    court_no: str = None,
    hearing_date_from: date = None,
    hearing_date_to: date = None,
    case_type: str = None,
    is_hrce: bool = None,
    fuzzy: bool = False,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query_obj = db.query(Cause)
    
    if fuzzy and (case_no or petitioner or respondent or advocate):
        all_causes = query_obj.all()
        results = []
        
        for cause in all_causes:
            score = 0
            matches = 0
            
            if case_no and cause.case_no:
                s = calculate_similarity(case_no, cause.case_no)
                if s > 0.6:
                    score += s
                    matches += 1
            
            if petitioner and cause.petitioner:
                s = calculate_similarity(petitioner, cause.petitioner)
                if s > 0.7:
                    score += s
                    matches += 1
            
            if respondent and cause.respondent:
                s = calculate_similarity(respondent, cause.respondent)
                if s > 0.7:
                    score += s
                    matches += 1
            
            if advocate and cause.advocate:
                s = calculate_similarity(advocate, cause.advocate)
                if s > 0.7:
                    score += s
                    matches += 1
            
            if matches > 0 and (score / matches) > 0.7:
                results.append(cause)
        
        if court_no:
            # Flexible filtering for fuzzy search results
            filtered_results = []
            for c in results:
                if c.court_no == court_no:
                    filtered_results.append(c)
                elif c.court_no and c.court_no.lower() == f"court no. {court_no}".lower():
                    filtered_results.append(c)
                elif c.court_no and len(court_no) == 1 and court_no.isdigit() and c.court_no.lower() == f"court no. 0{court_no}".lower():
                    filtered_results.append(c)
            results = filtered_results
            
        if hearing_date_from:
            results = [c for c in results if c.hearing_date and c.hearing_date >= hearing_date_from]
        if hearing_date_to:
            results = [c for c in results if c.hearing_date and c.hearing_date <= hearing_date_to]
        if case_type:
            results = [c for c in results if c.case_type == case_type]
        if is_hrce is not None:
            results = [c for c in results if c.is_hrce == is_hrce]
        
        return results[offset:offset+limit]
    
    else:
        if query:
            query_obj = query_obj.filter(
                or_(
                    Cause.case_no.ilike(f"%{query}%"),
                    Cause.petitioner.ilike(f"%{query}%"),
                    Cause.respondent.ilike(f"%{query}%"),
                    Cause.advocate.ilike(f"%{query}%"),
                    Cause.raw_text.ilike(f"%{query}%")
                )
            )
        
        if case_no:
            query_obj = query_obj.filter(Cause.case_no.ilike(f"%{case_no}%"))
        if petitioner:
            query_obj = query_obj.filter(Cause.petitioner.ilike(f"%{petitioner}%"))
        if respondent:
            query_obj = query_obj.filter(Cause.respondent.ilike(f"%{respondent}%"))
        if advocate:
            query_obj = query_obj.filter(Cause.advocate.ilike(f"%{advocate}%"))
        if court_no:
            # Handle flexible court number searching
            # Matches: "1", "01", "COURT NO. 1", "COURT NO. 01"
            court_filters = [
                Cause.court_no == court_no,
                Cause.court_no.ilike(f"COURT NO. {court_no}"),
                Cause.court_no.ilike(f"COURT NO. 0{court_no}") if len(court_no) == 1 and court_no.isdigit() else None
            ]
            # Filter out None values
            court_filters = [f for f in court_filters if f is not None]
            query_obj = query_obj.filter(or_(*court_filters))
            
        if hearing_date_from:
            query_obj = query_obj.filter(Cause.hearing_date >= hearing_date_from)
        if hearing_date_to:
            query_obj = query_obj.filter(Cause.hearing_date <= hearing_date_to)
        if case_type:
            query_obj = query_obj.filter(Cause.case_type.ilike(f"%{case_type}%"))
        if is_hrce is not None:
            query_obj = query_obj.filter(Cause.is_hrce == is_hrce)
        
        results = query_obj.offset(offset).limit(limit).all()
        return results


@router.get("/{cause_id}", response_model=CauseResponse)
async def get_cause(
    cause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cause = db.query(Cause).filter(Cause.id == cause_id).first()
    if not cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    return cause


@router.get("/{cause_id}/related", response_model=List[RelatedCase])
async def get_related_causes(
    cause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cause = db.query(Cause).filter(Cause.id == cause_id).first()
    if not cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    
    all_causes = db.query(Cause).filter(Cause.id != cause_id).all()
    related = []
    
    for other_cause in all_causes:
        max_score = 0
        reason = ""
        
        if cause.petitioner and other_cause.petitioner:
            pet_score = calculate_similarity(cause.petitioner, other_cause.petitioner)
            if pet_score > max_score and pet_score > 0.75:
                max_score = pet_score
                reason = "Similar petitioner name"
        
        if cause.respondent and other_cause.respondent:
            res_score = calculate_similarity(cause.respondent, other_cause.respondent)
            if res_score > max_score and res_score > 0.75:
                max_score = res_score
                reason = "Similar respondent name"
        
        if cause.advocate and other_cause.advocate:
            adv_score = calculate_similarity(cause.advocate, other_cause.advocate)
            if adv_score > max_score and adv_score > 0.8:
                max_score = adv_score
                reason = "Same advocate"
        
        if max_score > 0.75:
            related.append(RelatedCase(
                cause=other_cause,
                similarity_score=max_score,
                match_reason=reason
            ))
    
    related.sort(key=lambda x: x.similarity_score, reverse=True)
    return related[:10]


@router.get("/download-pdf")
async def download_causes_pdf(
    query: str = None,
    case_no: str = None,
    petitioner: str = None,
    respondent: str = None,
    advocate: str = None,
    court_no: str = None,
    hearing_date_from: date = None,
    hearing_date_to: date = None,
    case_type: str = None,
    is_hrce: bool = None,
    fuzzy: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f"Generating PDF for user {current_user.username}")
        query_obj = db.query(Cause)
        
        causes = []
        
        if fuzzy and (case_no or petitioner or respondent or advocate):
            all_causes = query_obj.all()
            results = []
            
            for cause in all_causes:
                score = 0
                matches = 0
                
                if case_no and cause.case_no:
                    s = calculate_similarity(case_no, cause.case_no)
                    if s > 0.6:
                        score += s
                        matches += 1
                
                if petitioner and cause.petitioner:
                    s = calculate_similarity(petitioner, cause.petitioner)
                    if s > 0.7:
                        score += s
                        matches += 1
                
                if respondent and cause.respondent:
                    s = calculate_similarity(respondent, cause.respondent)
                    if s > 0.7:
                        score += s
                        matches += 1
                
                if advocate and cause.advocate:
                    s = calculate_similarity(advocate, cause.advocate)
                    if s > 0.7:
                        score += s
                        matches += 1
                
                if matches > 0 and (score / matches) > 0.7:
                    results.append(cause)
            
            if court_no:
                filtered_results = []
                for c in results:
                    if c.court_no == court_no:
                        filtered_results.append(c)
                    elif c.court_no and c.court_no.lower() == f"court no. {court_no}".lower():
                        filtered_results.append(c)
                    elif c.court_no and len(court_no) == 1 and court_no.isdigit() and c.court_no.lower() == f"court no. 0{court_no}".lower():
                        filtered_results.append(c)
                results = filtered_results
                
            if hearing_date_from:
                results = [c for c in results if c.hearing_date and c.hearing_date >= hearing_date_from]
            if hearing_date_to:
                results = [c for c in results if c.hearing_date and c.hearing_date <= hearing_date_to]
            if case_type:
                results = [c for c in results if c.case_type == case_type]
            if is_hrce is not None:
                results = [c for c in results if c.is_hrce == is_hrce]
            
            causes = results
        else:
            if query:
                query_obj = query_obj.filter(
                    or_(
                        Cause.case_no.ilike(f"%{query}%"),
                        Cause.petitioner.ilike(f"%{query}%"),
                        Cause.respondent.ilike(f"%{query}%"),
                        Cause.advocate.ilike(f"%{query}%"),
                        Cause.raw_text.ilike(f"%{query}%")
                    )
                )
            
            if case_no:
                query_obj = query_obj.filter(Cause.case_no.ilike(f"%{case_no}%"))
            if petitioner:
                query_obj = query_obj.filter(Cause.petitioner.ilike(f"%{petitioner}%"))
            if respondent:
                query_obj = query_obj.filter(Cause.respondent.ilike(f"%{respondent}%"))
            if advocate:
                query_obj = query_obj.filter(Cause.advocate.ilike(f"%{advocate}%"))
            if court_no:
                court_filters = [
                    Cause.court_no == court_no,
                    Cause.court_no.ilike(f"COURT NO. {court_no}"),
                    Cause.court_no.ilike(f"COURT NO. 0{court_no}") if len(court_no) == 1 and court_no.isdigit() else None
                ]
                court_filters = [f for f in court_filters if f is not None]
                query_obj = query_obj.filter(or_(*court_filters))
                
            if hearing_date_from:
                query_obj = query_obj.filter(Cause.hearing_date >= hearing_date_from)
            if hearing_date_to:
                query_obj = query_obj.filter(Cause.hearing_date <= hearing_date_to)
            if case_type:
                query_obj = query_obj.filter(Cause.case_type.ilike(f"%{case_type}%"))
            if is_hrce is not None:
                query_obj = query_obj.filter(Cause.is_hrce == is_hrce)
                
            causes = query_obj.all()
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("Cause List Search Results", styles['Title']))
        elements.append(Spacer(1, 12))
        
        data = [['Court No', 'Case No', 'Petitioner', 'Respondent', 'Advocate', 'Date']]
        
        for cause in causes:
            data.append([
                cause.court_no or "",
                cause.case_no or "",
                (cause.petitioner or "")[:30] + "..." if len(cause.petitioner or "") > 30 else (cause.petitioner or ""),
                (cause.respondent or "")[:30] + "..." if len(cause.respondent or "") > 30 else (cause.respondent or ""),
                (cause.advocate or "")[:30] + "..." if len(cause.advocate or "") > 30 else (cause.advocate or ""),
                str(cause.hearing_date)
            ])
            
        table = Table(data, colWidths=[80, 100, 150, 150, 150, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cause_list_results.pdf"}
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
