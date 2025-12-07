from django.shortcuts import get_object_or_404, render
import pandas as pd
from django.http import JsonResponse, HttpResponse
from .models import interviewSchedule
from Authentication.models import Hr
import secrets
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import redirect
import json
import datetime

# Add these imports for PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import os

#SOME IMPORTANT FUNCTIONS
from django.utils.timezone import now


def schedule_next_interview():
    today = now().date()
    schedule_start_date = today + datetime.timedelta(days=7)

    # Get the last scheduled interview date and time
    last_scheduled = (
        interviewSchedule.objects.order_by("-interviewDate", "-interviewTime").first()
    )

    if last_scheduled:
        # If the last scheduled date is greater than today's date + 7 days
        if last_scheduled.interviewDate > schedule_start_date:
            current_date = last_scheduled.interviewDate
            current_time = last_scheduled.interviewTime
        elif last_scheduled.interviewDate == schedule_start_date:
            current_date = last_scheduled.interviewDate
            current_time = last_scheduled.interviewTime
        else:
            current_date = schedule_start_date
            current_time = datetime.time(9, 0)
    else:
        # If no interviews are scheduled, start from the calculated schedule_start_date
        current_date = schedule_start_date
        current_time = datetime.time(9, 0)

    # Check for available slots and adjust
    students_in_slot = (
        interviewSchedule.objects.filter(
            interviewDate=current_date, interviewTime=current_time
        ).count()
    )
    if students_in_slot >= 3:
        current_time = (datetime.datetime.combine(today, current_time) + datetime.timedelta(hours=1)).time()
        if current_time >= datetime.time(21, 0):
            # Move to the next day if slots for the current day are full
            current_date += datetime.timedelta(days=1)
            current_time = datetime.time(9, 0)

    return current_date, current_time



def mailer(subject, message, email_from, recipient_list):
    send_mail(subject, message, email_from, recipient_list)


