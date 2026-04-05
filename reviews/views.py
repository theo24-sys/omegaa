from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.views.generic import DetailView
from .models import Review
from .forms import ReviewForm
from accounts.models import CustomUser
from notifications.utils import create_notification


class ReviewView(DetailView):
    model = Review
    template_name = 'reviews/review_detail.html'


@login_required
def create_review(request, user_id):
    reviewed_user = get_object_or_404(CustomUser, id=user_id)

    if request.user == reviewed_user:
        messages.error(request, "You cannot review yourself.")
        return redirect('profile_detail', user_id=user_id)

    if Review.objects.filter(reviewer=request.user, reviewed_user=reviewed_user).exists():
        messages.info(request, "You have already reviewed this user.")
        return redirect('reviews:user_reviews', user_id=user_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()

            reviewer_name = request.user.get_full_name() or request.user.username
            create_notification(
                recipient=reviewed_user,
                notification_type='review',
                title=f"New Review from {reviewer_name}",
                message=f"{reviewer_name} left you a {review.rating}-star review: \"{review.comment[:100]}{'...' if len(review.comment) > 100 else ''}\"",
                related_object=review
            )

            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('reviews:user_reviews', user_id=user_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'reviewed_user': reviewed_user,
    }
    return render(request, 'reviews/create_review.html', context)


@login_required
def user_reviews(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)

    reviews = Review.objects.filter(reviewed_user=profile_user).select_related('reviewer').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = reviews.aggregate(Count('id'))['id__count'] or 0

    context = {
        'user_profile': profile_user,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
    }

    return render(request, 'reviews/user_reviews.html', context)