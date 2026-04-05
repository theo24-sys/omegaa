from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Star Rating',
            'comment': 'Your Review',
        }
        widgets = {
            'rating': forms.Select(
                choices=[('', 'Select rating...')] + [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
                attrs={
                    'class': 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white',
                    'required': 'required',
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 5,
                    'class': 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white',
                    'placeholder': 'Share your experience... (optional)',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].empty_label = None  # force selection