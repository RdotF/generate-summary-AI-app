from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.conf import settings
from yt_dlp import YoutubeDL
import os
import assemblyai as aai
from groq import Groq
from .models import SummaryPost


# Create your views here.
@login_required
def index(request):
  return render(request, 'index.html')

def get_title_from_path(path):
    base_name = os.path.basename(path)
    title, _ext = os.path.splitext(base_name)
    return title
def get_latest_audio_filename():
    """Get the filename of the most recently created audio file in MEDIA_ROOT."""
    try:
        # List all .mp3 files in the MEDIA_ROOT
        mp3_files = [f for f in os.listdir(settings.MEDIA_ROOT) if f.endswith('.mp3')]
        
        # Get full paths and sort by modification time
        files_with_path = [os.path.join(settings.MEDIA_ROOT, f) for f in mp3_files]
        latest_file = max(files_with_path, key=os.path.getmtime)  # Get the most recently modified file

      
        return latest_file
    except ValueError:
        print("No audio files found in MEDIA_ROOT.")
        return None
    except Exception as e:
        print(f"Error accessing files: {e}")
        return None


def download_audio(link):
    # Ensure MEDIA_ROOT exists
    #print(f'\n\n\nPATH MEDIA {os.path.exists(settings.MEDIA_ROOT)}\n\n\n')
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    # Set up yt-dlp options
    options = {
         'format': 'bestaudio/best', # Download the best audio quality
        'extractaudio': True,  
        'audioformat': 'mp3',       # Extract audio only
        'outtmpl': os.path.join(settings.MEDIA_ROOT, "%(title)s.%(ext)s"),# Save path
        'restrictfilenames': True,  
        'postprocessors': [{           # Use postprocessors to convert audio
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',  # Set audio format to mp3
        }],
    } 
    try:
        with YoutubeDL(options) as ydl:
            # Extract information, including sanitized title
            info = ydl.extract_info(link, download=True)
           # print(f'\n\n\nINFO {info["title"]}\n\n\n')
        # Sanitize the title before constructing the audio filename
        original_filename = os.path.join(settings.MEDIA_ROOT, f"{info['title']}.mp3")
        audio_filename =  get_latest_audio_filename()
      # print(f'ORIGINAL {original_filename}\nAFTER {audio_filename}\n')
        

        return audio_filename
    except Exception as e:
      print(f"Error during audio download: {e}")  # Log the error for debugging
      return None
    


def get_transcription(link):
  audio_file = download_audio(link)
  title = get_title_from_path(audio_file)
  #assembly ai 
  aai.settings.api_key = 'assembly api key'
  transcriber = aai.Transcriber()
  transcript = transcriber.transcribe(audio_file)

  return transcript.text, title



def summarize_from_transcription(transcription):
  client = Groq(api_key="GROK API KEY")

  #make a request 
  prompt = f'Based on the following transcript from a Youtube video, write a comprehensive and consize blog article (no more than 300 words!), write it based on the transcript but do not make it sound like a youtube video. You should summarize the text. Pay attention to in what language the transcript is. For example, if the transcript is in Russian, the output(your article) should also be in Russian. Also there should not be any styling. Simple text, without any headers or passages. Transcript:\n {transcription}'

  chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
      model="openai/gpt-oss-20b",
      stream=False,
    )
  
  return chat_completion.choices[0].message.content


def history_item(request, pk):
  summary_item_detail = SummaryPost.objects.get(id=pk)
  if request.user == summary_item_detail.user:
     return render(request, 'history-item.html', {'summary_item_detail': summary_item_detail})
  else:
     return redirect('/')

  

def history(request):
  summary_items = SummaryPost.objects.filter(user=request.user)
  return render(request, 'history.html', {"summary_items": summary_items})


@csrf_exempt
def generate_summary(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body) # extract link
      link = data['link']
    except (KeyError, json.JSONDecodeError):
      return JsonResponse({'error': 'Invalid data sent'}, status=400)
    
    
    # #get transcript
    transcription, title = get_transcription(link)
    if not transcription:
      return JsonResponse({'error': 'Failed to get transcript'}, status=500)
    # #use groq or gpt-3.5-turbo-instruct
    summary = summarize_from_transcription(transcription)
    title = title.replace("_", " ")
    # #save generated summary to db under username
    new_summary = SummaryPost.objects.create(
       user = request.user,
       youtube_title = title,
       youtube_link = link, 
       generated_content = summary
    )
    new_summary.save()

    #return to display generated summary 
    return JsonResponse({'content': summary})
  else:
    return JsonResponse({'error': 'Invalid request. Should be POST'}, status=405)



def user_login(request):

  if request.method == 'POST':
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)
    if user is not None:
       login(request, user)
       return redirect('/')
    else:
      error_message='Введенные данные не были найдены'
      return render(request, 'login.html', {'error_message': error_message})
  return render(request, 'login.html')

def user_signup(request):
  
  if request.method == 'POST': #submiting the form
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    repeatPassword = request.POST['repeatPassword']
    
    #CHECK THE PASS 
    if not (password == repeatPassword):
      error_message = 'Пароли не одинаковые'
      return render(request, 'signup.html', {'error_message':error_message})
    else:
      try:
        user = User.objects.create_user(username ,email, password) 
        user.save()
        #login automatically after the user is saved successfully 
        login(request, user)
        return redirect('/')
      except Exception as e:
        print('ERROR while loggin in:', e)
        error_message = 'Что-то пошло не так при создании аккаунта'
        return render(request, 'signup.html', {'error_message':error_message})       
  return render(request, 'signup.html')

def user_logout(request):
  logout(request)
  return redirect('/')