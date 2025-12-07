from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from Hr.models import interviewSchedule
from datetime import datetime, timedelta

from .utils import generate, pdf_ocr, evaluation
from django.http import JsonResponse
from .models import Feedback
from django.views.decorators.csrf import csrf_exempt

import cv2
import numpy as np
import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json



name = ""

pdf_link = ""

job_description = """"""



def check_interview_schedule(interview_schedule):
    # Getting current date and time
    current_date = datetime.now().date()
    current_time = datetime.now().time()
    
    print("current_date: ", current_date)
    print("current_time: ", current_time)

    # Extracting date and time from the database object
    interview_date = interview_schedule.interviewDate
    interview_time = interview_schedule.interviewTime

    # Checking if the interview date is today, past, or future
    if interview_date < current_date:
        
        status=0    #  0 Signifies PAST Date Time
    elif interview_date == current_date:
        date_status = "Today"

        # Defining the time window
        start_time = interview_time  # Interview time from DB
        end_time = (datetime.combine(current_date, interview_time) + timedelta(hours=1)).time()  # +1 hour

        # Check if current time is within the window
        if start_time <= current_time <= end_time:
            # time_status = "Within 1 hour window"
            status=1    #  1 Signifies CURRENT Date Time
        elif current_time > end_time:
            # time_status = "Outside 1 hour window"
            status=0    #  0 Signifies PAST Date Time
        elif current_time < start_time:
            status=2    #  2 Signifies FUTURE Date Time
    else:
        # date_status = "Future"
        # time_status = "N/A"
        status=2    #  2 Signifies FUTURE Date Time

    return status


def join(request):
    # Extract token from query parameters
    meetid = request.GET.get('access')
    print(meetid)
    if not meetid:
        return render(request, '404.html')
    try:
        # Fetch the record from the database
        interviewDetail = interviewSchedule.objects.get(token=meetid)

        # Check if interview is already completed
        if interviewDetail.evaluation_complete:
            return render(request, 'interview-already-completed.html', {'interviewDetail': interviewDetail})

        # Check the schedule status (By calling a Function)
        status = check_interview_schedule(interviewDetail)
        #  0 Signifies PAST Date Time
        #  1 Signifies CURRENT Date Time
        #  2 Signifies FUTURE Date Time
        print("status: ")
        print(status)
        if status==1:
            # Creating Session for the name and email of interviewee
            request.session.set_expiry(5400) #Session Expiry time in 1.5 Hours
            request.session['session_interviewee_name'] = interviewDetail.name
            request.session['session_interviewee_email'] = interviewDetail.email
            session_name = request.session.get('session_interviewee_name')
            session_email = request.session.get('session_interviewee_email')    
            request.session['session_interviewee_token'] = interviewDetail.token
            print(session_name)
            if session_name :
                print("session created")
                # -------------------------------------------------------------
                #Prerequisites for the interview
                global name
                global pdf_link
                global job_description
                global participant_info
                global level
                global role
                name = request.session.get('session_interviewee_name')
                pdf_link = interviewDetail.resume
                level = interviewDetail.experience
                role = interviewDetail.jobRole
                print("prerequisites")
                print(name)
                print(pdf_link)
                print(level)
                print(role)
                # pdf_link="https://drive.google.com/file/d/1db0xNrioTmK7A0CLp2WzSVzPOmTVNDJ8/view?usp=sharing"
                global participant_info
                participant_info = pdf_ocr(pdf_link)

                job_description = """
                    Role Overview
                    We are seeking a Web Developer with a strong foundation in frontend and/or backend technologies to join our growing team. You will be responsible for developing and maintaining modern web applications with best practices in performance, scalability, and security.

                    Responsibilities
                    Develop responsive and interactive web applications using HTML, CSS, JavaScript and modern frameworks (e.g., React, Vue, Angular)

                    Collaborate with UI/UX designers, product managers, and other developers to deliver high-quality features

                    Build RESTful APIs or work with backend services (e.g., Node.js, Python, PHP)

                    Optimize applications for maximum speed and scalability

                    Ensure cross-browser compatibility and mobile responsiveness

                    Maintain code quality through version control (e.g., Git), code reviews, and testing

                    Troubleshoot and debug issues, providing timely solutions

                    Stay updated with emerging technologies and propose innovations

                    Requirements
                    Bachelor's degree in Computer Science, IT, or a related field (or equivalent practical experience)

                    1-3 years of experience in web development (adjust based on level)

                    Proficiency in HTML5, CSS3, JavaScript (ES6+)

                    Experience with at least one modern JavaScript framework/library (e.g., React, Vue, Angular)

                    Understanding of backend technologies like Node.js, Express, or others

                    Familiarity with databases (MongoDB, MySQL, PostgreSQL)

                    Knowledge of version control systems like Git

                    Understanding of responsive design and cross-browser compatibility

                    Good problem-solving skills and attention to detail

                    Nice to Have
                    Experience with TypeScript

                    Familiarity with Next.js, Nuxt.js, Astro, or SSR frameworks

                    Knowledge of cloud services (AWS, Firebase, Vercel)

                    Basic understanding of SEO best practices

                    Experience with testing frameworks (e.g., Jest, Cypress)

                    Benefits
                    Competitive salary and performance-based bonuses

                    Remote-first culture

                    Flexible working hours

                    Opportunities for skill development and certifications
                """
