from user_agents import parse as ua_parse


def parse_user_agent(ua_string: str | None) -> dict:
    if not ua_string:
        return {"device_type": "Unknown", "browser": "Unknown", "os": "Unknown"}
    ua = ua_parse(ua_string)
    if ua.is_mobile:
        device = "Mobile"
    elif ua.is_tablet:
        device = "Tablet"
    elif ua.is_pc:
        device = "Desktop"
    else:
        device = "Other"
    return {
        "device_type": device,
        "browser": str(ua.browser.family),
        "os": str(ua.os.family),
    }


def get_referrer_source(referrer: str | None) -> str:
    if not referrer:
        return "Direct"
    referrer_lower = referrer.lower()
    source_map = {
        "twitter.com": "Twitter",
        "x.com": "Twitter",
        "facebook.com": "Facebook",
        "linkedin.com": "LinkedIn",
        "instagram.com": "Instagram",
        "youtube.com": "YouTube",
        "reddit.com": "Reddit",
        "github.com": "GitHub",
        "google.com": "Google",
        "bing.com": "Bing",
    }
    for domain, name in source_map.items():
        if domain in referrer_lower:
            return name
    return "Other"
