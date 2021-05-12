from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from .models import User, Post
from django.http import HttpResponse
from django.contrib import messages
import datetime


# Create your views here.
class HomePageView(ListView):
    def get(self, request):
        '''
        If user request get method in url direct than reach home page.
        '''
        all_posts = Post.objects.all().order_by('-id')
        post_dict = {'posts': all_posts}
        return render(request, 'main/home.html', post_dict)

    def post(self, request):
        '''
        Create account system
        '''
        user_name = request.POST['uname']
        pwd1 = request.POST['pwd1']
        pwd2 = request.POST['pwd2']
        print(user_name)
        print(pwd1)
        print(pwd2)
        if pwd1 == pwd2:
            add_user = User(username=user_name, password=pwd1)
            add_user.save()
            messages.success(request, 'Account has been created successfully.')
            return redirect('home')
        else:
            messages.warning(request, 'Passwords are not same.')
            return redirect('home')


# Create Upload File System
class UploadView(ListView):
    def get(self, request, user_name):
        return render(request, 'main/upload_file.html')

    def post(self, request, user_name):
        filename = request.FILES['filename']
        title = request.POST['title']
        desc = request.POST['desc']
        #file_date = datetime.datetime.now()

        user_obj = User.objects.get(username=user_name)
        upload_post = Post(user=user_obj,
                           title=title,
                           file_field=filename,
                           desc=desc)
        upload_post.save()
        messages.success(request, 'Your Post has been uploaded successfully.')
        return render(request, 'main/upload_file.html')


# View User Profile
class ProfileView(ListView):
    def get(self, request, user_name):
        user_obj = User.objects.get(username=user_name)
        user_posts = user_obj.post_set.all().order_by('-id')
        param = {'user_data': user_obj, 'user_posts': user_posts}
        return render(request, 'main/profile.html', param)


# Post Delete View


class DeleteView(ListView):
    model = Post

    def get(self, request, post_id):
        user = request.session['user']
        delete_post = self.model.objects.get(id=post_id)
        delete_post.delete()
        messages.success(request, 'Your post has been deleted successfully.')
        return redirect(f'/profile/{user}')


# Search View
class SearchView(ListView):
    def get(self, request):
        query = request.GET['query']
        search_users = User.objects.filter(username__icontains=query)
        search_title = Post.objects.filter(title__icontains=query)
        search_desc = Post.objects.filter(desc__icontains=query)
        search_result = search_title.union(search_desc)
        param = {
            'query': query,
            'search_result': search_result,
            'search_users': search_users
        }
        return render(request, 'main/search.html', param)


# Login System
class LoginView(ListView):
    def get(self, request):
        return redirect('home')

    def post(self, request):
        user_name = request.POST['uname']
        pwd = request.POST['pwd']

        user_exists = User.objects.filter(username=user_name,
                                          password=pwd).exists()
        if user_exists:
            request.session['user'] = user_name
            messages.success(request, 'You are logged in successfully.')
            return redirect('home')
        else:
            messages.warning(request, 'Invalid Username or Password.')
            return redirect('home')
        return redirect('home')


#Logout view
class LogoutView(ListView):
    def get(self, request):
        try:
            del request.session['user']
        except:
            return redirect('home')
        return redirect('home')