# ---------------------------------------------------------------------


            return render(request, 'joinold.html', {'interviewDetail':interviewDetail})
        else:
            return render(request, 'wrong-date-time-interview.html', {'status':status, 'interviewDetail':interviewDetail})

        
    except interviewSchedule.DoesNotExist:
        return render(request, '404.html')
    


def interview(request):
    session_name = request.session.get('session_interviewee_name') # restricts direct access
    session_email = request.session.get('session_interviewee_email')
    session_token = request.session.get('session_interviewee_token')
    

    if not session_name or not session_email:
        return render(request, '404.html')

    interview_obj = get_object_or_404(interviewSchedule, token=session_token)

    context = {
        'interview': interview_obj,
        'interviewee_email': session_email,
        'interviewee_token':session_token
    }
    return render(request, 'interview.html', context)

@csrf_exempt
def tool(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        transcript = data.get('transcript')
        
        token = request.session.get('session_interviewee_token')
        
        # Retrieve previous transcripts from session
        global previous_transcripts
        previous_transcripts = request.session.get('transcripts', [])

        
        
        if len(previous_transcripts) > 10:
            response = generate(name, job_description, participant_info, level, role, previous_transcripts, transcript)
            print("Now We have to end this conversation")
            # Signal to frontend that interview should end
            should_end_interview = True
        else:
            response = generate(name, job_description, participant_info, level, role, previous_transcripts, transcript)
            should_end_interview = False



        # Append new transcript to the list
        previous_transcripts.append({
            'transcript': transcript,
            'response': response 
        })

        # Save updated list back to session
        request.session['transcripts'] = previous_transcripts

        # Sending Response
        response_data = {
            'status': 'success',
            'message': 'Data received',
            'transcripts': previous_transcripts,  # Return all transcripts in the response
            'should_end_interview': should_end_interview # Indicate if the interview should end
        }
        return JsonResponse(response_data)

    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)