def dashboard(request):
    # HR logout code
    logout_status_code = request.GET.get('logout', None)
    print(type(logout_status_code))
    if logout_status_code:
        if logout_status_code == '1':
            del request.session['hr_email']

    # -----------------------------------------------------
    hr_session_email = request.session.get('hr_email', None)
    
    hr_obj = Hr.objects.filter(email=hr_session_email).first()
    print(hr_obj)

    if hr_session_email is not None:
       
        if request.method == "POST" and request.FILES['file']:
            # Get the uploaded Excel file
            excel_file = request.FILES['file']

            try:
                # Read the Excel file into a DataFrame
                df = pd.read_excel(excel_file)

                # Iterate through the DataFrame and save to the database
                for _, row in df.iterrows():
                    candidateName = row['Name']
                    print(row['Name'])
                    print(row['Email'])
                    candidateRole=row['Job_Role']
                    print(row['Job_Role'])
                    print(row['Experience'])
                    print(row['Resume_Link'])
                    currentToken=secrets.token_hex(16)[:32]
                    print(currentToken)
                   

                    # Call the scheduling function to get the next available date and time
                    interviewDate, interviewTime = schedule_next_interview()
                    
                    print(interviewDate)
                    print(interviewTime)

                    # SENDING DATA FROM EXCEL TO DATABASE
                    interviewSchedule.objects.create(
                        name=row['Name'],
                        email=row['Email'],
                        jobRole=row['Job_Role'],
                        experience=row['Experience'],
                        resume=row['Resume_Link'],
                        interviewDate=interviewDate,
                        interviewTime=interviewTime,
                        token=currentToken,
                        Assigned_hr = hr_session_email,


                    )
                    # MAILING Functionality-----------------------------------------
                    subject = '[IMPORTANT] Congratulations! You have been selected for the Technical Interview'
                    message = (
                        f"Dear {candidateName},\n\n"
                        "Congratulations! You have been shortlisted for the next stage of our recruitment process: the Technical Interview.\n\n"
                        "Interview Details:\n"
                        f"- Date: {interviewDate}\n"
                        f"- Time: {interviewTime}\n"
                        f"- Mode: Online (AI-Powered Platform)\n"
                        f"- Interview Link: https://evalio.com/join/?access={currentToken}\n\n"
                        "This interview will be conducted by our advanced AI system, which is designed to assess your technical expertise, problem-solving skills, and overall suitability for the role. The AI will guide you through a series of questions and tasks. Your responses will be analyzed in real-time to ensure a fair and objective evaluation.\n\n"
                        "Preparation Guidelines:\n"
                        "1. Ensure a stable internet connection and a functional microphone and camera.\n"
                        "2. Have a quiet, well-lit space for the interview.\n"
                        "3. Familiarize yourself with the role requirements.\n\n"
                        "Important Note:\n"
                        "Please join the interview using the provided link at the scheduled time. If you experience any issues accessing the interview or have questions about the process, contact us at hr@abc.com.\n\n"
                        "We are excited to see how you perform in this innovative interview process. Good luck!\n\n"
                        "Best Regards,\n"
                        "HR Head\n"
                        "ABC Technologies Pvt Ltd\n"
                    )
                    email_from = 'cafearoumaa@gmail.com'
                    recip_email=row['Email']
                    recipient_list = [recip_email]
                    mailer(subject, message, email_from, recipient_list)

                    # MAILING Functionality (ends)-------------------------------

                allCandidates = interviewSchedule.objects.filter(Assigned_hr=hr_session_email)
                context={
                    'allcandidates':allCandidates
                }
                return render(request, 'dashboard.html', context)
            except Exception as e:
                return render(request, 'dashboard.html', {'status':"OOps"})
        allCandidates = interviewSchedule.objects.filter(Assigned_hr=hr_session_email)
        query = request.GET.get('q', '')
        if query:
             allCandidates = interviewSchedule.objects.filter(
        Assigned_hr=hr_session_email
    ).filter(
        Q(name__icontains=query) | Q(email__icontains=query) | Q(jobRole__icontains=query)
    )
            
            
        else:
            allCandidates = interviewSchedule.objects.filter(Assigned_hr=hr_session_email)
        context={
                "hrObj":hr_obj
            }
        return render(request, 'dashboard.html', {"hrObj":hr_obj, "allcandidates":allCandidates})
    else:
        return redirect('/auth/login/')


    
    



def Result_report(request, id):
    candidate = get_object_or_404(interviewSchedule, id=id)

    # strengths and weaknesses as lists if they are stored as newline separated strings
    strengths_list = [s.strip() for s in candidate.strengths.split("\n") if s.strip()] if candidate.strengths else []
    weaknesses_list = [w.strip() for w in candidate.weaknesses.split("\n") if w.strip()] if candidate.weaknesses else []

    context = {
        "name": candidate.name,
        "email": candidate.email,
        "jobRole": candidate.jobRole,
        "experience": candidate.experience,
        "resume": candidate.resume,
        "strengths": strengths_list,
        "weaknesses": weaknesses_list,
        "accuracy": candidate.accuracy,
        "communication": candidate.communication,
        "technical_depth": candidate.technical_depth,
        "good_fit": candidate.good_fit,
        "evaluation_complete": candidate.evaluation_complete,
        "cheatingScore": candidate.cheatingScore,
        "interviewDate": candidate.interviewDate,
        "interviewTime": candidate.interviewTime,
        "createdAt": candidate.createdAt,
    }

    return render(request, 'ResultReport.html', context)




def safe_lower(s):
    if isinstance(s, str):
        return s.lower()
    return ''

def hiring_suggestions(request):
    hr_session_email = request.session.get('hr_email', None)
    candidates = interviewSchedule.objects.filter(Assigned_hr= hr_session_email).filter(evaluation_complete=True)
    sorted_candidates = candidates.order_by('-accuracy', '-technical_depth')

    evaluated_candidates = []
    for c in sorted_candidates:
        accuracy_str = (c.accuracy or '').replace('%', '').strip()
        try:
            accuracy = float(accuracy_str)
        except (ValueError, TypeError):
            accuracy = 0.0

        cheating_score = safe_lower(c.cheatingScore)
        good_fit = safe_lower(c.good_fit)

        is_cheating = cheating_score == 'no'
        is_good_fit = good_fit == 'yes'

        if accuracy > 80 and is_good_fit and is_cheating:
            status = 'Good Fit'
        elif not is_cheating :
            status = 'Needs Review'

        evaluated_candidates.append({
            'name': c.name,
            'jobRole': c.jobRole,
            'accuracy': accuracy,
            'status': status,
            'cheatingScore': c.cheatingScore,
            'good_fit': c.good_fit,
        })

    count = len(evaluated_candidates)

    return render(request, 'HiringSuggestionsSam.html', {'candidates': evaluated_candidates,'count': count})

