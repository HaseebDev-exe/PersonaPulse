"""Presets for PersonaPulse - realistic customer reviews across 3 industries."""

PRESETS_DATA = {
    "Fast Food / Restaurant": [
        "Ordered a chicken burger and fries, delivery took 50 minutes and fries were cold. Taste was good but delivery bohat late thi, very disappointed.",
        "Price thora zyada laga for the family deal, Rs. 2500 for 2 burgers and drinks? Packaging was neat though, boxes were sealed and clean.",
        "Packaging bilkul kharab thi, burger box was crushed and sauce leaked everywhere. Food was fresh but presentation ruined the experience.",
    ],
    "B2B SaaS / Software": [
        "The dashboard is clean and onboarding was smooth, but seat limits on the starter plan are too strict. We hit 5 seats in week one and had to upgrade, pricing feels steep for small teams.",
        "Support response is fast and API docs are solid. Lekin per-user pricing samajh nahi aayi, $29 per seat per month is too much for our Pakistan-based team.",
        "We love the automation features, but the renewal increased 40% without warning. Seat management bhi confusing hai, inactive users still count towards billing.",
    ],
    "E-Commerce / Fashion Store": [
        "Ordered a kurti size M, delivery in 3 days to Lahore which was quick. Fabric quality is excellent but return window sirf 7 days ka hai, thora short hai.",
        "Packaging was premium, box with ribbon and thank you card, very impressive. Lekin price zyada hai compared to local markets, 4500 for a simple shirt is too high.",
        "Size chart was misleading, shoes tight nikle. Return process was smooth though, refund mil gaya in 5 days. Delivery charges bhi reasonable thay, overall mixed experience.",
    ]
}


def get_preset_categories():
    """Return list of available preset industry categories."""
    return list(PRESETS_DATA.keys())
