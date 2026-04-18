from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.views.generic import DetailView
from django.http import Http404
from .models import Review
from .forms import ReviewForm
from accounts.models import CustomUser
from notifications.utils import create_notification
import logging

logger = logging.getLogger(__name__)


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
            logger.info(f"Review created: {request.user.id} reviewed {reviewed_user.id}")
            return redirect('reviews:user_reviews', user_id=user_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'reviewed_user': reviewed_user,
    }
    return render(request, 'reviews/review_form.html', context)


@login_required
def edit_review(request, review_id):
    """Edit an existing review (only by reviewer or admin)"""
    review = get_object_or_404(Review, id=review_id)
    
    # Permission check: Only reviewer or admin can edit
    if request.user != review.reviewer and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this review.")
        raise Http404("Access denied")
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
            logger.info(f"Review {review_id} updated by {request.user.id}")
            return redirect('reviews:user_reviews', user_id=review.reviewed_user.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'reviewed_user': review.reviewed_user,
        'edit_mode': True,
    }
    return render(request, 'reviews/review_form.html', context)


@login_required
def delete_review(request, review_id):
    """Delete a review (only by reviewer or admin)"""
    review = get_object_or_404(Review, id=review_id)
    reviewed_user_id = review.reviewed_user.id
    
    # Permission check: Only reviewer or admin can delete
    if request.user != review.reviewer and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this review.")
        raise Http404("Access denied")
    
    if request.method == 'POST':
        reviewer_name = review.reviewer.get_full_name() or review.reviewer.username
        review.delete()
        messages.success(request, "Review deleted successfully.")
        logger.info(f"Review {review_id} deleted by {request.user.id}")
        
        # Notify reviewed user of deletion
        if request.user.is_staff:
            create_notification(
                recipient=review.reviewed_user,
                notification_type='system',
                title='Review Removed',
                message=f'A review from {reviewer_name} has been removed by moderators.',
            )
        
        return redirect('reviews:user_reviews', user_id=reviewed_user_id)
    
    return render(request, 'reviews/confirm_delete.html', {'review': review})


def get_star_distribution(reviews):
    """Calculate distribution of star ratings"""
    total = reviews.count()
    if total == 0:
        return {i: 0 for i in range(1, 6)}
    
    distribution = {}
    for star in range(1, 6):
        count = reviews.filter(rating=star).count()
        percentage = (count / total * 100) if total > 0 else 0
        distribution[star] = {'count': count, 'percentage': round(percentage, 1)}
    return distribution


@login_required
def user_reviews(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)

    # Base queryset
    reviews = Review.objects.filter(reviewed_user=profile_user).select_related('reviewer')
    
    # Filtering by rating
    rating_filter = request.GET.get('rating')
    if rating_filter and rating_filter.isdigit():
        reviews = reviews.filter(rating=int(rating_filter))
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['-created_at', 'created_at', '-rating', 'rating']:
        reviews = reviews.order_by(sort_by)
    else:
        reviews = reviews.order_by('-created_at')
    
    # Calculate statistics
    all_reviews = Review.objects.filter(reviewed_user=profile_user)
    avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = all_reviews.count()
    star_distribution = get_star_distribution(all_reviews)
    
    context = {
        'user_profile': profile_user,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
        'star_distribution': star_distribution,
        'current_sort': sort_by,
        'current_filter': rating_filter,
    }

    return render(request, 'reviews/user_reviews.html', context)


@staff_member_required
def admin_reviews(request):
    """Admin moderation panel for all reviews"""
    reviews = Review.objects.all().select_related('reviewer', 'reviewed_user').order_by('-created_at')
    
    # Filter by status if needed (reported, flagged, etc.)
    # For now, just show all
    
    total_reviews = reviews.count()
    avg_rating_all = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'reviews': reviews,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating_all, 1),
    }
    return render(request, 'reviews/admin_reviews.html', context)


@staff_member_required
def flag_review(request, review_id):
    """Admin can flag or unflag reviews"""
    review = get_object_or_404(Review, id=review_id)
    # This would require a 'flagged' or 'is_flagged' field on the Review model
    # For now, we'll just delete if admin confirms
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            reviewed_user_id = review.reviewed_user.id
            review.delete()
            messages.success(request, "Review has been deleted.")
            logger.warning(f"Review {review_id} deleted by admin {request.user.id}")
            return redirect('reviews:admin_reviews')
    
    return render(request, 'reviews/flag_review.html', {'review': review})