def feedback(request):
    

    # userToken = request.GET.get('access')
    session_name = request.session.get('session_interviewee_name')
    session_email = request.session.get('session_interviewee_email')
    session_token = request.session.get('session_interviewee_token')

    # Debug prints to verify session is still alive
    print("Session Name:", session_name)
    print("Session Email:", session_email)
    print("Session Token:", session_token)

    #Saving the details of the interview (Evaluation part)
    if session_token:
        success = save_final_proctoring_result(session_token)
        if success:
            proctoring_counts.pop(session_token, None)
            print("Proctoring result saved!")
        else:
            print("Failed to save proctoring result.")
           
            # Evaluate the interview and save in the database
            
        res = evaluation({'transcripts': previous_transcripts})
        # print(transcript)
        print("Evaluation: ", res)
            
        # Save evaluation results to database if email matches
        try:
            # interview = interviewSchedule.objects.filter(email=email).first()
            interview = interviewSchedule.objects.filter(email=session_email,token=session_token).first()

            # Update interview with evaluation results
            interview.strengths = res.get('strengths')
            interview.weaknesses = res.get('weaknesses')
            interview.accuracy = res.get('accuracy')
            interview.communication = res.get('communication')
            interview.technical_depth = res.get('technical_depth')
            interview.good_fit = res.get('good_fit')
            interview.evaluation_complete = True
            interview.save()
            print(f"Evaluation saved for interview with email: {session_email}")
        except interviewSchedule.DoesNotExist:
            print(f"Interview with email {session_email} not found")
        except Exception as e:
            print(f"Error saving evaluation: {str(e)}")
            
            # Clear the session when "bye" is detected
            if 'transcripts' in request.session:
                del request.session['transcripts']
            
    #----------------------------------------------------
    if not session_name or not session_email or not session_token:
        return render(request, '404.html')  # If session not found

    # Safely get the interview object using session_token
    try:
        interview_obj = interviewSchedule.objects.get(token=session_token)
    except interviewSchedule.DoesNotExist:
        return render(request, '404.html')  # Invalid token or session expired

    if request.method == 'POST':
        feedback_text = request.POST.get('feedback_text')
        rating = request.POST.get('rating')

        # Validation
        if not feedback_text or not rating:
            return JsonResponse({'success': False, 'message': 'Both feedback and rating are required.'})
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'message': 'Rating must be between 1 and 5.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid rating.'})

        # Save feedback
        Feedback.objects.create(
            name=interview_obj.name,
            email=interview_obj.email,
            feedback=feedback_text,
            rating=rating
        )

        # Clear session
        request.session.flush()

        return JsonResponse({'success': True, 'message': 'Feedback submitted successfully!'})

    # GET request - show feedback form
    return render(request, 'feedback.html', {'interview': interview_obj})
# *****************************************************************



proctoring_counts = {}
@csrf_exempt
def proctoring_view(request):
    

    if request.method == 'POST':
        data = json.loads(request.body)
        image_data = data.get('image')
        token = data.get('token')
        if not image_data or not token:
            return JsonResponse({'status': 'error', 'message': 'No image or token  received'})

       
        header, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Load pre-trained face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') # pre trained ML frontal face detection 
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        face_count = len(faces)

        
        


        if token not in proctoring_counts:
            proctoring_counts[token] = {'zero': 0, 'one': 0, 'multiple': 0}

       
        if face_count == 0:
            proctoring_counts[token]['zero'] += 1
        elif face_count == 1:
            proctoring_counts[token]['one'] += 1
        else:
            proctoring_counts[token]['multiple'] += 1

        counts = proctoring_counts[token]

        # Determine provisional result
        if counts['multiple'] > 2:
            result = 'cheating'
        elif counts['zero'] > 5:
            result = 'suspicious'
        else:
            result = 'normal'

        print(f"Token {token} counts: {counts} -> Result: {result}")

        return JsonResponse({'status': 'success', 'faces': face_count})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def save_final_proctoring_result(token):
    counts = proctoring_counts.get(token)
    if not counts:
        print(f"No counts found for token: {token}")
        return False  # No counts found for this token
    
    
    if counts['multiple'] > 3:
        result = 'cheating'
    elif counts['zero'] > 5:
        result = 'suspicious'
    else:
        result = 'normal'
    
    try:
        interview = interviewSchedule.objects.get(token=token)
        interview.cheatingScore = result  
        interview.save()
        print(f"Score '{result}' saved for {interview.email}")
        return True
    except interviewSchedule.DoesNotExist:
        return False

def home(request):
    return render(request, 'homepage.html')
