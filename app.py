from flask import Flask, render_template, request, jsonify, session
import os
import uuid
import json
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import colorsys

app = Flask(__name__)
app.secret_key = 'glowmatch-secret-key-2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# ── Product Database ────────────────────────────────────────────────────────────

PRODUCTS = {
    "foundation": [
        {"name": "Soft Matte Long-Wear Foundation", "brand": "NARS", "shades": {"fair-cool": "Deauville", "fair-neutral": "Syracuse", "fair-warm": "Cabiria", "light-cool": "Barcelona", "light-neutral": "Stromboli", "light-warm": "Ceylan", "medium-cool": "Vallauris", "medium-neutral": "Macao", "medium-warm": "Syracuse", "tan-cool": "Maldives", "tan-neutral": "Tahoe", "tan-warm": "Marquises", "deep-cool": "Seychelles", "deep-neutral": "Liberia", "deep-warm": "Benares", "rich-cool": "Namibia", "rich-neutral": "Malawi", "rich-warm": "Nubia"}, "finish": "Matte", "coverage": "Full", "price": 36, "skin_types": ["oily", "combination", "normal"], "link": "https://www.narscosmetics.co.uk"},
        {"name": "Pro Filt'r Soft Matte Foundation", "brand": "Fenty Beauty", "shades": {"fair-cool": "110N", "fair-neutral": "120N", "fair-warm": "130W", "light-cool": "210N", "light-neutral": "220N", "light-warm": "230W", "medium-cool": "310N", "medium-neutral": "330N", "medium-warm": "340W", "tan-cool": "390N", "tan-neutral": "400N", "tan-warm": "420W", "deep-cool": "450N", "deep-neutral": "470N", "deep-warm": "490W", "rich-cool": "498N", "rich-neutral": "499N", "rich-warm": "500W"}, "finish": "Matte", "coverage": "Medium-Full", "price": 34, "skin_types": ["oily", "combination", "normal"], "link": "https://www.fentybeauty.com"},
        {"name": "Luminous Silk Foundation", "brand": "Giorgio Armani", "shades": {"fair-cool": "2", "fair-neutral": "3", "fair-warm": "4", "light-cool": "5", "light-neutral": "5.5", "light-warm": "6", "medium-cool": "7", "medium-neutral": "8", "medium-warm": "8.5", "tan-cool": "9", "tan-neutral": "10", "tan-warm": "10.5", "deep-cool": "11", "deep-neutral": "12", "deep-warm": "13", "rich-cool": "14", "rich-neutral": "15", "rich-warm": "16"}, "finish": "Luminous", "coverage": "Medium", "price": 52, "skin_types": ["dry", "normal", "combination"], "link": "https://www.giorgioarmanibeauty.co.uk"},
        {"name": "Skin Tint SPF 30", "brand": "Charlotte Tilbury", "shades": {"fair-cool": "1 Fair", "fair-neutral": "2 Fair", "fair-warm": "3 Fair", "light-cool": "4 Light", "light-neutral": "5 Light", "light-warm": "6 Light", "medium-cool": "7 Medium", "medium-neutral": "8 Medium", "medium-warm": "9 Medium", "tan-cool": "10 Tan", "tan-neutral": "11 Tan", "tan-warm": "12 Tan", "deep-cool": "13 Deep", "deep-neutral": "14 Deep", "deep-warm": "15 Deep", "rich-cool": "16 Rich", "rich-neutral": "17 Rich", "rich-warm": "18 Rich"}, "finish": "Natural", "coverage": "Light-Medium", "price": 42, "skin_types": ["normal", "dry", "combination"], "link": "https://www.charlottetilbury.com"},
        {"name": "Catrice HD Liquid Coverage Foundation", "brand": "Catrice", "shades": {"fair-cool": "010", "fair-neutral": "020", "fair-warm": "030", "light-cool": "032", "light-neutral": "034", "light-warm": "036", "medium-cool": "038", "medium-neutral": "040", "medium-warm": "042", "tan-cool": "044", "tan-neutral": "046", "tan-warm": "048", "deep-cool": "050", "deep-neutral": "060", "deep-warm": "070", "rich-cool": "080", "rich-neutral": "090", "rich-warm": "100"}, "finish": "Natural", "coverage": "Full", "price": 9, "skin_types": ["oily", "combination", "normal", "dry"], "link": "https://www.catrice.eu"},
        {"name": "Fit Me Matte & Poreless Foundation", "brand": "Maybelline", "shades": {"fair-cool": "102 Fair Ivory", "fair-neutral": "110 Porcelain", "fair-warm": "115 Ivory", "light-cool": "120 Classic Ivory", "light-neutral": "125 Nude Beige", "light-warm": "130 Buff Beige", "medium-cool": "220 Natural Beige", "medium-neutral": "230 Natural Buff", "medium-warm": "235 Pure Beige", "tan-cool": "310 Sun Beige", "tan-neutral": "320 Natural Tan", "tan-warm": "330 Toffee", "deep-cool": "355 Coconut", "deep-neutral": "360 Mocha", "deep-warm": "370 Espresso", "rich-cool": "380 Chestnut", "rich-neutral": "385 Truffle", "rich-warm": "390 Ebony"}, "finish": "Matte", "coverage": "Medium", "price": 10, "skin_types": ["oily", "combination", "normal"], "link": "https://www.boots.com"},
        {"name": "Fit Me Dewy & Smooth Foundation", "brand": "Maybelline", "shades": {"fair-cool": "102 Fair Ivory", "fair-neutral": "110 Porcelain", "fair-warm": "115 Ivory", "light-cool": "120 Classic Ivory", "light-neutral": "125 Nude Beige", "light-warm": "130 Buff Beige", "medium-cool": "220 Natural Beige", "medium-neutral": "230 Natural Buff", "medium-warm": "235 Pure Beige", "tan-cool": "310 Sun Beige", "tan-neutral": "320 Natural Tan", "tan-warm": "330 Toffee", "deep-cool": "355 Coconut", "deep-neutral": "360 Mocha", "deep-warm": "370 Espresso", "rich-cool": "380 Chestnut", "rich-neutral": "385 Truffle", "rich-warm": "390 Ebony"}, "finish": "Dewy", "coverage": "Medium", "price": 10, "skin_types": ["dry", "normal"], "link": "https://www.boots.com"},
        {"name": "True Match Foundation", "brand": "L'Oreal", "shades": {"fair-cool": "1.C Rose Ivory", "fair-neutral": "1.N Ivory", "fair-warm": "1.W Golden Ivory", "light-cool": "2.C Rose Vanilla", "light-neutral": "2.N Vanilla", "light-warm": "2.W Golden Vanilla", "medium-cool": "3.C Rose Beige", "medium-neutral": "3.N Creamy Beige", "medium-warm": "3.W Golden Beige", "tan-cool": "4.C Rose Beige", "tan-neutral": "4.N Beige", "tan-warm": "4.W Natural Gold", "deep-cool": "6.C Rose", "deep-neutral": "6.N Honey", "deep-warm": "6.W Ocher", "rich-cool": "8.C Cappuccino", "rich-neutral": "8.N Cappuccino", "rich-warm": "8.W Chestnut"}, "finish": "Natural", "coverage": "Medium", "price": 11, "skin_types": ["all"], "link": "https://www.boots.com"},
        {"name": "Lasting Perfection Foundation", "brand": "Collection", "shades": {"fair-cool": "1 Fair", "fair-neutral": "2 Ivory", "fair-warm": "3 Warm Ivory", "light-cool": "4 Light", "light-neutral": "5 Medium", "light-warm": "6 Warm Beige", "medium-cool": "7 Natural Beige", "medium-neutral": "8 Sand", "medium-warm": "9 Warm Sand", "tan-cool": "10 Soft Tan", "tan-neutral": "11 Tan", "tan-warm": "12 Warm Tan", "deep-cool": "13 Caramel", "deep-neutral": "14 Deep", "deep-warm": "15 Warm Deep", "rich-cool": "16 Dark", "rich-neutral": "17 Rich", "rich-warm": "18 Warm Rich"}, "finish": "Matte", "coverage": "Full", "price": 6, "skin_types": ["oily", "combination", "normal"], "link": "https://www.boots.com"},
        {"name": "16HR Camo Foundation", "brand": "e.l.f.", "shades": {"fair-cool": "100 W Fair", "fair-neutral": "110 N Fair", "fair-warm": "120 W Fair", "light-cool": "130 C Light", "light-neutral": "140 N Light", "light-warm": "150 W Light", "medium-cool": "160 C Medium", "medium-neutral": "170 N Medium", "medium-warm": "180 W Medium", "tan-cool": "190 C Tan", "tan-neutral": "200 N Tan", "tan-warm": "210 W Tan", "deep-cool": "220 C Deep", "deep-neutral": "230 N Deep", "deep-warm": "240 W Deep", "rich-cool": "250 C Rich", "rich-neutral": "260 N Rich", "rich-warm": "270 W Rich"}, "finish": "Matte", "coverage": "Full", "price": 13, "skin_types": ["oily", "combination", "normal"], "link": "https://www.elfcosmetics.co.uk"},
        {"name": "Infallible 24H Fresh Wear Foundation", "brand": "L'Oreal", "shades": {"fair-cool": "10 Porcelain", "fair-neutral": "15 Porcelain", "fair-warm": "20 Ivory", "light-cool": "100 Linen", "light-neutral": "110 Rose Vanilla", "light-warm": "120 Vanilla", "medium-cool": "130 True Beige", "medium-neutral": "140 Golden Beige", "medium-warm": "150 Beige", "tan-cool": "200 Golden Sand", "tan-neutral": "210 Cappuccino", "tan-warm": "220 Sand", "deep-cool": "230 Honey", "deep-neutral": "240 Amber", "deep-warm": "260 Golden Sun", "rich-cool": "300 Amber", "rich-neutral": "310 Chestnut", "rich-warm": "330 Hazelnut"}, "finish": "Natural", "coverage": "Full", "price": 13, "skin_types": ["all"], "link": "https://www.boots.com"},
        {"name": "Stay Matte Foundation", "brand": "Rimmel", "shades": {"fair-cool": "000 Transparent", "fair-neutral": "010 Light Porcelain", "fair-warm": "100 Ivory", "light-cool": "101 Classic Ivory", "light-neutral": "102 Light Beige", "light-warm": "103 True Ivory", "medium-cool": "200 Soft Beige", "medium-neutral": "201 Classic Beige", "medium-warm": "202 Sundown", "tan-cool": "300 Sand", "tan-neutral": "301 Honey", "tan-warm": "302 True Beige", "deep-cool": "400 Natural Beige", "deep-neutral": "401 Mocha", "deep-warm": "402 Deep Mocha", "rich-cool": "500 Chestnut", "rich-neutral": "600 Warm Caramel", "rich-warm": "700 Soft Black"}, "finish": "Matte", "coverage": "Medium", "price": 7, "skin_types": ["oily", "combination", "normal"], "link": "https://www.superdrug.com"},
        {"name": "Miracle Pure Foundation", "brand": "Rimmel", "shades": {"fair-cool": "010 Light Porcelain", "fair-neutral": "100 Ivory", "fair-warm": "101 True Ivory", "light-cool": "102 Light Beige", "light-neutral": "103 Nude Beige", "light-warm": "104 Warm Ivory", "medium-cool": "200 Soft Beige", "medium-neutral": "201 Classic Beige", "medium-warm": "202 Warm Beige", "tan-cool": "300 Sand", "tan-neutral": "301 Honey", "tan-warm": "302 Natural Beige", "deep-cool": "400 Mocha", "deep-neutral": "401 Deep Mocha", "deep-warm": "402 Caramel", "rich-cool": "500 Chestnut", "rich-neutral": "600 Caramel", "rich-warm": "601 Dark Caramel"}, "finish": "Natural", "coverage": "Medium", "price": 10, "skin_types": ["all"], "link": "https://www.superdrug.com"},
        {"name": "Revolution Conceal & Define Full Coverage Foundation", "brand": "Revolution", "shades": {"fair-cool": "F0.5", "fair-neutral": "F1", "fair-warm": "F1.5", "light-cool": "F2", "light-neutral": "F3", "light-warm": "F4", "medium-cool": "F5", "medium-neutral": "F6", "medium-warm": "F7", "tan-cool": "F8", "tan-neutral": "F9", "tan-warm": "F10", "deep-cool": "F11", "deep-neutral": "F12", "deep-warm": "F13", "rich-cool": "F14", "rich-neutral": "F15", "rich-warm": "F16"}, "finish": "Natural", "coverage": "Full", "price": 8, "skin_types": ["all"], "link": "https://www.makeuprevolution.com"},
    ],
    "concealer": [
        {"name": "Touche Éclat All-Over Brightening Pen", "brand": "YSL", "shades": {"fair-cool": "1", "fair-neutral": "1.5", "fair-warm": "2", "light-cool": "2.5", "light-neutral": "3", "light-warm": "3.5", "medium-cool": "4", "medium-neutral": "4.5", "medium-warm": "5", "tan-cool": "5.5", "tan-neutral": "6", "tan-warm": "6.5", "deep-cool": "7", "deep-neutral": "7.5", "deep-warm": "8", "rich-cool": "8.5", "rich-neutral": "9", "rich-warm": "9.5"}, "coverage": "Light", "price": 33, "skin_types": ["all"], "link": "https://www.yslbeauty.co.uk"},
        {"name": "Shape Tape Full Coverage Concealer", "brand": "Tarte", "shades": {"fair-cool": "8S Fair", "fair-neutral": "12N Fair", "fair-warm": "16W Fair", "light-cool": "20S Light", "light-neutral": "22N Light", "light-warm": "24W Light", "medium-cool": "29S Medium", "medium-neutral": "32N Medium", "medium-warm": "35W Medium", "tan-cool": "42S Tan", "tan-neutral": "44N Tan", "tan-warm": "46W Tan", "deep-cool": "53S Deep", "deep-neutral": "55N Deep", "deep-warm": "57W Deep", "rich-cool": "63S Rich", "rich-neutral": "65N Rich", "rich-warm": "67W Rich"}, "coverage": "Full", "price": 27, "skin_types": ["oily", "combination"], "link": "https://tartecosmetics.com"},
        {"name": "Makeup Revolution Conceal & Define", "brand": "Revolution", "shades": {"fair-cool": "C1", "fair-neutral": "C2", "fair-warm": "C3", "light-cool": "C4", "light-neutral": "C5", "light-warm": "C6", "medium-cool": "C8", "medium-neutral": "C9", "medium-warm": "C10", "tan-cool": "C12", "tan-neutral": "C13", "tan-warm": "C14", "deep-cool": "C15", "deep-neutral": "C16", "deep-warm": "C17", "rich-cool": "C18", "rich-neutral": "C19", "rich-warm": "C20"}, "coverage": "Full", "price": 5, "skin_types": ["all"], "link": "https://www.makeuprevolution.com"},
        {"name": "16HR Camo Concealer", "brand": "e.l.f.", "shades": {"fair-cool": "Fair Ivory", "fair-neutral": "Fair", "fair-warm": "Light Ivory", "light-cool": "Light", "light-neutral": "Light Beige", "light-warm": "Warm Light", "medium-cool": "Medium", "medium-neutral": "Medium Beige", "medium-warm": "Warm Medium", "tan-cool": "Tan", "tan-neutral": "Medium Tan", "tan-warm": "Warm Tan", "deep-cool": "Deep", "deep-neutral": "Deep Caramel", "deep-warm": "Warm Deep", "rich-cool": "Rich Ebony", "rich-neutral": "Rich", "rich-warm": "Warm Rich"}, "coverage": "Full", "price": 8, "skin_types": ["all"], "link": "https://www.elfcosmetics.co.uk"},
        {"name": "Dream Lumi Touch Highlighting Concealer", "brand": "Maybelline", "shades": {"fair-cool": "10 Porcelain", "fair-neutral": "20 Ivory", "fair-warm": "25 Nude", "light-cool": "30 Beige", "light-neutral": "35 Natural", "light-warm": "40 Caramel", "medium-cool": "45 Light Honey", "medium-neutral": "50 Nude Beige", "medium-warm": "55 Buff", "tan-cool": "60 Sand", "tan-neutral": "65 Tan", "tan-warm": "70 Warm Tan", "deep-cool": "75 Cappuccino", "deep-neutral": "80 Toffee", "deep-warm": "85 Caramel", "rich-cool": "90 Mocha", "rich-neutral": "95 Ebony", "rich-warm": "98 Espresso"}, "coverage": "Light-Medium", "price": 9, "skin_types": ["dry", "normal", "combination"], "link": "https://www.maybelline.co.uk"},
        {"name": "Instant Anti-Age Eraser Concealer", "brand": "Maybelline", "shades": {"fair-cool": "05 Ivory", "fair-neutral": "10 Light", "fair-warm": "15 Nude", "light-cool": "20 Sand", "light-neutral": "25 Classic Ivory", "light-warm": "30 Honey", "medium-cool": "35 Buff", "medium-neutral": "40 Caramel", "medium-warm": "45 Warm Beige", "tan-cool": "50 Medium Deep", "tan-neutral": "55 Deep", "tan-warm": "60 Warm Deep", "deep-cool": "70 Dark", "deep-neutral": "75 Deep Toffee", "deep-warm": "80 Deep Caramel", "rich-cool": "85 Dark Mocha", "rich-neutral": "90 Ebony", "rich-warm": "95 Rich Espresso"}, "coverage": "Full", "price": 10, "skin_types": ["all"], "link": "https://www.maybelline.co.uk"},
        {"name": "Catrice Liquid Camouflage Concealer", "brand": "Catrice", "shades": {"fair-cool": "005", "fair-neutral": "010", "fair-warm": "015", "light-cool": "020", "light-neutral": "025", "light-warm": "030", "medium-cool": "035", "medium-neutral": "040", "medium-warm": "045", "tan-cool": "050", "tan-neutral": "055", "tan-warm": "060", "deep-cool": "065", "deep-neutral": "070", "deep-warm": "075", "rich-cool": "080", "rich-neutral": "085", "rich-warm": "090"}, "coverage": "Full", "price": 5, "skin_types": ["all"], "link": "https://www.catrice.eu"},
    ],
    "powder": [
        {"name": "Airbrush Flawless Finish Powder", "brand": "Charlotte Tilbury", "shades": {"fair-cool": "1 Fair", "fair-neutral": "1 Fair", "fair-warm": "2 Light", "light-cool": "2 Light", "light-neutral": "2 Light", "light-warm": "3 Medium", "medium-cool": "3 Medium", "medium-neutral": "3 Medium", "medium-warm": "4 Medium Deep", "tan-cool": "4 Medium Deep", "tan-neutral": "4 Medium Deep", "tan-warm": "5 Deep", "deep-cool": "5 Deep", "deep-neutral": "5 Deep", "deep-warm": "6 Rich", "rich-cool": "6 Rich", "rich-neutral": "6 Rich", "rich-warm": "6 Rich"}, "price": 37, "skin_types": ["all"], "link": "https://www.charlottetilbury.com"},
        {"name": "Banana Powder", "brand": "Ben Nye", "shades": {"fair-cool": "Banana", "fair-neutral": "Banana", "fair-warm": "Banana", "light-cool": "Banana", "light-neutral": "Banana", "light-warm": "Banana", "medium-cool": "Medium", "medium-neutral": "Medium", "medium-warm": "Medium", "tan-cool": "Buff", "tan-neutral": "Buff", "tan-warm": "Buff", "deep-cool": "Chestnut", "deep-neutral": "Chestnut", "deep-warm": "Chestnut", "rich-cool": "Dark", "rich-neutral": "Dark", "rich-warm": "Dark"}, "price": 14, "skin_types": ["all"], "link": "https://www.bennye.com"},
        {"name": "Loose Baking Powder", "brand": "e.l.f.", "shades": {"fair-cool": "Porcelain", "fair-neutral": "Porcelain", "fair-warm": "Nude", "light-cool": "Nude", "light-neutral": "Nude", "light-warm": "Buff", "medium-cool": "Buff", "medium-neutral": "Buff", "medium-warm": "Warm", "tan-cool": "Warm", "tan-neutral": "Warm", "tan-warm": "Medium Tan", "deep-cool": "Deep", "deep-neutral": "Deep", "deep-warm": "Espresso", "rich-cool": "Espresso", "rich-neutral": "Espresso", "rich-warm": "Espresso"}, "price": 8, "skin_types": ["all"], "link": "https://www.elfcosmetics.co.uk"},
        {"name": "Stay Matte Pressed Powder", "brand": "Rimmel", "shades": {"fair-cool": "001 Transparent", "fair-neutral": "002 Pink Blossom", "fair-warm": "003 Peach", "light-cool": "004 Sandstorm", "light-neutral": "005 Silky Beige", "light-warm": "006 Sun Beige", "medium-cool": "007 Natural", "medium-neutral": "008 Cashmere", "medium-warm": "009 Amber", "tan-cool": "010 Warm Tan", "tan-neutral": "011 Tawny", "tan-warm": "012 Honey", "deep-cool": "013 Chestnut", "deep-neutral": "014 Deep Bronze", "deep-warm": "015 Walnut", "rich-cool": "016 Ebony", "rich-neutral": "017 Rich Dark", "rich-warm": "018 Espresso"}, "price": 5, "skin_types": ["oily", "combination", "normal"], "link": "https://www.rimmel.com"},
        {"name": "Revolution Bake & Blot Powder", "brand": "Revolution", "shades": {"fair-cool": "Translucent", "fair-neutral": "Translucent", "fair-warm": "Banana", "light-cool": "Banana", "light-neutral": "Banana", "light-warm": "Vanilla", "medium-cool": "Vanilla", "medium-neutral": "Vanilla", "medium-warm": "Caramel", "tan-cool": "Caramel", "tan-neutral": "Caramel", "tan-warm": "Toffee", "deep-cool": "Toffee", "deep-neutral": "Chocolate", "deep-warm": "Chocolate", "rich-cool": "Dark Chocolate", "rich-neutral": "Dark Chocolate", "rich-warm": "Dark Chocolate"}, "price": 5, "skin_types": ["all"], "link": "https://www.makeuprevolution.com"},
    ]
}

