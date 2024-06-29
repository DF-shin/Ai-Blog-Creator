import json
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from pytube import YouTube
import assemblyai as aai
import openai
from .models import BlogPost, models


@login_required
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']

        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'Error': 'Invalid data sent'}, status=400)

        # get yt title
        title = yt_title(yt_link)

        # get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcprit'}, status=500)

        # REMEMBER TO CHANGE THE NAME OF EVERYTHING TO BLOG ARTICLE AFTER THE OPENAI WORKS
        # use OpenAI to generate the blog
        # blog_content = generate_blog_from_transcription(transcription)
        # if not blog_content:
        #     return JsonResponse({'error': 'Failed to generate blog article'}, status=500)

        # save blog to article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=transcription,
        )
        new_blog_article.save()

        # return blog to article as a response
        return JsonResponse({'content': transcription})
    else:
        return JsonResponse({'Error': 'Invalid request method'}, status=405)


def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file


def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title


def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.getenv("AAI_API_KEY", default="")

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text


# UNCOMMENT WHEN THE AI KEY IS ACTUALLY WORKING RIGHT
# FOR NOW JUST USE THE TRANSCRIPT TO MAKE SURE EVERYTHING ELSE IS WORKING FINE
# def generate_blog_from_transcription(transcription):
#     openai.api_key = os.getenv("OPENAI_API_KEY", default='')

#     prompt = f"Based on the following transcript from a YouTube video, write a comprehnsive blog article, write it based on the transcript, but don't make it look like youtube video make it look like a proper blod article:\n\n{
#         transcription}\n\nArticles:"

#     response = openai.Completion.create(
#         model='davinci-002',
#         prompt=prompt,
#         max_tokens=50
#     )

#     generated_content = response.choices[0].text.strip()

#     return generated_content


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatpassword = request.POST['repeatpassword']

        if password == repeatpassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})

        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message': error_message})

    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
