# Certification Courses - Quick Setup Guide

## Courses Added

| # | Course Title | Price (KES) | Status |
|---|---|---|---|
| 1 | Professional Domestic Service Standards | **FREE** | ✓ |
| 2 | Childcare Assistant Certification | 1,500 | ✓ |
| 3 | Elderly Care Support Certification | 1,500 | ✓ |
| 4 | Home Care & Kitchen Essentials Certification | 1,800 | ✓ |
| 5 | Household Appliance Safety and Maintenance | 1,200 | ✓ |
| 6 | Garments and Laundry Care Certification | **700** | ✓ |

---

## How to Add Courses to Database

### Option 1: Using Django Management Command (Recommended)

```bash
python manage.py add_certification_courses
```

This is the cleanest and most Django-friendly way.

### Option 2: Using Django Shell

```bash
python manage.py shell < add_courses.py
```

---

## Course Details

### 1. Professional Domestic Service Standards (FREE)
- **Price:** KES 0
- **Duration:** 1-2 weeks
- **Description:** Master essential skills for professional domestic service including workplace boundaries, communication, and hygiene standards.
- **Features:** Professional standards, Workplace ethics, Communication skills, Hygiene protocols
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d7153-c37e-740c-955f-f5a5f84f694e/about

### 2. Childcare Assistant Certification
- **Price:** KES 1,500
- **Duration:** 2-3 weeks
- **Description:** Comprehensive training for childcare assistance including infant safety, early development, and childcare best practices.
- **Features:** Infant care, Child safety, Development milestones, Play & learning
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d7153-c37f-7363-b5d2-e22a2cd57f4a/about

### 3. Elderly Care Support Certification
- **Price:** KES 1,500
- **Duration:** 2-3 weeks
- **Description:** Training for providing compassionate and professional elderly care, including health monitoring and personal care assistance.
- **Features:** Elderly care basics, Health monitoring, Personal care, Mobility assistance
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d7153-c399-70cf-8afa-9ed53f258018/about

### 4. Home Care & Kitchen Essentials Certification
- **Price:** KES 1,800
- **Duration:** 2-3 weeks
- **Description:** Master home care management and kitchen essentials including food safety, nutrition, and kitchen organization.
- **Features:** Home management, Food safety, Nutrition, Kitchen organization
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d7153-c399-7a98-a651-3528c3666af5/about

### 5. Household Appliance Safety and Maintenance
- **Price:** KES 1,200
- **Duration:** 1-2 weeks
- **Description:** Essential training on safely using and maintaining household appliances including troubleshooting common issues.
- **Features:** Appliance safety, Maintenance tips, Troubleshooting, Energy efficiency
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d9df0-38f9-7ccd-a446-ee2e274982ff/about

### 6. Garments and Laundry Care Certification
- **Price:** KES 700
- **Duration:** 1-2 weeks
- **Description:** Complete training on garment care, laundry management, stain removal, and fabric handling for professional results.
- **Features:** Laundry basics, Stain removal, Fabric care, Garment storage
- **Platform:** Coursebox.ai
- **URL:** https://my.coursebox.ai/courses/019d7153-c40d-7258-a87d-31b5bd9360a1/about

---

## Modifying Prices

If you need to adjust prices, you can:

### Option 1: Django Admin Panel
1. Go to `/admin/courses/course/`
2. Click on the course you want to edit
3. Update the `price` field
4. Click Save

### Option 2: Direct Database Update
```python
python manage.py shell

from courses.models import Course

# Update a specific course
course = Course.objects.get(title='Childcare Assistant Certification')
course.price = 2000  # New price in KES
course.save()
```

### Option 3: Bulk Update Script
Edit `add_courses.py` and update the prices in the `courses_data` list, then run it again.

---

## Verification

After adding courses, verify they were added correctly:

```python
python manage.py shell

from courses.models import Course

# View all courses
for course in Course.objects.all():
    print(f"{course.title}: KES {course.price}")
```

---

## Frontend Integration

The courses are now available at:
- **Courses page:** `/courses/`
- **Individual course:** `/courses/<course-id>/`
- **Checkout:** `/payments/checkout/<plan-id>/`

Students can:
1. View course descriptions
2. See course pricing
3. Enroll and pay (except the free course)
4. Access iframe content from Coursebox.ai
5. Track completion and get certificates

---

## Notes

- Course 1 is marked as **FREE** (`is_free=True`) and has no price
- Courses 2-5 have placeholder prices - adjust as needed
- Course 6 is set to **700 KES** as specified
- All courses use embedded iframes from Coursebox.ai
- Students need to be logged in to access courses
- Payment is required for all paid courses before access

---

## Troubleshooting

### Courses not appearing in frontend?
- Run migrations: `python manage.py migrate`
- Clear cache: `python manage.py clear_cache`
- Restart Django server

### Iframe not loading?
- Verify the URL is correct in the admin panel
- Check browser console for mixed content warnings (HTTPS required)
- Ensure Coursebox.ai is accessible from your deployment environment

### Payment issues?
- Verify M-Pesa integration is working
- Check payment gateway logs
- Ensure course prices are set correctly

---

**Created:** April 18, 2026
**Total Courses:** 6
**Total Revenue Potential:** KES 7,100 (excluding free course)