MAKEUP_STYLES = {
    "warm": {
        "recommended_styles": ["Golden Hour Glam", "Terracotta Goddess", "Bronze Sunset"],
        "colour_palette": ["terracotta", "burnt orange", "warm gold", "copper", "caramel brown"],
        "avoid": ["cool pinks", "blue-toned reds", "silver"],
        "lip_colours": ["warm coral", "brick red", "nude peach", "burnt sienna"],
        "blush": ["peach", "warm apricot", "terracotta"],
        "eyeshadow": ["warm browns", "gold", "bronze", "copper", "rust"],
        "highlighter": ["gold", "bronze", "champagne"],
        "description": "Your warm undertone means golden, peachy and earthy tones will make your complexion glow. Lean into bronzes, coppers and terracottas."
    },
    "cool": {
        "recommended_styles": ["Soft Glam", "Berry Romantic", "Cool Editorial"],
        "colour_palette": ["rose pink", "mauve", "berry", "cool taupe", "icy lilac"],
        "avoid": ["orange", "warm yellows", "bronze"],
        "lip_colours": ["cool berry", "raspberry", "plum", "rose pink", "deep wine"],
        "blush": ["cool pink", "rose", "berry", "mauve"],
        "eyeshadow": ["cool taupes", "silver", "grey", "mauve", "plum"],
        "highlighter": ["silver", "pearl", "icy pink"],
        "description": "Your cool undertone is beautifully complemented by rosy pinks, berries and cool mauves. Silver jewellery tones and blue-based hues are your best friends."
    },
    "neutral": {
        "recommended_styles": ["Effortless No-Makeup Makeup", "Classic Elegance", "Versatile Everyday"],
        "colour_palette": ["soft rose", "warm nude", "dusty pink", "taupe", "soft caramel"],
        "avoid": ["extreme cool or warm tones"],
        "lip_colours": ["your natural lip colour +1", "MLBB (my lips but better)", "soft rose", "warm nude"],
        "blush": ["soft peach-pink", "rose beige", "dusty rose"],
        "eyeshadow": ["neutral taupes", "champagne", "soft browns", "rosy mauve"],
        "highlighter": ["champagne", "rose gold"],
        "description": "Lucky you — neutral undertones suit both warm and cool palettes. You have incredible versatility. Focus on MLBB (My Lips But Better) tones and your natural skin tone as a guide."
    },
    "olive": {
        "recommended_styles": ["Mediterranean Glow", "Earthy Luxe", "Sun-Kissed Radiance"],
        "colour_palette": ["warm olive", "earthy green", "gold", "burnt sienna", "deep plum"],
        "avoid": ["anything too ashy", "cool greys", "stark whites"],
        "lip_colours": ["terracotta", "warm red", "deep nude", "plum-brown"],
        "blush": ["warm peach", "soft coral", "earthy rose"],
        "eyeshadow": ["warm greens", "gold", "bronze", "deep browns", "earthy tones"],
        "highlighter": ["gold", "warm bronze", "green-gold"],
        "description": "Olive undertones carry beautiful green and golden hues. Rich earthy tones, warm golds and deep jewel tones complement your complexion magnificently."
    }
}

