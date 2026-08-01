from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='styled_list')
def styled_list(value):
    """
    Detects lines starting with *, -, or • and converts them into
    modern, icon-based HTML lists using Tailwind.
    """
    if not value:
        return ""

    lines = value.split('\n')
    output = []
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for bullet indicators
        if line.startswith(('*', '-', '•')):
            if not in_list:
                output.append('<ul class="mt-4 space-y-3">')
                in_list = True
            
            # Clean the line of the bullet character
            content = re.sub(r'^[*\-•]\s*', '', line)
            
            # Add styled list item with SVG icon
            item_html = (
                f'<li class="flex items-start gap-3 group">'
                f'  <div class="flex-shrink-0 w-5 h-5 rounded-full bg-pink-50 flex items-center justify-center text-pink-500 mt-0.5 group-hover:bg-pink-100 transition shadow-sm">'
                f'    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                f'      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />'
                f'    </svg>'
                f'  </div>'
                f'  <span class="text-gray-700 leading-tight">{content}</span>'
                f'</li>'
            )
            output.append(item_html)
        else:
            if in_list:
                output.append('</ul>')
                in_list = False
            output.append(f'<p class="text-gray-600 leading-relaxed mt-2">{line}</p>')

    if in_list:
        output.append('</ul>')

    return mark_safe('\n'.join(output))
