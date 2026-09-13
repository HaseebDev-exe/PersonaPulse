"""Presets for PersonaPulse - realistic multi-platform customer reviews.

Each review is a dict with 'text' and 'source' (platform metadata), so the
RAG audit trail can display per-quote data badges.
"""

PRESETS_DATA = {
    "F&B / Restaurant": [
        {
            "text": "Ordered a chicken burger and fries, delivery took 50 minutes and fries were cold. Taste was good but delivery bohat late thi, very disappointed.",
            "source": "Trustpilot - Verified Buyer",
        },
        {
            "text": "Price thora zyada laga for the family deal, Rs. 2500 for 2 burgers and drinks? Packaging was neat though, boxes were sealed and clean.",
            "source": "Google Customer Review",
        },
        {
            "text": "Packaging bilkul kharab thi, burger box was crushed and sauce leaked everywhere. Food was fresh but presentation ruined the experience.",
            "source": "Reddit Discussion",
        },
        {
            "text": "Late-night biryani order arrived in 25 minutes, still steaming hot. Rider was polite and the raita cups were sealed tight. Isi service ki wajah se loyal customer ban gaya hoon.",
            "source": "Trustpilot - Verified Buyer",
        },
    ],
    "B2B SaaS / Software": [
        {
            "text": "The dashboard is clean and onboarding was smooth, but seat limits on the starter plan are too strict. We hit 5 seats in week one and had to upgrade, pricing feels steep for small teams.",
            "source": "G2 Software Review",
        },
        {
            "text": "Support response is fast and API docs are solid. Lekin per-user pricing samajh nahi aayi, $29 per seat per month is too much for our Pakistan-based team.",
            "source": "Capterra Review",
        },
        {
            "text": "We love the automation features, but the renewal increased 40% without warning. Seat management bhi confusing hai, inactive users still count towards billing.",
            "source": "G2 Software Review",
        },
        {
            "text": "Switched from a competitor and migration took one afternoon. The free tier is generous, though SSO sirf enterprise plan mein hai which pushed our upgrade decision.",
            "source": "Reddit Discussion",
        },
    ],
    "E-Commerce / Fashion Store": [
        {
            "text": "Ordered a kurti size M, delivery in 3 days to Lahore which was quick. Fabric quality is excellent but return window sirf 7 days ka hai, thora short hai.",
            "source": "Trustpilot - Verified Buyer",
        },
        {
            "text": "Packaging was premium, box with ribbon and thank you card, very impressive. Lekin price zyada hai compared to local markets, 4500 for a simple shirt is too high.",
            "source": "Google Customer Review",
        },
        {
            "text": "Size chart was misleading, shoes tight nikle. Return process was smooth though, refund mil gaya in 5 days. Delivery charges bhi reasonable thay, overall mixed experience.",
            "source": "Reddit Discussion",
        },
        {
            "text": "Cash on delivery available and parcel arrived a day early. Winter jacket ki stitching top-notch hai, I have already recommended this store to my cousins.",
            "source": "Trustpilot - Verified Buyer",
        },
    ],
    "Logistics / Delivery": [
        {
            "text": "Parcel from Karachi to Islamabad took 6 days instead of the promised 2. Tracking stuck on 'in transit' for 4 days, customer support ne koi clear jawab nahi diya.",
            "source": "Google Customer Review",
        },
        {
            "text": "Same-day delivery within Lahore actually works. Courier called before arriving and handled the fragile box carefully. Pricing thori high hai but reliability worth it.",
            "source": "Trustpilot - Verified Buyer",
        },
        {
            "text": "My package was marked delivered but never arrived. Claim process took 3 weeks and refund sirf shipping charges ka mila, item price ka nahi. Avoid for valuables.",
            "source": "Reddit Discussion",
        },
        {
            "text": "COD remittance settled in 48 hours straight to our bank. Dashboard shows per-city delivery rates, though rural areas mein delays common hain during sales season.",
            "source": "G2 Software Review",
        },
    ],
    "Health Apps / Fitness": [
        {
            "text": "The workout plans adapt nicely and calorie tracking is accurate. Lekin premium subscription auto-renewed without a reminder, Rs. 1800 cut gaya unexpectedly.",
            "source": "App Store Review",
        },
        {
            "text": "Sleep tracking matches my smartwatch data and the diet charts are practical for desi food. Free version mein ads bohat zyada hain, every second screen is an upsell.",
            "source": "Google Customer Review",
        },
        {
            "text": "Cancelled my subscription but the app kept showing premium features for a week, then locked everything mid-program. Refund policy unclear hai, support just sends template replies.",
            "source": "Reddit Discussion",
        },
        {
            "text": "Lost 4kg in two months following the guided plans. Coach check-ins feel personal and the Urdu exercise videos are a nice touch for my mother who also uses it.",
            "source": "App Store Review",
        },
    ],
}


def get_preset_categories():
    """Return list of available preset industry categories."""
    return list(PRESETS_DATA.keys())


def get_preset_sources():
    """Return sorted list of all platform sources across presets."""
    return sorted({r["source"] for reviews in PRESETS_DATA.values() for r in reviews})