SKIN_TYPE_TIPS = {
    "oily": {
        "tip": "Look for oil-free, non-comedogenic and mattifying formulas. Water-based products are your best friend.",
        "finish": "Matte",
        "avoid": "Heavy oil-based products, thick creams"
    },
    "dry": {
        "tip": "Prioritise hydrating, moisturising formulas. Oil-based and serum foundations add a beautiful glow.",
        "finish": "Dewy or Luminous",
        "avoid": "Matte, powder-heavy formulas which can cling to dry patches"
    },
    "combination": {
        "tip": "Use a water-based foundation for the T-zone and a slightly more hydrating product on drier areas.",
        "finish": "Natural / Satin",
        "avoid": "Heavy oils on the T-zone"
    },
    "normal": {
        "tip": "You have the most flexibility — nearly any formula works. Focus on the finish you prefer.",
        "finish": "Any",
        "avoid": "Nothing specific — experiment!"
    },
    "sensitive": {
        "tip": "Choose fragrance-free, hypoallergenic and mineral formulas. Always patch test new products.",
        "finish": "Natural",
        "avoid": "Fragranced products, heavy silicones"
    },
    "acne-prone": {
        "tip": "Look strictly for non-comedogenic labels. Avoid dimethicone and cyclomethicone. Salicylic acid in makeup can help.",
        "finish": "Matte or Natural",
        "avoid": "Silicone-heavy products, comedogenic ingredients like coconut oil"
    }
}

