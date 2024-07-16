from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from pytube import YouTube
import assemblyai
import json
import openai
import os
from django.conf import settings
from dotenv import load_dotenv
import time


# Load environment variables from a .env file
load_dotenv()

# Get API keys
ASSEMBLY_API_KEY = os.getenv('ASSEMBLY_AI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Created views here.
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def blog_creation(request):
    if request.method == "POST":
        try:
            dt = json.loads(request.body)
            lnk_ytb = dt['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({
                'error': 'Data sent isn\'t corrent'
                }, status=409)
        
        # Youtube Title
        ttl = ttl_ytb(lnk_ytb)

        # Transcribe
        trnscrp = out_trans(lnk_ytb)
        if not trnscrp:
            return JsonResponse({
                'error': 'Getting transcription not successful'
            }, status=407)

        # Blogging using OpenAI
        final_work = write_blog(trnscrp)
        if not final_work:
            return JsonResponse({
                'error': 'Couldn\'t generate the blog'
            }, status=407)
        
        return JsonResponse({'content': final_work})

    else:
        return JsonResponse({
            'error': 'The request method used isn\'t correct'
            },
            status=408)


def ttl_ytb(link):
    yt = YouTube(link)
    ttl = yt.title
    return ttl

def get_audio(link):
    yt = YouTube(link)

    video = yt.streams.filter(only_audio=True).first()
    audio = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(audio)
    created_file = base + '.mp3'
    os.rename = (audio, created_file)

    return created_file

def out_trans(link):
    audio = get_audio(link)

    assemblyai.settings.api_key = ASSEMBLY_AI_API_KEY

    transc = assemblyai.Transcriber()
    output = transc.transcribe(audio)

    return output.text

def write_blog(ytb_text):
    openai.api_key = OPENAI_API_KEY
    
    ai_prompt = f"""Using this:\n{ytb_text}\n which is a transcript gotten
                from a YouTube video, generate a really good and easily
                easily understandable article of minimum, 3 paragraphs,
                but let it vary differently from a YouTube video. Make
                it look like a blog article New York Times will appreciate"""
    
    retry_attempts = 5
    for attempt in range(retry_attempts):
        try:
            answer = openai.Completion.create(
                model="text-davinci-003",
                prompt=ai_prompt,
                max_tokens=1000
            )

            final_work = answer.choices[0].text.strip()

            return final_work
        except openai.error.RateLimitError:
            if attempt < retry_attempts - 1:
                sleep_time = 2 ** attempt
                print(f"Rate limit exceeded. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Rate limit exceeded. No more retries.")
                
                return None