def manual_schedule(request):
    hr_session_email = request.session.get('hr_email', None)
    
    if not hr_session_email:
        return redirect('/auth/login/')
    
    hr_obj = Hr.objects.filter(email=hr_session_email).first()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            job_role = request.POST.get('jobRole')
            experience = request.POST.get('experience')
            resume = request.POST.get('resume')
            interview_date = request.POST.get('interviewDate')
            interview_time = request.POST.get('interviewTime')
            notes = request.POST.get('notes', '')
            use_auto_schedule = request.POST.get('useAutoSchedule') == 'on'
            
            # Validate required fields
            if not all([name, email, job_role, experience, resume]):
                return JsonResponse({
                    'success': False,
                    'message': 'All required fields must be filled.'
                })
            
            # Generate token
            current_token = secrets.token_hex(16)[:32]
            print(f"Generated token: {current_token}")
            
            # Determine schedule
            if use_auto_schedule or not interview_date or not interview_time:
                # Use automatic scheduling
                interview_date, interview_time = schedule_next_interview()
            else:
                # Parse manual date and time
                interview_date = datetime.datetime.strptime(interview_date, '%Y-%m-%d').date()
                interview_time = datetime.datetime.strptime(interview_time, '%H:%M').time()
            
            # Create interview schedule
            interview_schedule = interviewSchedule.objects.create(
                name=name,
                email=email,
                jobRole=job_role,
                experience=float(experience),
                resume=resume,
                interviewDate=interview_date,
                interviewTime=interview_time,
                token=current_token,
                Assigned_hr=hr_session_email,
            )
            
            # Send email
            subject = '[IMPORTANT] Congratulations! You have been selected for the Technical Interview'
            message = (
                f"Dear {name},\n\n"
                "Congratulations! You have been shortlisted for the next stage of our recruitment process: the Technical Interview.\n\n"
                "Interview Details:\n"
                f"- Date: {interview_date}\n"
                f"- Time: {interview_time}\n"
                f"- Mode: Online (AI-Powered Platform)\n"
                f"- Interview Link: https://evalio.com/join/?access={current_token}\n\n"
                "This interview will be conducted by our advanced AI system, which is designed to assess your technical expertise, problem-solving skills, and overall suitability for the role.\n\n"
                "Preparation Guidelines:\n"
                "1. Ensure a stable internet connection and a functional microphone and camera.\n"
                "2. Have a quiet, well-lit space for the interview.\n"
                "3. Familiarize yourself with the role requirements.\n\n"
            )
            
            if notes:
                message += f"Special Instructions:\n{notes}\n\n"
            
            message += (
                "Important Note:\n"
                "Please join the interview using the provided link at the scheduled time. If you experience any issues, contact us at hr@abc.com.\n\n"
                "Best Regards,\n"
                "HR Team\n"
                "ABC Technologies Pvt Ltd\n"
            )
            
            email_from = 'cafearoumaa@gmail.com'
            recipient_list = [email]
            mailer(subject, message, email_from, recipient_list)
            
            return JsonResponse({
                'success': True,
                'message': 'Interview scheduled successfully and email sent to candidate.',
                'interview_date': str(interview_date),
                'interview_time': str(interview_time),
                'token': current_token
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error scheduling interview: {str(e)}'
            })
    
    # GET request - render the form
    context = {
        'hrObj': hr_obj
    }
    return render(request, 'manual_schedule.html', context)