# ── Helper Functions ─────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))


def analyse_skin_tone(image_path):
    """
    Analyses the dominant skin tone in the uploaded image using K-Means clustering.
    Samples the centre region of the image (most likely to be face/skin).
    Returns tone category, undertone, hex colour and confidence metrics.
    """
    img = Image.open(image_path).convert('RGB')
    
    # Crop to the centre 40% of the image to focus on facial skin
    w, h = img.size
    left = int(w * 0.3)
    top = int(h * 0.2)
    right = int(w * 0.7)
    bottom = int(h * 0.75)
    img_cropped = img.crop((left, top, right, bottom))
    
    img_array = np.array(img_cropped)
    pixels = img_array.reshape(-1, 3).astype(float)
    
    # Filter out very dark (shadows) and very light (highlights/background) pixels
    brightness = pixels.mean(axis=1)
    skin_pixels = pixels[(brightness > 40) & (brightness < 230)]
    
    if len(skin_pixels) < 100:
        skin_pixels = pixels  # fallback if filtering too aggressive
    
    # K-Means to find dominant colour clusters
    n_clusters = min(5, len(skin_pixels))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(skin_pixels)
    
    # Pick the most represented cluster as the dominant skin tone
    counts = np.bincount(kmeans.labels_)
    dominant_idx = np.argmax(counts)
    dominant_colour = kmeans.cluster_centers_[dominant_idx]
    
    r, g, b = dominant_colour
    hex_colour = rgb_to_hex(r, g, b)
    
    # Determine skin tone depth from luminance
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    
    if luminance > 200:
        tone_depth = "fair"
    elif luminance > 175:
        tone_depth = "light"
    elif luminance > 145:
        tone_depth = "medium"
    elif luminance > 115:
        tone_depth = "tan"
    elif luminance > 80:
        tone_depth = "deep"
    else:
        tone_depth = "rich"
    
    # Determine undertone using colour channel ratios
    # Warm: high R relative to B, yellowish
    # Cool: high B relative to R, pinkish
    # Olive: green channel prominent relative to red/blue balance
    # Neutral: balanced
    
    r_b_diff = r - b
    g_balance = g - (r + b) / 2
    
    if g_balance > 8:
        undertone = "olive"
    elif r_b_diff > 30:
        undertone = "warm"
    elif r_b_diff < 10:
        undertone = "cool"
    else:
        undertone = "neutral"
    
    # Convert to HSV for additional insight
    h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    hue_degrees = h_val * 360
    
    tone_key = f"{tone_depth}-{undertone}"
    
    return {
        "hex_colour": hex_colour,
        "rgb": {"r": int(r), "g": int(g), "b": int(b)},
        "tone_depth": tone_depth,
        "undertone": undertone,
        "tone_key": tone_key,
        "luminance": round(luminance, 1),
        "hue": round(hue_degrees, 1),
        "saturation": round(s_val * 100, 1)
    }


