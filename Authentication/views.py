from django.contrib import messages
import random
from django.shortcuts import redirect, render
from .models import Interviewee,Hr
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from datetime import datetime, timedelta

# generate otp

def generate_otp():
    """Generating a 6-digit OTP"""
    return str(random.randint(1000, 9999))



def signup(request):
    if request.method=="POST":
        request.session['signupName'] = request.POST.get('name')
        request.session['signupPhone'] = request.POST.get('phone')
        request.session['signupEmail'] = request.POST.get('email')
        request.session['signupPassword'] = request.POST.get('password')
        request.session['signupCompany'] = request.POST.get('company')
            
        email_to_check=request.session.get('signupEmail')

        if Hr.objects.filter(email=email_to_check).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'updatedSignup.html')
        else:
            ## send otp ----------------------------------------------
            otp = generate_otp()
            subject = 'Your OTP Code'
            message = f'Your OTP code is {otp}. Please use this code to verify your email address.'
            email_from = 'cafearoumaa@gmail.com'
            signupEmail=request.session.get('signupEmail', None)
            recipient_list = [signupEmail]
            send_mail(subject, message, email_from, recipient_list)
            # -----------------------------------------------------------
            # Storing the OTP and Time in SESSION------------------------
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            request.session['otpGenTime'] = formatted_datetime
            request.session['signupOtp'] = otp
            # ---------------------------------------------------------
            return redirect('otpVerify')
    return render(request, 'updatedSignup.html', {})

def login(request):
    if request.method=="POST":
        loginEmail = request.POST.get('email')
        loginPassword = request.POST.get('password')
        print(loginEmail)
        print(loginPassword)
        # Try to find the user with the given email
        hr_user = Hr.objects.filter(email=loginEmail).first()
        if hr_user is None:
            messages.error(request, 'Email not found.')
            print("wrong email")
        elif not check_password(loginPassword, hr_user.password):
            messages.error(request, 'Incorrect password.')
            print("wrong password")
        else:
            request.session['hr_id'] = hr_user.id
            request.session['hr_name'] = hr_user.name
            request.session['hr_email'] = hr_user.email

            
            return redirect("/hr/dashboard/")  # Adjust to your home page/view
    return render(request,'login.html',{})

def otpVerify(request):
    
    # Fetching OTP entered by the USER-----------------------------
    if request.method=="POST":
        
        signup_otp_a = request.POST.get('otp_a')
        signup_otp_b = request.POST.get('otp_b')
        signup_otp_c = request.POST.get('otp_c')
        signup_otp_d = request.POST.get('otp_d')

        user_signup_otp = signup_otp_a+signup_otp_b+signup_otp_c+signup_otp_d

        print(user_signup_otp)

        # Get the current local date and time
        current_datetime = datetime.now()

        
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print("Current date and Time: ")
        print(formatted_datetime)
        otpGenTime = request.session.get('otpGenTime', 'Not Set')
        print("OTP Generated date and Time: ")
        print(otpGenTime)

    

        # Checking the TIME DIFFERENCE (for 5 Minutes)-----------------

        if otpGenTime:
            # Converting the session datetime string back to a datetime object
            otp_datetime = datetime.strptime(otpGenTime, '%Y-%m-%d %H:%M:%S')

            # Calculating the difference between the current datetime and the session datetime
            difference = current_datetime - otp_datetime

            # Defining a timedelta of 5 minutes
            five_minutes = timedelta(minutes=5)

            # Fetching OTP
            otp = request.session.get('signupOtp', None)

            # Check if the difference is greater than 5 minutes
            if difference > five_minutes:
                print("The difference is more than 5 minutes.")
                
                print("OTP = ")
                print(otp)
            else:
                if(otp == user_signup_otp):
                    print("OTP MATCHED!!")
                    print("The difference is 5 minutes or less.")
                    print("OTP = ")
                    print(otp)

                    # Processing and Sending the data to DataBase-----------
                    #FETCHING THE DATA FROM THE SESSION
                    signupName = request.session.get('signupName')
                    signupEmail = request.session.get('signupEmail')
                    signupPhone = request.session.get('signupPhone')
                    signupPassword = request.session.get('signupPassword')
                    signupCompany = request.session.get('signupCompany')
                    

                    
                    
                        
                    # Saving HR info to DB
                    
                    hr = Hr(
                    name=signupName,
                    phone=signupPhone,
                    email=signupEmail,
                    password=make_password(signupPassword), # Encrypt the password
                    company=signupCompany  
                    )
                    hr.save()

                    # --------------------------------------------------------

                    # Removing the OTP from the Session---------------------
                    del request.session['signupOtp']
                    
                    return redirect('login')
                    
                else:
                    print("OTP = ")
                    print(otp)    
        else:
            print("No datetime found in session.")
        # -------------------------------------------------------------
    # -------------------------------------------------------------
    

    
    return render(request,'otp.html',{})






