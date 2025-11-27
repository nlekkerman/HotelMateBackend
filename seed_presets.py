"""
Seed presets for the public page builder.
Run this script after migrations to populate the Preset table with default presets.

Usage:
    python seed_presets.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Preset


def seed_presets():
    """Create all default presets for sections, cards, images, news blocks, footers, and page themes."""
    
    presets_data = [
        # ============================================================================
        # HERO SECTION PRESETS
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'hero',
            'key': 'hero_classic_centered',
            'name': 'Classic Centered Hero',
            'description': 'Traditional centered hero with large title, subtitle, and centered CTA button',
            'is_default': True,
            'config': {
                'layout': 'centered',
                'text_alignment': 'center',
                'image_position': 'background',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'hero',
            'key': 'hero_split_image_left',
            'name': 'Split Layout - Image Left',
            'description': 'Split layout with image on left, text content on right',
            'is_default': False,
            'config': {
                'layout': 'split',
                'image_position': 'left',
                'text_alignment': 'left',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'hero',
            'key': 'hero_image_background',
            'name': 'Full Background Image',
            'description': 'Full-width background image with overlay and centered text',
            'is_default': False,
            'config': {
                'layout': 'fullwidth',
                'image_position': 'background',
                'overlay': True,
                'text_alignment': 'center',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'hero',
            'key': 'hero_minimal',
            'name': 'Minimal Hero',
            'description': 'Clean minimal design with small title and subtle background',
            'is_default': False,
            'config': {
                'layout': 'minimal',
                'text_alignment': 'center',
                'image_position': 'none',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'hero',
            'key': 'hero_left_text_floating',
            'name': 'Floating Text Left',
            'description': 'Text content floating on left side with background image',
            'is_default': False,
            'config': {
                'layout': 'floating',
                'text_alignment': 'left',
                'image_position': 'background',
            }
        },
        
        # ============================================================================
        # GALLERY SECTION PRESETS
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'gallery',
            'key': 'gallery_grid',
            'name': 'Grid Gallery',
            'description': 'Clean grid layout with equal-sized images',
            'is_default': True,
            'config': {
                'layout': 'grid',
                'columns': 3,
                'gap': 'medium',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'gallery',
            'key': 'gallery_masonry',
            'name': 'Masonry Gallery',
            'description': 'Pinterest-style masonry layout with varying heights',
            'is_default': False,
            'config': {
                'layout': 'masonry',
                'columns': 3,
                'gap': 'small',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'gallery',
            'key': 'gallery_slider',
            'name': 'Slider Gallery',
            'description': 'Horizontal slider/carousel for browsing images',
            'is_default': False,
            'config': {
                'layout': 'slider',
                'autoplay': True,
                'show_dots': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'gallery',
            'key': 'gallery_collage',
            'name': 'Collage Gallery',
            'description': 'Artistic collage layout with featured large images',
            'is_default': False,
            'config': {
                'layout': 'collage',
                'featured_count': 2,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'gallery',
            'key': 'gallery_tiled',
            'name': 'Tiled Gallery',
            'description': 'Compact tiled layout with no gaps',
            'is_default': False,
            'config': {
                'layout': 'tiled',
                'columns': 4,
                'gap': 'none',
            }
        },
        
        # ============================================================================
        # LIST SECTION PRESETS (for cards)
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'list',
            'key': 'list_3_column',
            'name': '3-Column Grid',
            'description': 'Three equal-width columns for cards',
            'is_default': True,
            'config': {
                'layout': 'grid',
                'columns': 3,
                'gap': 'large',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'list',
            'key': 'list_vertical',
            'name': 'Vertical Stack',
            'description': 'Single column stacked layout',
            'is_default': False,
            'config': {
                'layout': 'vertical',
                'columns': 1,
                'gap': 'medium',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'list',
            'key': 'list_two_column_alt',
            'name': '2-Column Alternating',
            'description': 'Two columns with alternating image positions',
            'is_default': False,
            'config': {
                'layout': 'alternating',
                'columns': 2,
                'gap': 'large',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'list',
            'key': 'list_horizontal_scroll',
            'name': 'Horizontal Scroll',
            'description': 'Scrollable horizontal layout for browsing cards',
            'is_default': False,
            'config': {
                'layout': 'horizontal_scroll',
                'card_width': 'medium',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'list',
            'key': 'list_timeline',
            'name': 'Timeline Layout',
            'description': 'Vertical timeline with cards on alternating sides',
            'is_default': False,
            'config': {
                'layout': 'timeline',
                'show_line': True,
            }
        },
        
        # ============================================================================
        # NEWS SECTION PRESETS
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'news',
            'key': 'news_grid',
            'name': 'News Grid',
            'description': 'Grid layout for news articles',
            'is_default': True,
            'config': {
                'layout': 'grid',
                'columns': 3,
                'show_date': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'news',
            'key': 'news_featured',
            'name': 'Featured News',
            'description': 'Large featured article with smaller articles below',
            'is_default': False,
            'config': {
                'layout': 'featured',
                'featured_count': 1,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'news',
            'key': 'news_magazine',
            'name': 'Magazine Layout',
            'description': 'Magazine-style layout with varied card sizes',
            'is_default': False,
            'config': {
                'layout': 'magazine',
                'show_excerpt': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'news',
            'key': 'news_list',
            'name': 'News List',
            'description': 'Simple list view for news articles',
            'is_default': False,
            'config': {
                'layout': 'list',
                'show_thumbnail': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'news',
            'key': 'news_cards',
            'name': 'News Cards',
            'description': 'Card-based layout with shadows and hover effects',
            'is_default': False,
            'config': {
                'layout': 'cards',
                'columns': 2,
                'show_cta': True,
            }
        },
        
        # ============================================================================
        # ROOMS SECTION PRESETS
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'rooms',
            'key': 'rooms_grid_3col',
            'name': 'Rooms Grid - 3 Columns',
            'description': 'Classic 3-column grid layout for room types',
            'is_default': True,
            'config': {
                'layout': 'grid',
                'columns': 3,
                'gap': 'large',
                'show_price': True,
                'show_amenities': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'rooms',
            'key': 'rooms_grid_2col',
            'name': 'Rooms Grid - 2 Columns',
            'description': 'Wider 2-column grid for larger room cards',
            'is_default': False,
            'config': {
                'layout': 'grid',
                'columns': 2,
                'gap': 'large',
                'show_price': True,
                'show_amenities': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'rooms',
            'key': 'rooms_list',
            'name': 'Rooms List',
            'description': 'Vertical list layout with image beside text',
            'is_default': False,
            'config': {
                'layout': 'list',
                'image_position': 'left',
                'show_price': True,
                'show_amenities': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'rooms',
            'key': 'rooms_carousel',
            'name': 'Rooms Carousel',
            'description': 'Horizontal scrolling carousel of room cards',
            'is_default': False,
            'config': {
                'layout': 'carousel',
                'autoplay': False,
                'show_dots': True,
                'show_price': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'rooms',
            'key': 'rooms_luxury',
            'name': 'Luxury Display',
            'description': 'Premium layout with large images and elegant spacing',
            'is_default': False,
            'config': {
                'layout': 'luxury',
                'columns': 2,
                'gap': 'extra_large',
                'show_price': True,
                'show_amenities': True,
                'hover_effect': 'zoom',
            }
        },
        
        # ============================================================================
        # FOOTER SECTION PRESETS
        # ============================================================================
        {
            'target_type': 'section',
            'section_type': 'footer',
            'key': 'footer_minimal',
            'name': 'Minimal Footer',
            'description': 'Simple footer with contact info and social links',
            'is_default': True,
            'config': {
                'layout': 'minimal',
                'columns': 1,
                'show_social': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'footer',
            'key': 'footer_three_column',
            'name': '3-Column Footer',
            'description': 'Three-column footer with links and info',
            'is_default': False,
            'config': {
                'layout': 'three_column',
                'columns': 3,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'footer',
            'key': 'footer_split',
            'name': 'Split Footer',
            'description': 'Split layout with logo/info on left, links on right',
            'is_default': False,
            'config': {
                'layout': 'split',
                'show_logo': True,
            }
        },
        {
            'target_type': 'section',
            'section_type': 'footer',
            'key': 'footer_dark',
            'name': 'Dark Footer',
            'description': 'Dark background footer with light text',
            'is_default': False,
            'config': {
                'layout': 'dark',
                'theme': 'dark',
            }
        },
        {
            'target_type': 'section',
            'section_type': 'footer',
            'key': 'footer_cta',
            'name': 'Footer with CTA',
            'description': 'Footer with prominent call-to-action section',
            'is_default': False,
            'config': {
                'layout': 'cta',
                'show_cta': True,
            }
        },
        
        # ============================================================================
        # CARD STYLE PRESETS
        # ============================================================================
        {
            'target_type': 'card',
            'section_type': None,
            'key': 'card_image_top',
            'name': 'Image on Top',
            'description': 'Classic card with image above text content',
            'is_default': True,
            'config': {
                'image_position': 'top',
                'text_alignment': 'left',
                'show_shadow': True,
            }
        },
        {
            'target_type': 'card',
            'section_type': None,
            'key': 'card_text_only',
            'name': 'Text Only',
            'description': 'No image, text content only',
            'is_default': False,
            'config': {
                'image_position': 'none',
                'text_alignment': 'center',
                'border': True,
            }
        },
        {
            'target_type': 'card',
            'section_type': None,
            'key': 'card_with_icon',
            'name': 'With Icon',
            'description': 'Icon-based card with centered content',
            'is_default': False,
            'config': {
                'show_icon': True,
                'text_alignment': 'center',
                'icon_position': 'top',
            }
        },
        {
            'target_type': 'card',
            'section_type': None,
            'key': 'card_price_badge',
            'name': 'With Price Badge',
            'description': 'Card with prominent price badge overlay',
            'is_default': False,
            'config': {
                'show_badge': True,
                'badge_position': 'top-right',
            }
        },
        {
            'target_type': 'card',
            'section_type': None,
            'key': 'card_shadow_big',
            'name': 'Large Shadow',
            'description': 'Card with prominent shadow and hover effect',
            'is_default': False,
            'config': {
                'show_shadow': True,
                'shadow_size': 'large',
                'hover_effect': 'lift',
            }
        },
        
        # ============================================================================
        # ROOM CARD PRESETS (for rooms section)
        # ============================================================================
        {
            'target_type': 'room_card',
            'section_type': None,
            'key': 'room_card_standard',
            'name': 'Standard Room Card',
            'description': 'Classic room card with image, details, and booking button',
            'is_default': True,
            'config': {
                'image_height': '250px',
                'show_occupancy': True,
                'show_bed_setup': True,
                'show_description': True,
                'show_price': True,
                'show_badge': True,
                'button_style': 'primary',
                'hover_effect': 'lift',
            }
        },
        {
            'target_type': 'room_card',
            'section_type': None,
            'key': 'room_card_compact',
            'name': 'Compact Room Card',
            'description': 'Compact card with less details, good for mobile',
            'is_default': False,
            'config': {
                'image_height': '200px',
                'show_occupancy': True,
                'show_bed_setup': False,
                'show_description': False,
                'show_price': True,
                'show_badge': False,
                'button_style': 'outline',
                'hover_effect': 'none',
            }
        },
        {
            'target_type': 'room_card',
            'section_type': None,
            'key': 'room_card_luxury',
            'name': 'Luxury Room Card',
            'description': 'Premium card with large image and detailed information',
            'is_default': False,
            'config': {
                'image_height': '350px',
                'show_occupancy': True,
                'show_bed_setup': True,
                'show_description': True,
                'show_price': True,
                'show_badge': True,
                'button_style': 'primary',
                'hover_effect': 'zoom',
                'border': True,
                'shadow': 'large',
            }
        },
        {
            'target_type': 'room_card',
            'section_type': None,
            'key': 'room_card_minimal',
            'name': 'Minimal Room Card',
            'description': 'Clean minimal design with essential info only',
            'is_default': False,
            'config': {
                'image_height': '300px',
                'show_occupancy': False,
                'show_bed_setup': False,
                'show_description': True,
                'show_price': True,
                'show_badge': False,
                'button_style': 'text',
                'hover_effect': 'opacity',
            }
        },
        {
            'target_type': 'room_card',
            'section_type': None,
            'key': 'room_card_horizontal',
            'name': 'Horizontal Room Card',
            'description': 'Wide horizontal layout with image on left',
            'is_default': False,
            'config': {
                'layout': 'horizontal',
                'image_width': '40%',
                'show_occupancy': True,
                'show_bed_setup': True,
                'show_description': True,
                'show_price': True,
                'show_badge': True,
                'button_style': 'primary',
            }
        },
        
        # ============================================================================
        # SECTION HEADER PRESETS
        # ============================================================================
        {
            'target_type': 'section_header',
            'section_type': None,
            'key': 'header_centered',
            'name': 'Centered Header',
            'description': 'Centered title and subtitle',
            'is_default': True,
            'config': {
                'text_alignment': 'center',
                'title_size': 'large',
                'show_subtitle': True,
                'show_divider': False,
                'margin_bottom': 'large',
            }
        },
        {
            'target_type': 'section_header',
            'section_type': None,
            'key': 'header_left',
            'name': 'Left Aligned Header',
            'description': 'Left-aligned title with subtitle',
            'is_default': False,
            'config': {
                'text_alignment': 'left',
                'title_size': 'large',
                'show_subtitle': True,
                'show_divider': False,
                'margin_bottom': 'medium',
            }
        },
        {
            'target_type': 'section_header',
            'section_type': None,
            'key': 'header_with_divider',
            'name': 'Header with Divider',
            'description': 'Centered header with decorative bottom line',
            'is_default': False,
            'config': {
                'text_alignment': 'center',
                'title_size': 'large',
                'show_subtitle': True,
                'show_divider': True,
                'divider_style': 'solid',
                'margin_bottom': 'large',
            }
        },
        {
            'target_type': 'section_header',
            'section_type': None,
            'key': 'header_minimal',
            'name': 'Minimal Header',
            'description': 'Simple title without subtitle',
            'is_default': False,
            'config': {
                'text_alignment': 'center',
                'title_size': 'medium',
                'show_subtitle': False,
                'show_divider': False,
                'margin_bottom': 'small',
            }
        },
        {
            'target_type': 'section_header',
            'section_type': None,
            'key': 'header_luxury',
            'name': 'Luxury Header',
            'description': 'Elegant header with decorative elements',
            'is_default': False,
            'config': {
                'text_alignment': 'center',
                'title_size': 'extra_large',
                'show_subtitle': True,
                'show_divider': True,
                'divider_style': 'decorative',
                'font_style': 'serif',
                'margin_bottom': 'extra_large',
            }
        },
        
        # ============================================================================
        # IMAGE PRESETS (for gallery images, generic image styles)
        # ============================================================================
        {
            'target_type': 'image',
            'section_type': None,
            'key': 'img_rounded',
            'name': 'Rounded Corners',
            'description': 'Image with rounded corners',
            'is_default': True,
            'config': {
                'border_radius': 'medium',
                'hover_effect': 'zoom',
            }
        },
        {
            'target_type': 'image',
            'section_type': None,
            'key': 'img_polaroid',
            'name': 'Polaroid Style',
            'description': 'Polaroid-style image with white border and shadow',
            'is_default': False,
            'config': {
                'border': True,
                'border_color': 'white',
                'padding': 'medium',
                'show_shadow': True,
            }
        },
        {
            'target_type': 'image',
            'section_type': None,
            'key': 'img_circle',
            'name': 'Circular Image',
            'description': 'Image cropped to circle shape',
            'is_default': False,
            'config': {
                'shape': 'circle',
                'aspect_ratio': '1:1',
            }
        },
        {
            'target_type': 'image',
            'section_type': None,
            'key': 'img_shadowed',
            'name': 'With Shadow',
            'description': 'Image with drop shadow',
            'is_default': False,
            'config': {
                'show_shadow': True,
                'shadow_size': 'medium',
            }
        },
        {
            'target_type': 'image',
            'section_type': None,
            'key': 'img_borderless',
            'name': 'No Border',
            'description': 'Clean image with no styling',
            'is_default': False,
            'config': {
                'border': False,
                'border_radius': 'none',
                'show_shadow': False,
            }
        },
        
        # ============================================================================
        # NEWS BLOCK PRESETS
        # ============================================================================
        {
            'target_type': 'news_block',
            'section_type': None,
            'key': 'news_simple',
            'name': 'Simple Block',
            'description': 'Clean simple block style',
            'is_default': True,
            'config': {
                'padding': 'medium',
                'text_alignment': 'left',
            }
        },
        {
            'target_type': 'news_block',
            'section_type': None,
            'key': 'news_featured',
            'name': 'Featured Block',
            'description': 'Highlighted featured block with background',
            'is_default': False,
            'config': {
                'background': True,
                'padding': 'large',
                'border': True,
            }
        },
        {
            'target_type': 'news_block',
            'section_type': None,
            'key': 'news_compact',
            'name': 'Compact Block',
            'description': 'Compact spacing for dense content',
            'is_default': False,
            'config': {
                'padding': 'small',
                'font_size': 'small',
            }
        },
        {
            'target_type': 'news_block',
            'section_type': None,
            'key': 'news_banner',
            'name': 'Banner Block',
            'description': 'Full-width banner style block',
            'is_default': False,
            'config': {
                'width': 'full',
                'background': True,
            }
        },
        {
            'target_type': 'news_block',
            'section_type': None,
            'key': 'news_highlight',
            'name': 'Highlight Block',
            'description': 'Block with colored background highlight',
            'is_default': False,
            'config': {
                'background': True,
                'background_color': 'accent',
                'padding': 'medium',
            }
        },
        
        # ============================================================================
        # PAGE THEME PRESETS
        # ============================================================================
        {
            'target_type': 'page_theme',
            'section_type': None,
            'key': 'theme_modern_gold',
            'name': 'Modern Gold',
            'description': 'Modern luxury theme with gold accents',
            'is_default': True,
            'config': {
                'primary_color': '#d4af37',
                'secondary_color': '#2c3e50',
                'font_family': 'sans-serif',
            }
        },
        {
            'target_type': 'page_theme',
            'section_type': None,
            'key': 'theme_modern_blue',
            'name': 'Modern Blue',
            'description': 'Clean modern theme with blue tones',
            'is_default': False,
            'config': {
                'primary_color': '#3498db',
                'secondary_color': '#2c3e50',
                'font_family': 'sans-serif',
            }
        },
        {
            'target_type': 'page_theme',
            'section_type': None,
            'key': 'theme_minimal',
            'name': 'Minimal',
            'description': 'Clean minimal black and white theme',
            'is_default': False,
            'config': {
                'primary_color': '#000000',
                'secondary_color': '#ffffff',
                'font_family': 'serif',
            }
        },
        {
            'target_type': 'page_theme',
            'section_type': None,
            'key': 'theme_luxury_dark',
            'name': 'Luxury Dark',
            'description': 'Dark elegant theme for luxury brands',
            'is_default': False,
            'config': {
                'primary_color': '#1a1a1a',
                'secondary_color': '#d4af37',
                'font_family': 'serif',
                'mode': 'dark',
            }
        },
        {
            'target_type': 'page_theme',
            'section_type': None,
            'key': 'theme_nature_forest',
            'name': 'Nature Forest',
            'description': 'Natural earth tones with green accents',
            'is_default': False,
            'config': {
                'primary_color': '#27ae60',
                'secondary_color': '#8b4513',
                'font_family': 'sans-serif',
            }
        },
    ]
    
    # Create presets
    created_count = 0
    updated_count = 0
    
    for preset_data in presets_data:
        preset, created = Preset.objects.update_or_create(
            key=preset_data['key'],
            defaults={
                'target_type': preset_data['target_type'],
                'section_type': preset_data['section_type'],
                'name': preset_data['name'],
                'description': preset_data['description'],
                'is_default': preset_data['is_default'],
                'config': preset_data['config'],
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created preset: {preset.name} ({preset.key})")
        else:
            updated_count += 1
            print(f"↻ Updated preset: {preset.name} ({preset.key})")
    
    print(f"\n{'='*60}")
    print(f"Preset seeding complete!")
    print(f"Created: {created_count} presets")
    print(f"Updated: {updated_count} presets")
    print(f"Total: {created_count + updated_count} presets")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Starting preset seeding...\n")
    seed_presets()
