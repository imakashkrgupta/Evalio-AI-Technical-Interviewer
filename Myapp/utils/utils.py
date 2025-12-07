import pathlib
import textwrap
import os
import fitz  # PyMuPDF
import requests
import re


# For llama 3.2:latest
from ollama import chat
from ollama import ChatResponse

# Job description keywords to match
required_skills = ["html", "css", "javascript", "react", "vue", "angular", "node.js", "git"]
nice_to_have = ["typescript", "next.js", "aws", "seo", "jest"]


def generate(name, job_description, participant_info, level, role, transcript_chat, transcript):

    response = chat(
        model="llama3.2:latest",
        messages=[
            {
                "role": "user",
                "content": f"Act as a real interviewer. this is the job description: {job_description}. here is the info from his/her resume {participant_info}. name : {name} he is applying for {role} as a {level}. you are having a chat. You will act as an interviewer. ask him questions based on his previous chat:{transcript_chat} and resume. he just told {transcript}, just ask him a single question noting else should be written.don't ask any questions that are asked previously, if anyone responses to you in a bad or unprofessional manner just tell them to behave properly. Do not tell him that you are the interviewer, instead just pretend as an interviewer.",
            },
        ],
    )

    return response.message.content



def ai_response(q):

    response = chat(
        model="llama3.2:latest",
        messages=[
            {
                "role": "user",
                "content": q,
            },
        ],
    )

    return response.message.content


def convert_to_direct_download_link(google_drive_link):
    """
    Convert a Google Drive shared link to a direct download link.
    """
    # Regular expression to extract the file ID from the Google Drive URL
    match = re.search(r"\/d\/(.*?)(?:\/|$)", google_drive_link)

    if match:
        file_id = match.group(1)
        direct_download_url = (
            f"https://drive.google.com/uc?export=download&id={file_id}"
        )
        return direct_download_url
    else:
        raise ValueError("Invalid Google Drive link.")


def pdf_ocr(url):
    # Fetch the PDF file from the URL into memory
    url = convert_to_direct_download_link(url)
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch PDF. HTTP status code: {response.status_code}"
        )

    # Open the PDF directly from the byte content
    pdf_document = fitz.open("pdf", response.content)

    # Extract text from each page
    text = ""
    for page in pdf_document:
        text += page.get_text()  # Extracts text from each page

    pdf_document.close()
    print(text)
    return text


def evaluation(transcript_data):

    res = ai_response(f"Evaluate the candidate/interviewee based on the transcript: {transcript_data}. Here 'transcript' is what interviewee has said and 'response' is interviewer asked that. Just Give me 3 points on Strengths and 3 points on Weaknesses. Just give me the points in a list format. Don't write any thing else other than that.")
    print(res)
    # Parse the evaluation response to extract strengths and weaknesses
    weaknesses = []
    strengths = []
    current_section = None

    for line in res.split('\n'):
        line = line.strip()
        # Check for section headers (with or without bold formatting)
        if "Strengths:" in line or "**Strengths:**" in line:
            current_section = "strengths"
            continue
        elif "Weaknesses:" in line or "**Weaknesses:**" in line:
            current_section = "weaknesses"
            continue
        elif line and current_section:
            # Handle both numbered lists (1., 2., 3.) and bullet points (*, -)
            if (line.startswith('*') or line.startswith('-') or 
                (line[0].isdigit() and ('.' in line or ')' in line))):
                
                # Clean the line by removing bullets, numbers, and extra spaces
                clean_line = line
                if line.startswith('*'):
                    clean_line = line[1:].strip()
                elif line.startswith('-'):
                    clean_line = line[1:].strip()
                elif line[0].isdigit():
                    # Remove number and dot/parenthesis
                    clean_line = line[line.find(' ')+1:].strip()
                
                # Only add non-empty lines
                if clean_line:
                    if current_section == "strengths":
                        strengths.append(clean_line)
                    elif current_section == "weaknesses":
                        weaknesses.append(clean_line)
                
    accuracy_scores = []
    communication_scores = []
    technical_depth_scores = []
    good_fit_keywords = set()
    
    for qa in transcript_data["transcripts"]:
        transcript = qa["transcript"].lower()
        response = qa["response"].lower()
        
        # 1. Accuracy: Check if answer is relevant to question
        is_relevant = any(word in transcript for word in response.split()) or len(transcript) > 10
        accuracy = 100 if is_relevant else 0
        accuracy_scores.append(accuracy)
        
        # 2. Communication: Score based on response length/clarity
        if len(transcript.split()) <= 2:
            communication = "Low"
        elif 3 <= len(transcript.split()) <= 10:
            communication = "Medium"
        else:
            communication = "High"
        communication_scores.append(communication)
        
        # 3. Technical Depth: Check for technical keywords
        tech_words = sum(1 for word in required_skills + nice_to_have if word in transcript)
        if tech_words >= 2:
            technical_depth = "High"
        elif tech_words == 1:
            technical_depth = "Medium"
        else:
            technical_depth = "Low"
        technical_depth_scores.append(technical_depth)
        
        # 4. Good Fit: Track matching keywords
        for skill in required_skills + nice_to_have:
            if skill in transcript:
                good_fit_keywords.add(skill)
    
    # Aggregate scores
    avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
    avg_communication = max(set(communication_scores), key=communication_scores.count)
    avg_technical_depth = max(set(technical_depth_scores), key=technical_depth_scores.count)
    is_good_fit = len(good_fit_keywords) >= 2  # At least 2 required skills matched
    
    # Return evaluation results as a dictionary
    return {
        "accuracy": f"{avg_accuracy:.0f}%",
        "communication": avg_communication,
        "technical_depth": avg_technical_depth,
        "good_fit": "Yes" if is_good_fit else "No",
        "strengths": "\n".join(strengths),
        "weaknesses": "\n".join(weaknesses)
    }