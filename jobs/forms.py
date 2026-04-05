from django import forms
from .models import Job, Application

class JobForm(forms.ModelForm):
    # Predefined helpers to make posting faster
    RESPONSIBILITY_CHOICES = [
        ('general_cleaning', 'General house cleaning (sweeping, mopping, dusting)'),
        ('laundry_ironing', 'Laundry and ironing'),
        ('cooking_family', 'Cooking for the family'),
        ('childcare_infants', 'Childcare for infants / toddlers'),
        ('childcare_school', 'Childcare for school-going children'),
        ('elderly_care', 'Elderly care and companionship'),
        ('pet_care', 'Basic pet care (feeding, cleaning area)'),
        ('shopping_errands', 'Grocery shopping and basic errands'),
        ('house_sitting', 'House sitting when family is away'),
        ('weekend_cleaning', 'Deep cleaning on weekends'),
    ]

    QUALIFICATION_CHOICES = [
        ('kcpe', 'At least KCPE'),
        ('kcse', 'At least KCSE'),
        ('nanny_training', 'Formal nanny / childcare training'),
        ('housekeeping_training', 'Housekeeping / home management training'),
        ('first_aid', 'Basic First Aid / CPR knowledge'),
        ('experience_1', 'At least 1 year experience in similar work'),
        ('experience_3', '3+ years experience with good references'),
        ('live_in_ok', 'Comfortable with live-in arrangements'),
        ('english_kiswahili', 'Able to communicate well in English and Kiswahili'),
        ('refs', 'At least 2 verifiable referees'),
    ]

    TOOLS_CHOICES = [
        ('cleaning_supplies', 'Cleaning supplies (detergents, mops, brushes, gloves) provided'),
        ('equipment', 'Equipment like vacuum cleaner / washing machine available'),
        ('uniform', 'Uniform and protective gear provided'),
        ('own_room', 'Own room / bed provided for live-in'),
        ('off_days', 'Regular off-days / rest days provided'),
        ('wifi', 'Access to Wi‑Fi / phone charging'),
        ('meals', 'Meals provided while on duty'),
        ('transport', 'Transport / fare support where necessary'),
    ]

    # Extra helper fields (not stored directly; used to build text)
    extra_responsibilities = forms.MultipleChoiceField(
        label="Pick common responsibilities",
        required=False,
        choices=RESPONSIBILITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    extra_qualifications = forms.MultipleChoiceField(
        label="Preferred qualifications",
        required=False,
        choices=QUALIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    tools_provided = forms.MultipleChoiceField(
        label="Tools / benefits you will provide",
        required=False,
        choices=TOOLS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'responsibilities', 'requirements',
            'salary', 'city', 'location', 'job_type', 'experience_level'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'responsibilities': forms.Textarea(attrs={'rows': 2}),
            'requirements': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_class = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'
        checkbox_fields = {'extra_responsibilities', 'extra_qualifications', 'tools_provided'}

        for field_name, field in self.fields.items():
            if field_name in checkbox_fields:
                # Use simpler styling for checkbox groups
                field.widget.attrs.update({'class': 'space-y-2'})
                field.required = False
                continue

            field.widget.attrs.update({'class': common_class})
            if field_name == 'description':
                field.widget.attrs['placeholder'] = 'Briefly describe your household and what you need help with...'
            elif field_name == 'responsibilities':
                field.widget.attrs['placeholder'] = 'Optional: add any extra responsibilities not covered above.'
            elif field_name == 'requirements':
                field.widget.attrs['placeholder'] = 'Optional: add any extra requirements or clarifications.'

            # location can stay optional; the rest of the core job fields should be filled
            if field_name == 'location':
                field.required = False

        # Guide salary into a sensible Kenyan range
        if 'salary' in self.fields:
            self.fields['salary'].widget.attrs.update({
                'min': 5000,
                'max': 50000,
                'step': 500,
                'placeholder': 'e.g. 15000 (KES per month)',
            })
            self.fields['salary'].help_text = 'Monthly salary in KES (recommended range KSh 5,000 – 50,000).'

        # Make city / town label clearer
        if 'city' in self.fields:
            self.fields['city'].label = 'City / Town'
            self.fields['city'].help_text = 'Choose the nearest major town or city.'

    def save(self, commit=True):
        """
        On new jobs, fold the picked responsibilities / qualifications / tools
        into the free-text responsibilities and requirements to save typing.
        """
        job = super().save(commit=False)

        # Only auto-build text when creating a new job
        is_new = not self.instance.pk
        if is_new and self.is_valid():
            resp_selected = self.cleaned_data.get('extra_responsibilities') or []
            qual_selected = self.cleaned_data.get('extra_qualifications') or []
            tools_selected = self.cleaned_data.get('tools_provided') or []

            resp_map = dict(self.RESPONSIBILITY_CHOICES)
            qual_map = dict(self.QUALIFICATION_CHOICES)
            tools_map = dict(self.TOOLS_CHOICES)

            # Build responsibilities block
            resp_blocks = []
            if job.responsibilities:
                resp_blocks.append(job.responsibilities.strip())
            if resp_selected:
                resp_blocks.append(
                    "Key responsibilities:\n" +
                    "\n".join(f"- {resp_map[val]}" for val in resp_selected)
                )
            if resp_blocks:
                job.responsibilities = "\n\n".join(resp_blocks)

            # Build requirements block
            req_blocks = []
            if job.requirements:
                req_blocks.append(job.requirements.strip())
            if qual_selected:
                req_blocks.append(
                    "Qualifications:\n" +
                    "\n".join(f"- {qual_map[val]}" for val in qual_selected)
                )
            if tools_selected:
                req_blocks.append(
                    "Tools / benefits provided:\n" +
                    "\n".join(f"- {tools_map[val]}" for val in tools_selected)
                )
            if req_blocks:
                job.requirements = "\n\n".join(req_blocks)

        if commit:
            job.save()
        return job


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume', 'experience', 'availability', 'preferred_hours', 'additional_notes']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 6}),
            'additional_notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_class = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'
        for field in self.fields.values():
            field.widget.attrs.update({'class': common_class})

class JobSearchForm(forms.Form):
    keyword = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search jobs...'}))
    city = forms.ChoiceField(
        required=False,
        choices=[('', 'Any city / town')] + list(Job.CITY_CHOICES),
    )
    salary_min = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min Salary'}))
    job_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any job type')] + list(Job.JOB_TYPE_CHOICES),
    )
    experience_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Any experience level')] + list(Job.EXPERIENCE_LEVEL_CHOICES),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_class = 'w-full px-4 py-3 rounded-lg border border-pink-300 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 bg-white transition'
        for field in self.fields.values():
            field.widget.attrs.update({'class': common_class})