def download_report_pdf(request, id):
    candidate = get_object_or_404(interviewSchedule, id=id)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4C1D95'),
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#6B21A8'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leading=14
    )
    
    # Title
    story.append(Paragraph("INTERVIEW EVALUATION REPORT", title_style))
    story.append(Spacer(1, 12))
    
    # Header information table
    header_data = [
        ['Candidate Name:', candidate.name],
        ['Email:', candidate.email],
        ['Position:', candidate.jobRole],
        ['Experience:', f"{candidate.experience} years"],
        ['Interview Date:', str(candidate.interviewDate)],
        ['Interview Time:', str(candidate.interviewTime)],
        ['Report Generated:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    header_table = Table(header_data, colWidths=[2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Assessment Status
    status = "COMPLETED" if candidate.evaluation_complete else "PENDING"
    status_color = colors.HexColor('#10B981') if candidate.evaluation_complete else colors.HexColor('#EF4444')
    
    status_style = ParagraphStyle(
        'StatusStyle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=status_color,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=status_color,
        borderPadding=8
    )
    
    story.append(Paragraph(f"Assessment Status: {status}", status_style))
    story.append(Spacer(1, 20))
    
    if candidate.evaluation_complete:
        # Performance Metrics
        story.append(Paragraph("PERFORMANCE METRICS", heading_style))
        
        metrics_data = [
            ['Metric', 'Score', 'Description'],
            ['Accuracy', candidate.accuracy or 'N/A', 'Percentage of correct answers'],
            ['Communication', candidate.communication or 'N/A', 'Fluency and clarity assessment'],
            ['Technical Depth', candidate.technical_depth or 'N/A', 'Technical knowledge evaluation'],
            ['Cultural Fit', candidate.good_fit or 'N/A', 'Alignment with company values'],
            ['Integrity Score', candidate.cheatingScore or 'N/A', 'Assessment authenticity check']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B21A8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Strengths
        if candidate.strengths:
            story.append(Paragraph("STRENGTHS", heading_style))
            strengths_list = [s.strip() for s in candidate.strengths.split("\n") if s.strip()]
            for strength in strengths_list:
                story.append(Paragraph(f"• {strength}", normal_style))
            story.append(Spacer(1, 15))
        
        # Areas for Improvement
        if candidate.weaknesses:
            story.append(Paragraph("AREAS FOR IMPROVEMENT", heading_style))
            weaknesses_list = [w.strip() for w in candidate.weaknesses.split("\n") if w.strip()]
            for weakness in weaknesses_list:
                story.append(Paragraph(f"• {weakness}", normal_style))
            story.append(Spacer(1, 15))
        
        # Overall Assessment
        story.append(Paragraph("OVERALL ASSESSMENT", heading_style))
        
        # Calculate overall score based on available metrics
        overall_assessment = "Based on the evaluation metrics, "
        
        accuracy_num = 0
        try:
            if candidate.accuracy:
                accuracy_num = float(candidate.accuracy.replace('%', '').strip())
        except:
            pass
        
        good_fit_status = candidate.good_fit and candidate.good_fit.lower() == 'yes'
        cheating_status = candidate.cheatingScore and candidate.cheatingScore.lower() == 'no'
        
        if accuracy_num >= 80 and good_fit_status and cheating_status:
            overall_assessment += "this candidate demonstrates strong performance across all evaluation criteria and is recommended for further consideration."
        elif accuracy_num >= 60:
            overall_assessment += "this candidate shows satisfactory performance with some areas that may need development."
        else:
            overall_assessment += "this candidate may require additional evaluation or training before proceeding to the next stage."
        
        story.append(Paragraph(overall_assessment, normal_style))
    
    else:
        story.append(Paragraph("ASSESSMENT PENDING", heading_style))
        story.append(Paragraph("The candidate has not yet completed the assessment. Please ensure they access the interview link provided.", normal_style))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6B7280')
    )
    
    story.append(Paragraph("This report is confidential and generated by Evalio AI Interview Platform", footer_style))
    story.append(Paragraph("For questions regarding this assessment, please contact the HR department", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Interview_Report_{candidate.name}_{candidate.id}.pdf"'
    
    return response