def get_recommendations(tone_key, skin_type, budget_max=None, preferred_brands=None):
    """
    Generates personalised product recommendations based on skin tone key and skin type.
    Skin type filtering only applies to foundations. Concealers and powders show all products.
    Optionally filters by budget and brand.
    """
    recommendations = {}
    
    for category, products in PRODUCTS.items():
        matched = []
        for product in products:
            # Budget filter
            if budget_max and product['price'] > budget_max:
                continue
            
            # Brand filter
            if preferred_brands and product['brand'].lower() not in [b.lower() for b in preferred_brands]:
                continue
            
            # Skin type compatibility — only strictly filter foundations
            compatible = ('all' in product.get('skin_types', ['all']) or 
                         skin_type in product.get('skin_types', ['all']))
            
            # Get the shade for this tone
            shade = product.get('shades', {}).get(tone_key)
            if not shade:
                # Try fallback to nearest tone depth
                depth = tone_key.split('-')[0]
                shade = next((v for k, v in product.get('shades', {}).items() 
                             if k.startswith(depth)), "Ask in-store")
            
            matched.append({
                "name": product['name'],
                "brand": product['brand'],
                "recommended_shade": shade,
                "price": product['price'],
                "finish": product.get('finish', 'N/A'),
                "coverage": product.get('coverage', 'N/A'),
                "link": product.get('link', '#'),
                "skin_compatible": compatible,
                "skin_type_note": "" if compatible else "Check compatibility with your skin type"
            })
        
        # Sort: compatible first, then by price
        matched.sort(key=lambda x: (not x['skin_compatible'], x['price']))
        recommendations[category] = matched
    
    return recommendations


