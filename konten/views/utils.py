def generate_profile_link(platform, username):
    # Bersihkan untuk URL (hilangkan @ jika ada di awal)
    clean_username = username.strip()
    if clean_username.startswith('@'):
        clean_username = clean_username[1:] # Buang karakter pertama (@)
    
    if platform == 'INSTAGRAM':
        return f"https://www.instagram.com/{clean_username}/"
    elif platform == 'TIKTOK':
        return f"https://www.tiktok.com/@{clean_username}"
    elif platform == 'FACEBOOK':
        return f"https://www.facebook.com/{clean_username}"
    elif platform == 'TWITTER':
        return f"https://twitter.com/{clean_username}"
    elif platform == 'YOUTUBE':
        return f"https://www.youtube.com/@{clean_username}"
    return f"#{clean_username}"
