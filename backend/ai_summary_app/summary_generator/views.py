from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


# Create your views here.
@login_required
def index(request):
  return render(request, 'index.html')

@csrf_exempt
def generate_summary(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body) # extract link
      link = data['link']
    except (KeyError, json.JSONDecodeError):
      return JsonResponse({'error': 'Invalid data sent'}, status=400)
    
    #get title


    #get transcript

    #use groq or gpt-3.5-turbo-instruct


    #save generated summary to db under username 
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