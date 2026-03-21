import os
from dotenv import load_dotenv

# Load .env from project root (one level up from broll_bot/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Claude Code settings
CLAUDE_CODE_PATH = "claude"
CLAUDE_MAX_TOKENS = 16384

# YouTube settings
YOUTUBE_RESULTS_PER_QUERY = 5
MAX_TRANSCRIPT_LENGTH = 50000
MIN_VIEW_COUNT = 1000
MAX_SHORT_DURATION = 60  # seconds; videos <= this are considered Shorts
COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'www.youtube.com_cookies.txt')

# Image settings
MIN_IMAGE_WIDTH = 1280
MIN_IMAGE_HEIGHT = 720
MAX_IMAGES_PER_QUERY = 5

# Quality thresholds
QUALITY_THRESHOLDS = {
    "min_broll_unique_sources": 60,
    "target_broll_unique_sources": 80,
    "min_still_images": 45,
    "target_still_images": 60,
    "min_custom_visuals": 1,
    "max_custom_visuals": 3,
    "max_gap_percentage": 5.0,
    "max_stock_footage_percentage": 10.0,
    "min_coverage_percentage": 90.0,
    "target_coverage_percentage": 98.0,
    "min_avg_relevance_score": 6.0,
    "max_era_mismatch_count": 0,
    "min_broll_per_minute": 8.0,
    "min_images_per_minute": 6.0,
}

MAX_ITERATIONS = 3
ITERATION_STRATEGY = "targeted"
