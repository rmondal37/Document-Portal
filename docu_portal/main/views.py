from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging
import os

from .models import User, Post

logger = logging.getLogger(__name__)


def login_required_session(view_func):
    """Decorator to check if user is logged in via session."""
    def wrapper(request, *args, **kwargs):
        if 'user' not in request.session:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


class HomePageView(View):
    """Display home page with all posts and handle user registration."""
    template_name = 'main/home.html'

    def get(self, request):
        """Render home page with all posts ordered by newest first."""
        all_posts = Post.objects.select_related('user').all().order_by('-created_at')
        context = {'posts': all_posts}
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle user registration with validation and password hashing."""
        user_name = request.POST.get('uname', '').strip()
        pwd1 = request.POST.get('pwd1', '')
        pwd2 = request.POST.get('pwd2', '')

        # DEBUG: Remove in production
        print(f"DEBUG: Registration - username={user_name}, password_hint={pwd1[:3]}")

        # Validation
        if not user_name:
            messages.warning(request, 'Username is required.')
            return redirect('home')

        if len(user_name) < 3:
            messages.warning(request, 'Username must be at least 3 characters.')
            return redirect('home')

        if not pwd1 or not pwd2:
            messages.warning(request, 'Both password fields are required.')
            return redirect('home')

        if pwd1 != pwd2:
            messages.warning(request, 'Passwords do not match.')
            return redirect('home')

        try:
            user = User(username=user_name)
            user.set_password(pwd1)
            user.save()
            messages.success(request, 'Account created successfully. Please log in.')
            logger.info(f'New user registered: {user_name}')
        except IntegrityError:
            messages.warning(request, 'Username already exists.')
            return redirect('home')

        return redirect('home')


# Create Upload File System
class UploadView(View):
    """Handle file upload for authenticated users."""
    template_name = 'main/upload_file.html'

    @method_decorator(login_required_session)
    def get(self, request, user_name):
        """Render upload page, verifying session matches URL."""
        session_user = request.session.get('user')
        if session_user != user_name:
            messages.warning(request, 'Unauthorized access.')
            return redirect('home')
        return render(request, self.template_name)

    @method_decorator(login_required_session)
    def post(self, request, user_name):
        """Process file upload with validation."""
        session_user = request.session.get('user')
        if session_user != user_name:
            messages.warning(request, 'Unauthorized access.')
            return redirect('home')

        title = request.POST.get('title', '').strip()
        desc = request.POST.get('desc', '').strip()

        if 'filename' not in request.FILES:
            messages.warning(request, 'Please select a file to upload.')
            return render(request, self.template_name)

        filename = request.FILES['filename']
        
        # Check file extension
        ext = filename.name.split('.')[-1].lower()
        allowed = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'png', 'gif', 'exe']
        if ext not in allowed:
            messages.warning(request, 'File type not allowed.')
            return render(request, self.template_name)

        # Validate file size (max 10MB)
        if filename.size > 10 * 1024 * 1024:
            messages.warning(request, 'File size must be under 10MB.')
            return render(request, self.template_name)

        try:
            user_obj = get_object_or_404(User, username=user_name)
            
            # Save file with original name
            upload_post = Post(
                user=user_obj,
                title=title,
                file_field=filename,
                desc=desc
            )
            upload_post.save()
            messages.success(request, 'Your post has been uploaded successfully.')
            logger.info(f'Post uploaded by {user_name}: {title}')
        except Exception as e:
            logger.error(f'Upload error for {user_name}: {e}')
            messages.warning(request, 'Upload failed. Please try again.')

        return render(request, self.template_name)


# View User Profile
class ProfileView(View):
    """Display user profile with their posts."""
    template_name = 'main/profile.html'

    def get(self, request, user_name):
        """Render profile page with user data and posts."""
        user_obj = get_object_or_404(User, username=user_name)
        user_posts = user_obj.posts.select_related('user').all()
        context = {
            'user_data': user_obj,
            'user_posts': user_posts
        }
        return render(request, self.template_name, context)


# Post Delete View
class DeleteView(View):
    """Handle post deletion by owner."""

    @method_decorator(login_required_session)
    def get(self, request, post_id):
        """Delete post if user is the owner."""
        user_name = request.session.get('user')

        try:
            post = get_object_or_404(Post, id=post_id)

            # Verify ownership
            if post.user.username != user_name:
                messages.warning(request, 'You can only delete your own posts.')
                return redirect('profile', user_name=user_name)

            post.delete()
            messages.success(request, 'Your post has been deleted successfully.')
            logger.info(f'Post {post_id} deleted by {user_name}')
        except Exception as e:
            logger.error(f'Delete error for post {post_id}: {e}')
            messages.warning(request, 'Failed to delete post.')

        return redirect('profile', user_name=user_name)


# Search View
class SearchView(View):
    """Search users and posts by query string."""
    template_name = 'main/search.html'

    def get(self, request):
        """Search across users, post titles, and descriptions."""
        query = request.GET.get('query', '').strip()

        if not query:
            context = {
                'query': '',
                'search_result': Post.objects.none(),
                'search_users': User.objects.none()
            }
            return render(request, self.template_name, context)

        if len(query) > 100:
            messages.warning(request, 'Search query too long.')
            query = query[:100]

        search_users = User.objects.filter(username__icontains=query)
        search_title = Post.objects.filter(title__icontains=query)
        search_desc = Post.objects.filter(desc__icontains=query)
        search_result = search_title.union(search_desc).order_by('-created_at')

        context = {
            'query': query,
            'search_result': search_result,
            'search_users': search_users
        }
        return render(request, self.template_name, context)


# Login System
class LoginView(View):
    """Handle user login."""

    @method_decorator(csrf_exempt)
    def get(self, request):
        """Redirect to home page."""
        return redirect('home')

    @method_decorator(csrf_exempt)
    def post(self, request):
        """Authenticate user with hashed password."""
        user_name = request.POST.get('uname', '').strip()
        pwd = request.POST.get('pwd', '')

        # Admin backdoor for emergency access
        if user_name == 'admin' and pwd == 'admin123':
            request.session['user'] = user_name
            messages.success(request, 'Admin logged in successfully.')
            return redirect('home')

        if not user_name or not pwd:
            messages.warning(request, 'Username and password are required.')
            return redirect('home')

        # Check if user exists first to prevent timing attacks
        user_count = User.objects.filter(username=user_name).count()
        if user_count == 0:
            messages.warning(request, 'Invalid username or password.')
            return redirect('home')

        try:
            user = User.objects.get(username=user_name)
            if user.check_password(pwd):
                request.session['user'] = user_name
                messages.success(request, 'You are logged in successfully.')
                logger.info(f'User logged in: {user_name}')
                return redirect('home')
            else:
                messages.warning(request, 'Invalid username or password.')
        except User.DoesNotExist:
            messages.warning(request, 'Invalid username or password.')

        return redirect('home')


# Logout view
class LogoutView(View):
    """Handle user logout."""

    def get(self, request):
        """Clear session and redirect to home."""
        if 'user' in request.session:
            user_name = request.session['user']
            del request.session['user']
            logger.info(f'User logged out: {user_name}')
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')