# ── Routes ───────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyse', methods=['POST'])
def analyse():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    skin_type = request.form.get('skin_type', 'normal')
    budget = request.form.get('budget', None)
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a JPG, PNG or WEBP image.'}), 400
    
    # Save with unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    # Store filename in session for deletion
    if 'uploaded_files' not in session:
        session['uploaded_files'] = []
    session['uploaded_files'] = session.get('uploaded_files', []) + [unique_filename]
    session.modified = True
    
    try:
        # Run skin tone analysis
        analysis = analyse_skin_tone(file_path)
        tone_key = analysis['tone_key']
        
        # Get product recommendations
        budget_max = int(budget) if budget and budget.isdigit() else None
        recommendations = get_recommendations(tone_key, skin_type, budget_max)
        
        # Get makeup style suggestions
        undertone = analysis['undertone']
        style_guide = MAKEUP_STYLES.get(undertone, MAKEUP_STYLES['neutral'])
        
        # Skin type tips
        skin_tips = SKIN_TYPE_TIPS.get(skin_type, SKIN_TYPE_TIPS['normal'])
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'analysis': analysis,
            'recommendations': recommendations,
            'style_guide': style_guide,
            'skin_tips': skin_tips,
            'skin_type': skin_type
        })
    
    except Exception as e:
        # Clean up file if analysis fails
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/delete-data', methods=['POST'])
def delete_data():
    """
    Permanently deletes all uploaded images for this session.
    Satisfies FR5 and NFR4 (user privacy and data deletion).
    """
    deleted_count = 0
    uploaded_files = session.get('uploaded_files', [])
    
    for filename in uploaded_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_count += 1
    
    session['uploaded_files'] = []
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': f'{deleted_count} image(s) permanently deleted from our system.',
        'deleted_count': deleted_count
    })


@app.route('/delete-single', methods=['POST'])
def delete_single():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    # Security: only allow deletion of files belonging to this session
    session_files = session.get('uploaded_files', [])
    if filename not in session_files:
        return jsonify({'error': 'Unauthorised'}), 403
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    updated = [f for f in session_files if f != filename]
    session['uploaded_files'] = updated
    session.modified = True
    
    return jsonify({'success': True, 'message': 'Image deleted successfully.'})


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)